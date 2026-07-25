"""复盘编排服务（spec FR-REVIEW-01/02, 7.4）.

编排 storage 聚合周期数据 + 对比上周期。
同比/环比必须明确时间窗口（analysis-rules.md 第 6 条）。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from run_flow_skills_mcp.services.analysis_service import AnalysisService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

_PERIOD_DAYS: dict[str, int] = {
    "week": 7,
    "month": 30,
    "season": 91,  # 13 周
    "year": 365,
}


class ReviewService:
    """复盘编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store
        self.analysis = AnalysisService(parquet_store, json_store)

    def get_period_summary(
        self, period: str = "week", date_ref: Optional[str] = None
    ) -> dict:
        """聚合周期数据 + 对比上周期.

        Args:
            period: week/month/season/year
            date_ref: 参考日期（默认今天），YYYY-MM-DD

        Returns:
            {total_distance, total_tss, avg_vdot, load_change, sessions_count,
             vdot_trend, hrv_trend}
        """
        days = _PERIOD_DAYS.get(period)
        if days is None:
            return self._empty_summary()

        end = (
            datetime.strptime(date_ref, "%Y-%m-%d")
            if date_ref
            else datetime.now(timezone.utc)
        )
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)

        date_from = start.strftime("%Y-%m-%d")
        date_to = end.strftime("%Y-%m-%d")

        # 本期 sessions
        sessions = self.parquet_store.query_sessions(
            date_from=date_from, date_to=date_to
        )
        if not sessions:
            return self._empty_summary()

        # 聚合指标
        metrics = self.parquet_store.query_metrics(
            [s.session_id for s in sessions]
        )
        metrics_map = {m.session_id: m for m in metrics}

        total_distance = sum(s.distance_m for s in sessions) / 1000.0  # km
        total_tss = sum(m.tss for m in metrics if m.tss)
        vdots = [m.vdot for m in metrics if m.vdot is not None]
        avg_vdot = sum(vdots) / len(vdots) if vdots else None

        # VDOT 趋势
        vdot_trend = [
            {"date": s.activity_date.strftime("%Y-%m-%d"),
             "vdot": metrics_map[s.session_id].vdot}
            for s in sessions
            if s.session_id in metrics_map and metrics_map[s.session_id].vdot
        ]

        # HRV 趋势
        signals = self.json_store.query_body_signals(date_from, date_to)
        hrv_trend = [
            {"date": sig.date, "hrv": sig.hrv_rmssd}
            for sig in signals if sig.hrv_rmssd is not None
        ]

        # 上期数据（环比）
        prev_sessions = self.parquet_store.query_sessions(
            date_from=prev_start.strftime("%Y-%m-%d"),
            date_to=start.strftime("%Y-%m-%d"),
        )
        prev_metrics = self.parquet_store.query_metrics(
            [s.session_id for s in prev_sessions]
        )
        prev_tss = sum(m.tss for m in prev_metrics if m.tss)
        load_change = {
            "tss_change": total_tss - prev_tss,
            "tss_change_pct": ((total_tss - prev_tss) / prev_tss * 100) if prev_tss > 0 else None,
            "comparison_window": f"vs 上{period}",
        }

        return {
            "total_distance": round(total_distance, 2),
            "total_tss": round(total_tss, 2),
            "avg_vdot": round(avg_vdot, 2) if avg_vdot else None,
            "load_change": load_change,
            "sessions_count": len(sessions),
            "vdot_trend": vdot_trend,
            "hrv_trend": hrv_trend,
        }

    def _empty_summary(self) -> dict:
        return {
            "total_distance": 0,
            "total_tss": 0,
            "avg_vdot": None,
            "load_change": {"tss_change": 0, "tss_change_pct": None, "comparison_window": ""},
            "sessions_count": 0,
            "vdot_trend": [],
            "hrv_trend": [],
        }
