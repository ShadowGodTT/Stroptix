from __future__ import annotations

from pathlib import Path

from stroptix.config import load_config
from stroptix.io_excel import read_input
from stroptix.library import load_library
from stroptix.mapping import depth_range_mm, quantize_depth
from stroptix.rules import apply_feature, r1_min_thickness, r2_max_bt_flange, r3_depth_in_range


def main() -> int:
    input_path = Path("str_optix_starter_pack/input_template.xlsx")
    config_path = Path("str_optix_starter_pack/config.yaml")
    library_path = Path("str_optix_starter_pack/plate_library.xlsx")

    inp = read_input(input_path)
    cfg = load_config(config_path)
    lib = load_library(library_path)

    min_depth_mm, max_depth_mm = depth_range_mm(inp.frame_type, inp.span_m, cfg.depth_mapping)

    total = 0
    fail_r1 = 0
    fail_r2 = 0
    fail_r3 = 0
    pass_all = 0

    for web in lib.webs:
        start_depth = quantize_depth(min_depth_mm, web.depth_step_mm)
        end_depth = quantize_depth(max_depth_mm, web.depth_step_mm)

        for ifl in lib.flanges:
            for ofl in lib.flanges:
                total += 1

                if apply_feature("R1_min_thickness", cfg):
                    if not (r1_min_thickness("web", web.thickness_mm, cfg)
                            and r1_min_thickness("flange", ifl.thickness_mm, cfg)
                            and r1_min_thickness("flange", ofl.thickness_mm, cfg)):
                        fail_r1 += 1
                        continue

                if apply_feature("R2_max_bt", cfg):
                    if not (r2_max_bt_flange(ifl.width_mm, ifl.thickness_mm, inp.design_code, cfg)
                            and r2_max_bt_flange(ofl.width_mm, ofl.thickness_mm, inp.design_code, cfg)):
                        fail_r2 += 1
                        continue

                if apply_feature("R3_depth_range", cfg):
                    if not (r3_depth_in_range(start_depth, min_depth_mm, max_depth_mm)
                            and r3_depth_in_range(end_depth, min_depth_mm, max_depth_mm)):
                        fail_r3 += 1
                        continue

                pass_all += 1

    print("Input frame:", getattr(inp.frame_type, "value", inp.frame_type), "span_m=", inp.span_m)
    print("Depth range (mm):", min_depth_mm, "to", max_depth_mm)
    print("Library: webs=", len(lib.webs), "flanges=", len(lib.flanges))
    print("Feature flags:", cfg.features)
    print("Totals: combos=", total, "pass_all=", pass_all)
    print("Failed R1 (min thickness):", fail_r1)
    print("Failed R2 (flange b/t):", fail_r2)
    print("Failed R3 (depth range):", fail_r3)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


