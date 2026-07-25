"""Parquet 存储测试（spec 5.1, FR-IMPORT-07）."""
from datetime import datetime
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import Session, TrainingMetrics
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def store(tmp_data_dir: Path) -> ParquetStore:
    return ParquetStore(data_dir=tmp_data_dir)


def _make_session(session_id: str, date: datetime, source: str = "garmin") -> Session:
    return Session(
        session_id=session_id,
        activity_date=date,
        distance_m=10000.0,
        duration_s=3600,
        avg_pace_s_per_km=360.0,
        source=source,
        raw_file_hash="abc123",
    )


def test_append_and_query_session(store: ParquetStore):
    s = _make_session("sess_20260725_001", datetime(2026, 7, 25, 6, 0))
    store.append_session(s)
    result = store.query_sessions()
    assert len(result) == 1
    assert result[0].session_id == "sess_20260725_001"


def test_query_by_date_range(store: ParquetStore):
    store.append_session(_make_session("sess_20260701_001", datetime(2026, 7, 1)))
    store.append_session(_make_session("sess_20260725_001", datetime(2026, 7, 25)))
    store.append_session(_make_session("sess_20260815_001", datetime(2026, 8, 15)))

    result = store.query_sessions(date_from="2026-07-01", date_to="2026-07-31")
    assert len(result) == 2


def test_query_by_source(store: ParquetStore):
    store.append_session(_make_session("sess_20260725_001", datetime(2026, 7, 25), "garmin"))
    store.append_session(_make_session("sess_20260725_002", datetime(2026, 7, 25), "apple"))

    result = store.query_sessions(source="garmin")
    assert len(result) == 1
    assert result[0].source == "garmin"


def test_query_limit(store: ParquetStore):
    for i in range(5):
        store.append_session(_make_session(f"sess_20260725_{i+1:03d}", datetime(2026, 7, 25)))
    result = store.query_sessions(limit=3)
    assert len(result) == 3


def test_find_by_hash(store: ParquetStore):
    s = _make_session("sess_20260725_001", datetime(2026, 7, 25))
    s.raw_file_hash = "unique_hash_123"
    store.append_session(s)

    found = store.find_by_hash("unique_hash_123")
    assert found is not None
    assert found.session_id == "sess_20260725_001"

    not_found = store.find_by_hash("nonexistent")
    assert not_found is None


def test_yearly_sharding(store: ParquetStore):
    """跨年存储应分到不同 parquet 文件（spec 5.1）."""
    store.append_session(_make_session("sess_20251231_001", datetime(2025, 12, 31)))
    store.append_session(_make_session("sess_20260101_001", datetime(2026, 1, 1)))

    assert (store.data_dir / "sessions" / "sessions_2025.parquet").exists()
    assert (store.data_dir / "sessions" / "sessions_2026.parquet").exists()


def test_append_metrics_and_query(store: ParquetStore):
    s = _make_session("sess_20260725_001", datetime(2026, 7, 25))
    store.append_session(s)
    m = TrainingMetrics(
        session_id="sess_20260725_001",
        vdot=45.0,
        vdot_confidence="high",
        tss=100.0,
        intensity_factor=0.85,
        pace_zone="T",
    )
    store.append_metrics(m)

    result = store.query_metrics(["sess_20260725_001"])
    assert len(result) == 1
    assert result[0].vdot == 45.0
