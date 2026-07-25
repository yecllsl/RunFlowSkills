"""get_trends / analyze_fatigue tool 测试（spec FR-ANALYZE-04/05）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.analyze_fatigue import analyze_fatigue
from run_flow_skills_mcp.tools.get_trends import get_trends
from run_flow_skills_mcp.tools.import_manual import import_manual


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed_sessions(tmp_path: Path, n: int = 10):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=n - i - 1)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {"activity_date": date, "distance_m": 10000.0, "duration_s": 3000, "source": "manual"},
            _data_dir=tmp_path,
        )


def _seed_hrv(tmp_path: Path, n: int = 7):
    _deps.reset_services_cache()
    services = _deps.get_services(tmp_path)
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        services.coach_service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=45.0, rpe=5)
        )


def test_get_trends_vdot_returns_prompt_and_series(tmp_path: Path):
    """get_trends(metric=vdot) 返回 series + prompt."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 5)
    result = get_trends(days=30, metric="vdot", _data_dir=tmp_path)
    for key in ("prompt", "series", "change_pct", "baseline"):
        assert key in result
    assert isinstance(result["series"], list)


def test_get_trends_load_metric(tmp_path: Path):
    """get_trends(metric=load) 返回 CTL/ATL 序列."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 5)
    result = get_trends(days=30, metric="load", _data_dir=tmp_path)
    assert "series" in result
    assert "prompt" in result


def test_get_trends_invalid_metric_returns_empty(tmp_path: Path):
    """无效 metric 返回空 series + prompt（降级）."""
    _deps.reset_services_cache()
    result = get_trends(days=7, metric="invalid", _data_dir=tmp_path)
    assert result["series"] == []
    assert "prompt" in result


def test_analyze_fatigue_returns_prompt_and_fields(tmp_path: Path):
    """analyze_fatigue 返回所有字段 + prompt."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 5)
    _seed_hrv(tmp_path, 7)
    result = analyze_fatigue(days=7, _data_dir=tmp_path)
    for key in ("prompt", "fatigue_score", "risk_level", "main_factors", "hrv_deviation", "tsb"):
        assert key in result


def test_analyze_fatigue_no_data_returns_low(tmp_path: Path):
    """无数据返回低风险 + prompt."""
    _deps.reset_services_cache()
    result = analyze_fatigue(days=7, _data_dir=tmp_path)
    assert result["risk_level"] == "low"
    assert "prompt" in result
