"""训练计划编排服务（spec FR-PLAN-01/02/03/04, 7.3）.

编排 calculators + storage：
- generate_plan: 周期化计划生成（base/build/peak/taper）+ 配速区间 + plan_prompt
- query_plan: 查询计划 + 计算执行忠实度
- compute_fidelity: planned_vs_actual 对比

漏练自适应（spec 7.3）：后续负荷重新分配，负荷守恒不追加。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, cast

from run_flow_skills_mcp.calculators.pace_zones import calc_pace_zones
from run_flow_skills_mcp.models import (
    GoalType,
    PlanPhase,
    PlanSession,
    PlanWeek,
    TrainingPlan,
)
from run_flow_skills_mcp.prompts.plan_prompt import PLAN_PROMPT
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

# 目标时间 → 目标 VDOT 反算表（简化版，ponytail: 经验值，不调 ML）
# 升级路径：v0.2.0 用 Powers 反算
_GOAL_VDOT_TABLE: dict[str, dict[str, float]] = {
    "full_marathon": {"03:59:59": 43.5, "03:29:59": 50.0, "02:59:59": 58.0},
    "half_marathon": {"01:59:59": 45.0, "01:44:59": 50.0, "01:29:59": 58.0},
    "10k": {"00:49:59": 48.0, "00:44:59": 53.0, "00:39:59": 60.0},
    "5k": {"00:24:59": 47.0, "00:21:59": 53.0, "00:19:59": 60.0},
}


def _estimate_target_vdot(goal_type: str, goal_time: str) -> float:
    """由目标反算 VDOT（简化查表，找不到时按 5% 提升估算）."""
    table = _GOAL_VDOT_TABLE.get(goal_type, {})
    if goal_time in table:
        return table[goal_time]
    # 取最接近的目标时间，按比例调整
    if table:
        def _total_seconds(t: str) -> int:
            parts = t.split(":")
            return sum(int(x) * (60 ** (len(parts) - 1 - i)) for i, x in enumerate(parts))

        closest = min(table.keys(), key=lambda t: abs(_total_seconds(t) - _total_seconds(goal_time)))
        return table[closest] * 1.05
    return 45.0  # 默认值


# 周期化阶段分配比例（base/build/peak/taper）
_PHASE_RATIOS: dict[str, float] = {
    "base": 0.34,   # 约 1/3
    "build": 0.33,  # 约 1/3
    "peak": 0.22,   # 约 1/5
    "taper": 0.11,  # 约 1/10
}


class PlanService:
    """训练计划编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def generate_plan(
        self,
        goal_type: str,
        goal_time: str,
        race_date: str,
        weeks: int,
        current_vdot: float,
    ) -> dict:
        """生成周期化训练计划."""
        target_vdot = _estimate_target_vdot(goal_type, goal_time)
        pace_zones = calc_pace_zones(current_vdot)
        vdot_gap = target_vdot - current_vdot

        # 周期化阶段
        phases = self._build_phases(weeks, pace_zones, current_vdot)

        plan_id = self._next_plan_id()
        plan = TrainingPlan(
            plan_id=plan_id,
            goal_type=cast(GoalType, goal_type),
            goal_time=goal_time,
            race_date=race_date,
            weeks=weeks,
            current_vdot=current_vdot,
            target_vdot=target_vdot,
            phases=phases,
            created_at=datetime.now(timezone.utc),
            status="draft",
        )
        self.json_store.save_plan(plan)

        # 生成 plan_prompt（供宿主 AI 解释计划）
        plan_prompt = PLAN_PROMPT.format(
            goal_type=goal_type,
            goal_time=goal_time,
            race_date=race_date,
            weeks=weeks,
            current_vdot=current_vdot,
            target_vdot=target_vdot,
            vdot_gap=vdot_gap,
            plan_struct=self._plan_struct_summary(phases),
        )

        return {
            "plan_id": plan_id,
            "phases": phases,
            "pace_zones": pace_zones,
            "target_vdot": target_vdot,
            "vdot_gap": vdot_gap,
            "plan_prompt": plan_prompt,
        }

    def query_plan(self, plan_id: Optional[str] = None) -> dict:
        """查询计划（plan_id=None 返回最新计划）+ 计算忠实度."""
        if plan_id:
            plan = self.json_store.load_plan(plan_id)
        else:
            plans = self.json_store.list_plans()
            plan = plans[-1] if plans else None

        if plan is None:
            return {"plan": None, "fidelity": None}

        fidelity = self.compute_fidelity(plan)
        return {"plan": plan, "fidelity": fidelity}

    def compute_fidelity(self, plan: TrainingPlan) -> dict:
        """计算计划执行忠实度（planned_vs_actual）.

        简化策略（ponytail: 按日期匹配，不精确到课表）：
        统计计划期内每周是否有对应训练日。
        """
        # 统计计划内总课表数
        planned_sessions = sum(
            len(week.sessions)
            for phase in plan.phases
            for week in phase.weeks
        )

        # 查询计划期内实际训练数
        race_date = datetime.strptime(plan.race_date, "%Y-%m-%d")
        start_date = race_date - timedelta(weeks=plan.weeks)
        actual_sessions = self.parquet_store.query_sessions(
            date_from=start_date.strftime("%Y-%m-%d"),
            date_to=plan.race_date,
        )
        completed = len(actual_sessions)

        fidelity_rate = completed / planned_sessions if planned_sessions > 0 else 0.0

        return {
            "planned_sessions": planned_sessions,
            "completed_sessions": completed,
            "fidelity_rate": round(fidelity_rate, 2),
            "missing_sessions": max(0, planned_sessions - completed),
        }

    def _build_phases(
        self, weeks: int, pace_zones: dict, vdot: float
    ) -> list[PlanPhase]:
        """构建周期化阶段（base/build/peak/taper）."""
        # 分配每周数（向下取整，剩余加到 base）
        base_weeks = max(1, int(weeks * _PHASE_RATIOS["base"]))
        build_weeks = max(1, int(weeks * _PHASE_RATIOS["build"]))
        peak_weeks = max(1, int(weeks * _PHASE_RATIOS["peak"]))
        taper_weeks = weeks - base_weeks - build_weeks - peak_weeks
        if taper_weeks < 1:
            taper_weeks = 1
            base_weeks = weeks - build_weeks - peak_weeks - taper_weeks

        phases: list[PlanPhase] = []
        week_idx = 1
        for phase_type, n_weeks in [
            ("base", base_weeks),
            ("build", build_weeks),
            ("peak", peak_weeks),
            ("taper", taper_weeks),
        ]:
            weeks_list: list[PlanWeek] = []
            for _ in range(n_weeks):
                weeks_list.append(self._build_week(week_idx, phase_type, pace_zones))
                week_idx += 1
            phases.append(
                PlanPhase(phase_type=cast(Literal["base", "build", "peak", "taper"], phase_type), weeks=weeks_list)
            )
        return phases

    def _build_week(
        self, week_index: int, phase_type: str, pace_zones: dict
    ) -> PlanWeek:
        """构建单周课表（简化：每 phase 固定模板）."""
        # ponytail: MVP 用固定模板，v0.2.0 可用 ML 生成
        e_lo, e_hi = pace_zones.get("E", (300, 400))
        m_lo, m_hi = pace_zones.get("M", (280, 320))
        t_lo, t_hi = pace_zones.get("T", (260, 290))

        if phase_type == "base":
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=3600,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="E", duration_s=2400,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=3000,
                            pace_range_s_per_km=(m_lo, m_hi)),
                PlanSession(day=6, pace_zone="E", duration_s=5400,
                            pace_range_s_per_km=(e_lo, e_hi)),
            ]
        elif phase_type == "build":
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=3600,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="T", duration_s=2400,
                            pace_range_s_per_km=(t_lo, t_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=3600,
                            pace_range_s_per_km=(m_lo, m_hi)),
                PlanSession(day=6, pace_zone="E", duration_s=5400,
                            pace_range_s_per_km=(e_lo, e_hi)),
            ]
        elif phase_type == "peak":
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=3000,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="T", duration_s=3000,
                            pace_range_s_per_km=(t_lo, t_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=4200,
                            pace_range_s_per_km=(m_lo, m_hi)),
                PlanSession(day=6, pace_zone="E", duration_s=4800,
                            pace_range_s_per_km=(e_lo, e_hi)),
            ]
        else:  # taper
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=2400,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="E", duration_s=1800,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=1800,
                            pace_range_s_per_km=(m_lo, m_hi)),
            ]
        return PlanWeek(week_index=week_index, sessions=sessions)

    def _next_plan_id(self) -> str:
        """生成下一个 plan_id：plan_YYYYMMDD_NNN."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        existing = self.json_store.list_plans()
        same_day = [p for p in existing if p.plan_id.startswith(f"plan_{date_str}")]
        return f"plan_{date_str}_{len(same_day) + 1:03d}"

    def _plan_struct_summary(self, phases: list[PlanPhase]) -> str:
        """生成 plan_struct 摘要（用于 plan_prompt 填充）."""
        lines: list[str] = []
        for phase in phases:
            n_weeks = len(phase.weeks)
            total_sessions = sum(len(w.sessions) for w in phase.weeks)
            lines.append(
                f"- {phase.phase_type}: {n_weeks} 周, {total_sessions} 次课表"
            )
        return "\n".join(lines)
