"""get_statistics / export_data tool 测试（spec FR-STATS-01/02）."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.export_data import export_data
from run_flow_skills_mcp.tools.get_statistics import get_statistics
from run_flow_skills_mcp.tools.import_manual import import_manual


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed(tmp_path: Path, n: int = 4):
    sources = ["garmin", "apple", "garmin", "coros"]
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {
                "activity_date": date,
                "distance_m": 10000.0,
                "duration_s": 3000,
                "source": sources[i % len(sources)],
            },
            _data_dir=tmp_path,
        )


def test_get_statistics_returns_prompt_and_groups(tmp_path: Path):
    """get_statistics 返回 groups + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = get_statistics(dimension="by_source", _data_dir=tmp_path)
    for key in ("prompt", "groups", "dimension"):
        assert key in result
    assert isinstance(result["groups"], list)
    assert len(result["groups"]) > 0


def test_get_statistics_invalid_dimension(tmp_path: Path):
    """无效 dimension 返回空 groups + prompt."""
    _deps.reset_services_cache()
    result = get_statistics(dimension="invalid", _data_dir=tmp_path)
    assert result["groups"] == []
    assert "prompt" in result


def test_export_data_csv(tmp_path: Path):
    """导出 CSV 返回 file_path + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = export_data(export_format="csv", _data_dir=tmp_path)
    assert result["format"] == "csv"
    assert result["rows_count"] > 0
    assert Path(result["file_path"]).exists()
    assert "prompt" in result


def test_export_data_json(tmp_path: Path):
    """导出 JSON."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = export_data(export_format="json", _data_dir=tmp_path)
    assert result["format"] == "json"
    assert Path(result["file_path"]).exists()
    assert "prompt" in result


def test_export_data_invalid_format_returns_error(tmp_path: Path):
    """不支持的格式返回 error + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = export_data(export_format="xml", _data_dir=tmp_path)
    assert "error" in result
    assert "prompt" in result


def test_export_data_include_ai_logs(tmp_path: Path):
    """include_ai_logs=True 含决策日志."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    # 灌入决策日志
    services = _deps.get_services(tmp_path)
    services.coach_service.save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="test",
        recommendation="test",
        confidence=0.7,
        trace_chain=["a"],
    )
    _deps.reset_services_cache()

    result = export_data(export_format="json", include_ai_logs=True, _data_dir=tmp_path)
    assert result["rows_count"] > 0
