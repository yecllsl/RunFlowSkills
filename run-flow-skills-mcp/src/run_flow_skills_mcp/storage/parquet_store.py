"""Parquet 存储引擎 - Session/Metrics 按年分片（spec 5.1）."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import polars as pl

from run_flow_skills_mcp.models import Session, TrainingMetrics


def _year_from_datetime(dt: datetime) -> int:
    """从 datetime 提取年份."""
    return dt.year


def _session_to_row(s: Session) -> dict[str, object]:
    """将 Session 转为可写入 Parquet 的字典行."""
    return {
        "session_id": s.session_id,
        "activity_date": s.activity_date,
        "distance_m": s.distance_m,
        "duration_s": s.duration_s,
        "avg_pace_s_per_km": s.avg_pace_s_per_km,
        "avg_hr": s.avg_hr,
        "max_hr": s.max_hr,
        "hr_zones": s.hr_zones,
        "cadence": s.cadence,
        "elevation_gain_m": s.elevation_gain_m,
        "source": s.source,
        "raw_file_hash": s.raw_file_hash,
        "raw_file_path": s.raw_file_path,
        "notes": s.notes,
    }


def _row_to_session(row: dict[str, object]) -> Session:
    """将 Parquet 字典行还原为 Session."""
    return Session.model_validate(row)


def _metrics_to_row(m: TrainingMetrics) -> dict[str, object]:
    """将 TrainingMetrics 转为可写入 Parquet 的字典行."""
    return {
        "session_id": m.session_id,
        "vdot": m.vdot,
        "vdot_confidence": m.vdot_confidence,
        "tss": m.tss,
        "intensity_factor": m.intensity_factor,
        "efficiency_factor": m.efficiency_factor,
        "pace_zone": m.pace_zone,
    }


class ParquetStore:
    """Parquet 存储引擎，Session/Metrics 按年分片."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.sessions_dir = data_dir / "sessions"
        self.metrics_dir = data_dir / "metrics"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def _sessions_path(self, year: int) -> Path:
        return self.sessions_dir / f"sessions_{year}.parquet"

    def _metrics_path(self, year: int) -> Path:
        return self.metrics_dir / f"metrics_{year}.parquet"

    def append_session(self, session: Session) -> None:
        """追加一个 Session 到对应年份的 parquet 文件."""
        year = _year_from_datetime(session.activity_date)
        path = self._sessions_path(year)
        new_df = pl.DataFrame([_session_to_row(session)])

        if path.exists():
            existing = pl.read_parquet(path)
            combined = pl.concat([existing, new_df], how="vertical_relaxed")
            combined.write_parquet(path)
        else:
            new_df.write_parquet(path)

    def append_metrics(self, metrics: TrainingMetrics) -> None:
        """追加一个 TrainingMetrics（与 Session 同年份）."""
        # 通过 session_id 查找对应年份，找不到则用当前年
        year = self._find_session_year(metrics.session_id)
        if year is None:
            year = datetime.now().year

        path = self._metrics_path(year)
        new_df = pl.DataFrame([_metrics_to_row(metrics)])

        if path.exists():
            existing = pl.read_parquet(path)
            combined = pl.concat([existing, new_df], how="vertical_relaxed")
            combined.write_parquet(path)
        else:
            new_df.write_parquet(path)

    def _find_session_year(self, session_id: str) -> Optional[int]:
        """从所有 sessions_YYYY.parquet 中查找 session_id 对应年份."""
        for path in self.sessions_dir.glob("sessions_*.parquet"):
            df = pl.scan_parquet(path).filter(
                pl.col("session_id") == session_id
            ).collect()
            if len(df) > 0:
                stem = path.stem  # sessions_YYYY
                return int(stem.split("_")[1])
        return None

    def query_sessions(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Session]:
        """查询 Session 列表.

        Args:
            date_from: 起始日期（含），格式 YYYY-MM-DD
            date_to: 结束日期（含当天），格式 YYYY-MM-DD
            source: 数据来源过滤
            limit: 返回条数上限（按时间倒序后截取）
        """
        # 收集所有年份的 parquet
        paths = sorted(self.sessions_dir.glob("sessions_*.parquet"))
        if not paths:
            return []

        df = pl.concat([pl.scan_parquet(p) for p in paths], how="vertical_relaxed")

        # 日期过滤（使用 datetime 对象比较，避免字符串解析歧义）
        if date_from:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            df = df.filter(pl.col("activity_date") >= dt_from)
        if date_to:
            # date_to 含当天，设为 23:59:59
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            df = df.filter(pl.col("activity_date") <= dt_to)
        if source:
            df = df.filter(pl.col("source") == source)

        df = df.sort("activity_date", descending=True)
        if limit:
            df = df.head(limit)

        collected = df.collect()
        return [_row_to_session(row) for row in collected.to_dicts()]

    def query_metrics(self, session_ids: list[str]) -> list[TrainingMetrics]:
        """查询给定 session_id 列表对应的 metrics."""
        if not session_ids:
            return []
        paths = sorted(self.metrics_dir.glob("metrics_*.parquet"))
        if not paths:
            return []

        df = pl.concat([pl.scan_parquet(p) for p in paths], how="vertical_relaxed")
        df = df.filter(pl.col("session_id").is_in(session_ids))
        collected = df.collect()
        return [TrainingMetrics.model_validate(row) for row in collected.to_dicts()]

    def find_by_hash(self, raw_file_hash: str) -> Optional[Session]:
        """通过 raw_file_hash 查找 Session（去重用）."""
        if not raw_file_hash:
            return None
        paths = sorted(self.sessions_dir.glob("sessions_*.parquet"))
        for path in paths:
            df = pl.scan_parquet(path).filter(
                pl.col("raw_file_hash") == raw_file_hash
            ).collect()
            if len(df) > 0:
                return _row_to_session(df.to_dicts()[0])
        return None
