"""calc_metrics Tool（spec FR-ANALYZE-01, 6.1, 6.2）.

薄包装：调 AnalysisService.calc_metrics → 用 ANALYZE_PROMPT 填充 → 返回。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.prompts.analyze_prompt import ANALYZE_PROMPT
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def calc_metrics(
    date_from: str,
    date_to: str,
    _data_dir: Optional[Path] = None,
) -> dict:
    """聚合区间训练指标.

    Args:
        date_from: 起始日期 YYYY-MM-DD
        date_to: 结束日期 YYYY-MM-DD
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, vdot_trend, tss_sum, ctl, atl, tsb, hr_zones_dist}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.analysis_service.calc_metrics(date_from, date_to)

    # 心率区间分布格式化（zone:pct%, ...）
    hr_zones_dist = data.get("hr_zones_dist", {})
    hr_zones_str = ", ".join(
        f"{zone}:{pct * 100:.0f}%" for zone, pct in hr_zones_dist.items()
    ) or "无数据"

    # VDOT 趋势最新值
    vdot_trend = data.get("vdot_trend", [])
    latest_vdot = vdot_trend[-1]["vdot"] if vdot_trend else None

    # 计算天数（用于 prompt 上下文）
    try:
        days = (
            datetime.strptime(date_to, "%Y-%m-%d")
            - datetime.strptime(date_from, "%Y-%m-%d")
        ).days
    except (ValueError, TypeError):
        days = 30

    prompt = ANALYZE_PROMPT.format(
        days=days,
        vdot=latest_vdot if latest_vdot is not None else "无数据",
        tss=data.get("tss_sum", 0),
        ctl=data.get("ctl", 0),
        atl=data.get("atl", 0),
        tsb=data.get("tsb", 0),
        hr_zones_dist=hr_zones_str,
    )

    return {
        "prompt": prompt,
        "vdot_trend": vdot_trend,
        "tss_sum": data.get("tss_sum", 0),
        "ctl": data.get("ctl", 0),
        "atl": data.get("atl", 0),
        "tsb": data.get("tsb", 0),
        "hr_zones_dist": hr_zones_dist,
    }
