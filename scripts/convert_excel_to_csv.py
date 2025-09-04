from __future__ import annotations

import sys
from pathlib import Path
import os


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_excel_to_csv.py <excel_path>")
        return 2
    excel_path = Path(sys.argv[1])
    if not excel_path.exists():
        print(f"File not found: {excel_path}")
        return 1

    # Ensure project root is importable
    sys.path.insert(0, os.getcwd())
    import excel_to_csv_logic as mod

    # If MBSConverter.generate_in_file is not implemented, stub it so CSV export still works
    if hasattr(mod, "MBSConverter") and not hasattr(mod.MBSConverter, "generate_in_file"):
        def _gen(self):  # type: ignore[no-redef]
            return None
        setattr(mod.MBSConverter, "generate_in_file", _gen)

    output_csv, _mbs = mod.process_excel_file(str(excel_path))
    print("CSV:", output_csv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


