"""get_period_summary / read_body_signals tool 测试（spec FR-REVIEW-01/02, FR-COACH-01）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.get_period_summary import get_period_summary
from run_flow_skills_mcp.tools.import_manual import import_manual
from run_flow_skills_mcp.tools.read_body_signals import read_body_signals


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed_sessions(tmp_path: Path, n: int = 7):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=n - i - 1)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {"activity_date": date, "distance_m": 10000.0, "duration_s": 3000, "source": "manual"},
            _data_dir=tmp_path,
        )


def _seed_hrv(tmp_path: Path, n: int = 7):
    services = _deps.get_services(tmp_path)
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        services.coach_service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=45.0, rpe=5, resting_hr=55, sleep_quality=4)
        )


def test_get_period_summary_returns_prompt_and_data(tmp_path: Path):
    """get_period_summary 返回所有字段 + prompt."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 7)
    result = get_period_summary(period="week", date_ref="2026-07-25", _data_dir=tmp_path)
    for key in ("prompt", "total_distance", "total_tss", "avg_vdot", "load_change", "sessions_count", "vdot_trend", "hrv_trend"):
        assert key in result
    # prompt 应已填充（不再是 {period}）
    assert "{period}" not in result["prompt"]


def test_get_period_summary_invalid_period(tmp_path: Path):
    """无效 period 返回零值 + prompt."""
    _deps.reset_services_cache()
    result = get_period_summary(period="invalid", date_ref="2026-07-25", _data_dir=tmp_path)
    assert result["sessions_count"] == 0
    assert "prompt" in result


def test_read_body_signals_returns_prompt_and_data(tmp_path: Path):
    """read_body_signals 返回所有字段 + prompt."""
    _deps.reset_services_cache()
    _seed_hrv(tmp_path, 7)
    result = read_body_signals(date="2026-07-25", _data_dir=tmp_path)
    for key in ("prompt", "hrv", "resting_hr", "sleep", "rpe", "baseline", "deviation_pct", "readiness_level", "yesterday_session", "recent_high_intensity"):
        assert key in result
    # prompt 应已填充
    assert "{readiness_level}" not in result["prompt"]


def test_read_body_signals_no_data_returns_none_values(tmp_path: Path):
    """无数据返回 None 值 + prompt."""
    _deps.reset_services_cache()
    result = read_body_signals(date="2026-07-25", _data_dir=tmp_path)
    assert result["hrv"] is None
    assert result["readiness_level"] in ("green", "yellow", "red")
    assert "prompt" in result
