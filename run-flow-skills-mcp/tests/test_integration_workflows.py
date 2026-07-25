"""端到端工作流集成测试（spec 11.1）.

验证完整链路：
导入 → 查询 → 分析 → 计划 → 复盘 → 教练 → 决策 → 统计 → 导出

确保 tool 返回都含 prompt（spec 10.2）+ 数据一致性。
"""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.analyze_fatigue import analyze_fatigue
from run_flow_skills_mcp.tools.calc_metrics import calc_metrics
from run_flow_skills_mcp.tools.export_data import export_data
from run_flow_skills_mcp.tools.generate_plan import generate_plan
from run_flow_skills_mcp.tools.get_decision_trace import get_decision_trace
from run_flow_skills_mcp.tools.get_period_summary import get_period_summary
from run_flow_skills_mcp.tools.get_statistics import get_statistics
from run_flow_skills_mcp.tools.get_trends import get_trends
from run_flow_skills_mcp.tools.import_manual import import_manual
from run_flow_skills_mcp.tools.query_plan import query_plan
from run_flow_skills_mcp.tools.query_sessions import query_sessions
from run_flow_skills_mcp.tools.read_body_signals import read_body_signals
from run_flow_skills_mcp.tools.save_decision_log import save_decision_log


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed_full_workflow(tmp_path: Path):
    """灌入完整工作流数据：10 天 sessions + 7 天 HRV."""
    # 10 天训练记录
    for i in range(10):
        date = (datetime(2026, 7, 25) - timedelta(days=9 - i)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {
                "activity_date": date,
                "distance_m": 10000.0,
                "duration_s": 3000,  # 配速 5'00"/km
                "source": "garmin" if i % 2 == 0 else "apple",
                "avg_hr": 150,
            },
            _data_dir=tmp_path,
        )
    # 7 天 HRV
    services = _deps.get_services(tmp_path)
    for i in range(7):
        date = (datetime(2026, 7, 25) - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        services.coach_service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=45.0, rpe=5, resting_hr=55, sleep_quality=4)
        )
    _deps.reset_services_cache()


def test_full_workflow_import_to_export(tmp_path: Path):
    """完整工作流：导入 → 查询 → 分析 → 计划 → 复盘 → 教练 → 决策 → 统计 → 导出."""
    _deps.reset_services_cache()
    _seed_full_workflow(tmp_path)

    # 1. 查询验证导入成功
    q = query_sessions(date_from="2026-07-15", date_to="2026-07-25", _data_dir=tmp_path)
    assert q["total"] >= 10
    assert "prompt" in q

    # 2. 分析指标
    m = calc_metrics(date_from="2026-07-15", date_to="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in m
    assert m["tss_sum"] > 0

    # 3. 趋势
    t = get_trends(days=30, metric="vdot", _data_dir=tmp_path)
    assert "prompt" in t

    # 4. 计划生成
    p = generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=42.0,
        _data_dir=tmp_path,
    )
    assert "prompt" in p
    plan_id = p["plan_id"]

    # 5. 计划查询 + 忠实度
    pq = query_plan(plan_id, _data_dir=tmp_path)
    assert "prompt" in pq
    assert pq["plan"] is not None

    # 6. 复盘
    r = get_period_summary(period="week", date_ref="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in r
    assert r["sessions_count"] >= 1

    # 7. 教练（身体信号）
    c = read_body_signals(date="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in c
    assert c["readiness_level"] in ("green", "yellow", "red")

    # 8. 疲劳分析
    f = analyze_fatigue(days=7, _data_dir=tmp_path)
    assert "prompt" in f

    # 9. 保存决策
    d = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 45, "tsb": 5},
        reasoning="HRV 正常，TSB 充足",
        recommendation="E 区间 30 分钟",
        confidence=0.8,
        trace_chain=["HRV=45", "baseline=45", "TSB=5"],
        related_session_ids=[q["sessions"][0]["session_id"]],
        _data_dir=tmp_path,
    )
    assert d["saved"] is True
    decision_id = d["decision_id"]

    # 10. 查询决策溯源
    dt = get_decision_trace(decision_id, _data_dir=tmp_path)
    assert dt["found"] is True
    assert "prompt" in dt

    # 11. 统计
    s = get_statistics(dimension="by_source", _data_dir=tmp_path)
    assert "prompt" in s
    assert len(s["groups"]) > 0

    # 12. 导出
    e = export_data(format="json", include_ai_logs=True, _data_dir=tmp_path)
    assert e["rows_count"] > 0
    assert Path(e["file_path"]).exists()
    assert "prompt" in e


def test_all_tools_return_prompt(tmp_path: Path):
    """所有 14 个 tool 调用后必须返回 prompt 字段（spec 10.2）."""
    _deps.reset_services_cache()
    _seed_full_workflow(tmp_path)

    results = [
        import_manual(
            {"activity_date": "2026-07-26T06:00:00", "distance_m": 5000.0, "duration_s": 1500, "source": "manual"},
            _data_dir=tmp_path,
        ),
        query_sessions(_data_dir=tmp_path),
        calc_metrics("2026-07-15", "2026-07-25", _data_dir=tmp_path),
        get_trends(_data_dir=tmp_path),
        analyze_fatigue(_data_dir=tmp_path),
        generate_plan("5k", "00:25:00", "2026-10-19", 8, 42.0, _data_dir=tmp_path),
        query_plan(_data_dir=tmp_path),
        get_period_summary(_data_dir=tmp_path),
        read_body_signals("2026-07-25", _data_dir=tmp_path),
        save_decision_log("coach", {"test": 1}, "r", "rec", 0.5, ["a"], _data_dir=tmp_path),
        get_statistics("by_source", _data_dir=tmp_path),
        export_data("csv", _data_dir=tmp_path),
    ]

    for i, r in enumerate(results):
        assert "prompt" in r, f"第 {i+1} 个 tool 缺少 prompt 字段: {r}"

    # import_file 单独测（需要真实文件）
    gpx = tmp_path / "test.gpx"
    gpx.write_text(
        '<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">'
        '<trk><trkseg>'
        '<trkpt lat="39.9" lon="116.4"><time>2026-07-27T06:00:00Z</time></trkpt>'
        '<trkpt lat="39.91" lon="116.41"><time>2026-07-27T06:30:00Z</time></trkpt>'
        '</trkseg></trk></gpx>',
        encoding="utf-8",
    )
    from run_flow_skills_mcp.tools.import_file import import_file
    r = import_file(str(gpx), _data_dir=tmp_path)
    assert "prompt" in r

    # get_decision_trace 单独测
    saved = save_decision_log("coach", {"x": 1}, "r", "rec", 0.7, ["a"], _data_dir=tmp_path)
    r = get_decision_trace(saved["decision_id"], _data_dir=tmp_path)
    assert "prompt" in r


def test_decision_log_persistence_across_tools(tmp_path: Path):
    """save_decision_log 持久化后，get_decision_trace 可查询（数据一致性）."""
    _deps.reset_services_cache()
    saved = save_decision_log(
        decision_type="analysis",
        inputs={"vdot": 45},
        reasoning="VDOT 上升",
        recommendation="加量",
        confidence=0.7,
        trace_chain=["vdot=45", "上周=43"],
        _data_dir=tmp_path,
    )
    _deps.reset_services_cache()  # 清缓存模拟新进程

    trace = get_decision_trace(saved["decision_id"], _data_dir=tmp_path)
    assert trace["found"] is True
    assert trace["trace"]["recommendation"] == "加量"
    assert trace["trace"]["confidence"] == 0.7


def test_plan_fidelity_with_actual_sessions(tmp_path: Path):
    """计划生成后导入实际训练，fidelity 应反映完成情况."""
    _deps.reset_services_cache()
    # 生成计划（8 周）
    gen = generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
        _data_dir=tmp_path,
    )
    # 导入一些训练（在计划期内）
    import_manual(
        {"activity_date": "2026-08-26T06:00:00", "distance_m": 8000.0, "duration_s": 2400, "source": "manual"},
        _data_dir=tmp_path,
    )
    import_manual(
        {"activity_date": "2026-08-28T06:00:00", "distance_m": 6000.0, "duration_s": 1800, "source": "manual"},
        _data_dir=tmp_path,
    )
    _deps.reset_services_cache()

    result = query_plan(gen["plan_id"], _data_dir=tmp_path)
    fidelity = result["fidelity"]
    assert fidelity is not None
    assert fidelity["completed_sessions"] >= 2
    assert 0 <= fidelity["fidelity_rate"] <= 1
