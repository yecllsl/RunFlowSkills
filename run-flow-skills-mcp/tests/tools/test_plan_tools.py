"""generate_plan / query_plan tool 测试（spec FR-PLAN-01/02/03/04）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.generate_plan import generate_plan
from run_flow_skills_mcp.tools.query_plan import query_plan


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def test_generate_plan_returns_prompt_and_data(tmp_path: Path):
    """generate_plan 返回 plan_prompt + 结构化数据."""
    _deps.reset_services_cache()
    result = generate_plan(
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
        _data_dir=tmp_path,
    )
    for key in ("prompt", "plan_id", "phases", "pace_zones", "target_vdot", "vdot_gap"):
        assert key in result
    # prompt 应是 service 填充后的 plan_prompt
    assert "42.0" in result["prompt"] or "42" in result["prompt"]


def test_generate_plan_invalid_goal_type_still_returns(tmp_path: Path):
    """无效 goal_type 也能返回（service 内部降级）."""
    _deps.reset_services_cache()
    result = generate_plan(
        goal_type="invalid",
        goal_time="00:30:00",
        race_date="2026-10-19",
        weeks=4,
        current_vdot=40.0,
        _data_dir=tmp_path,
    )
    assert "prompt" in result
    assert "plan_id" in result


def test_query_plan_returns_plan_and_fidelity(tmp_path: Path):
    """query_plan 返回 plan + fidelity + prompt."""
    _deps.reset_services_cache()
    gen = generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
        _data_dir=tmp_path,
    )
    result = query_plan(gen["plan_id"], _data_dir=tmp_path)
    for key in ("prompt", "plan", "fidelity"):
        assert key in result


def test_query_plan_not_found_returns_none(tmp_path: Path):
    """不存在的 plan_id 返回 plan=None + prompt."""
    _deps.reset_services_cache()
    result = query_plan("plan_20260101_999", _data_dir=tmp_path)
    assert result["plan"] is None
    assert "prompt" in result


def test_query_plan_no_id_returns_latest(tmp_path: Path):
    """plan_id=None 返回最新计划."""
    _deps.reset_services_cache()
    generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
        _data_dir=tmp_path,
    )
    result = query_plan(_data_dir=tmp_path)
    assert result["plan"] is not None
    assert "prompt" in result
