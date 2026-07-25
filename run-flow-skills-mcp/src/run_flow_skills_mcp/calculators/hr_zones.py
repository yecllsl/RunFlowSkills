"""心率区间计算器（spec 8.1.5, FR-IMPORT-06）.

心率区间基于个人最大心率，不可使用 220-年龄通用公式（spec 8.1.5）。
默认值见 constants.DEFAULT_MAX_HR，可经 Web /settings 覆盖。
"""

from __future__ import annotations

from run_flow_skills_mcp.constants import DEFAULT_MAX_HR, HR_ZONE_FACTORS


def calc_hr_zones_boundaries(max_hr: int) -> dict[str, tuple[int, int]]:
    """计算各心率区间边界（bpm）.

    Args:
        max_hr: 个人最大心率

    Returns:
        {"Z1": (0, 50%max), "Z2": (50%, 60%), ..., "Z5": (90%, max)}
    """
    if max_hr <= 0:
        max_hr = DEFAULT_MAX_HR

    # 区间比例上限（spec constants.HR_ZONE_FACTORS）
    # Z1: 0-50%, Z2: 50-60%, Z3: 60-70%, Z4: 70-90%, Z5: 90-100%
    boundaries: dict[str, tuple[int, int]] = {
        "Z1": (0, int(HR_ZONE_FACTORS["Z1"] * max_hr)),  # 0-100
        "Z2": (int(HR_ZONE_FACTORS["Z1"] * max_hr), int(HR_ZONE_FACTORS["Z2"] * max_hr)),
        "Z3": (int(HR_ZONE_FACTORS["Z2"] * max_hr), int(HR_ZONE_FACTORS["Z3"] * max_hr)),
        "Z4": (int(HR_ZONE_FACTORS["Z3"] * max_hr), int(HR_ZONE_FACTORS["Z4"] * max_hr)),
        "Z5": (int(HR_ZONE_FACTORS["Z4"] * max_hr), max_hr),  # 90%-max
    }
    return boundaries


def classify_hr_samples(hr_samples: list[int], max_hr: int) -> dict[str, float]:
    """将心率样本分类到各区间，返回时间占比.

    Args:
        hr_samples: 心率样本列表（bpm）
        max_hr: 个人最大心率，0 时回退到 DEFAULT_MAX_HR

    Returns:
        {"Z1": 0.1, "Z2": 0.4, ...}，总和=1.0；空样本返回 {}
    """
    if not hr_samples:
        return {}

    if max_hr <= 0:
        max_hr = DEFAULT_MAX_HR

    boundaries = calc_hr_zones_boundaries(max_hr)
    counts: dict[str, int] = {z: 0 for z in boundaries}

    for hr in hr_samples:
        for zone, (lo, hi) in boundaries.items():
            if lo <= hr <= hi:
                counts[zone] += 1
                break
        else:
            # 高于所有区间上限归入 Z5
            if hr > max_hr:
                counts["Z5"] += 1

    total = len(hr_samples)
    return {z: count / total for z, count in counts.items() if count > 0}
