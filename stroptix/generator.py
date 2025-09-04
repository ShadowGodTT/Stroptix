from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import List, Tuple

from .mapping import depth_range_mm, quantize_depth, quantize_depth_nearest
from .models import (
    ConfigModel,
    InputModel,
    LibraryModel,
    MemberCandidate,
)
from .rules import apply_feature, r1_min_thickness, r2_max_bt_flange, r3_depth_in_range
from .parsing import parse_bay_pattern


@dataclass
class GenerationContext:
    input: InputModel
    config: ConfigModel
    library: LibraryModel


def compute_weight_kg_per_m(
    web_thickness_mm: float,
    web_start_depth_mm: int,
    web_end_depth_mm: int,
    if_width_mm: float,
    if_thickness_mm: float,
    of_width_mm: float,
    of_thickness_mm: float,
    density_kg_per_m3: float,
) -> float:
    # Simplified tapered web area per meter: average depth * thickness
    avg_depth_m = 0.5 * (web_start_depth_mm + web_end_depth_mm) / 1000.0
    web_thickness_m = web_thickness_mm / 1000.0
    web_area_m2 = avg_depth_m * web_thickness_m

    # Two flanges (inside and outside). Assume widths are full-width plates, 1 meter long segment
    if_area_m2 = (if_width_mm / 1000.0) * (if_thickness_mm / 1000.0)
    of_area_m2 = (of_width_mm / 1000.0) * (of_thickness_mm / 1000.0)

    total_area_m2 = web_area_m2 + if_area_m2 + of_area_m2
    return density_kg_per_m3 * total_area_m2


def generate_candidates(ctx: GenerationContext) -> List[MemberCandidate]:
    inp = ctx.input
    cfg = ctx.config
    lib = ctx.library

    # Depth ranges from mapping
    min_depth_mm, max_depth_mm = depth_range_mm(inp.frame_type, inp.span_m, cfg.depth_mapping)

    candidates: List[MemberCandidate] = []

    # Iterate simple combinations; for start/end, we will quantize to each web's depth step within range
    for web, ifl, ofl in product(lib.webs, lib.flanges, lib.flanges):
        # Rule R1: min thickness
        if apply_feature("R1_min_thickness", cfg):
            if not (r1_min_thickness("web", web.thickness_mm, cfg) and
                    r1_min_thickness("flange", ifl.thickness_mm, cfg) and
                    r1_min_thickness("flange", ofl.thickness_mm, cfg)):
                continue

        # Rule R2: flange b/t
        if apply_feature("R2_max_bt", cfg):
            if not (r2_max_bt_flange(ifl.width_mm, ifl.thickness_mm, inp.design_code, cfg) and
                    r2_max_bt_flange(ofl.width_mm, ofl.thickness_mm, inp.design_code, cfg)):
                continue

        # Choose start/end depths by scanning within range on this web's step
        start_depth = quantize_depth_nearest(min_depth_mm, web.depth_step_mm)
        end_depth = quantize_depth_nearest(max_depth_mm, web.depth_step_mm)

        # Enforce R3 depth range
        if apply_feature("R3_depth_range", cfg):
            if not (r3_depth_in_range(start_depth, min_depth_mm, max_depth_mm) and
                    r3_depth_in_range(end_depth, min_depth_mm, max_depth_mm)):
                continue

        weight = compute_weight_kg_per_m(
            web_thickness_mm=web.thickness_mm,
            web_start_depth_mm=start_depth,
            web_end_depth_mm=end_depth,
            if_width_mm=ifl.width_mm,
            if_thickness_mm=ifl.thickness_mm,
            of_width_mm=ofl.width_mm,
            of_thickness_mm=ofl.thickness_mm,
            density_kg_per_m3=cfg.density_kg_per_m3,
        )

        candidate = MemberCandidate(
            member_id="",
            web_start_depth_mm=start_depth,
            web_end_depth_mm=end_depth,
            web_thickness_mm=web.thickness_mm,
            if_width_mm=ifl.width_mm,
            if_thickness_mm=ifl.thickness_mm,
            of_width_mm=ofl.width_mm,
            of_thickness_mm=ofl.thickness_mm,
            weight_kg_per_m=weight,
        )
        candidates.append(candidate)

    # Sort globally by weight and return
    candidates.sort(key=lambda c: c.weight_kg_per_m)
    return candidates


def pick_top_per_member(ctx: GenerationContext, num_members: int) -> List[MemberCandidate]:
    # For Lite version, choose top N overall and assign member ids sequentially
    candidates = generate_candidates(ctx)
    top = candidates[: max(0, num_members)]
    for idx, cand in enumerate(top, start=1):
        cand.member_id = f"M{idx}"
    return top


# New: segmentation and per-segment selection
def _segment_lengths_mm(span_m: float, bay_spacing_m: float | None, side_wall_bay_spacing_expr: str | None) -> List[int]:
    # Prefer pattern if provided; else use uniform bay spacing; else single segment = span
    if side_wall_bay_spacing_expr:
        try:
            res = parse_bay_pattern(side_wall_bay_spacing_expr)
            return res.bays_mm
        except Exception:
            pass
    if bay_spacing_m and bay_spacing_m > 0:
        total_mm = int(round(span_m * 1000))
        bay_mm = int(round(bay_spacing_m * 1000))
        if bay_mm <= 0:
            return [total_mm]
        n_full = total_mm // bay_mm
        rem = total_mm - n_full * bay_mm
        segs = [bay_mm] * int(n_full)
        if rem > 0:
            segs.append(int(rem))
        return segs if segs else [total_mm]
    return [int(round(span_m * 1000))]


def assign_member_segments(span_mm: int, splice_limit_mm: int, cutback_mm: int = 90, bay_segments_mm: List[int] | None = None) -> List[int]:
    """Return segment lengths honoring splice limit and optional bay grid.

    - If bay_segments_mm is provided, cut segments at bay boundaries first, then enforce splice limit.
    - Apply cutback at each internal splice: reduce segments by cutback at both ends, but preserve total span.
    """
    if splice_limit_mm <= 0:
        return [span_mm]

    # Start from bay-aligned segments if provided; else single span
    base = list(bay_segments_mm or [span_mm])
    result: List[int] = []
    for seg in base:
        remaining = seg
        while remaining > splice_limit_mm:
            result.append(splice_limit_mm)
            remaining -= splice_limit_mm
        if remaining > 0:
            result.append(remaining)

    # Apply cutbacks to internal joints (reduce adjacent segments equally where possible)
    if cutback_mm > 0 and len(result) > 1:
        for i in range(len(result) - 1):
            # reduce end of segment i and start of segment i+1 by cutback, but not below 1
            take = min(cutback_mm, max(result[i] - 1, 1), max(result[i + 1] - 1, 1))
            result[i] -= take
            result[i + 1] -= take

    return result


def _best_candidate_for_segment(ctx: GenerationContext) -> MemberCandidate | None:
    inp = ctx.input
    cfg = ctx.config
    lib = ctx.library
    min_depth_mm, max_depth_mm = depth_range_mm(inp.frame_type, inp.span_m, cfg.depth_mapping)

    best: MemberCandidate | None = None
    for web, ifl, ofl in product(lib.webs, lib.flanges, lib.flanges):
        if apply_feature("R1_min_thickness", cfg):
            if not (r1_min_thickness("web", web.thickness_mm, cfg)
                    and r1_min_thickness("flange", ifl.thickness_mm, cfg)
                    and r1_min_thickness("flange", ofl.thickness_mm, cfg)):
                continue

        if apply_feature("R2_max_bt", cfg):
            if not (r2_max_bt_flange(ifl.width_mm, ifl.thickness_mm, inp.design_code, cfg)
                    and r2_max_bt_flange(ofl.width_mm, ofl.thickness_mm, inp.design_code, cfg)):
                continue

        start_depth = quantize_depth_nearest(min_depth_mm, web.depth_step_mm)
        end_depth = quantize_depth_nearest(max_depth_mm, web.depth_step_mm)
        if apply_feature("R3_depth_range", cfg):
            if not (r3_depth_in_range(start_depth, min_depth_mm, max_depth_mm)
                    and r3_depth_in_range(end_depth, min_depth_mm, max_depth_mm)):
                continue

        weight = compute_weight_kg_per_m(
            web_thickness_mm=web.thickness_mm,
            web_start_depth_mm=start_depth,
            web_end_depth_mm=end_depth,
            if_width_mm=ifl.width_mm,
            if_thickness_mm=ifl.thickness_mm,
            of_width_mm=ofl.width_mm,
            of_thickness_mm=ofl.thickness_mm,
            density_kg_per_m3=cfg.density_kg_per_m3,
        )

        cand = MemberCandidate(
            member_id="",
            web_start_depth_mm=start_depth,
            web_end_depth_mm=end_depth,
            web_thickness_mm=web.thickness_mm,
            if_width_mm=ifl.width_mm,
            if_thickness_mm=ifl.thickness_mm,
            of_width_mm=ofl.width_mm,
            of_thickness_mm=ofl.thickness_mm,
            weight_kg_per_m=weight,
        )
        if best is None or cand.weight_kg_per_m < best.weight_kg_per_m:
            best = cand

    return best


def generate_segment_rows(
    ctx: GenerationContext,
    members_count: int,
    mode: str | None = None,
    splice_limit_mm: int | None = None,
    cutback_mm: int = 90,
) -> List[Tuple[str, int, MemberCandidate]]:
    """Return rows per segment: (mark, web_length_mm, candidate).

    mode: "safe" (default) uses bay-spacing segmentation only.
          "cad" enforces splice_limit_mm (default 7000) and uses cutbacks; respects bay boundaries first.
    """
    inp = ctx.input
    bay_segs = _segment_lengths_mm(
        inp.span_m, getattr(inp, "bay_spacing_m", None), getattr(inp, "side_wall_bay_spacing_expr", None)
    )

    total_span_mm = int(round(inp.span_m * 1000))
    if (mode or "safe").lower() == "cad":
        limit = splice_limit_mm if splice_limit_mm and splice_limit_mm > 0 else 7000
        seg_lengths = assign_member_segments(total_span_mm, limit, cutback_mm, bay_segs)
    else:
        seg_lengths = bay_segs

    rows: List[Tuple[str, int, MemberCandidate]] = []
    for m_idx in range(1, max(0, members_count) + 1):
        best = _best_candidate_for_segment(ctx)
        if best is None:
            continue
        for s_idx, seg_len in enumerate(seg_lengths, start=1):
            mark = f"M{m_idx}-{s_idx}"
            rows.append((mark, seg_len, best))
    return rows








