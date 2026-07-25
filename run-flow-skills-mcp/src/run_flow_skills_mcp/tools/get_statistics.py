"""get_statistics Tool（spec FR-STATS-01, 6.2, 7.6）.

薄包装：调 StatsService.get_statistics → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_STATS_PROMPT = """已查询用户训练统计（按 {dimension} 分组）。

## 统计结果
共 {groups_count} 个分组：

{groups_detail}

## 你的任务
1. 用简洁中文列出各分组关键指标（数量 + 总跑量 + 平均配速 + 总 TSS）
2. 若某分组显著偏高/偏低，提示并分析原因
3. 若分组为空，提示用户先导入数据
"""


def get_statistics(
    dimension: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """按维度分组统计.

    Args:
        dimension: 分组维度（by_source/by_week/by_month/by_year/by_pace_zone/by_distance_range）
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, groups, dimension}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.stats_service.get_statistics(
        dimension=dimension, date_from=date_from, date_to=date_to
    )

    groups = data.get("groups", [])
    groups_detail = "\n".join(
        f"- {g['key']}: {g['count']} 次, {g.get('total_distance_km', 0)} km, "
        f"平均配速 {g.get('avg_pace_s_per_km', 0)} s/km, TSS {g.get('total_tss', 0)}"
        for g in groups
    ) or "（无数据）"

    prompt = _STATS_PROMPT.format(
        dimension=dimension,
        groups_count=len(groups),
        groups_detail=groups_detail,
    )

    return {
        "prompt": prompt,
        "groups": groups,
        "dimension": dimension,
    }
