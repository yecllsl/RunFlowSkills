"""训练负荷计算器 - TSS/CTL/ATL/TSB（spec 8.1.2, 8.1.3, 8.1.7）."""
from __future__ import annotations

from run_flow_skills_mcp.constants import ATL_WINDOW_DAYS, CTL_WINDOW_DAYS


def calc_tss(duration_s: int, intensity_factor: float) -> float:
    """计算单次训练 TSS = duration_s × IF² × 100.

    Args:
        duration_s: 时长（秒）
        intensity_factor: 强度因子（IF）

    Returns:
        TSS 值
    """
    if duration_s <= 0 or intensity_factor <= 0:
        return 0.0
    return duration_s * intensity_factor**2 * 100 / 3600.0  # 归一化到小时


def calc_ewma(values: list[float], window: int) -> list[float]:
    """计算 EWMA 序列（spec 8.1.7）.

    α = 2/(N+1)，ewma[t] = α × values[t] + (1-α) × ewma[t-1]

    Args:
        values: 时间序列值（按时间升序）
        window: EWMA 窗口 N

    Returns:
        与 values 等长的 EWMA 序列，空输入返回空列表
    """
    if not values or window <= 0:
        return []
    alpha = 2.0 / (window + 1)
    result: list[float] = [values[0]]
    for v in values[1:]:
        prev = result[-1]
        result.append(alpha * v + (1 - alpha) * prev)
    return result


def calc_ctl(daily_tss: list[float]) -> float:
    """计算 CTL（42 天 EWMA 末值）."""
    if not daily_tss:
        return 0.0
    ewma = calc_ewma(daily_tss, CTL_WINDOW_DAYS)
    return ewma[-1]


def calc_atl(daily_tss: list[float]) -> float:
    """计算 ATL（7 天 EWMA 末值）."""
    if not daily_tss:
        return 0.0
    ewma = calc_ewma(daily_tss, ATL_WINDOW_DAYS)
    return ewma[-1]


def calc_tsb(ctl: float, atl: float) -> float:
    """计算 TSB = CTL - ATL."""
    return ctl - atl


def calc_intensity_factor(
    avg_pace_s_per_km: float, threshold_pace_s_per_km: float
) -> float:
    """计算 IF = threshold_pace / actual_pace.

    配速越快（秒数越小），IF 越高；实际配速 = 阈值配速时 IF=1.0。

    Args:
        avg_pace_s_per_km: 实际平均配速（秒/km）
        threshold_pace_s_per_km: 阈值配速（秒/km）

    Returns:
        强度因子 IF
    """
    if avg_pace_s_per_km <= 0 or threshold_pace_s_per_km <= 0:
        return 0.0
    return threshold_pace_s_per_km / avg_pace_s_per_km
