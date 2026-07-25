"""export_data Tool（spec FR-STATS-02, 6.2, 7.6）.

薄包装：调 StatsService.export_data → 附 prompt。

注意（interaction-rules.md 第 3 条）：导出前需用户确认。
本 tool 仅执行导出，确认由调用方（Skill/Web）处理。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_EXPORT_PROMPT = """已导出用户训练数据。

## 导出结果
- 格式: {format}
- 文件路径: {file_path}
- 记录数: {rows_count}
- 含决策日志: {include_ai_logs}

## 你的任务
1. 告知用户导出完成 + 文件路径
2. 提醒用户数据仅本地存储（data-safety-rules.md 第 1 条）
3. 若失败，给出降级方案（如换格式重试）
"""


def export_data(
    format: str,
    filters: Optional[dict] = None,
    include_ai_logs: bool = False,
    _data_dir: Optional[Path] = None,
) -> dict:
    """导出训练数据.

    Args:
        format: 导出格式（csv/json/parquet/md）
        filters: 过滤条件 {date_from?, date_to?, source?}
        include_ai_logs: 是否包含决策日志
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, file_path, rows_count, format} 或 {prompt, error}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.stats_service.export_data(
        format=format, filters=filters, include_ai_logs=include_ai_logs
    )

    if "error" in result:
        result["prompt"] = _EXPORT_PROMPT.format(
            format=format,
            file_path="（失败）",
            rows_count=0,
            include_ai_logs=include_ai_logs,
        )
        return result

    result["prompt"] = _EXPORT_PROMPT.format(
        format=result.get("format", format),
        file_path=result.get("file_path", ""),
        rows_count=result.get("rows_count", 0),
        include_ai_logs=include_ai_logs,
    )
    return result
