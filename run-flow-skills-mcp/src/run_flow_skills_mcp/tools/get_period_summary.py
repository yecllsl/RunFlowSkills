"""get_period_summary Tool（spec FR-REVIEW-01/02, 6.2, 7.4）.

薄包装：调 ReviewService.get_period_summary → 用 REVIEW_PROMPT 填充 → 返回。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.prompts.review_prompt import REVIEW_PROMPT
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def get_period_summary(
    period: str = "week",
    date_ref: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """聚合周期训练数据.

    Args:
        period: 周期类型（week/month/season/year）
        date_ref: 参考日期 YYYY-MM-DD（默认今天）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, total_distance, total_tss, avg_vdot, load_change,
         sessions_count, vdot_trend, hrv_trend}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.review_service.get_period_summary(period=period, date_ref=date_ref)

    # 填充 REVIEW_PROMPT
    load_change = data.get("load_change", {})
    vdot_trend = data.get("vdot_trend", [])
    hrv_trend = data.get("hrv_trend", [])

    prompt = REVIEW_PROMPT.format(
        period=period,
        total_distance=data.get("total_distance", 0),
        total_tss=data.get("total_tss", 0),
        load_change=load_change,
        vdot_trend=vdot_trend,
        hrv_trend=hrv_trend,
        sessions_count=data.get("sessions_count", 0),
    )

    return {
        "prompt": prompt,
        "total_distance": data.get("total_distance", 0),
        "total_tss": data.get("total_tss", 0),
        "avg_vdot": data.get("avg_vdot"),
        "load_change": load_change,
        "sessions_count": data.get("sessions_count", 0),
        "vdot_trend": vdot_trend,
        "hrv_trend": hrv_trend,
    }
