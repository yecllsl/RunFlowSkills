"""analysis_service 测试（spec FR-ANALYZE-01/04/05）."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.services.analysis_service import AnalysisService
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> AnalysisService:
    return AnalysisService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


def _seed_sessions(import_service: ImportService, n: int = 10):
    """通过 import_service 灌入 n 个手动 Session."""
    for i in range(n):
        days_ago = n - i
        date = (datetime(2026, 7, 25) - timedelta(days=days_ago)).strftime("%Y-%m-%dT06:00:00")
        import_service.import_manual(
            {
                "activity_date": date,
                "distance_m": 10000.0,
                "duration_s": 3000,  # 50 分钟，配速 5'00"/km
                "source": "manual",
                "avg_hr": 150,
            }
        )


def test_calc_metrics_returns_required_fields(
    service: AnalysisService, import_service: ImportService
):
    """calc_metrics 必须返回 spec 6.1 定义的所有字段."""
    _seed_sessions(import_service, 10)
    result = service.calc_metrics("2026-07-15", "2026-07-25")

    for key in ("vdot_trend", "tss_sum", "ctl", "atl", "tsb", "hr_zones_dist"):
        assert key in result, f"missing {key}"


def test_calc_metrics_empty_data_returns_zeros(service: AnalysisService):
    """无数据时应返回零值，不抛异常."""
    result = service.calc_metrics("2026-07-01", "2026-07-25")
    assert result["tss_sum"] == 0
    assert result["ctl"] == 0
    assert result["atl"] == 0


def test_get_trends_vdot_returns_series(service: AnalysisService, import_service: ImportService):
    """get_trends(metric=vdot) 返回 series 列表."""
    _seed_sessions(import_service, 10)
    result = service.get_trends(days=30, metric="vdot")

    assert "series" in result
    assert isinstance(result["series"], list)
    for point in result["series"]:
        assert "date" in point
        assert "value" in point


def test_get_trends_load_metric(service: AnalysisService, import_service: ImportService):
    """get_trends(metric=load) 返回 CTL/ATL 序列."""
    _seed_sessions(import_service, 10)
    result = service.get_trends(days=30, metric="load")
    assert "series" in result


def test_get_trends_invalid_metric_returns_empty(service: AnalysisService):
    """无效 metric 返回空 series（降级方案）."""
    result = service.get_trends(days=7, metric="invalid")
    assert result["series"] == []


def test_analyze_fatigue_returns_required_fields(
    service: AnalysisService, import_service: ImportService
):
    """analyze_fatigue 返回 spec 6.1 字段."""
    _seed_sessions(import_service, 10)
    # 灌入 HRV 数据
    for i in range(7):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        service.json_store.upsert_body_signal(BodySignal(date=date, hrv_rmssd=45.0, rpe=5))

    result = service.analyze_fatigue(days=7)
    for key in ("fatigue_score", "risk_level", "main_factors", "hrv_deviation", "tsb"):
        assert key in result


def test_analyze_fatigue_no_data_returns_low(service: AnalysisService):
    """无 HRV/负荷数据时返回低风险 + insufficient_data."""
    result = service.analyze_fatigue(days=7)
    assert result["risk_level"] == "low"
    assert "insufficient_data" in result["main_factors"]
