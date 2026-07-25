"""import_file Tool（spec FR-IMPORT-01, 6.2）.

薄包装：参数校验 → 调 ImportService.import_file → 附 prompt。
Tool 不调 LLM，由宿主 AI 用 prompt 调 LLM 生成自然语言反馈。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

# 导入文件反馈 prompt 模板（纯字符串）
_IMPORT_FILE_PROMPT = """用户已导入训练文件：{file_path}。

## 导入结果
- 状态: {status}
- session_id: {session_id}
- 指标摘要: {metrics_summary}

## 你的任务
1. 用简洁中文反馈导入结果（成功/跳过/失败）
2. 若跳过，说明原因（重复文件 / 跨平台重复）并询问是否 --force 重新导入
3. 若成功，简要解读 VDOT/TSS/配速区间，给出 1-2 句训练负荷提示
4. 若失败，给出降级方案（interaction-rules.md 第 4 条）：建议手动录入
"""


def import_file(
    file_path: str,
    force: bool = False,
    source: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """导入训练文件（FIT/TCX/GPX）.

    Args:
        file_path: 文件绝对路径
        force: 是否强制覆盖重复文件
        source: 数据源标注（garmin/apple/coros/strava/manual），可选
        _data_dir: 测试注入数据目录（生产用默认 data/）

    Returns:
        {prompt, imported, session_id?, metrics_summary?, skipped?, reason?, error?}
    """
    if not file_path:
        return {
            "prompt": _IMPORT_FILE_PROMPT.format(
                file_path="",
                status="失败",
                session_id="无",
                metrics_summary="文件路径为空",
            ),
            "imported": False,
            "error": "file_path 不能为空",
        }

    # 测试隔离：若传了 _data_dir，重置缓存以确保使用新目录
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.import_service.import_file(
        Path(file_path), force=force, source=source
    )

    # 附 prompt（根据结果状态填充）
    if result.get("imported"):
        status = "成功"
        session_id = result.get("session_id", "")
        metrics = result.get("metrics_summary", {})
    elif result.get("skipped"):
        status = f"跳过（{result.get('reason', '未知')}）"
        session_id = result.get("existing_session_id", "")
        metrics = {}
    else:
        status = "失败"
        session_id = "无"
        metrics = result.get("error", "未知错误")

    result["prompt"] = _IMPORT_FILE_PROMPT.format(
        file_path=file_path,
        status=status,
        session_id=session_id,
        metrics_summary=metrics,
    )
    return result
