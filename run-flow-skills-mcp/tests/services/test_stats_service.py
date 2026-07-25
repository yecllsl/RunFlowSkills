"""stats_service 测试（spec FR-STATS-01/02）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.stats_service import StatsService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> StatsService:
    return StatsService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


def _seed(import_service: ImportService):
    sources = ["garmin", "apple", "garmin", "coros"]
    for i, src in enumerate(sources):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%dT06:00:00")
        import_service.import_manual({
            "activity_date": date, "distance_m": 10000.0,
            "duration_s": 3000, "source": src,
        })


def test_get_statistics_by_source(service: StatsService, import_service: ImportService):
    """按数据源分组统计."""
    _seed(import_service)
    result = service.get_statistics(dimension="by_source")

    assert "groups" in result
    assert len(result["groups"]) > 0
    # garmin 应有 2 条
    garmin_group = next(g for g in result["groups"] if g["key"] == "garmin")
    assert garmin_group["count"] == 2


def test_get_statistics_by_week(service: StatsService, import_service: ImportService):
    """按周分组统计."""
    _seed(import_service)
    result = service.get_statistics(dimension="by_week")
    assert "groups" in result


def test_get_statistics_by_pace_zone(service: StatsService, import_service: ImportService):
    """按配速区间分组."""
    _seed(import_service)
    result = service.get_statistics(dimension="by_pace_zone")
    assert "groups" in result


def test_get_statistics_invalid_dimension_returns_empty(service: StatsService):
    """无效 dimension 返回空 groups."""
    result = service.get_statistics(dimension="invalid")
    assert result["groups"] == []


def test_export_data_csv(service: StatsService, import_service: ImportService):
    """导出 CSV."""
    _seed(import_service)
    result = service.export_data(format="csv")
    assert result["format"] == "csv"
    assert result["rows_count"] > 0
    assert Path(result["file_path"]).exists()


def test_export_data_json(service: StatsService, import_service: ImportService):
    """导出 JSON."""
    _seed(import_service)
    result = service.export_data(format="json")
    assert result["format"] == "json"
    assert Path(result["file_path"]).exists()


def test_export_data_parquet(service: StatsService, import_service: ImportService):
    """导出 Parquet."""
    _seed(import_service)
    result = service.export_data(format="parquet")
    assert result["format"] == "parquet"
    assert Path(result["file_path"]).exists()


def test_export_data_md(service: StatsService, import_service: ImportService):
    """导出 Markdown."""
    _seed(import_service)
    result = service.export_data(format="md")
    assert result["format"] == "md"
    assert Path(result["file_path"]).exists()


def test_export_data_include_ai_logs(service: StatsService, import_service: ImportService):
    """include_ai_logs=True 时导出含决策日志."""
    _seed(import_service)
    # 灌入一个决策日志
    from run_flow_skills_mcp.services.coach_service import CoachService
    coach = CoachService(service.parquet_store, service.json_store)
    coach.save_decision_log(
        decision_type="coach", inputs={"hrv": 38},
        reasoning="test", recommendation="test",
        confidence=0.7, trace_chain=["a"],
    )

    result = service.export_data(format="json", include_ai_logs=True)
    assert result["rows_count"] > 0  # 含决策日志行
