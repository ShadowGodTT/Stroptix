from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd


def _norm_frame_type(val: str) -> str:
    if not val:
        return "ClearSpan"
    v = str(val).strip().lower().replace(" ", "")
    if v in {"clearspan", "clear", "clear-span"}:
        return "ClearSpan"
    if v in {"multispan", "multi-span", "multi"}:
        return "MultiSpan"
    if v in {"monoslope", "mono"}:
        return "MonoSlope"
    if v in {"multigable", "multi-gable", "gable"}:
        return "MultiGable"
    return "ClearSpan"


def _norm_code(val: str) -> str:
    s = (val or "").upper()
    if "AISC" in s:
        return "AISC"
    if "IS800" in s or "IS 800" in s or s.strip() == "IS" or s.startswith("IS"):
        return "IS800"
    return "IS800"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/spec_csv_to_input.py <filtered_csv> [out.xlsx]")
        return 2
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 1
    out_xlsx = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results/spec_input.xlsx")
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    # Build a quick lookup dict (first match per parameter)
    param_to_val: dict[str, str] = {}
    for _, r in df.iterrows():
        p = str(r.get("Parameter", "")).strip()
        v = str(r.get("Value", "")).strip()
        if p and p not in param_to_val and v not in {"-", "NA", ""}:
            param_to_val[p] = v

    # Extract fields
    frame_type = _norm_frame_type(param_to_val.get("Building type", "Clear Span"))
    # Prefer Width as span per the UI
    span = param_to_val.get("Width in m (o/o of steel)") or param_to_val.get("Length in m (o/o of steel)") or "30"
    try:
        span_m = float(str(span).split()[0])
    except Exception:
        span_m = 30.0

    eave_h = param_to_val.get("Left eave height in m") or param_to_val.get("Right eave height in m") or "8"
    try:
        eave_height_m = float(str(eave_h).split()[0])
    except Exception:
        eave_height_m = 8.0

    bay_pattern = param_to_val.get("Side wall bay spacing", "")

    design_code = _norm_code(param_to_val.get("Desing code") or param_to_val.get("Design code", "IS800"))

    def _num(pname: str, default: float = 0.0) -> float:
        v = param_to_val.get(pname)
        try:
            return float(str(v).split()[0]) if v is not None else default
        except Exception:
            return default

    dead = _num("Dead Load in kN/m2", 0.1)
    live = _num("Live Load in kN/m2", 0.57)
    coll = _num("Collateral load kN/m2", 0.05)
    wind = _num("Max wind speed in m/s", 39)
    seis = param_to_val.get("Seismic zone  co-efficient (III)", "III (0.16)")
    steel_grade = str(param_to_val.get("Steel material grade (Mpa)") or param_to_val.get("Primary sections grade (Mpa)") or "350")

    # Minimal required fields for our input
    row = {
        "design_code": design_code,
        "frame_type": frame_type,
        "span_m": span_m,
        "eave_height_m": eave_height_m,
        "Side wall bay spacing": bay_pattern,
        "dead_load_kPa": dead,
        "live_load_kPa": live,
        "collateral_kPa": coll,
        "wind_speed_mps": wind,
        "seismic_zone": seis,
        "steel_grade": steel_grade,
        "Members_count": 6,
        # Keep originals for reference
        "Building type": param_to_val.get("Building type", ""),
        "Width in m (o/o of steel)": param_to_val.get("Width in m (o/o of steel)", ""),
        "Right eave height in m": param_to_val.get("Right eave height in m", ""),
        # Keep right end wall spacing as text; numeric column is not required by our model
        "Right end wall bay spacing in m": str(param_to_val.get("Right end wall bay spacing in m", "")),
    }

    # Drop non-numeric right end wall spacing if it looks like a pattern (e.g., 5@6.706)
    rew = row.get("Right end wall bay spacing in m")
    if isinstance(rew, str) and "@" in rew:
        row.pop("Right end wall bay spacing in m", None)

    out_df = pd.DataFrame([row])
    with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
        out_df.to_excel(writer, sheet_name="Input", index=False)
    print("Wrote input Excel:", out_xlsx)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


