from pathlib import Path

import pandas as pd

from stroptix.config import load_config
from stroptix.generator import GenerationContext, pick_top_per_member
from stroptix.io_excel import read_input, write_output, OUTPUT_SHEET_NAME
from stroptix.library import load_library


def test_end_to_end(tmp_path: Path):
    # Prepare paths
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    input_path = data_dir / "sample_input.xlsx"
    library_path = data_dir / "plate_library.xlsx"
    config_path = data_dir / "config.yaml"
    output_path = tmp_path / "results" / "output.xlsx"

    # Use default bootstrapping by not creating input/library; provide config
    repo_config = Path(__file__).parents[1] / "data" / "config.yaml"
    config_path.write_text(repo_config.read_text(encoding="utf-8"), encoding="utf-8")

    inp = read_input(input_path)
    lib = load_library(library_path)
    cfg = load_config(config_path)

    ctx = GenerationContext(input=inp, config=cfg, library=lib)
    members = pick_top_per_member(ctx, inp.members_count)
    assert len(members) > 0

    write_output(output_path, members)
    assert output_path.exists()

    # Validate output columns
    xl = pd.ExcelFile(output_path)
    df = pd.read_excel(xl, sheet_name=OUTPUT_SHEET_NAME)
    assert "Member id" in df.columns
    assert len(df) == len(members)








