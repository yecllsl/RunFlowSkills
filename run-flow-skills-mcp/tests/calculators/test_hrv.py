"""HRV 计算单元测试（spec 8.1.8, FR-ANALYZE-04）."""

import pytest

from run_flow_skills_mcp.calculators.hrv import (
    calc_hrv_baseline,
    calc_hrv_deviation_pct,
    calc_pnn50,
    calc_rmssd,
    calc_sdnn,
)


def test_rmssd_normal():
    """RMSSD = sqrt(mean(diff²))."""
    # RR 间隔 [800, 850, 820, 880] ms
    rr = [800.0, 850.0, 820.0, 880.0]
    rmssd = calc_rmssd(rr)
    assert rmssd is not None
    assert rmssd > 0


def test_rmssd_empty_returns_none():
    assert calc_rmssd([]) is None


def test_rmssd_single_value_returns_none():
    """单点无法计算差分."""
    assert calc_rmssd([800.0]) is None


def test_sdnn_normal():
    """SDNN = std(RR)."""
    rr = [800.0, 850.0, 820.0, 880.0]
    sdnn = calc_sdnn(rr)
    assert sdnn is not None
    assert sdnn > 0


def test_sdnn_empty_returns_none():
    assert calc_sdnn([]) is None


def test_pnn50_normal():
    """pNN50 = 占比(|diff|>50ms)."""
    # 差分：60, 40, 70 → 2/3 > 50ms ≈ 66.67%
    rr = [800.0, 860.0, 820.0, 890.0]
    pnn50 = calc_pnn50(rr)
    assert pnn50 is not None
    assert 60 <= pnn50 <= 70  # 约 66.67


def test_pnn50_empty_returns_none():
    assert calc_pnn50([]) is None


def test_hrv_baseline_7day_mean():
    """基线 = 7 天滚动均值（spec 8.1.8）."""
    recent = [40.0, 42.0, 41.0, 43.0, 40.0, 42.0, 44.0]
    baseline = calc_hrv_baseline(recent)
    assert baseline is not None
    assert 41 <= baseline <= 43


def test_hrv_baseline_insufficient_data_returns_none():
    """数据不足 7 天仍可计算（用现有数据均值），但空数据返回 None."""
    assert calc_hrv_baseline([]) is None


def test_hrv_deviation_pct_above_baseline():
    """当前 HRV 高于基线 → 正偏离."""
    dev = calc_hrv_deviation_pct(current_hrv=48.0, baseline=40.0)
    assert dev == pytest.approx(20.0, rel=1e-2)


def test_hrv_deviation_pct_below_baseline():
    """当前 HRV 低于基线 → 负偏离（spec 场景 3.3：HRV 偏低 12ms）."""
    dev = calc_hrv_deviation_pct(current_hrv=38.0, baseline=45.0)
    assert dev == pytest.approx(-15.56, rel=1e-1)


def test_hrv_deviation_pct_zero_baseline_returns_zero():
    """基线为 0 时无法计算，返回 0 避免除零."""
    dev = calc_hrv_deviation_pct(current_hrv=40.0, baseline=0.0)
    assert dev == 0.0
