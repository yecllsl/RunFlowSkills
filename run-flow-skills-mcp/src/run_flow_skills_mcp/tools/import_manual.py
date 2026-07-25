"""import_manual Tool（spec FR-IMPORT-05, 6.2）.

薄包装：参数校验 → 调 ImportService.import_manual → 附 prompt。
"""

from __future__ import annotations

from pathlib import Path

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_IMPORT_MANUAL_PROMPT = """用户已手动录入训练记录。

## 录入结果
- 状态: {status}
- session_id: {session_id}
- 指标摘要: {metrics_summary}

## 你的任务
1. 用简洁中文反馈录入结果
2. 若成功，简要解读 VDOT/TSS/配速区间
3. 若失败，明确指出哪个字段无效，给出正确格式示例
"""


def import_manual(
    manual_data: dict,
    force: bool = False,
    _data_dir: Path | None = None,
) -> dict:
    """手动录入训练记录.

    Args:
        manual_data: {activity_date, distance_m, duration_s, source?, avg_hr?, max_hr?, notes?}
        force: 是否强制覆盖重复
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, imported, session_id?, metrics_summary?, error?}
    """
    if not isinstance(manual_data, dict):
        return {
            "prompt": _IMPORT_MANUAL_PROMPT.format(
                status="失败", session_id="无", metrics_summary="manual_data 必须是字典"
            ),
            "imported": False,
            "error": "manual_data 必须是字典",
        }

    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.import_service.import_manual(manual_data, force=force)

    if result.get("imported"):
        status = "成功"
        session_id = result.get("session_id", "")
        metrics = result.get("metrics_summary", {})
    else:
        status = "失败"
        session_id = "无"
        metrics = result.get("error", "未知错误")

    result["prompt"] = _IMPORT_MANUAL_PROMPT.format(
        status=status, session_id=session_id, metrics_summary=metrics
    )
    return result
