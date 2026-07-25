"""models.py 单元测试."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from run_flow_skills_mcp.models import (
    BodySignal,
    DecisionLog,
    PlanPhase,
    PlanSession,
    PlanWeek,
    Session,
    TrainingLoad,
    TrainingMetrics,
    TrainingPlan,
    UserConfig,
    generate_session_id,
)


def test_session_valid():
    s = Session(
        session_id="sess_20260725_001",
        activity_date=datetime(2026, 7, 25, 6, 0, 0),
        distance_m=10000.0,
        duration_s=3600,
        avg_pace_s_per_km=360.0,
        source="garmin",
    )
    assert s.session_id == "sess_20260725_001"
    assert s.avg_hr is None
    assert s.raw_file_hash is None


def test_session_invalid_distance_zero():
    with pytest.raises(ValidationError):
        Session(
            session_id="sess_20260725_001",
            activity_date=datetime(2026, 7, 25),
            distance_m=0,
            duration_s=3600,
            avg_pace_s_per_km=360.0,
            source="garmin",
        )


def test_session_invalid_duration_negative():
    with pytest.raises(ValidationError):
        Session(
            session_id="sess_20260725_001",
            activity_date=datetime(2026, 7, 25),
            distance_m=10000.0,
            duration_s=-1,
            avg_pace_s_per_km=360.0,
            source="garmin",
        )


def test_session_invalid_source():
    with pytest.raises(ValidationError):
        Session(
            session_id="sess_20260725_001",
            activity_date=datetime(2026, 7, 25),
            distance_m=10000.0,
            duration_s=3600,
            avg_pace_s_per_km=360.0,
            source="xiaomi",  # 不在枚举内
        )


def test_training_metrics_vdot_confidence_enum():
    m = TrainingMetrics(
        session_id="sess_20260725_001",
        vdot=45.0,
        vdot_confidence="high",
        tss=100.0,
        intensity_factor=0.85,
        pace_zone="T",
    )
    assert m.vdot_confidence == "high"


def test_training_metrics_invalid_confidence():
    with pytest.raises(ValidationError):
        TrainingMetrics(
            session_id="sess_20260725_001",
            vdot=45.0,
            vdot_confidence="medium",  # 不在枚举内
            tss=100.0,
            intensity_factor=0.85,
            pace_zone="T",
        )


def test_training_load_valid():
    load = TrainingLoad(
        date="2026-07-25",
        ctl=65.0,
        atl=58.0,
        tsb=7.0,
        weekly_tss=350.0,
        updated_at=datetime(2026, 7, 25, 23, 0, 0),
    )
    assert load.tsb == load.ctl - load.atl


def test_body_signal_optional_fields():
    b = BodySignal(date="2026-07-25")
    assert b.hrv_rmssd is None
    assert b.rpe is None


def test_decision_log_trace_chain():
    d = DecisionLog(
        decision_id="dec_20260725_001",
        timestamp=datetime(2026, 7, 25, 8, 0, 0),
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="HRV 偏低",
        recommendation="E 区间 30 分钟",
        confidence=0.7,
        trace_chain=["HRV=38", "baseline=45", "rule:HRV偏离>10%"],
    )
    assert len(d.trace_chain) == 3
    assert d.user_feedback is None


def test_training_plan_with_phases():
    plan = TrainingPlan(
        plan_id="plan_20260725_001",
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
        target_vdot=43.5,
        phases=[
            PlanPhase(
                phase_type="base",
                weeks=[
                    PlanWeek(
                        week_index=1,
                        sessions=[
                            PlanSession(day=0, pace_zone="E", duration_s=1800),
                        ],
                    )
                ],
            )
        ],
        created_at=datetime(2026, 7, 25),
        status="draft",
    )
    assert plan.phases[0].weeks[0].sessions[0].pace_zone == "E"


def test_user_config_all_optional():
    """M-3 评审修正：所有字段可空，回退到 constants.py 默认值."""
    c = UserConfig()
    assert c.max_hr is None
    assert c.lthr is None
    assert c.updated_at is None


def test_user_config_gender_enum():
    c = UserConfig(gender="male", age=35)
    assert c.gender == "male"
    with pytest.raises(ValidationError):
        UserConfig(gender="other")  # 不在枚举内


def test_generate_session_id_format():
    """sess_YYYYMMDD_NNN，NNN 从 001 起."""
    assert generate_session_id("20260725", 0) == "sess_20260725_001"
    assert generate_session_id("20260725", 5) == "sess_20260725_006"
