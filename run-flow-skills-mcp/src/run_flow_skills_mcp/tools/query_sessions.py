"""query_sessions Tool（spec FR-ANALYZE-01, 6.1）.

薄包装：参数校验 → 查 Parquet → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_QUERY_SESSIONS_PROMPT = """已查询到用户训练记录。

## 查询结果
- 时间范围: {date_from} ~ {date_to}
- 数据源过滤: {source}
- 共 {total} 条记录

## 记录列表
{sessions_brief}

## 你的任务
1. 用简洁中文列出关键训练记录（日期 + 距离 + 时长 + 配速）
2. 若用户问特定记录，调 calc_metrics 获取详细指标
3. 若无记录，提示用户导入数据
"""


def query_sessions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    _data_dir: Optional[Path] = None,
) -> dict:
    """查询训练记录列表.

    Args:
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）
        source: 数据源过滤（可选）
        limit: 返回上限，默认 50
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, sessions, total}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    sessions = services.parquet_store.query_sessions(
        date_from=date_from, date_to=date_to, source=source
    )

    # 截断
    sessions = sessions[:limit]

    # 转为摘要 dict（字段精简，避免 prompt 过长）
    session_list = [
        {
            "session_id": s.session_id,
            "activity_date": s.activity_date.strftime("%Y-%m-%d"),
            "distance_km": round(s.distance_m / 1000, 2),
            "duration_min": round(s.duration_s / 60, 1),
            "avg_pace_min_per_km": f"{int(s.avg_pace_s_per_km // 60)}'{int(s.avg_pace_s_per_km % 60):02d}\"",
            "source": s.source,
        }
        for s in sessions
    ]

    sessions_brief = "\n".join(
        f"- {s['activity_date']} | {s['distance_km']}km | {s['duration_min']}min | {s['avg_pace_min_per_km']}/km"
        for s in session_list
    ) or "（无记录）"

    prompt = _QUERY_SESSIONS_PROMPT.format(
        date_from=date_from or "全部",
        date_to=date_to or "全部",
        source=source or "全部",
        total=len(session_list),
        sessions_brief=sessions_brief,
    )

    return {
        "prompt": prompt,
        "sessions": session_list,
        "total": len(session_list),
    }
