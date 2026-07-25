"""analyze_fatigue Tool（spec FR-ANALYZE-05, 6.1, 8.2）.

薄包装：调 AnalysisService.analyze_fatigue → 附 prompt。
"""

from __future__ import annotations

from pathlib import Path

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_FATIGUE_PROMPT = """已分析用户 {days} 天疲劳度。

## 疲劳度评估
- 疲劳分数: {fatigue_score}（0-100，越高越疲劳）
- 风险等级: {risk_level}（low/moderate/high）
- 主要风险因子: {main_factors}
- HRV 偏离: {hrv_deviation}%
- TSB: {tsb}

## 你的任务（严格遵守 analysis-rules.md）
1. **风险因子**：列出主要风险因子（如 "HRV 偏离 -15%"/"TSB=-20"），禁止笼统结论
2. **数据依据**：每个判断必须引用具体数值
3. **误差范围**：若数据不足 7 天，标注 "置信度低"
4. **建议**：根据风险等级给具体可执行建议（low=正常训练/moderate=减量/high=休息）
"""


def analyze_fatigue(
    days: int = 7,
    _data_dir: Path | None = None,
) -> dict:
    """综合疲劳度评估.

    Args:
        days: 分析天数，默认 7
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, fatigue_score, risk_level, main_factors, hrv_deviation, tsb}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.analysis_service.analyze_fatigue(days=days)

    prompt = _FATIGUE_PROMPT.format(
        days=days,
        fatigue_score=data.get("fatigue_score", 0),
        risk_level=data.get("risk_level", "low"),
        main_factors=data.get("main_factors", []),
        hrv_deviation=data.get("hrv_deviation")
        if data.get("hrv_deviation") is not None
        else "无数据",
        tsb=data.get("tsb") if data.get("tsb") is not None else "无数据",
    )

    return {
        "prompt": prompt,
        "fatigue_score": data.get("fatigue_score", 0),
        "risk_level": data.get("risk_level", "low"),
        "main_factors": data.get("main_factors", []),
        "hrv_deviation": data.get("hrv_deviation"),
        "tsb": data.get("tsb"),
    }
