"""query_plan Tool（spec FR-PLAN-02/04, 6.2）.

薄包装：调 PlanService.query_plan → 附 prompt。
"""

from __future__ import annotations

from pathlib import Path

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_QUERY_PLAN_PROMPT = """已查询用户训练计划。

## 计划信息
{plan_info}

## 执行忠实度
{fidelity_info}

## 你的任务
1. 用简洁中文概述计划（目标 + 周数 + 周期化阶段）
2. 解释配速区间如何基于 VDOT 计算（spec 7.3）
3. 若忠实度 < 0.7，提示用户漏练情况并说明漏练自适应策略
4. 若计划为空，引导用户调 generate_plan 生成
"""


def query_plan(
    plan_id: str | None = None,
    _data_dir: Path | None = None,
) -> dict:
    """查询训练计划 + 执行忠实度.

    Args:
        plan_id: 计划 ID（None 返回最新）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, plan, fidelity}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.plan_service.query_plan(plan_id)
    plan = result.get("plan")
    fidelity = result.get("fidelity")

    if plan is None:
        plan_info = "（无计划）"
        fidelity_info = "（无）"
    else:
        plan_info = (
            f"- plan_id: {plan.plan_id}\n"
            f"- 目标: {plan.goal_type} {plan.goal_time}\n"
            f"- 比赛日: {plan.race_date}\n"
            f"- 周数: {plan.weeks}\n"
            f"- 当前 VDOT: {plan.current_vdot} → 目标 VDOT: {plan.target_vdot}"
        )
        if fidelity:
            fidelity_info = (
                f"- 计划课表数: {fidelity.get('planned_sessions', 0)}\n"
                f"- 已完成: {fidelity.get('completed_sessions', 0)}\n"
                f"- 忠实度: {fidelity.get('fidelity_rate', 0)}"
            )
        else:
            fidelity_info = "（无）"

    prompt = _QUERY_PLAN_PROMPT.format(
        plan_info=plan_info,
        fidelity_info=fidelity_info,
    )

    return {
        "prompt": prompt,
        "plan": plan,
        "fidelity": fidelity,
    }
