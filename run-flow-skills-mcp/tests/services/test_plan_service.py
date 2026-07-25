"""plan_service 测试（spec FR-PLAN-01/02/03/04）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.plan_service import PlanService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> PlanService:
    return PlanService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


def test_generate_plan_full_marathon_12_weeks(service: PlanService):
    """生成 12 周全马计划：含 4 个周期化阶段（spec FR-PLAN-01）."""
    result = service.generate_plan(
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
    )

    assert result["plan_id"].startswith("plan_")
    assert len(result["phases"]) == 4  # base/build/peak/taper
    phase_types = [p.phase_type for p in result["phases"]]
    assert phase_types == ["base", "build", "peak", "taper"]

    # 配速区间基于 VDOT
    assert "E" in result["pace_zones"]
    assert "M" in result["pace_zones"]
    assert "T" in result["pace_zones"]

    # target_vdot 基于目标时间反算
    assert result["target_vdot"] > 42.0  # 全马破4 需要 VDOT ≈ 43.5


def test_generate_plan_includes_plan_prompt(service: PlanService):
    """生成计划必须附带 plan_prompt（spec 6.2）."""
    result = service.generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
    )
    assert "plan_prompt" in result
    assert "current_vdot" in result["plan_prompt"] or "40" in result["plan_prompt"]


def test_generate_plan_saves_to_json(service: PlanService):
    """生成后自动保存到 plans/plan_*.json（spec 5.1）."""
    result = service.generate_plan(
        goal_type="half_marathon", goal_time="01:59:59",
        race_date="2026-10-19", weeks=12, current_vdot=42.0,
    )
    plan_id = result["plan_id"]
    loaded = service.json_store.load_plan(plan_id)
    assert loaded is not None
    assert loaded.goal_type == "half_marathon"


def test_query_plan_returns_plan_and_fidelity(service: PlanService, import_service: ImportService):
    """query_plan 返回计划 + 可选 fidelity（spec FR-PLAN-04）."""
    gen = service.generate_plan(
        goal_type="10k", goal_time="00:50:00",
        race_date="2026-10-19", weeks=8, current_vdot=45.0,
    )
    result = service.query_plan(gen["plan_id"])
    assert "plan" in result
    assert "fidelity" in result  # 即使无实际训练，fidelity 也应返回（值为 0 或 null）


def test_query_plan_active_returns_latest(service: PlanService):
    """query_plan(plan_id=None) 返回最新的 active 计划."""
    service.generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
    )
    result = service.query_plan()
    assert "plan" in result


def test_compute_fidelity_empty_actual(service: PlanService):
    """无实际训练时 fidelity=0."""
    gen = service.generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
    )
    plan = service.json_store.load_plan(gen["plan_id"])
    fidelity = service.compute_fidelity(plan)
    assert fidelity["planned_sessions"] > 0
    assert fidelity["completed_sessions"] == 0
    assert fidelity["fidelity_rate"] == 0.0
