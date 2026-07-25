"""get_trends Tool（spec FR-ANALYZE-04, 6.1）.

薄包装：调 AnalysisService.get_trends → 附 prompt。
"""

from __future__ import annotations

from pathlib import Path

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_TREND_PROMPT = """已获取用户 {days} 天 {metric} 趋势数据。

## 趋势摘要
- 指标: {metric}
- 数据点数: {points}
- 变化百分比: {change_pct}%
- 基线值: {baseline}

## 你的任务
1. 用简洁中文描述趋势（上升/下降/平稳）+ 数据依据（analysis-rules.md 第 2 条）
2. 若 change_pct > 10% 或 < -10%，提示显著变化并分析原因
3. 若数据点 < 7，标注 "数据不足，置信度低"（analysis-rules.md 第 4 条）
"""


def get_trends(
    days: int = 30,
    metric: str = "vdot",
    _data_dir: Path | None = None,
) -> dict:
    """获取时间序列趋势.

    Args:
        days: 天数，默认 30
        metric: 指标类型（vdot/load/hrv）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, series, change_pct, baseline}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.analysis_service.get_trends(days=days, metric=metric)

    series = data.get("series", [])
    change_pct = data.get("change_pct", 0.0)
    baseline = data.get("baseline")

    prompt = _TREND_PROMPT.format(
        days=days,
        metric=metric,
        points=len(series),
        change_pct=round(change_pct, 2),
        baseline=baseline if baseline is not None else "无数据",
    )

    return {
        "prompt": prompt,
        "series": series,
        "change_pct": change_pct,
        "baseline": baseline,
    }
