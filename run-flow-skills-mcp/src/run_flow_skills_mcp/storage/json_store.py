"""JSON 存储引擎 - Load/BodySignal/DecisionLog/Plan/UserConfig（spec 5.1）."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from run_flow_skills_mcp.models import (
    BodySignal,
    DecisionLog,
    TrainingLoad,
    TrainingPlan,
    UserConfig,
)

T = TypeVar("T", bound=BaseModel)


def _load_json_list[T: BaseModel](path: Path, model_cls: type[T]) -> list[T]:
    """从 JSON 文件加载 list[model]."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [model_cls.model_validate(item) for item in data]


def _save_json_list(path: Path, items: list[BaseModel]) -> None:
    """保存 list[model] 到 JSON 文件."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            [item.model_dump(mode="json") for item in items],
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )


class JsonStore:
    """JSON 存储引擎."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.load_dir = data_dir / "load"
        self.body_signals_dir = data_dir / "body_signals"
        self.decisions_dir = data_dir / "decisions"
        self.plans_dir = data_dir / "plans"
        for d in [self.load_dir, self.body_signals_dir, self.decisions_dir, self.plans_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ============ TrainingLoad ============
    def save_load(self, load: TrainingLoad) -> None:
        """保存 TrainingLoad（同日覆盖）."""
        path = self.load_dir / "training_load.json"
        existing = _load_json_list(path, TrainingLoad)
        # 按 date 去重：移除同日记录，追加新记录
        existing = [item for item in existing if item.date != load.date]
        existing.append(load)
        existing.sort(key=lambda x: x.date)
        _save_json_list(path, existing)

    def query_load(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> list[TrainingLoad]:
        path = self.load_dir / "training_load.json"
        loads = _load_json_list(path, TrainingLoad)
        if date_from:
            loads = [item for item in loads if item.date >= date_from]
        if date_to:
            loads = [item for item in loads if item.date <= date_to]
        return sorted(loads, key=lambda x: x.date)

    # ============ BodySignal ============
    def upsert_body_signal(self, signal: BodySignal) -> None:
        """upsert BodySignal（同日覆盖）."""
        year_month = signal.date[:7]  # YYYY-MM
        path = self.body_signals_dir / f"body_signals_{year_month}.json"
        existing = _load_json_list(path, BodySignal)
        existing = [item for item in existing if item.date != signal.date]
        existing.append(signal)
        existing.sort(key=lambda x: x.date)
        _save_json_list(path, existing)

    def query_body_signals(self, date_from: str, date_to: str) -> list[BodySignal]:
        """按日期范围查询 BodySignal."""
        # 扫描所有月份文件
        results: list[BodySignal] = []
        for path in sorted(self.body_signals_dir.glob("body_signals_*.json")):
            signals = _load_json_list(path, BodySignal)
            results.extend([s for s in signals if date_from <= s.date <= date_to])
        return sorted(results, key=lambda x: x.date)

    # ============ DecisionLog ============
    def append_decision(self, decision: DecisionLog) -> None:
        """追加 DecisionLog（不覆盖）."""
        year_month = decision.timestamp.strftime("%Y-%m")
        path = self.decisions_dir / f"decisions_{year_month}.json"
        existing = _load_json_list(path, DecisionLog)
        existing.append(decision)
        _save_json_list(path, existing)

    def query_decisions(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> list[DecisionLog]:
        results: list[DecisionLog] = []
        for path in sorted(self.decisions_dir.glob("decisions_*.json")):
            decisions = _load_json_list(path, DecisionLog)
            for d in decisions:
                ts_date = d.timestamp.strftime("%Y-%m-%d")
                if date_from and ts_date < date_from:
                    continue
                if date_to and ts_date > date_to:
                    continue
                results.append(d)
        return sorted(results, key=lambda x: x.timestamp)

    # ============ TrainingPlan ============
    def save_plan(self, plan: TrainingPlan) -> None:
        path = self.plans_dir / f"{plan.plan_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(
                plan.model_dump(mode="json"),
                f,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

    def load_plan(self, plan_id: str) -> TrainingPlan | None:
        path = self.plans_dir / f"{plan_id}.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return TrainingPlan.model_validate(data)

    def list_plans(self) -> list[TrainingPlan]:
        plans: list[TrainingPlan] = []
        for path in sorted(self.plans_dir.glob("plan_*.json")):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            plans.append(TrainingPlan.model_validate(data))
        return plans

    # ============ UserConfig（M-3 评审修正）============
    def load_user_config(self) -> UserConfig:
        """读取 data/config.json，不存在返回空 UserConfig."""
        path = self.data_dir / "config.json"
        if not path.exists():
            return UserConfig()
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return UserConfig.model_validate(data)

    def save_user_config(self, config: UserConfig) -> None:
        """保存 UserConfig，部分字段更新（合并已有配置）."""
        existing = self.load_user_config()
        # 合并：新 config 中非 None 字段覆盖旧值
        merged_data = existing.model_dump(exclude_none=True)
        new_data = config.model_dump(exclude_none=True)
        merged_data.update(new_data)
        merged_data["updated_at"] = datetime.now(UTC).isoformat()

        path = self.data_dir / "config.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2, default=str)
