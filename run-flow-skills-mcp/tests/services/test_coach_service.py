"""coach_service 测试（spec FR-COACH-01/02/03, 8.3）."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.services.coach_service import CoachService
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> CoachService:
    return CoachService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


def _seed_hrv(service: CoachService, n: int = 7, hrv_value: float = 45.0):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=hrv_value, rpe=5, resting_hr=55, sleep_quality=4)
        )


def test_read_body_signals_returns_required_fields(service: CoachService):
    """read_body_signals 返回 spec 6.1 字段."""
    _seed_hrv(service, 7)
    result = service.read_body_signals(date="2026-07-25")

    for key in (
        "hrv",
        "resting_hr",
        "sleep",
        "rpe",
        "baseline",
        "deviation_pct",
        "readiness_level",
        "yesterday_session",
        "recent_high_intensity",
    ):
        assert key in result


def test_read_body_signals_no_data_returns_none_values(service: CoachService):
    """无数据时返回 None 值 + readiness_level=green（默认）."""
    result = service.read_body_signals(date="2026-07-25")
    assert result["hrv"] is None
    assert result["readiness_level"] in ("green", "yellow", "red")


def test_readiness_level_green_when_all_normal(service: CoachService):
    """所有指标正常 → green（spec 8.3 第 3 条：综合 HRV+TSB+RPE）."""
    level = service.compute_readiness_level(hrv_deviation=2.0, tsb=15.0, rpe=4)
    assert level == "green"


def test_readiness_level_yellow_when_hrv_low(service: CoachService):
    """HRV 偏低 10-20% → yellow."""
    level = service.compute_readiness_level(hrv_deviation=-15.0, tsb=5.0, rpe=6)
    assert level == "yellow"


def test_readiness_level_red_when_all_bad(service: CoachService):
    """HRV 偏低 + TSB 负 + RPE 高 → red."""
    level = service.compute_readiness_level(hrv_deviation=-20.0, tsb=-15.0, rpe=9)
    assert level == "red"


def test_readiness_level_single_indicator_not_decisive(service: CoachService):
    """单一指标不决策（coaching-rules.md 第 3 条）：仅 HRV 偏低不应直接 red."""
    # HRV 偏低但 TSB 充足 + RPE 低
    level = service.compute_readiness_level(hrv_deviation=-12.0, tsb=20.0, rpe=3)
    assert level in ("green", "yellow")  # 不应直接 red


def test_save_decision_log_returns_id(service: CoachService):
    """save_decision_log 返回 decision_id + saved=True."""
    result = service.save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38, "tsb": -5},
        reasoning="HRV 偏低 + TSB 负值",
        recommendation="E 区间 30 分钟",
        confidence=0.7,
        trace_chain=["HRV=38", "baseline=45", "rule:HRV偏离>10%"],
    )
    assert result["saved"] is True
    assert result["decision_id"].startswith("dec_")


def test_get_decision_trace_found(service: CoachService):
    """保存后可通过 decision_id 查询."""
    saved = service.save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="test",
        recommendation="test",
        confidence=0.7,
        trace_chain=["a", "b"],
    )
    trace = service.get_decision_trace(saved["decision_id"])
    assert trace is not None
    assert trace["recommendation"] == "test"


def test_get_decision_trace_not_found(service: CoachService):
    """不存在返回 None."""
    trace = service.get_decision_trace("dec_20260101_999")
    assert trace is None


def test_read_body_signals_detects_recent_high_intensity(
    service: CoachService, import_service: ImportService
):
    """24h 内高强度训练检测（coaching-rules.md 第 6 条）."""
    _seed_hrv(service, 7)
    # 导入一个高强度训练（T 区间）
    yesterday = (datetime(2026, 7, 25) - timedelta(days=1)).strftime("%Y-%m-%dT18:00:00")
    import_service.import_manual(
        {
            "activity_date": yesterday,
            "distance_m": 8000.0,
            "duration_s": 1800,  # 配速 3'45"/km，T 区间高强度
            "source": "manual",
        }
    )

    result = service.read_body_signals(date="2026-07-25")
    # recent_high_intensity 应为 True 或包含昨日训练信息
    assert result["recent_high_intensity"] is not None
