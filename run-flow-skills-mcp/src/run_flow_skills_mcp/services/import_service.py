"""导入编排服务（spec 5.4, FR-IMPORT-01/05）.

编排 importer + dedup + calculators + storage：
1. parse_file 解析文件 → Session
2. check_hash_duplicate 主去重
3. find_cross_platform_duplicate 跨平台去重
4. _compute_metrics 计算 VDOT/TSS/IF/pace_zone
5. 写入 Parquet + 重算 TrainingLoad
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, cast

from run_flow_skills_mcp.calculators.pace_zones import classify_pace_zone
from run_flow_skills_mcp.calculators.training_load import (
    calc_atl,
    calc_ctl,
    calc_intensity_factor,
    calc_tsb,
    calc_tss,
)
from run_flow_skills_mcp.calculators.vdot import calc_vdot
from run_flow_skills_mcp.constants import DEFAULT_LTHR
from run_flow_skills_mcp.models import (
    Session,
    SourceType,
    TrainingLoad,
    TrainingMetrics,
    generate_session_id,
)
from run_flow_skills_mcp.storage.dedup import (
    check_hash_duplicate,
    find_cross_platform_duplicate,
)
from run_flow_skills_mcp.storage.importer import ImportParseError, parse_file
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

# LTHR 对应配速的近似换算（秒/km）：LTHR 越高，阈值配速越快
# 经验值：LTHR 165 ≈ 5'00"/km（300s/km）
# ponytail: 线性近似，升级路径：v0.2.0 通过 UserConfig.lthr + VDOT 反算
_LTHR_TO_THRESHOLD_PACE: float = 49500.0  # 165 * 300


def _threshold_pace_from_lthr(lthr: int) -> float:
    """由 LTHR 估算阈值配速（秒/km）."""
    return _LTHR_TO_THRESHOLD_PACE / max(lthr, 1)


def _to_naive_utc(dt: datetime) -> datetime:
    """将 datetime 规范化为无时区信息的 UTC.

    ponytail: Windows 下 polars 读取 tz-aware datetime 会触发 ZoneInfoNotFoundError，
    内部统一用 naive UTC 存储，避免依赖系统 tzdata。
    升级路径：v0.2.0 引入 tzdata 包后可保留 tz 信息。
    """
    if dt.tzinfo is not None:
        # 转换到 UTC 再去掉 tzinfo
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class ImportService:
    """导入编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def import_file(
        self,
        file_path: Path,
        force: bool = False,
        source: Optional[SourceType] = None,
    ) -> dict:
        """导入文件：解析 → 去重 → 计算指标 → 存储."""
        try:
            session = parse_file(file_path, source=source)
        except ImportParseError as e:
            return {"imported": False, "error": str(e)}

        # 规范化 datetime：tz-aware → naive UTC（避免 Windows polars tz 问题）
        session.activity_date = _to_naive_utc(session.activity_date)
        # 重写 session_id（importer 生成的是临时 ID，需基于已存数量生成）
        session.session_id = self._next_session_id(session.activity_date)

        return self._import_session(session, force)

    def import_manual(self, manual_data: dict, force: bool = False) -> dict:
        """手动录入：构造 Session 后复用 _import_session."""
        try:
            activity_date = datetime.fromisoformat(manual_data["activity_date"])
            distance_m = float(manual_data["distance_m"])
            duration_s = int(manual_data["duration_s"])
            source_raw = manual_data.get("source", "manual")
            # SourceType 为 Literal，pydantic 会在 Session 构造时校验合法值
            source = cast(SourceType, source_raw)
            if distance_m <= 0 or duration_s <= 0:
                return {"imported": False, "error": "distance_m 和 duration_s 必须 >0"}

            # 规范化 datetime
            activity_date = _to_naive_utc(activity_date)
            avg_pace = duration_s / (distance_m / 1000)
            session = Session(
                session_id=self._next_session_id(activity_date),
                activity_date=activity_date,
                distance_m=distance_m,
                duration_s=duration_s,
                avg_pace_s_per_km=avg_pace,
                avg_hr=manual_data.get("avg_hr"),
                max_hr=manual_data.get("max_hr"),
                source=source,
                notes=manual_data.get("notes"),
            )
        except (KeyError, ValueError, TypeError) as e:
            return {"imported": False, "error": f"数据格式错误: {e}"}

        return self._import_session(session, force)

    def _import_session(self, session: Session, force: bool) -> dict:
        """统一的 Session 导入流程（去重 → 计算 → 存储）."""
        # 主去重：raw_file_hash
        if not force and session.raw_file_hash:
            existing = check_hash_duplicate(self.parquet_store, session.raw_file_hash)
            if existing is not None:
                return {
                    "imported": False,
                    "skipped": True,
                    "reason": "duplicate_hash",
                    "existing_session_id": existing.session_id,
                }

        # 跨平台去重
        if not force:
            cross = find_cross_platform_duplicate(self.parquet_store, session)
            if cross is not None:
                return {
                    "imported": False,
                    "skipped": True,
                    "reason": "cross_platform_duplicate",
                    "existing_session_id": cross.session_id,
                }

        # 计算指标
        metrics = self._compute_metrics(session)

        # 写入 Parquet
        self.parquet_store.append_session(session)
        self.parquet_store.append_metrics(metrics)

        # 重算 TrainingLoad
        self._recompute_training_load()

        return {
            "imported": True,
            "session_id": session.session_id,
            "metrics_summary": {
                "vdot": metrics.vdot,
                "vdot_confidence": metrics.vdot_confidence,
                "tss": metrics.tss,
                "intensity_factor": metrics.intensity_factor,
                "pace_zone": metrics.pace_zone,
            },
        }

    def _compute_metrics(self, session: Session) -> TrainingMetrics:
        """计算 VDOT/TSS/IF/pace_zone."""
        vdot, confidence = calc_vdot(session.distance_m, session.duration_s)

        # IF 基于阈值配速（由 LTHR 估算，实际应由 UserConfig 覆盖）
        threshold_pace = _threshold_pace_from_lthr(DEFAULT_LTHR)
        if_val = calc_intensity_factor(session.avg_pace_s_per_km, threshold_pace)
        tss = calc_tss(session.duration_s, if_val)

        pace_zone = classify_pace_zone(session.avg_pace_s_per_km, vdot) if vdot else "E"

        return TrainingMetrics(
            session_id=session.session_id,
            vdot=vdot,
            vdot_confidence=confidence,
            tss=tss,
            intensity_factor=if_val,
            pace_zone=pace_zone,
        )

    def _next_session_id(self, activity_date: datetime) -> str:
        """生成下一个 session_id：查当天已存数量 +1."""
        date_str = activity_date.strftime("%Y%m%d")
        date_iso = activity_date.strftime("%Y-%m-%d")
        existing = self.parquet_store.query_sessions(
            date_from=date_iso, date_to=date_iso
        )
        return generate_session_id(date_str, len(existing))

    def _recompute_training_load(self) -> None:
        """重算 TrainingLoad（CTL/ATL/TSB）并写入 JSON.

        简化策略（ponytail: O(N) 扫描所有 sessions，N 通常 <10000，可接受）：
        按日聚合 TSS → 计算 EWMA → 写入当日 TrainingLoad
        """
        from collections import defaultdict

        all_sessions = self.parquet_store.query_sessions()
        if not all_sessions:
            return

        # 按日聚合 TSS
        all_metrics = self.parquet_store.query_metrics(
            [s.session_id for s in all_sessions]
        )
        metrics_map = {m.session_id: m for m in all_metrics}

        daily_tss: dict[str, float] = defaultdict(float)
        for s in all_sessions:
            date_str = s.activity_date.strftime("%Y-%m-%d")
            m = metrics_map.get(s.session_id)
            if m:
                daily_tss[date_str] += m.tss

        # 按日期排序
        sorted_dates = sorted(daily_tss.keys())
        if not sorted_dates:
            return

        # 补全缺失日期（无训练日 TSS=0）
        start = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
        end = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
        full_dates: list[str] = []
        cur = start
        while cur <= end:
            full_dates.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)
        full_tss = [daily_tss.get(d, 0.0) for d in full_dates]

        # 滑动计算每日 CTL/ATL/TSB（用历史窗口）
        for i, date_str in enumerate(full_dates):
            hist_tss = full_tss[: i + 1]
            ctl = calc_ctl(hist_tss)
            atl = calc_atl(hist_tss)
            tsb = calc_tsb(ctl, atl)
            # 当周累计 TSS
            week_start = max(0, i - 6)
            weekly_tss = sum(full_tss[week_start : i + 1])

            load = TrainingLoad(
                date=date_str,
                ctl=ctl,
                atl=atl,
                tsb=tsb,
                weekly_tss=weekly_tss,
                updated_at=datetime.now(timezone.utc),
            )
            self.json_store.save_load(load)
