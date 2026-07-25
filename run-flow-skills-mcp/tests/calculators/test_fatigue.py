"""疲劳度评估单元测试（spec FR-ANALYZE-05, FR-COACH-01）."""
from run_flow_skills_mcp.calculators.fatigue import calc_fatigue_score


def test_fatigue_all_normal_returns_low():
    """所有指标正常 → 低风险."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=2.0, tsb=15.0, rpe_trend=[3, 4, 3]
    )
    assert level == "low"
    assert score < 30
    assert len(factors) == 0


def test_fatigue_hrv_low_returns_high():
    """HRV 偏低 15%+ TSB 负值 → 高风险."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=-15.0, tsb=-10.0, rpe_trend=[7, 8, 9]
    )
    assert level == "high"
    assert score >= 70
    assert "hrv_deviation" in factors
    assert "tsb_negative" in factors


def test_fatigue_partial_data_returns_moderate():
    """部分数据缺失仍可评估，但降级."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=-8.0, tsb=None, rpe_trend=None
    )
    assert level in ("moderate", "low")
    assert "hrv_deviation" in factors


def test_fatigue_rpe_trend_rising():
    """RPE 趋势上升 → 风险增加."""
    score1, _, _ = calc_fatigue_score(
        hrv_deviation_pct=0.0, tsb=10.0, rpe_trend=[3, 3, 3]
    )
    score2, _, _ = calc_fatigue_score(
        hrv_deviation_pct=0.0, tsb=10.0, rpe_trend=[5, 7, 9]
    )
    assert score2 > score1


def test_fatigue_all_none_returns_low_with_warning():
    """全部数据缺失 → 默认低风险但 factors 含 'insufficient_data'."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=None, tsb=None, rpe_trend=None
    )
    assert level == "low"
    assert "insufficient_data" in factors


def test_fatigue_score_in_range():
    """分数必须在 0-100."""
    for args in [
        (-50.0, -30.0, [10, 10, 10]),
        (50.0, 30.0, [1, 1, 1]),
        (None, None, None),
    ]:
        score, _, _ = calc_fatigue_score(*args)
        assert 0 <= score <= 100
