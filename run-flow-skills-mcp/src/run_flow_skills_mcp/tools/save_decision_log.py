"""save_decision_log Tool（spec FR-COACH-03, 6.2, 10.1, 10.2）.

薄包装：参数校验 → 调 CoachService.save_decision_log → 用 DECISION_TRACE_TEMPLATE 填充 prompt。

关键约束（spec 6.2）：
- reasoning/recommendation/trace_chain 由宿主 AI 生成后传入
- Tool 不调 LLM，只负责持久化
"""

from __future__ import annotations

from pathlib import Path

from run_flow_skills_mcp.prompts.decision_trace import DECISION_TRACE_TEMPLATE
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def save_decision_log(
    decision_type: str,
    inputs: dict,
    reasoning: str,
    recommendation: str,
    confidence: float,
    trace_chain: list[str],
    related_session_ids: list[str] | None = None,
    _data_dir: Path | None = None,
) -> dict:
    """保存 AI 决策记录.

    Args:
        decision_type: 决策类型（coach/plan/review/analyze）
        inputs: 决策输入数据（dict）
        reasoning: AI 推理过程（自然语言）
        recommendation: AI 最终建议
        confidence: 置信度（0-1）
        trace_chain: 溯源链步骤列表
        related_session_ids: 关联的 session_id 列表（可选）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, decision_id, saved} 或 {prompt, saved: False, error}
    """
    # 参数校验（输入层防御，spec 输入层约束）
    if not decision_type:
        return {
            "prompt": "参数错误：decision_type 不能为空",
            "saved": False,
            "error": "decision_type 不能为空",
        }
    if not isinstance(inputs, dict):
        return {
            "prompt": "参数错误：inputs 必须是字典",
            "saved": False,
            "error": "inputs 必须是字典",
        }
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        return {
            "prompt": f"参数错误：confidence={confidence} 越界（应为 0-1）",
            "saved": False,
            "error": f"confidence 越界: {confidence}",
        }
    if not isinstance(trace_chain, list):
        return {
            "prompt": "参数错误：trace_chain 必须是列表",
            "saved": False,
            "error": "trace_chain 必须是列表",
        }

    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.coach_service.save_decision_log(
        decision_type=decision_type,
        inputs=inputs,
        reasoning=reasoning,
        recommendation=recommendation,
        confidence=confidence,
        trace_chain=trace_chain,
        related_session_ids=related_session_ids,
    )

    # 用 DECISION_TRACE_TEMPLATE 填充 prompt
    prompt = DECISION_TRACE_TEMPLATE.format(
        inputs=inputs,
        reasoning=reasoning,
        recommendation=recommendation,
        confidence=confidence,
        related_session_ids=related_session_ids or [],
    )

    result["prompt"] = prompt
    return result
