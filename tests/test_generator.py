from stroptix.generator import compute_weight_kg_per_m
from stroptix.parsing import parse_bay_pattern


def test_compute_weight_positive():
    w = compute_weight_kg_per_m(
        web_thickness_mm=6,
        web_start_depth_mm=600,
        web_end_depth_mm=800,
        if_width_mm=200,
        if_thickness_mm=10,
        of_width_mm=200,
        of_thickness_mm=10,
        density_kg_per_m3=7850,
    )
    assert w > 0


def test_parse_bay_pattern():
    res = parse_bay_pattern("1@7.985+5@7.99+1@7.985")
    assert res.total_bays == 7
    assert res.total_frames == 8
    assert res.total_length_m == 55.92
    assert res.bays_mm[0] == 7985
    assert res.bays_mm[-1] == 7985


