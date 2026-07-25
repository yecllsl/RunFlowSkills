"""VDOT 计算器 - Powers 方法（spec 8.1.1, FR-ANALYZE-01）.

参考：Jack Daniels' VDOT formula
VDOT = (-4.6 + 0.182258 * VO2 + 0.000104 * VO2^2) / (0.8 + 0.1894393 * e^(-0.012778*t) + 0.2989558 * e^(-0.1932605*t))
VO2 = 0.000104 * distance_m^2 / duration_min + 0.182258 * distance_m / duration_min - 4.60
"""
from __future__ import annotations

import math
from typing import Literal, Optional

from run_flow_skills_mcp.constants import VDOT_MIN_DISTANCE_M


def _compute_vo2(distance_m: float, duration_min: float) -> float:
    """计算 VO2（ml/kg/min）.

    标准公式：VO2 = 0.000104 * v^2 + 0.182258 * v - 4.60
    其中 v = distance_m / duration_min（速度，m/min）
    """
    v = distance_m / duration_min  # 速度 m/min
    return 0.000104 * v**2 + 0.182258 * v - 4.60


def _compute_vdot_from_vo2(vo2: float, duration_min: float) -> float:
    """由 VO2 和时长计算 VDOT.

    VDOT = VO2 / 疲劳因子
    疲劳因子 = 0.8 + 0.1894393 * e^(-0.012778*t) + 0.2989558 * e^(-0.1932605*t)
    """
    e1 = math.exp(-0.012778 * duration_min)
    e2 = math.exp(-0.1932605 * duration_min)
    denom = 0.8 + 0.1894393 * e1 + 0.2989558 * e2
    return vo2 / denom


def calc_vdot(distance_m: float, duration_s: int) -> tuple[Optional[float], Literal["high", "estimated", "low"]]:
    """计算 VDOT（Powers 方法）.

    Args:
        distance_m: 距离（米），>0
        duration_s: 时长（秒），>0

    Returns:
        (vdot, confidence):
        - 距离 >=1500m：(计算值, "high")
        - 距离 <1500m 但 >0：(估算值, "estimated")
        - 距离=0 或时长<=0：(None, "low")
    """
    if distance_m <= 0 or duration_s <= 0:
        return None, "low"

    duration_min = duration_s / 60.0
    vo2 = _compute_vo2(distance_m, duration_min)
    vdot = _compute_vdot_from_vo2(vo2, duration_min)

    # 边界保护：VO2 必须为正
    if vo2 <= 0 or vdot <= 0:
        return None, "low"

    confidence = "high" if distance_m >= VDOT_MIN_DISTANCE_M else "estimated"
    return round(vdot, 2), confidence
