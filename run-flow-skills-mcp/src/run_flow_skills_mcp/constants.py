"""RunFlowSkills 默认配置与常量.

所有 # DEFAULT 标记的常量可被 data/config.json (UserConfig) 覆盖。
计算器读取顺序：data/config.json → 本文件默认值。
"""

from __future__ import annotations

from pathlib import Path

# ============ 数据目录默认值（Plan 2 _deps.py 使用）============
# 默认数据目录：run-flow-skills-mcp/data/（与 Plan 1 一致），由 Services 工厂初始化时创建
# constants.py 位于 run-flow-skills-mcp/src/run_flow_skills_mcp/，向上 3 级到 run-flow-skills-mcp/
DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data"

# ============ 用户生理参数默认值（M-3 评审修正）============
# DEFAULT — 用户可经 Web /settings 覆盖
DEFAULT_MAX_HR: int = 190
DEFAULT_LTHR: int = 165  # 乳酸阈值心率
DEFAULT_RESTING_HR: int = 60
DEFAULT_AGE: int = 30
DEFAULT_WEIGHT_KG: float = 65.0
DEFAULT_HEIGHT_CM: float = 170.0
DEFAULT_GENDER: str = "male"  # "male" | "female"，与 UserConfig.gender 对齐

# ============ VDOT 计算阈值（spec 8.1.1）============
VDOT_MIN_DISTANCE_M: float = 1500.0  # >=1500m 视为可信计算，否则标 "estimated"

# ============ EWMA 窗口（spec 8.1.3, 8.1.8）============
CTL_WINDOW_DAYS: int = 42
ATL_WINDOW_DAYS: int = 7
HRV_BASELINE_DAYS: int = 7

# ============ 配速区间占 VDOT 比例（spec 8.1.6）============
# (min_factor, max_factor)：配速 = VDOT 配速 / factor
PACE_ZONE_FACTORS: dict[str, tuple[float, float]] = {
    "E": (0.59, 0.74),  # 轻松跑
    "M": (0.75, 0.84),  # 马拉松配速
    "T": (0.88, 1.00),  # 乳酸阈值
    "I": (0.95, 1.00),  # 间歇
    "R": (1.00, 1.10),  # 重复
}

# ============ 心率区间占最大心率比例上限（spec 8.1.5）============
# 每个值表示该区间的上限占 max_hr 的比例；calc_hr_zones_boundaries 依此划分
HR_ZONE_FACTORS: dict[str, float] = {
    "Z1": 0.50,  # Z1: 0-50% max_hr
    "Z2": 0.60,  # Z2: 50-60% max_hr
    "Z3": 0.70,  # Z3: 60-70% max_hr
    "Z4": 0.90,  # Z4: 70-90% max_hr
    "Z5": 1.00,  # Z5: 90-100% max_hr
}

# ============ 去重容差（spec 5.3）============
DEDUP_TIME_TOLERANCE_S: int = 300  # 5 分钟
DEDUP_DISTANCE_TOLERANCE_PCT: float = 0.02  # 2%
DEDUP_DURATION_TOLERANCE_S: int = 30

# ============ 导入白名单（M-1 评审修正：含 GPX）============
SUPPORTED_IMPORT_EXT: tuple[str, ...] = (".fit", ".gpx", ".csv", ".tcx", ".xml")

# ============ Web 服务配置（spec 9.1）============
WEB_HOST: str = "127.0.0.1"
WEB_PORT: int = 8002

# ============ 文件大小/批量限制（spec 9.5）============
MAX_UPLOAD_FILE_SIZE_MB: int = 100
MAX_BATCH_UPLOAD_FILES: int = 100


def format_pace(s_per_km: float) -> str:
    """配速格式化为 M'SS"/km（spec 8.1.4）.

    >>> format_pace(340.0)
    "5'40\\"/km"
    """
    total_seconds = int(round(s_per_km))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}'{seconds:02d}\"/km"


def format_duration(seconds: int) -> str:
    """时长格式化为 HH:MM:SS（spec 8.1.4）.

    >>> format_duration(3725)
    "01:02:05"
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
