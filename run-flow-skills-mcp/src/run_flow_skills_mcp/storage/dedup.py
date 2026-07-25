"""去重逻辑（spec 5.3, FR-IMPORT-05）.

- 主去重键：raw_file_hash（SHA256）
- 跨平台去重：时间戳 ±5 分钟 + 距离 ±2% + 时长 ±30 秒
"""

from __future__ import annotations

from run_flow_skills_mcp.constants import (
    DEDUP_DISTANCE_TOLERANCE_PCT,
    DEDUP_DURATION_TOLERANCE_S,
    DEDUP_TIME_TOLERANCE_S,
)
from run_flow_skills_mcp.models import Session
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


def check_hash_duplicate(store: ParquetStore, raw_file_hash: str) -> Session | None:
    """通过 SHA256 查找已存在的 Session（spec 5.3 主去重键）."""
    if not raw_file_hash:
        return None
    return store.find_by_hash(raw_file_hash)


def is_cross_platform_match(s1: Session, s2: Session) -> bool:
    """判定两 Session 是否为跨平台同一活动（spec 5.3）.

    匹配条件（同时满足）：
    - 时间戳差 <= 5 分钟
    - 距离相对差 <= 2%
    - 时长差 <= 30 秒
    """
    # 时间戳匹配
    time_diff_s = abs((s1.activity_date - s2.activity_date).total_seconds())
    if time_diff_s > DEDUP_TIME_TOLERANCE_S:
        return False

    # 距离匹配（相对差）
    max_distance = max(s1.distance_m, s2.distance_m)
    if max_distance <= 0:
        return False
    distance_diff_pct = abs(s1.distance_m - s2.distance_m) / max_distance
    if distance_diff_pct > DEDUP_DISTANCE_TOLERANCE_PCT:
        return False

    # 时长匹配
    duration_diff_s = abs(s1.duration_s - s2.duration_s)
    if duration_diff_s > DEDUP_DURATION_TOLERANCE_S:
        return False

    return True


def find_cross_platform_duplicate(store: ParquetStore, candidate: Session) -> Session | None:
    """查找 candidate 是否与已存 Session 跨平台重复.

    Returns:
        重复的已存 Session（如有），否则 None
    """
    # 查询候选活动时间附近 ±1 天的所有 sessions（避免全表扫描）
    date_from = candidate.activity_date.strftime("%Y-%m-%d")
    date_to = candidate.activity_date.strftime("%Y-%m-%d")
    candidates = store.query_sessions(date_from=date_from, date_to=date_to)

    for existing in candidates:
        # 候选会话尚未入库，无需按 session_id 跳过自身
        if existing.source == candidate.source:
            # 同源不视为跨平台重复（同源应由 hash 去重）
            continue
        if is_cross_platform_match(existing, candidate):
            return existing
    return None
