from __future__ import annotations

from math import sqrt

from .models import ConfigModel, DesignCode


def r1_min_thickness(component: str, thickness_mm: float, config: ConfigModel) -> bool:
    min_thk = float(config.min_thickness_mm.get(component, 0))
    return thickness_mm + 1e-9 >= min_thk


def r2_max_bt_flange(width_mm: float, thickness_mm: float, code: DesignCode | str, config: ConfigModel) -> bool:
    if thickness_mm <= 0:
        return False
    key = code.value if hasattr(code, "value") else str(code)
    limit = float(config.max_bt.get(key, 12.0))
    return (width_mm / thickness_mm) <= limit + 1e-9


def r3_depth_in_range(value_mm: int, min_mm: int, max_mm: int) -> bool:
    return min_mm <= value_mm <= max_mm


def apply_feature(flag: str, config: ConfigModel) -> bool:
    return bool(config.features.get(flag, True))


# --- Section classification helpers (simplified) ---

def check_flange_classification_IS(b_outstand_mm: float, tf_mm: float, fy_mpa: float) -> str:
    if tf_mm <= 0:
        return "Invalid"
    eps = sqrt(250.0 / max(fy_mpa, 1.0))
    ratio = b_outstand_mm / tf_mm
    if ratio <= 9.4 * eps:
        return "Plastic"
    if ratio <= 10.5 * eps:
        return "Compact"
    if ratio <= 15.7 * eps:
        return "Semi-compact"
    return "Slender"


def check_web_classification_IS(d_mm: float, tw_mm: float, fy_mpa: float) -> str:
    if tw_mm <= 0:
        return "Invalid"
    eps = sqrt(250.0 / max(fy_mpa, 1.0))
    ratio = d_mm / tw_mm
    if ratio <= 200.0 * eps:
        return "Compact"  # treat within limit as compact for now
    return "Slender"


def check_flange_classification_AISC(bf_mm: float, tf_mm: float, fy_mpa: float, e_mpa: float) -> str:
    if tf_mm <= 0:
        return "Invalid"
    # AISC uses bf/2tf for outstand; compare to 0.38*sqrt(E/fy) for compactness baseline
    lam = (bf_mm / 2.0) / tf_mm
    lam_p = 0.38 * sqrt(e_mpa / max(fy_mpa, 1.0))
    return "Compact" if lam <= lam_p else "Slender"


def check_web_classification_AISC(h_mm: float, tw_mm: float, fy_mpa: float, e_mpa: float) -> str:
    if tw_mm <= 0:
        return "Invalid"
    lam = h_mm / tw_mm
    lam_p = 3.76 * sqrt(e_mpa / max(fy_mpa, 1.0))
    return "Compact" if lam <= lam_p else "Slender"

