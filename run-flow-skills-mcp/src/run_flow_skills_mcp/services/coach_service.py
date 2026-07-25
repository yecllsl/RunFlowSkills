"""AI 教练编排服务（spec FR-COACH-01/02/03, 7.5, 8.3）.

编排 storage + calculators + plan_service：
- read_body_signals: 读取身体信号 + 综合就绪状态（HRV + TSB + RPE）
- get_decision_trace: 查询历史决策
- save_decision_log: 持久化决策记录

约束（coaching-rules.md）：
- 就绪状态综合 HRV + TSB + RPE，单一指标不可决策
- 24h 内高强度训练必须考虑
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal, cast

from run_flow_skills_mcp.calculators.hrv import (
    calc_hrv_baseline,
    calc_hrv_deviation_pct,
)
from run_flow_skills_mcp.models import DecisionLog
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

ReadinessLevel = Literal["green", "yellow", "red"]
# DecisionLog.decision_type 的 Literal 取值（与 models.py 保持一致）
DecisionType = Literal["coach", "plan_adjust", "review", "analysis"]


class CoachService:
    """AI 教练编排服务."""

    def __init__(self, parquet_store: ParquetStore, json_store: JsonStore) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def read_body_signals(self, date: str | None = None) -> dict:
        """读取身体信号 + 计算就绪状态.

        spec 6.2: 内部同时读取 BodySignal（HRV/RPE）和 TrainingLoad（TSB），
        综合计算 readiness_level（HRV 偏离 + TSB + RPE，单一指标不可决策）。
        """
        target_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now(UTC)
        date_str = target_date.strftime("%Y-%m-%d")

        # 取近 7 天身体信号
        start = (target_date - timedelta(days=7)).strftime("%Y-%m-%d")
        signals = self.json_store.query_body_signals(start, date_str)

        today_signal = next((s for s in signals if s.date == date_str), None)

        hrv = today_signal.hrv_rmssd if today_signal else None
        resting_hr = today_signal.resting_hr if today_signal else None
        sleep = today_signal.sleep_quality if today_signal else None
        rpe = today_signal.rpe if today_signal else None

        # HRV 基线与偏离
        hrv_history = [s.hrv_rmssd for s in signals if s.hrv_rmssd is not None]
        baseline = calc_hrv_baseline(hrv_history) if hrv_history else None
        deviation_pct = (
            calc_hrv_deviation_pct(hrv, baseline)
            if hrv is not None and baseline is not None
            else None
        )

        # TSB（从 TrainingLoad 取）
        loads = self.json_store.query_load(date_from=start, date_to=date_str)
        latest_load = loads[-1] if loads else None
        ctl = latest_load.ctl if latest_load else None
        atl = latest_load.atl if latest_load else None
        tsb = latest_load.tsb if latest_load else None

        # 就绪状态（HRV + TSB + RPE 综合计算，spec 6.2）
        readiness_level = self.compute_readiness_level(deviation_pct, tsb, rpe)

        # 昨日训练
        yesterday_str = (target_date - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_sessions = self.parquet_store.query_sessions(
            date_from=yesterday_str, date_to=yesterday_str
        )
        yesterday_session = (
            {
                "session_id": yesterday_sessions[0].session_id,
                "distance_m": yesterday_sessions[0].distance_m,
                "duration_s": yesterday_sessions[0].duration_s,
            }
            if yesterday_sessions
            else None
        )

        # 24h 内高强度训练检测
        recent_high_intensity = self._detect_recent_high_intensity(target_date)

        return {
            "hrv": hrv,
            "resting_hr": resting_hr,
            "sleep": sleep,
            "rpe": rpe,
            "baseline": baseline,
            "deviation_pct": deviation_pct,
            "ctl": ctl,
            "atl": atl,
            "tsb": tsb,
            "readiness_level": readiness_level,
            "yesterday_session": yesterday_session,
            "recent_high_intensity": recent_high_intensity,
        }

    def compute_readiness_level(
        self,
        hrv_deviation: float | None,
        tsb: float | None,
        rpe: int | None,
    ) -> ReadinessLevel:
        """综合就绪状态评估（HRV + TSB + RPE，coaching-rules.md 第 3 条）.

        策略（ponytail: 加权评分，单一指标不直接 red）：
        - 每指标计 0/1/2 分（normal/warning/danger）
        - 总分 0-1: green, 2-3: yellow, 4+: red
        - 缺失指标计 0 分
        """
        score = 0

        # HRV 偏离（负偏离越大越糟）
        if hrv_deviation is not None:
            if hrv_deviation <= -20:
                score += 2
            elif hrv_deviation <= -10:
                score += 1

        # TSB（负值越大越糟）
        if tsb is not None:
            if tsb <= -15:
                score += 2
            elif tsb <= 0:
                score += 1

        # RPE（越高越糟）
        if rpe is not None:
            if rpe >= 8:
                score += 2
            elif rpe >= 6:
                score += 1

        if score >= 4:
            return "red"
        if score >= 2:
            return "yellow"
        return "green"

    def get_decision_trace(self, decision_id: str) -> dict | None:
        """查询决策溯源链."""
        all_decisions = self.json_store.query_decisions()
        for d in all_decisions:
            if d.decision_id == decision_id:
                return {
                    "decision_id": d.decision_id,
                    "decision_type": d.decision_type,
                    "inputs": d.inputs,
                    "reasoning": d.reasoning,
                    "recommendation": d.recommendation,
                    "confidence": d.confidence,
                    "trace_chain": d.trace_chain,
                    "related_session_ids": d.related_session_ids,
                    "user_feedback": d.user_feedback,
                }
        return None

    def save_decision_log(
        self,
        decision_type: str,
        inputs: dict,
        reasoning: str,
        recommendation: str,
        confidence: float,
        trace_chain: list[str],
        related_session_ids: list[str] | None = None,
    ) -> dict:
        """保存决策记录."""
        decision_id = self._next_decision_id()
        decision = DecisionLog(
            decision_id=decision_id,
            timestamp=datetime.now(UTC),
            decision_type=cast(DecisionType, decision_type),
            inputs=inputs,
            reasoning=reasoning,
            recommendation=recommendation,
            confidence=confidence,
            trace_chain=trace_chain,
            related_session_ids=related_session_ids or [],
        )
        self.json_store.append_decision(decision)
        return {"decision_id": decision_id, "saved": True}

    def _detect_recent_high_intensity(self, target_date: datetime) -> dict | None:
        """检测 24h 内高强度训练（coaching-rules.md 第 6 条）."""
        # 取目标日期前 24 小时的 sessions
        start = target_date - timedelta(days=1)
        start_str = start.strftime("%Y-%m-%d")
        end_str = target_date.strftime("%Y-%m-%d")
        sessions = self.parquet_store.query_sessions(date_from=start_str, date_to=end_str)
        if not sessions:
            return None

        # 查询 metrics 判断是否高强度
        metrics = self.parquet_store.query_metrics([s.session_id for s in sessions])
        metrics_map = {m.session_id: m for m in metrics}

        high_intensity_zones = {"T", "I", "R"}
        for s in sessions:
            m = metrics_map.get(s.session_id)
            if m and m.pace_zone in high_intensity_zones:
                return {
                    "session_id": s.session_id,
                    "pace_zone": m.pace_zone,
                    "tss": m.tss,
                    "hours_ago": (target_date - s.activity_date).total_seconds() / 3600,
                }
        return None

    def _next_decision_id(self) -> str:
        """生成下一个 decision_id：dec_YYYYMMDD_NNN."""
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        existing = self.json_store.query_decisions()
        same_day = [d for d in existing if d.decision_id.startswith(f"dec_{date_str}")]
        return f"dec_{date_str}_{len(same_day) + 1:03d}"
