from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class BayPatternResult:
    bays_m: List[float]
    bays_mm: List[int]
    total_bays: int
    total_frames: int
    total_length_m: float


def parse_bay_pattern(expr: str) -> BayPatternResult:
    if not expr or not isinstance(expr, str):
        raise ValueError("Empty bay pattern expression")

    parts = [p.strip() for p in expr.split("+") if p.strip()]
    bays_m: List[float] = []

    for part in parts:
        if "@" not in part:
            raise ValueError(f"Invalid segment '{part}'. Use n@w e.g. 5@7.5")
        count_str, width_str = part.split("@", 1)
        try:
            count = int(count_str)
        except ValueError as e:
            raise ValueError(f"Invalid count in '{part}'") from e
        try:
            width_m = float(width_str)
        except ValueError as e:
            raise ValueError(f"Invalid width in '{part}'") from e
        if count < 0 or width_m <= 0:
            raise ValueError(f"Non-positive values in '{part}'")
        bays_m.extend([width_m] * count)

    bays_mm = [int(round(b * 1000)) for b in bays_m]
    total_bays = len(bays_m)
    total_frames = total_bays + 1
    total_length_m = round(sum(bays_m), 3)

    return BayPatternResult(
        bays_m=bays_m,
        bays_mm=bays_mm,
        total_bays=total_bays,
        total_frames=total_frames,
        total_length_m=total_length_m,
    )
