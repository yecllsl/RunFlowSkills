"""web/schemas.py 请求模型测试."""

import pytest
from pydantic import ValidationError


def test_manual_input_request_valid():
    """有效的手动录入请求."""
    from run_flow_skills_mcp.web.schemas import ManualInputRequest

    req = ManualInputRequest(
        activity_date="2026-07-20T06:00:00",
        distance_m=10000,
        duration_s=3600,
        avg_hr=150,
        max_hr=170,
        source="manual",
        notes="晨跑",
    )
    assert req.distance_m == 10000
    assert req.duration_s == 3600


def test_manual_input_request_minimal():
    """最小必填字段."""
    from run_flow_skills_mcp.web.schemas import ManualInputRequest

    req = ManualInputRequest(
        activity_date="2026-07-20T06:00:00",
        distance_m=5000,
        duration_s=1800,
    )
    assert req.avg_hr is None
    assert req.source == "manual"  # 默认值


def test_manual_input_request_invalid_zero_distance():
    """距离为 0 时校验失败."""
    from run_flow_skills_mcp.web.schemas import ManualInputRequest

    with pytest.raises(ValidationError):
        ManualInputRequest(
            activity_date="2026-07-20T06:00:00",
            distance_m=0,
            duration_s=1800,
        )


def test_config_update_request_all_optional():
    """配置更新所有字段可选（部分更新）."""
    from run_flow_skills_mcp.web.schemas import ConfigUpdateRequest

    req = ConfigUpdateRequest()  # 空请求
    assert req.max_hr is None
    assert req.lthr is None


def test_config_update_request_partial():
    """部分更新：只传 max_hr."""
    from run_flow_skills_mcp.web.schemas import ConfigUpdateRequest

    req = ConfigUpdateRequest(max_hr=185)
    assert req.max_hr == 185
    assert req.lthr is None  # 其他字段保持 None


def test_config_update_request_invalid_max_hr():
    """max_hr 超出范围校验失败."""
    from run_flow_skills_mcp.web.schemas import ConfigUpdateRequest

    with pytest.raises(ValidationError):
        ConfigUpdateRequest(max_hr=300)  # >260
