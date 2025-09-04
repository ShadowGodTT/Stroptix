from stroptix.models import ConfigModel, DesignCode
from stroptix.rules import r1_min_thickness, r2_max_bt_flange, r3_depth_in_range


def test_r1_min_thickness():
    cfg = ConfigModel()
    assert r1_min_thickness("web", 4.0, cfg)
    assert not r1_min_thickness("web", 3.9, cfg)


def test_r2_bt_limit():
    cfg = ConfigModel(max_bt={"AISC": 12, "IS800": 10})
    assert r2_max_bt_flange(120, 10, DesignCode.AISC, cfg)
    assert not r2_max_bt_flange(130, 10, DesignCode.AISC, cfg)


def test_r3_depth_range():
    assert r3_depth_in_range(500, 300, 1200)
    assert not r3_depth_in_range(200, 300, 1200)








