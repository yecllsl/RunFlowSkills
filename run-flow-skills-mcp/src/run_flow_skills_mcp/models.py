"""RunFlowSkills Pydantic 数据模型.

所有核心实体在 models.py 统一定义，对应 spec 第四章。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ============ 类型别名 ============
SourceType = Literal["garmin", "coros", "apple", "suunto", "polar", "manual"]
PaceZone = Literal["E", "M", "T", "I", "R"]
GoalType = Literal["full_marathon", "half_marathon", "10k", "5k"]
Gender = Literal["male", "female"]


# ============ 4.1 Session ============
class Session(BaseModel):
    """单次跑步记录（核心实体，Parquet 按年分片）."""

    session_id: str = Field(..., pattern=r"^sess_\d{8}_\d{3}$")
    activity_date: datetime
    distance_m: float = Field(..., gt=0)
    duration_s: int = Field(..., gt=0)
    avg_pace_s_per_km: float = Field(..., gt=0)
    avg_hr: int | None = Field(None, ge=0, le=260)
    max_hr: int | None = Field(None, ge=0, le=260)
    hr_zones: dict[str, float] | None = None
    cadence: int | None = Field(None, ge=0, le=300)
    elevation_gain_m: float | None = Field(None, ge=0)
    source: SourceType
    raw_file_hash: str | None = None
    raw_file_path: str | None = None
    notes: str | None = None


# ============ 4.2 TrainingMetrics ============
class TrainingMetrics(BaseModel):
    """训练指标（由 Session 计算，Parquet 按年分片）."""

    session_id: str
    vdot: float | None = Field(None, ge=0, le=100)
    vdot_confidence: Literal["high", "estimated", "low"]
    tss: float = Field(..., ge=0)
    intensity_factor: float = Field(..., ge=0)
    efficiency_factor: float | None = None
    pace_zone: PaceZone


# ============ 4.3 TrainingLoad ============
class TrainingLoad(BaseModel):
    """训练负荷（日聚合，JSON 单文件追加）."""

    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    ctl: float
    atl: float
    tsb: float
    weekly_tss: float
    updated_at: datetime


# ============ 4.4 BodySignal ============
class BodySignal(BaseModel):
    """身体信号（日粒度，JSON 按月分文件）."""

    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    hrv_rmssd: float | None = Field(None, ge=0)
    hrv_sdnn: float | None = Field(None, ge=0)
    hrv_pnn50: float | None = Field(None, ge=0, le=100)
    resting_hr: int | None = Field(None, ge=0, le=260)
    sleep_quality: int | None = Field(None, ge=1, le=5)
    rpe: int | None = Field(None, ge=1, le=10)
    hrv_baseline: float | None = Field(None, ge=0)
    hrv_deviation_pct: float | None = None


# ============ 4.5 DecisionLog ============
class DecisionLog(BaseModel):
    """AI 决策记录（transparency 核心，JSON 按月分文件）."""

    decision_id: str = Field(..., pattern=r"^dec_\d{8}_\d{3}$")
    timestamp: datetime
    decision_type: Literal["coach", "plan_adjust", "review", "analysis"]
    inputs: dict
    reasoning: str
    recommendation: str
    confidence: float = Field(..., ge=0, le=1)
    trace_chain: list[str]
    related_session_ids: list[str] = []
    user_feedback: Literal["adopted", "rejected", "modified"] | None = None


# ============ 4.6 TrainingPlan ============
class PlanSession(BaseModel):
    """计划内单次训练."""

    day: int = Field(..., ge=0, le=6)
    pace_zone: Literal["E", "M", "T", "I", "R", "rest"]
    duration_s: int = Field(..., gt=0)
    distance_m: float | None = Field(None, gt=0)
    pace_range_s_per_km: tuple[float, float] | None = None
    hr_range: tuple[int, int] | None = None
    notes: str | None = None


class PlanWeek(BaseModel):
    """计划周."""

    week_index: int = Field(..., ge=1)
    sessions: list[PlanSession]


class PlanPhase(BaseModel):
    """计划阶段."""

    phase_type: Literal["base", "build", "peak", "taper"]
    weeks: list[PlanWeek]


class TrainingPlan(BaseModel):
    """训练计划（JSON 单文件/计划）."""

    plan_id: str = Field(..., pattern=r"^plan_\d{8}_\d{3}$")
    goal_type: GoalType
    goal_time: str
    race_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    weeks: int = Field(..., ge=1, le=52)
    current_vdot: float = Field(..., ge=0, le=100)
    target_vdot: float = Field(..., ge=0, le=100)
    phases: list[PlanPhase]
    created_at: datetime
    status: Literal["draft", "active", "completed", "abandoned"]


# ============ 4.7 UserConfig（M-3 评审修正）============
class UserConfig(BaseModel):
    """用户个人配置（JSON 单文件 data/config.json，覆盖 constants.py 默认值）."""

    max_hr: int | None = Field(None, ge=80, le=260)
    lthr: int | None = Field(None, ge=60, le=220)
    resting_hr: int | None = Field(None, ge=30, le=150)
    age: int | None = Field(None, ge=10, le=120)
    weight_kg: float | None = Field(None, gt=0, le=300)
    gender: Gender | None = None
    height_cm: float | None = Field(None, gt=0, le=300)
    updated_at: datetime | None = None


# ============ 工具函数 ============
def generate_session_id(date_str: str, existing_count: int) -> str:
    """生成 session_id：sess_YYYYMMDD_NNN.

    Args:
        date_str: 8 位日期字符串，如 "20260725"
        existing_count: 当天已存在的 session 数量

    Returns:
        形如 sess_20260725_001 的 ID（NNN = existing_count + 1）
    """
    return f"sess_{date_str}_{existing_count + 1:03d}"
