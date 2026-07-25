"""训练负荷计算单元测试（spec 8.1.2, 8.1.3, 8.1.7）."""

import pytest

from run_flow_skills_mcp.calculators.training_load import (
    calc_atl,
    calc_ctl,
    calc_ewma,
    calc_intensity_factor,
    calc_tsb,
    calc_tss,
)


def test_tss_basic_formula():
    """TSS = duration_s × IF² × 100（spec 8.1.2）."""
    # 60 分钟，IF=1.0 → TSS=100
    assert calc_tss(3600, 1.0) == 100.0
    # 60 分钟，IF=0.85 → TSS=72.25
    assert calc_tss(3600, 0.85) == pytest.approx(72.25, rel=1e-3)


def test_tss_zero_duration():
    assert calc_tss(0, 1.0) == 0.0


def test_ewma_alpha_formula():
    """α = 2/(N+1)，7 天窗口 α=0.25（spec 8.1.7）."""
    # 全 1 输入 → EWMA 全 1
    result = calc_ewma([1.0, 1.0, 1.0], window=3)
    assert result == [1.0, 1.0, 1.0]


def test_ewma_decays_old_values():
    """新值权重高于旧值."""
    result = calc_ewma([0.0, 0.0, 100.0], window=3)
    assert len(result) == 3
    # 第三个值受新值 100 拉高
    assert result[2] > result[1]  # 50.0 > 0.0
    assert result[2] < 100.0  # 但小于最新值


def test_ewma_empty_input():
    assert calc_ewma([], window=7) == []


def test_ctl_uses_42_day_window():
    """spec 8.1.3: CTL = 42 天 EWMA."""
    daily = [10.0] * 42
    ctl = calc_ctl(daily)
    # 42 天稳定值应接近 10
    assert 9.5 <= ctl <= 10.5


def test_atl_uses_7_day_window():
    """spec 8.1.3: ATL = 7 天 EWMA."""
    daily = [10.0] * 7
    atl = calc_atl(daily)
    assert 9.0 <= atl <= 11.0


def test_ctl_atl_respond_differently_to_spike():
    """ATL 对近期 spike 更敏感，CTL 反应平缓."""
    daily = [10.0] * 35 + [200.0] * 7  # 末 7 天 spike
    ctl = calc_ctl(daily)
    atl = calc_atl(daily)
    assert atl > ctl  # ATL 反应更强


def test_tsb_formula():
    """TSB = CTL - ATL（spec 8.1.3）."""
    assert calc_tsb(65.0, 58.0) == 7.0
    assert calc_tsb(50.0, 60.0) == -10.0


def test_intensity_factor_pace_based():
    """IF = threshold_pace / actual_pace（配速越快 IF 越高）."""
    # 阈值配速 5'00"/km（300s），实际 6'00"/km（360s）→ IF=0.833
    if_val = calc_intensity_factor(avg_pace_s_per_km=360.0, threshold_pace_s_per_km=300.0)
    assert if_val == pytest.approx(0.833, rel=1e-2)


def test_intensity_factor_at_threshold():
    """实际配速 = 阈值配速 → IF=1.0."""
    if_val = calc_intensity_factor(avg_pace_s_per_km=300.0, threshold_pace_s_per_km=300.0)
    assert if_val == 1.0
