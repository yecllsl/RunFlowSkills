"""配速区间计算单元测试（spec 8.1.6, FR-PLAN-03）."""
import pytest

from run_flow_skills_mcp.calculators.pace_zones import (
    calc_pace_zones,
    calc_vdot_pace_s_per_km,
    classify_pace_zone,
)


def test_vdot_pace_decreases_as_vdot_increases():
    """VDOT 越高，参考配速越快（秒数越小）."""
    pace_40 = calc_vdot_pace_s_per_km(40.0)
    pace_50 = calc_vdot_pace_s_per_km(50.0)
    assert pace_50 < pace_40


def test_pace_zones_returns_all_five_zones():
    zones = calc_pace_zones(45.0)
    assert set(zones.keys()) == {"E", "M", "T", "I", "R"}
    for zone, (lo, hi) in zones.items():
        assert lo > 0 and hi > 0
        assert lo <= hi, f"{zone} 区间 lo>hi"


def test_pace_zones_e_is_slowest():
    """E 区间最容易（最慢），R 区间最难（最快）."""
    zones = calc_pace_zones(45.0)
    e_lo, _ = zones["E"]
    r_lo, _ = zones["R"]
    assert e_lo > r_lo  # E 配速秒数 > R 配速秒数


def test_classify_pace_zone_easy_pace():
    """5'30"/km 在 VDOT 45 时应归为 E 或 M 区间."""
    pace = 330.0  # 5'30"
    zone = classify_pace_zone(pace, vdot=45.0)
    assert zone in ("E", "M")


def test_classify_pace_zone_threshold_pace():
    """接近阈值配速归为 T."""
    zones = calc_pace_zones(45.0)
    t_mid = (zones["T"][0] + zones["T"][1]) / 2
    zone = classify_pace_zone(t_mid, vdot=45.0)
    assert zone == "T"


def test_classify_pace_zone_interval_pace():
    """间歇配速归为 I 或 R."""
    zones = calc_pace_zones(45.0)
    i_mid = (zones["I"][0] + zones["I"][1]) / 2
    zone = classify_pace_zone(i_mid, vdot=45.0)
    assert zone in ("I", "R")


def test_pace_zones_factors_match_spec():
    """spec 8.1.6: E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110%."""
    zones = calc_pace_zones(45.0)
    vdot_pace = calc_vdot_pace_s_per_km(45.0)
    # E 区间：VDOT 配速 / 0.59 ~ VDOT 配速 / 0.74
    e_lo_expected = vdot_pace / 0.74  # 最快
    e_hi_expected = vdot_pace / 0.59  # 最慢
    assert zones["E"][0] == pytest.approx(e_lo_expected, rel=1e-3)
    assert zones["E"][1] == pytest.approx(e_hi_expected, rel=1e-3)
