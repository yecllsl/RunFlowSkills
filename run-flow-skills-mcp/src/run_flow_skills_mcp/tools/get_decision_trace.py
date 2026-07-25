"""get_decision_trace Tool（spec FR-COACH-02, 6.2, 10.1）.

薄包装：调 CoachService.get_decision_trace → 附 prompt。
"""

from __future__ import annotations

from pathlib import Path

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_GET_TRACE_PROMPT = """已查询决策溯源链。

## 查询结果
- decision_id: {decision_id}
- 找到: {found}

## 决策详情
{trace_detail}

## 你的任务
1. 若找到，用简洁中文复述决策链（输入 → 推理 → 建议 → 置信度）
2. 若未找到，告知用户该决策不存在，建议调 save_decision_log 记录新决策
3. 若 confidence < 0.6，提示 "此决策仅供参考"
"""


def get_decision_trace(
    decision_id: str,
    _data_dir: Path | None = None,
) -> dict:
    """查询决策溯源链.

    Args:
        decision_id: 决策 ID（dec_YYYYMMDD_NNN）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, decision_id, found, trace?}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    trace = services.coach_service.get_decision_trace(decision_id)

    if trace is None:
        trace_detail = "（未找到）"
        found = False
    else:
        found = True
        trace_detail = (
            f"- 类型: {trace.get('decision_type', '')}\n"
            f"- 输入: {trace.get('inputs', {})}\n"
            f"- 推理: {trace.get('reasoning', '')}\n"
            f"- 建议: {trace.get('recommendation', '')}\n"
            f"- 置信度: {trace.get('confidence', 0)}\n"
            f"- 溯源链: {trace.get('trace_chain', [])}"
        )

    prompt = _GET_TRACE_PROMPT.format(
        decision_id=decision_id,
        found=found,
        trace_detail=trace_detail,
    )

    result: dict = {
        "prompt": prompt,
        "decision_id": decision_id,
        "found": found,
    }
    if trace is not None:
        result["trace"] = trace
    return result
