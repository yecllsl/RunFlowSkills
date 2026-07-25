"""心率区间计算单元测试（spec 8.1.5, FR-IMPORT-06）."""
import pytest

from run_flow_skills_mcp.calculators.hr_zones import (
    calc_hr_zones_boundaries,
    classify_hr_samples,
)


def test_hr_zones_boundaries_5_zones():
    """5 个心率区间 Z1-Z5."""
    boundaries = calc_hr_zones_boundaries(max_hr=200)
    assert set(boundaries.keys()) == {"Z1", "Z2", "Z3", "Z4", "Z5"}
    for zone, (lo, hi) in boundaries.items():
        assert 0 <= lo <= hi <= 200


def test_hr_zones_boundaries_z5_high():
    """Z5 应覆盖 >=90% max_hr."""
    boundaries = calc_hr_zones_boundaries(max_hr=200)
    z5_lo, z5_hi = boundaries["Z5"]
    assert z5_lo == 180  # 90% of 200
    assert z5_hi == 200


def test_hr_zones_boundaries_z1_low():
    """Z1 应覆盖 <50% max_hr."""
    boundaries = calc_hr_zones_boundaries(max_hr=200)
    z1_lo, z1_hi = boundaries["Z1"]
    assert z1_lo == 0
    assert z1_hi == 100  # 50% of 200


def test_classify_hr_samples_distributes_correctly():
    """10 个心率样本，分布在 Z2/Z3 区间."""
    # max_hr=200, Z2=100-120, Z3=120-140, Z4=140-180, Z5=180-200
    samples = [110, 110, 130, 130, 150, 150, 150, 190, 190, 50]
    dist = classify_hr_samples(samples, max_hr=200)
    assert sum(dist.values()) == pytest.approx(1.0, rel=1e-3)
    assert dist["Z2"] == 0.2  # 110×2
    assert dist["Z3"] == 0.2  # 130×2
    assert dist["Z4"] == 0.3  # 150×3
    assert dist["Z5"] == 0.2  # 190×2
    assert dist["Z1"] == 0.1  # 50×1


def test_classify_hr_samples_empty_returns_empty():
    assert classify_hr_samples([], max_hr=200) == {}


def test_classify_hr_samples_uses_default_max_hr_when_zero():
    """max_hr=0 时回退到 constants.DEFAULT_MAX_HR."""
    dist = classify_hr_samples([100], max_hr=0)
    # 不应崩溃，且应基于 DEFAULT_MAX_HR=190 分类
    assert sum(dist.values()) == pytest.approx(1.0, rel=1e-3)
