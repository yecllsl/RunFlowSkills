"""去重逻辑测试（spec 5.3, FR-IMPORT-05）."""
from datetime import datetime
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import Session
from run_flow_skills_mcp.storage.dedup import (
    check_hash_duplicate,
    find_cross_platform_duplicate,
    is_cross_platform_match,
)
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def store(tmp_data_dir: Path) -> ParquetStore:
    return ParquetStore(data_dir=tmp_data_dir)


def _make_session(
    dt: datetime,
    distance: float = 10000.0,
    duration: int = 3600,
    source: str = "garmin",
    raw_hash: str = "hash_garmin",
) -> Session:
    return Session(
        session_id=f"sess_{dt.strftime('%Y%m%d')}_001",
        activity_date=dt,
        distance_m=distance,
        duration_s=duration,
        avg_pace_s_per_km=duration / (distance / 1000),
        source=source,
        raw_file_hash=raw_hash,
    )


def test_check_hash_duplicate_found(store: ParquetStore):
    s = _make_session(datetime(2026, 7, 25, 6, 0), raw_hash="abc")
    store.append_session(s)
    found = check_hash_duplicate(store, "abc")
    assert found is not None
    assert found.session_id == s.session_id


def test_check_hash_duplicate_not_found(store: ParquetStore):
    found = check_hash_duplicate(store, "nonexistent")
    assert found is None


def test_is_cross_platform_match_same_activity():
    """同一活动，Garmin 与 Apple Watch 时间相差 3 分钟，距离 0.5%."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0), source="garmin")
    s2 = _make_session(
        datetime(2026, 7, 25, 6, 3),  # +3 分钟（<5 分钟容差）
        distance=10050.0,  # +0.5%（<2%）
        duration=3610,  # +10 秒（<30 秒）
        source="apple",
    )
    assert is_cross_platform_match(s1, s2) is True


def test_is_cross_platform_match_different_activity():
    """时间相差 10 分钟，非同一活动."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0))
    s2 = _make_session(datetime(2026, 7, 25, 6, 10))  # +10 分钟（>5 分钟）
    assert is_cross_platform_match(s1, s2) is False


def test_is_cross_platform_match_distance_too_different():
    """距离相差 5%，超出容差."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0), distance=10000.0)
    s2 = _make_session(
        datetime(2026, 7, 25, 6, 3),
        distance=10500.0,  # +5%（>2%）
    )
    assert is_cross_platform_match(s1, s2) is False


def test_is_cross_platform_match_duration_too_different():
    """时长相差 60 秒，超出容差."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0), duration=3600)
    s2 = _make_session(
        datetime(2026, 7, 25, 6, 3),
        duration=3660,  # +60 秒（>30 秒）
    )
    assert is_cross_platform_match(s1, s2) is False


def test_find_cross_platform_duplicate_finds_match(store: ParquetStore):
    """已存 Garmin 活动，新导入 Apple 活动，应识别为重复."""
    garmin = _make_session(datetime(2026, 7, 25, 6, 0), source="garmin", raw_hash="g1")
    store.append_session(garmin)

    apple = _make_session(
        datetime(2026, 7, 25, 6, 3),
        distance=10050.0,
        duration=3610,
        source="apple",
        raw_hash="a1",  # 不同 hash
    )
    duplicate = find_cross_platform_duplicate(store, apple)
    assert duplicate is not None
    assert duplicate.source == "garmin"


def test_find_cross_platform_duplicate_no_match(store: ParquetStore):
    apple = _make_session(datetime(2026, 7, 25, 6, 0), source="apple", raw_hash="a1")
    duplicate = find_cross_platform_duplicate(store, apple)
    assert duplicate is None
