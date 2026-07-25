"""分析编排服务（spec FR-ANALYZE-01/04/05）.

编排 calculators + storage：
- calc_metrics: 聚合区间指标（VDOT 趋势/TSS/CTL/ATL/TSB/心率区间分布）
- get_trends: 时间序列（vdot/load/hrv）
- analyze_fatigue: 综合疲劳度评估（HRV + TSB + RPE）
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from run_flow_skills_mcp.calculators.fatigue import calc_fatigue_score
from run_flow_skills_mcp.calculators.hrv import (
    calc_hrv_baseline,
    calc_hrv_deviation_pct,
)
from run_flow_skills_mcp.calculators.training_load import (
    calc_atl,
    calc_ctl,
    calc_tsb,
)
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


class AnalysisService:
    """分析编排服务."""

    def __init__(self, parquet_store: ParquetStore, json_store: JsonStore) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def calc_metrics(self, date_from: str, date_to: str) -> dict:
        """聚合区间训练指标."""
        sessions = self.parquet_store.query_sessions(date_from=date_from, date_to=date_to)
        if not sessions:
            return {
                "vdot_trend": [],
                "tss_sum": 0.0,
                "ctl": 0.0,
                "atl": 0.0,
                "tsb": 0.0,
                "hr_zones_dist": {},
            }

        session_ids = [s.session_id for s in sessions]
        metrics = self.parquet_store.query_metrics(session_ids)
        metrics_map = {m.session_id: m for m in metrics}

        # VDOT 趋势
        vdot_trend = [
            {"date": s.activity_date.strftime("%Y-%m-%d"), "vdot": metrics_map[s.session_id].vdot}
            for s in sessions
            if s.session_id in metrics_map and metrics_map[s.session_id].vdot is not None
        ]

        # TSS 累计
        tss_sum = sum(m.tss for m in metrics if m.tss)

        # CTL/ATL/TSB：从 TrainingLoad 取最新值
        loads = self.json_store.query_load(date_from=date_from, date_to=date_to)
        if loads:
            latest = loads[-1]
            ctl, atl, tsb = latest.ctl, latest.atl, latest.tsb
        else:
            # 若无 TrainingLoad，临时计算
            daily_tss = self._daily_tss_map(sessions, metrics_map)
            sorted_tss = self._expand_daily_tss(daily_tss, date_from, date_to)
            ctl = calc_ctl(sorted_tss) if sorted_tss else 0.0
            atl = calc_atl(sorted_tss) if sorted_tss else 0.0
            tsb = calc_tsb(ctl, atl)

        # 心率区间分布（简化：从 sessions 的 hr_zones 聚合）
        hr_zones_dist: dict[str, float] = defaultdict(float)
        for s in sessions:
            if s.hr_zones:
                for zone, pct in s.hr_zones.items():
                    hr_zones_dist[zone] += pct
        # 归一化
        total = sum(hr_zones_dist.values())
        if total > 0:
            hr_zones_dist = {k: v / total for k, v in hr_zones_dist.items()}

        return {
            "vdot_trend": vdot_trend,
            "tss_sum": tss_sum,
            "ctl": ctl,
            "atl": atl,
            "tsb": tsb,
            "hr_zones_dist": dict(hr_zones_dist),
        }

    def get_trends(self, days: int = 30, metric: str = "vdot") -> dict:
        """获取时间序列趋势."""
        end = datetime.now(UTC)
        start = end - timedelta(days=days)
        date_from = start.strftime("%Y-%m-%d")
        date_to = end.strftime("%Y-%m-%d")

        if metric == "vdot":
            sessions = self.parquet_store.query_sessions(date_from=date_from, date_to=date_to)
            metrics = self.parquet_store.query_metrics([s.session_id for s in sessions])
            metrics_map = {m.session_id: m for m in metrics}
            series = [
                {
                    "date": s.activity_date.strftime("%Y-%m-%d"),
                    "value": metrics_map[s.session_id].vdot,
                }
                for s in sessions
                if s.session_id in metrics_map and metrics_map[s.session_id].vdot is not None
            ]
        elif metric == "load":
            loads = self.json_store.query_load(date_from=date_from, date_to=date_to)
            series = [
                {"date": load.date, "value": load.ctl, "atl": load.atl, "tsb": load.tsb}
                for load in loads
            ]
        elif metric == "hrv":
            signals = self.json_store.query_body_signals(date_from, date_to)
            series = [
                {"date": s.date, "value": s.hrv_rmssd} for s in signals if s.hrv_rmssd is not None
            ]
        else:
            return {"series": [], "change_pct": 0.0, "baseline": None}

        # 计算变化百分比和基线
        if len(series) >= 2:
            first_val = series[0]["value"] or 0
            last_val = series[-1]["value"] or 0
            change_pct = ((last_val - first_val) / first_val * 100) if first_val else 0.0
            non_null = [p["value"] for p in series if p["value"]]
            baseline = sum(non_null) / len(non_null) if non_null else None
        else:
            change_pct = 0.0
            baseline = series[0]["value"] if series else None

        return {"series": series, "change_pct": change_pct, "baseline": baseline}

    def analyze_fatigue(self, days: int = 7) -> dict:
        """综合疲劳度评估（HRV + TSB + RPE）."""
        end = datetime.now(UTC)
        start = end - timedelta(days=days)
        date_from = start.strftime("%Y-%m-%d")
        date_to = end.strftime("%Y-%m-%d")

        # HRV 数据
        signals = self.json_store.query_body_signals(date_from, date_to)
        hrv_values = [s.hrv_rmssd for s in signals if s.hrv_rmssd is not None]
        rpe_trend = [s.rpe for s in signals if s.rpe is not None] or None

        hrv_deviation: float | None = None
        if hrv_values:
            current_hrv = hrv_values[-1]
            baseline = calc_hrv_baseline(hrv_values[:-1] if len(hrv_values) > 1 else hrv_values)
            if baseline:
                hrv_deviation = calc_hrv_deviation_pct(current_hrv, baseline)

        # TSB
        loads = self.json_store.query_load(date_from=date_from, date_to=date_to)
        tsb = loads[-1].tsb if loads else None

        # 综合疲劳度（rpe_trend 已转为 None 当为空，确保 calc_fatigue_score 正确识别数据缺失）
        score, level, factors = calc_fatigue_score(hrv_deviation, tsb, rpe_trend)

        return {
            "fatigue_score": score,
            "risk_level": level,
            "main_factors": factors,
            "hrv_deviation": hrv_deviation,
            "tsb": tsb,
        }

    def _daily_tss_map(self, sessions: list, metrics_map: dict) -> dict[str, float]:
        """按日聚合 TSS."""
        daily: dict[str, float] = defaultdict(float)
        for s in sessions:
            date_str = s.activity_date.strftime("%Y-%m-%d")
            m = metrics_map.get(s.session_id)
            if m:
                daily[date_str] += m.tss
        return daily

    def _expand_daily_tss(
        self, daily: dict[str, float], date_from: str, date_to: str
    ) -> list[float]:
        """补全缺失日期（无训练日 TSS=0）."""
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        result: list[float] = []
        cur = start
        while cur <= end:
            result.append(daily.get(cur.strftime("%Y-%m-%d"), 0.0))
            cur += timedelta(days=1)
        return result
