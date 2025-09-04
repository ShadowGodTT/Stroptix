from __future__ import annotations

from math import floor

from .models import FrameType


def depth_range_mm(
    frame_type: FrameType | str, span_m: float, config: dict
) -> tuple[int, int]:
    key = frame_type.value if hasattr(frame_type, "value") else str(frame_type)
    frame_cfg = config.get(key) or {}
    rule = frame_cfg.get("default", {"min_mm": 300, "max_mm": 1200, "step_mm": 50})

    # Very simple heuristic: widen range a bit for longer spans
    base_min = int(rule.get("min_mm", 300))
    base_max = int(rule.get("max_mm", 1200))
    if span_m > 40:
        base_max = max(base_max, 1400)
    if span_m > 60:
        base_max = max(base_max, 1600)

    return base_min, base_max


def quantize_depth(value_mm: float, step_mm: int) -> int:
    # Round down to nearest step
    return int(step_mm * floor(value_mm / step_mm))


def quantize_depth_nearest(value_mm: float, step_mm: int) -> int:
    if step_mm <= 0:
        return int(round(value_mm))
    return int(round(value_mm / step_mm) * step_mm)


