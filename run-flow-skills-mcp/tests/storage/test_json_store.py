"""JSON 存储测试（spec 5.1, M-3 评审修正）."""
from datetime import datetime
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import (
    BodySignal,
    DecisionLog,
    TrainingLoad,
    TrainingPlan,
    UserConfig,
)
from run_flow_skills_mcp.storage.json_store import JsonStore


@pytest.fixture
def store(tmp_data_dir: Path) -> JsonStore:
    return JsonStore(data_dir=tmp_data_dir)


def test_save_and_query_load(store: JsonStore):
    load = TrainingLoad(
        date="2026-07-25",
        ctl=65.0,
        atl=58.0,
        tsb=7.0,
        weekly_tss=350.0,
        updated_at=datetime(2026, 7, 25, 23, 0),
    )
    store.save_load(load)
    result = store.query_load()
    assert len(result) == 1
    assert result[0].ctl == 65.0


def test_save_load_multiple_replaces_by_date(store: JsonStore):
    """同日 TrainingLoad 应覆盖（全量重写按 date 去重）."""
    load1 = TrainingLoad(
        date="2026-07-25", ctl=60.0, atl=55.0, tsb=5.0, weekly_tss=300.0,
        updated_at=datetime(2026, 7, 25, 10, 0),
    )
    load2 = TrainingLoad(
        date="2026-07-25", ctl=65.0, atl=58.0, tsb=7.0, weekly_tss=350.0,
        updated_at=datetime(2026, 7, 25, 23, 0),
    )
    store.save_load(load1)
    store.save_load(load2)
    result = store.query_load(date_from="2026-07-25", date_to="2026-07-25")
    assert len(result) == 1
    assert result[0].ctl == 65.0  # 后写入覆盖


def test_upsert_body_signal_overwrites_same_date(store: JsonStore):
    s1 = BodySignal(date="2026-07-25", hrv_rmssd=45.0, rpe=5)
    s2 = BodySignal(date="2026-07-25", hrv_rmssd=38.0, rpe=7)
    store.upsert_body_signal(s1)
    store.upsert_body_signal(s2)
    result = store.query_body_signals("2026-07-01", "2026-07-31")
    assert len(result) == 1
    assert result[0].hrv_rmssd == 38.0


def test_body_signals_monthly_sharding(store: JsonStore):
    """按月分文件（spec 5.1）."""
    s1 = BodySignal(date="2026-07-25", hrv_rmssd=45.0)
    s2 = BodySignal(date="2026-08-01", hrv_rmssd=42.0)
    store.upsert_body_signal(s1)
    store.upsert_body_signal(s2)

    assert (store.data_dir / "body_signals" / "body_signals_2026-07.json").exists()
    assert (store.data_dir / "body_signals" / "body_signals_2026-08.json").exists()


def test_append_decision(store: JsonStore):
    d = DecisionLog(
        decision_id="dec_20260725_001",
        timestamp=datetime(2026, 7, 25, 8, 0),
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="HRV 偏低",
        recommendation="E 区间 30 分钟",
        confidence=0.7,
        trace_chain=["HRV=38"],
    )
    store.append_decision(d)
    result = store.query_decisions()
    assert len(result) == 1
    assert result[0].decision_id == "dec_20260725_001"


def test_save_and_load_plan(store: JsonStore):
    plan = TrainingPlan(
        plan_id="plan_20260725_001",
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
        target_vdot=43.5,
        phases=[],
        created_at=datetime(2026, 7, 25),
        status="draft",
    )
    store.save_plan(plan)
    loaded = store.load_plan("plan_20260725_001")
    assert loaded is not None
    assert loaded.goal_type == "full_marathon"


def test_list_plans(store: JsonStore):
    for i in range(3):
        plan = TrainingPlan(
            plan_id=f"plan_2026072{i}_001",
            goal_type="full_marathon",
            goal_time="03:59:59",
            race_date="2026-10-19",
            weeks=12,
            current_vdot=42.0,
            target_vdot=43.5,
            phases=[],
            created_at=datetime(2026, 7, 25),
            status="draft",
        )
        store.save_plan(plan)
    plans = store.list_plans()
    assert len(plans) == 3


def test_load_user_config_empty_when_missing(store: JsonStore):
    """config.json 不存在时返回空 UserConfig（M-3 评审修正）."""
    config = store.load_user_config()
    assert config.max_hr is None
    assert config.lthr is None


def test_save_and_load_user_config(store: JsonStore):
    """M-3 评审修正：读写 data/config.json."""
    config = UserConfig(
        max_hr=195,
        lthr=170,
        age=32,
        weight_kg=68.0,
        gender="male",
        updated_at=datetime(2026, 7, 25),
    )
    store.save_user_config(config)
    loaded = store.load_user_config()
    assert loaded.max_hr == 195
    assert loaded.lthr == 170
    assert loaded.gender == "male"

    # 文件确实存在
    assert (store.data_dir / "config.json").exists()


def test_save_user_config_partial_update(store: JsonStore):
    """部分字段更新应保留其他字段."""
    full = UserConfig(max_hr=195, lthr=170, age=32)
    store.save_user_config(full)

    partial = UserConfig(max_hr=200)
    store.save_user_config(partial)

    loaded = store.load_user_config()
    assert loaded.max_hr == 200
    assert loaded.lthr == 170  # 保留
    assert loaded.age == 32  # 保留
