"""VDOT 计算单元测试（spec 8.1.1, FR-ANALYZE-01）."""
from run_flow_skills_mcp.calculators.vdot import calc_vdot


def test_vdot_5k_normal():
    """5K 25 分钟 → VDOT 约 38（标准 Daniels 公式）."""
    vdot, conf = calc_vdot(5000.0, 1500)
    assert vdot is not None
    assert 36 <= vdot <= 40
    assert conf == "high"


def test_vdot_marathon_sub4():
    """全马 4 小时 → VDOT 约 36-37."""
    vdot, conf = calc_vdot(42195.0, 14400)
    assert vdot is not None
    assert 35 <= vdot <= 39
    assert conf == "high"


def test_vdot_below_1500m_marked_estimated():
    """距离 <1500m 标 'estimated'（spec 8.1.1）."""
    vdot, conf = calc_vdot(1200.0, 360)
    assert conf == "estimated"
    assert vdot is not None  # 仍给出估算值


def test_vdot_exactly_1500m_high_confidence():
    """距离 =1500m 视为达标（spec FR-ANALYZE-01 边界）."""
    vdot, conf = calc_vdot(1500.0, 360)
    assert conf == "high"


def test_vdot_zero_duration_returns_none():
    vdot, conf = calc_vdot(5000.0, 0)
    assert vdot is None
    assert conf == "low"


def test_vdot_negative_duration_returns_none():
    vdot, conf = calc_vdot(5000.0, -10)
    assert vdot is None
    assert conf == "low"


def test_vdot_zero_distance_returns_none():
    vdot, conf = calc_vdot(0.0, 1500)
    assert vdot is None
    assert conf == "low"


def test_vdot_elite_runner():
    """全马 2:30 → VDOT 约 60-65."""
    vdot, conf = calc_vdot(42195.0, 9012)
    assert vdot is not None
    assert 58 <= vdot <= 67
    assert conf == "high"
