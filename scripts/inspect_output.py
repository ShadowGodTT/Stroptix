from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


def main() -> int:
    # Optional first argument for path; default to results/output.xlsx
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/output.xlsx")
    if not path.exists():
        print(f"Output not found: {path}")
        return 1

    xl = pd.ExcelFile(path)
    print("Sheets:", xl.sheet_names)
    sheet = "StrOptix Output" if "StrOptix Output" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(xl, sheet_name=sheet)
    print("Sheet used:", sheet)
    print("Columns:", list(df.columns))
    print("Rows:", len(df))
    if len(df) > 0:
        print(df.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


