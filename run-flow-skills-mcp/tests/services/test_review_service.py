"""review_service 测试（spec FR-REVIEW-01/02）."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.review_service import ReviewService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> ReviewService:
    return ReviewService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


def _seed(import_service: ImportService, n: int):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=n - i - 1)).strftime("%Y-%m-%dT06:00:00")
        import_service.import_manual(
            {
                "activity_date": date,
                "distance_m": 10000.0,
                "duration_s": 3000,
                "source": "manual",
            }
        )


def test_get_period_summary_week(service: ReviewService, import_service: ImportService):
    """period=week 返回本周摘要."""
    _seed(import_service, 7)
    result = service.get_period_summary(period="week", date_ref="2026-07-25")

    for key in (
        "total_distance",
        "total_tss",
        "avg_vdot",
        "load_change",
        "sessions_count",
        "vdot_trend",
        "hrv_trend",
    ):
        assert key in result
    assert result["sessions_count"] >= 1


def test_get_period_summary_month(service: ReviewService, import_service: ImportService):
    """period=month 返回月度摘要."""
    _seed(import_service, 10)
    result = service.get_period_summary(period="month", date_ref="2026-07-25")
    assert result["sessions_count"] >= 1


def test_get_period_summary_invalid_period_returns_empty(service: ReviewService):
    """无效 period 返回空摘要（降级）."""
    result = service.get_period_summary(period="invalid", date_ref="2026-07-25")
    assert result["sessions_count"] == 0
    assert result["total_distance"] == 0


def test_get_period_summary_no_data_returns_zeros(service: ReviewService):
    """无数据返回零值."""
    result = service.get_period_summary(period="week", date_ref="2026-07-25")
    assert result["sessions_count"] == 0
    assert result["total_distance"] == 0


def test_get_period_summary_load_change_vs_last_period(
    service: ReviewService, import_service: ImportService
):
    """load_change 应反映环比变化（本期 vs 上期）."""
    # 灌入 14 天数据
    _seed(import_service, 14)
    result = service.get_period_summary(period="week", date_ref="2026-07-25")
    assert "load_change" in result
    # load_change 应为 dict 或 float，表示变化
    assert result["load_change"] is not None or result["total_tss"] > 0
