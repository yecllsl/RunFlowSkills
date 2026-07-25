"""配速区间计算器 - E/M/T/I/R（spec 8.1.6, FR-PLAN-03）.

配速区间基于个人 VDOT：
- E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110% VDOT
- 配速 = VDOT 参考配速 / factor（factor 越大，配速越快）
"""

from __future__ import annotations

from typing import Literal

from run_flow_skills_mcp.constants import PACE_ZONE_FACTORS

PaceZone = Literal["E", "M", "T", "I", "R"]

# VDOT 与参考配速的近似换算（VDOT 45 ≈ 4:36/km = 276s/km，即阈值配速）
# 公式：VDOT_pace = COEFF / VDOT（秒/km，经验近似）
# ponytail: 修正系数，原 4320 与注释 276*45=12420 不一致，导致 pace_zone 全部偏快
_VDOT_PACE_COEFF: float = 12420.0


def calc_vdot_pace_s_per_km(vdot: float) -> float:
    """计算 VDOT 对应的参考配速（秒/km）."""
    if vdot <= 0:
        return 0.0
    return _VDOT_PACE_COEFF / vdot


def calc_pace_zones(vdot: float) -> dict[str, tuple[float, float]]:
    """计算各配速区间（秒/km）.

    Args:
        vdot: 个人 VDOT 值

    Returns:
        {"E": (min_pace, max_pace), "M": ..., "T": ..., "I": ..., "R": ...}
        min_pace 为区间最快配速（秒数小），max_pace 为最慢（秒数大）
    """
    if vdot <= 0:
        return {}
    vdot_pace = calc_vdot_pace_s_per_km(vdot)
    zones: dict[str, tuple[float, float]] = {}
    for zone, (lo_factor, hi_factor) in PACE_ZONE_FACTORS.items():
        # factor 大 → 配速快（秒数小）
        fastest = vdot_pace / hi_factor
        slowest = vdot_pace / lo_factor
        zones[zone] = (fastest, slowest)
    return zones


def classify_pace_zone(avg_pace_s_per_km: float, vdot: float) -> PaceZone:
    """判断某配速属于哪个区间.

    Args:
        avg_pace_s_per_km: 实际平均配速
        vdot: 个人 VDOT

    Returns:
        E/M/T/I/R 中最接近的区间；若快于 R 区间返回 "R"，慢于 E 返回 "E"
    """
    zones = calc_pace_zones(vdot)
    if not zones:
        return "E"

    # 从最快区间（R）到最慢区间（E）依次检查
    for zone in ("R", "I", "T", "M", "E"):
        lo, hi = zones[zone]
        if lo <= avg_pace_s_per_km <= hi:
            return zone
        if avg_pace_s_per_km < lo and zone == "R":
            return "R"  # 比 R 还快
    return "E"  # 比 E 还慢
