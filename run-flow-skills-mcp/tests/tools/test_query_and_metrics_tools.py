"""query_sessions / calc_metrics tool 测试（spec FR-ANALYZE-01, 6.1）."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.calc_metrics import calc_metrics
from run_flow_skills_mcp.tools.import_manual import import_manual
from run_flow_skills_mcp.tools.query_sessions import query_sessions


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed(tmp_path: Path, n: int = 3):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {"activity_date": date, "distance_m": 10000.0, "duration_s": 3000, "source": "manual"},
            _data_dir=tmp_path,
        )


def test_query_sessions_returns_list(tmp_path: Path):
    """query_sessions 返回 sessions 列表 + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 3)
    result = query_sessions(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in result
    assert "sessions" in result
    assert isinstance(result["sessions"], list)
    assert result["total"] >= 1
    # 每个 session 应有摘要字段
    for s in result["sessions"]:
        assert "session_id" in s
        assert "activity_date" in s


def test_query_sessions_empty_returns_empty_list(tmp_path: Path):
    """无数据返回空列表 + prompt."""
    _deps.reset_services_cache()
    result = query_sessions(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    assert result["sessions"] == []
    assert result["total"] == 0
    assert "prompt" in result


def test_query_sessions_limit_truncates(tmp_path: Path):
    """limit 截断结果."""
    _deps.reset_services_cache()
    _seed(tmp_path, 5)
    result = query_sessions(
        date_from="2026-07-15", date_to="2026-07-25", limit=2, _data_dir=tmp_path
    )
    assert len(result["sessions"]) <= 2


def test_calc_metrics_returns_prompt_with_placeholders(tmp_path: Path):
    """calc_metrics 返回的 prompt 已填充关键占位符."""
    _deps.reset_services_cache()
    _seed(tmp_path, 5)
    result = calc_metrics(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    for key in ("vdot_trend", "tss_sum", "ctl", "atl", "tsb", "hr_zones_dist", "prompt"):
        assert key in result
    # prompt 应已填充（不再是原始模板的 {vdot}）
    assert "{vdot}" not in result["prompt"]


def test_calc_metrics_empty_data_returns_zeros(tmp_path: Path):
    """无数据返回零值."""
    _deps.reset_services_cache()
    result = calc_metrics(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    assert result["tss_sum"] == 0
    assert result["ctl"] == 0
    assert "prompt" in result
