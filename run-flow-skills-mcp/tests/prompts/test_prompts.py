"""prompts 模板单元测试."""
from run_flow_skills_mcp.prompts.analyze_prompt import ANALYZE_PROMPT
from run_flow_skills_mcp.prompts.plan_prompt import PLAN_PROMPT
from run_flow_skills_mcp.prompts.review_prompt import REVIEW_PROMPT
from run_flow_skills_mcp.prompts.coach_prompt import COACH_PROMPT
from run_flow_skills_mcp.prompts.decision_trace import DECISION_TRACE_TEMPLATE


def test_analyze_prompt_has_placeholders():
    """分析模板必须包含关键占位符（spec 8.2 分析规则）."""
    assert "{vdot}" in ANALYZE_PROMPT
    assert "{tss}" in ANALYZE_PROMPT
    assert "{ctl}" in ANALYZE_PROMPT
    assert "{atl}" in ANALYZE_PROMPT
    assert "{tsb}" in ANALYZE_PROMPT
    # 必须提示 AI 附数据依据 + 列风险因子 + 标注误差范围
    assert "数据依据" in ANALYZE_PROMPT
    assert "风险因子" in ANALYZE_PROMPT
    assert "误差范围" in ANALYZE_PROMPT


def test_plan_prompt_has_placeholders():
    """计划模板必须包含目标与 VDOT 占位符（spec 7.3）."""
    assert "{goal_type}" in PLAN_PROMPT
    assert "{goal_time}" in PLAN_PROMPT
    assert "{race_date}" in PLAN_PROMPT
    assert "{weeks}" in PLAN_PROMPT
    assert "{current_vdot}" in PLAN_PROMPT
    assert "{target_vdot}" in PLAN_PROMPT
    # 必须提示 AI 解释配速区间依据
    assert "配速区间" in PLAN_PROMPT


def test_review_prompt_has_placeholders():
    """复盘模板必须包含周期与负荷变化占位符（spec 7.4）."""
    assert "{period}" in REVIEW_PROMPT
    assert "{total_distance}" in REVIEW_PROMPT
    assert "{total_tss}" in REVIEW_PROMPT
    assert "{load_change}" in REVIEW_PROMPT
    assert "{vdot_trend}" in REVIEW_PROMPT
    # 必须提示 AI 列出跑量/负荷/VDOT/HRV/伤病风险/下周建议
    assert "跑量" in REVIEW_PROMPT
    assert "下周建议" in REVIEW_PROMPT


def test_coach_prompt_has_placeholders():
    """教练模板必须包含身体信号与就绪状态占位符（spec 7.5, 8.3）."""
    assert "{hrv}" in COACH_PROMPT
    assert "{tsb}" in COACH_PROMPT
    assert "{readiness_level}" in COACH_PROMPT
    assert "{today_plan}" in COACH_PROMPT
    # 必须提示 AI 给具体可执行建议 + 溯源链 + 置信度 + 替代方案
    assert "具体可执行" in COACH_PROMPT
    assert "溯源" in COACH_PROMPT
    assert "替代方案" in COACH_PROMPT


def test_decision_trace_template_has_placeholders():
    """决策溯源链模板（spec 4.5）."""
    assert "{inputs}" in DECISION_TRACE_TEMPLATE
    assert "{reasoning}" in DECISION_TRACE_TEMPLATE
    assert "{recommendation}" in DECISION_TRACE_TEMPLATE
    assert "{confidence}" in DECISION_TRACE_TEMPLATE


def test_prompts_format_correctly():
    """模板可用 .format() 填充."""
    filled = ANALYZE_PROMPT.format(
        vdot=45.0, tss=100.0, ctl=65.0, atl=58.0, tsb=7.0,
        hr_zones_dist="Z2:40%, Z3:30%", days=30,
    )
    assert "45.0" in filled
    assert "65.0" in filled
