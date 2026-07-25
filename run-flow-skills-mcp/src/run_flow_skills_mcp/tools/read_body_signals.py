"""read_body_signals Tool（spec FR-COACH-01, 6.2, 8.3）.

薄包装：调 CoachService.read_body_signals → 用 COACH_PROMPT 填充 → 返回。

注意：readiness_level 由 service 内部综合 HRV + TSB + RPE 计算（spec 6.2）。
"""

from __future__ import annotations

from pathlib import Path

from run_flow_skills_mcp.prompts.coach_prompt import COACH_PROMPT
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def read_body_signals(
    date: str | None = None,
    _data_dir: Path | None = None,
) -> dict:
    """读取今日身体信号 + 计算就绪状态.

    Args:
        date: 日期 YYYY-MM-DD（默认今天）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, hrv, resting_hr, sleep, rpe, baseline, deviation_pct,
         tsb, readiness_level, yesterday_session, recent_high_intensity}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.coach_service.read_body_signals(date=date)

    # 填充 COACH_PROMPT（None 值统一替换为 "无数据" 以避免 str.format 报错）
    prompt = COACH_PROMPT.format(
        hrv=data.get("hrv") if data.get("hrv") is not None else "无数据",
        hrv_baseline=data.get("baseline") if data.get("baseline") is not None else "无数据",
        hrv_deviation_pct=(
            round(data["deviation_pct"], 1) if data.get("deviation_pct") is not None else "无数据"
        ),
        resting_hr=data.get("resting_hr") if data.get("resting_hr") is not None else "无数据",
        sleep_quality=data.get("sleep") if data.get("sleep") is not None else "无数据",
        rpe=data.get("rpe") if data.get("rpe") is not None else "无数据",
        readiness_level=data.get("readiness_level", "green"),
        ctl=data.get("ctl", 0) if data.get("ctl") is not None else "无数据",
        atl=data.get("atl", 0) if data.get("atl") is not None else "无数据",
        tsb=data.get("tsb") if data.get("tsb") is not None else "无数据",
        yesterday_session=data.get("yesterday_session") or "无",
        recent_high_intensity=data.get("recent_high_intensity") or "无",
        today_plan="（请通过 query_plan 获取今日课表）",
    )

    return {
        "prompt": prompt,
        "hrv": data.get("hrv"),
        "resting_hr": data.get("resting_hr"),
        "sleep": data.get("sleep"),
        "rpe": data.get("rpe"),
        "baseline": data.get("baseline"),
        "deviation_pct": data.get("deviation_pct"),
        "tsb": data.get("tsb"),
        "readiness_level": data.get("readiness_level", "green"),
        "yesterday_session": data.get("yesterday_session"),
        "recent_high_intensity": data.get("recent_high_intensity"),
    }
