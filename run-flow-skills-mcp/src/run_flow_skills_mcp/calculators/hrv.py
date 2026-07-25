"""HRV 计算器 - RMSSD/SDNN/pNN50 + 基线偏离（spec 8.1.8, FR-ANALYZE-04）."""

from __future__ import annotations

import math


def calc_rmssd(rr_intervals: list[float]) -> float | None:
    """计算 RMSSD（ms）= sqrt(mean(successive_diff²))."""
    if len(rr_intervals) < 2:
        return None
    diffs = [rr_intervals[i + 1] - rr_intervals[i] for i in range(len(rr_intervals) - 1)]
    mean_sq = sum(d * d for d in diffs) / len(diffs)
    return math.sqrt(mean_sq)


def calc_sdnn(rr_intervals: list[float]) -> float | None:
    """计算 SDNN（ms）= std(RR_intervals)."""
    if not rr_intervals:
        return None
    mean = sum(rr_intervals) / len(rr_intervals)
    variance = sum((r - mean) ** 2 for r in rr_intervals) / len(rr_intervals)
    return math.sqrt(variance)


def calc_pnn50(rr_intervals: list[float]) -> float | None:
    """计算 pNN50（%）= |diff|>50ms 的占比 × 100."""
    if len(rr_intervals) < 2:
        return None
    diffs = [abs(rr_intervals[i + 1] - rr_intervals[i]) for i in range(len(rr_intervals) - 1)]
    count_gt_50 = sum(1 for d in diffs if d > 50.0)
    return count_gt_50 / len(diffs) * 100.0


def calc_hrv_baseline(recent_hrv: list[float]) -> float | None:
    """计算 HRV 基线（7 天滚动均值，spec 8.1.8）.

    Args:
        recent_hrv: 最近 N 天的 HRV 值（RMSSD），最末元素为最新

    Returns:
        基线均值，空输入返回 None
    """
    if not recent_hrv:
        return None
    return sum(recent_hrv) / len(recent_hrv)


def calc_hrv_deviation_pct(current_hrv: float, baseline: float) -> float:
    """计算 HRV 偏离基线百分比.

    Returns:
        偏离百分比，正数=高于基线，负数=低于基线；baseline=0 时返回 0
    """
    if baseline <= 0:
        return 0.0
    return (current_hrv - baseline) / baseline * 100.0
