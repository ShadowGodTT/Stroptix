from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .models import LibraryModel, PlateFlange, PlateWeb


@dataclass
class LibraryPaths:
    web_sheet: str = "web"
    flange_sheet: str = "flange"


def _bootstrap_library_if_missing(library_path: Path) -> None:
    library_path.parent.mkdir(parents=True, exist_ok=True)
    if library_path.exists():
        return

    # Create minimal demo library
    web_df = pd.DataFrame(
        {
            "thickness_mm": [4, 5, 6, 8],
            "depth_step_mm": [50, 50, 50, 50],
        }
    )
    # Choose flange pairs that satisfy b/t <= 12 for AISC (e.g., width/thickness = 10)
    flange_df = pd.DataFrame(
        {
            "width_mm": [120, 140, 160, 180],
            "thickness_mm": [12, 14, 16, 18],
        }
    )
    with pd.ExcelWriter(library_path, engine="xlsxwriter") as writer:
        web_df.to_excel(writer, sheet_name="web", index=False)
        flange_df.to_excel(writer, sheet_name="flange", index=False)


def load_library(path: str | Path) -> LibraryModel:
    p = Path(path)
    _bootstrap_library_if_missing(p)

    xl = pd.ExcelFile(p)
    web_df = pd.read_excel(xl, sheet_name="web")
    flange_df = pd.read_excel(xl, sheet_name="flange")

    webs = [
        PlateWeb(thickness_mm=float(r.thickness_mm), depth_step_mm=int(r.depth_step_mm))
        for r in web_df.itertuples(index=False)
    ]

    flanges = [
        PlateFlange(width_mm=float(r.width_mm), thickness_mm=float(r.thickness_mm))
        for r in flange_df.itertuples(index=False)
    ]
    return LibraryModel(webs=webs, flanges=flanges)
