from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .models import ConfigModel


def _coerce_from_starter_pack(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Translate starter pack config.yaml schema into our ConfigModel dict.

    Starter pack keys (examples):
      app.steel_density_kg_per_m3
      feature_flags.enable_bt_limits, enable_depth_range
      heuristics.frame_type_map.{Frame}.start_depth_min/max, end_depth_min/max
    """
    out: Dict[str, Any] = {}

    # Density
    density = (
        raw.get("density_kg_per_m3")
        or raw.get("app", {}).get("steel_density_kg_per_m3")
    )
    if density:
        out["density_kg_per_m3"] = float(density)

    # Features
    features = {
        "R1_min_thickness": True,  # default on
        "R2_max_bt": True,
        "R3_depth_range": True,
    }
    ff = raw.get("feature_flags") or {}
    if "enable_bt_limits" in ff:
        features["R2_max_bt"] = bool(ff.get("enable_bt_limits"))
    if "enable_depth_range" in ff:
        features["R3_depth_range"] = bool(ff.get("enable_depth_range"))
    out["features"] = features

    # Min thickness (optional in starter pack -> keep defaults if absent)
    if "min_thickness_mm" in raw:
        out["min_thickness_mm"] = dict(raw["min_thickness_mm"])  # type: ignore[arg-type]

    # Max b/t mapping by code (optional)
    if "max_bt" in raw:
        out["max_bt"] = dict(raw["max_bt"])  # type: ignore[arg-type]

    # Depth range mapping derived from heuristics.frame_type_map
    heur = raw.get("heuristics") or {}
    ft_map = heur.get("frame_type_map") or {}
    if ft_map:
        depth_mapping: Dict[str, Any] = {}
        for frame_type, limits in ft_map.items():
            try:
                start_min = float(limits.get("start_depth_min", 0))
                end_min = float(limits.get("end_depth_min", 0))
                start_max = float(limits.get("start_depth_max", 0))
                end_max = float(limits.get("end_depth_max", 0))
            except Exception:
                continue
            # Combine to a single inclusive range
            min_mm = int(min(start_min, end_min))
            max_mm = int(max(start_max, end_max))
            depth_mapping[str(frame_type)] = {
                "default": {"min_mm": min_mm, "max_mm": max_mm, "step_mm": 50}
            }
        if depth_mapping:
            out["depth_mapping"] = depth_mapping

    return out


def load_config(path: str | Path) -> ConfigModel:
    """Load YAML config and return a ConfigModel.

    Supports both the demo schema under data/config.yaml and the starter pack schema
    under str_optix_starter_pack/config.yaml.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f) or {}

    # If it already looks like our schema, pass through
    looks_like_ours = any(k in raw for k in ("density_kg_per_m3", "features", "depth_mapping"))
    if looks_like_ours:
        return ConfigModel(**raw)

    # Otherwise try to coerce from starter pack schema
    coerced = _coerce_from_starter_pack(raw)
    return ConfigModel(**coerced)





