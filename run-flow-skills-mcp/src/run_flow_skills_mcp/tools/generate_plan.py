"""generate_plan Tool（spec FR-PLAN-01, 6.2）.

薄包装：调 PlanService.generate_plan → service 已填充 plan_prompt → 重命名为 prompt 返回。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

# 降级 prompt（interaction-rules.md 第 4 条：错误发生时提供降级方案而非直接报错）
_DEGRADED_PROMPT = """训练计划生成失败。

## 失败原因
{error}

## 你的任务
1. 用简洁中文反馈失败原因
2. 引导用户使用正确参数（goal_type: 5k/10k/half_marathon/full_marathon；goal_time: HH:MM:SS）
3. 给出一个参数示例：goal_type=5k, goal_time=00:25:00,
   race_date=2026-10-19, weeks=8, current_vdot=40
"""


def generate_plan(
    goal_type: str,
    goal_time: str,
    race_date: str,
    weeks: int,
    current_vdot: float,
    _data_dir: Path | None = None,
) -> dict:
    """生成周期化训练计划.

    Args:
        goal_type: 目标类型（5k/10k/half_marathon/full_marathon）
        goal_time: 目标时间 HH:MM:SS
        race_date: 比赛日 YYYY-MM-DD
        weeks: 训练周数
        current_vdot: 当前 VDOT
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, plan_id, phases, pace_zones, target_vdot, vdot_gap}
        参数无效时返回降级结构（含 plan_id 占位、空 phases、prompt 含错误说明）。
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    try:
        result = services.plan_service.generate_plan(
            goal_type=goal_type,
            goal_time=goal_time,
            race_date=race_date,
            weeks=weeks,
            current_vdot=current_vdot,
        )
    except ValidationError as e:
        # 参数校验失败：降级返回结构化错误 + prompt（interaction-rules.md 第 4 条）
        return {
            "prompt": _DEGRADED_PROMPT.format(error=str(e)),
            "plan_id": "",
            "phases": [],
            "pace_zones": {},
            "target_vdot": current_vdot,
            "vdot_gap": 0.0,
            "error": str(e),
        }
    # service 返回 plan_prompt，统一为 prompt 字段名（spec 10.2）
    result["prompt"] = result.pop("plan_prompt")
    return result
