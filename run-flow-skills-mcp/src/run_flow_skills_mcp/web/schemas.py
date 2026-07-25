"""Web 请求模型（spec 9.3 API 路由用）.

手动录入和配置更新的 Pydantic 请求体，复用 models.UserConfig 的字段约束。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ManualInputRequest(BaseModel):
    """手动录入请求体（POST /api/import/manual）.

    activity_date/distance_m/duration_s 必填，其余可选。
    复用 ImportService.import_manual 的入参格式。
    """

    activity_date: str = Field(..., description="活动日期 ISO 格式，如 2026-07-20T06:00:00")
    distance_m: float = Field(..., gt=0, description="距离（米），>0")
    duration_s: int = Field(..., gt=0, description="时长（秒），>0")
    avg_hr: int | None = Field(None, ge=30, le=260, description="平均心率")
    max_hr: int | None = Field(None, ge=30, le=260, description="最大心率")
    source: Literal["garmin", "coros", "apple", "suunto", "polar", "manual"] = "manual"
    notes: str | None = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求体（PUT /api/config）.

    所有字段可选，支持部分更新。字段约束与 models.UserConfig 一致。
    """

    max_hr: int | None = Field(None, ge=80, le=260)
    lthr: int | None = Field(None, ge=60, le=220)
    resting_hr: int | None = Field(None, ge=30, le=150)
    age: int | None = Field(None, ge=10, le=120)
    weight_kg: float | None = Field(None, gt=0, le=300)
    gender: Literal["male", "female"] | None = None
    height_cm: float | None = Field(None, gt=0, le=300)
