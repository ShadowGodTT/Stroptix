from __future__ import annotations

import logging
from pathlib import Path

import typer

from .config import load_config
from .generator import (
    GenerationContext,
    generate_segment_rows,
)
from .io_excel import read_input, write_output, write_member_table, write_output_template, write_member_table_final, write_member_table_compact, write_output_template_from_rows
from .library import load_library
from .parsing import parse_bay_pattern
from .version import __version__

app = typer.Typer(help="StrOptix Lite CLI")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )


@app.command()
def run(
    input: str = typer.Option(
        "str_optix_final_pack/input_template.xlsx",
        "--input",
        help="Input Excel file",
        show_default=True,
    ),
    library: str = typer.Option(
        "str_optix_final_pack/plate_library.xlsx",
        "--library",
        help="Plate library Excel file",
        show_default=True,
    ),
    config: str = typer.Option(
        "str_optix_final_pack/config.yaml",
        "--config",
        help="YAML config file",
        show_default=True,
    ),
    codelimits: str = typer.Option(
        "str_optix_final_pack/code_limits.json",
        "--codelimits",
        help="JSON file with code limits (IS 800 / AISC 360). Currently unused; reserved for future checks.",
        show_default=True,
    ),
    out: str = typer.Option(
        "results/output.xlsx", "--out", help="Output Excel file", show_default=True
    ),
    mode: str = typer.Option(
        "safe", "--mode", help="Generation mode: safe or cad", show_default=True
    ),
    splicelimit: int = typer.Option(
        7000, "--splicelimit", help="Splice limit in mm (cad mode)", show_default=True
    ),
):
    """Run StrOptix Lite generation pipeline."""
    setup_logging()
    logging.info(f"StrOptix Lite v{__version__}")

    # Resolve and log actual file paths used
    input_path = str(Path(input).resolve())
    library_path = str(Path(library).resolve())
    config_path = str(Path(config).resolve())
    codelimits_path = str(Path(codelimits).resolve())
    out_path = str(Path(out).resolve())

    logging.info("Using input: %s", input_path)
    logging.info("Using library: %s", library_path)
    logging.info("Using config: %s", config_path)
    logging.info("Using code limits: %s", codelimits_path)
    logging.info("Output will be written to: %s", out_path)

    # Fallback to starter pack if final pack files are missing
    def _fallback(p: str, alt: str) -> str:
        return str(Path(p).resolve()) if Path(p).exists() else str(Path(alt).resolve())

    input_path = _fallback(input_path, "str_optix_starter_pack/input_template.xlsx")
    library_path = _fallback(library_path, "str_optix_starter_pack/plate_library.xlsx")
    config_path = _fallback(config_path, "str_optix_starter_pack/config.yaml")

    inp = read_input(input_path)
    cfg = load_config(config_path)
    lib = load_library(library_path)

    # Optional bay pattern logging if provided
    if getattr(inp, "side_wall_bay_spacing_expr", None):
        try:
            bay_res = parse_bay_pattern(inp.side_wall_bay_spacing_expr)  # type: ignore[arg-type]
            logging.info(
                "Side wall bays: %d bays, %d frames, total length=%.3f m",
                bay_res.total_bays,
                bay_res.total_frames,
                bay_res.total_length_m,
            )
        except Exception as e:  # pragma: no cover
            logging.warning("Could not parse bay spacing: %s", e)

    logging.info(
        "Input summary: code=%s, frame=%s, span=%.2f m, members=%d",
        getattr(inp.design_code, "value", inp.design_code),
        getattr(inp.frame_type, "value", inp.frame_type),
        inp.span_m,
        inp.members_count,
    )
    logging.info(
        "Library: %d web variants, %d flange variants", len(lib.webs), len(lib.flanges)
    )

    ctx = GenerationContext(input=inp, config=cfg, library=lib)
    seg_rows = generate_segment_rows(ctx, inp.members_count, mode=mode, splice_limit_mm=splicelimit)

    # Build final member table rows
    rows: list[dict] = []
    for mark, seg_len_mm, cand in seg_rows:
        rows.append({
            "Mark": mark,
            "Web Start Depth (mm)": cand.web_start_depth_mm,
            "Web End Depth (mm)": cand.web_end_depth_mm,
            "Web Thickness (mm)": cand.web_thickness_mm,
            "Web Plate Length (mm)": int(round(seg_len_mm)),
            "Outside Flange Width (mm)": int(round(cand.of_width_mm)),
            "Outside Flange Thickness (mm)": int(round(cand.of_thickness_mm)),
            "Outside Flange Length (mm)": int(round(seg_len_mm)),
            "Inside Flange Width (mm)": int(round(cand.if_width_mm)),
            "Inside Flange Thickness (mm)": int(round(cand.if_thickness_mm)),
            "Inside Flange Length (mm)": int(round(seg_len_mm)),
            "Weight (kg/m)": round(cand.weight_kg_per_m, 2),
            "Status": cand.status,
        })

    write_member_table_final(out_path, rows)
    # Also write compact Member Table for CAD-aligned view
    write_member_table_compact(out_path, rows)
    # And write the grouped header template sheet
    write_output_template_from_rows(out_path, rows)
    logging.info("Wrote output: %s (%d rows)", out_path, len(rows))


@app.callback()
def main():
    pass


if __name__ == "__main__":  # pragma: no cover
    app()


