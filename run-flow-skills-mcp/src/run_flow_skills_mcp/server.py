"""RunFlowSkills MCP Server 入口（spec 10.2）.

注册所有 14 个 MCP tools，通过 FastMCP 框架对外提供服务。
Tool 函数体使用懒导入（函数体内 import），确保 server.py 本身可正常加载。

Tool 不调 LLM（spec 10.2），只返回 {prompt, ...data}，由宿主 AI 用 prompt 调 LLM。
"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="run-flow-skills-mcp",
    instructions=(
        "跑步数据管理 + AI 教练 MCP Server，"
        "提供 14 个 tools：导入/查询/分析/计划/复盘/教练/统计/导出/决策溯源"
    ),
)


# ──────────────────────────────────────────
# 导入类（2 个）
# ──────────────────────────────────────────


@mcp.tool()
def import_file(file_path: str, force: bool = False, source: str = "") -> dict:
    """导入训练文件（FIT/TCX/GPX），自动解析 + 去重 + 计算指标.

    Args:
        file_path: 文件绝对路径
        force: 是否强制覆盖重复文件（默认 False）
        source: 数据源标注（garmin/apple/coros/strava/manual），可选

    Returns:
        {prompt, imported, session_id?, metrics_summary?, skipped?, reason?, error?}
    """
    from run_flow_skills_mcp.tools.import_file import import_file as _impl

    return _impl(file_path, force=force, source=source or None)


@mcp.tool()
def import_manual(manual_data: dict, force: bool = False) -> dict:
    """手动录入训练记录.

    Args:
        manual_data: {activity_date, distance_m, duration_s, source?, avg_hr?, max_hr?, notes?}
        force: 是否强制覆盖重复（默认 False）

    Returns:
        {prompt, imported, session_id?, metrics_summary?, error?}
    """
    from run_flow_skills_mcp.tools.import_manual import import_manual as _impl

    return _impl(manual_data, force=force)


# ──────────────────────────────────────────
# 查询分析类（4 个）
# ──────────────────────────────────────────


@mcp.tool()
def query_sessions(
    date_from: str = "",
    date_to: str = "",
    source: str = "",
    limit: int = 50,
) -> dict:
    """查询训练记录列表.

    Args:
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）
        source: 数据源过滤（可选）
        limit: 返回上限，默认 50

    Returns:
        {prompt, sessions, total}
    """
    from run_flow_skills_mcp.tools.query_sessions import query_sessions as _impl

    return _impl(
        date_from=date_from or None,
        date_to=date_to or None,
        source=source or None,
        limit=limit,
    )


@mcp.tool()
def calc_metrics(date_from: str, date_to: str) -> dict:
    """聚合区间训练指标（VDOT/TSS/CTL/ATL/TSB/心率区间）.

    Args:
        date_from: 起始日期 YYYY-MM-DD
        date_to: 结束日期 YYYY-MM-DD

    Returns:
        {prompt, vdot_trend, tss_sum, ctl, atl, tsb, hr_zones_dist}
    """
    from run_flow_skills_mcp.tools.calc_metrics import calc_metrics as _impl

    return _impl(date_from, date_to)


@mcp.tool()
def get_trends(days: int = 30, metric: str = "vdot") -> dict:
    """获取时间序列趋势.

    Args:
        days: 天数，默认 30
        metric: 指标（vdot/load/hrv），默认 vdot

    Returns:
        {prompt, series, change_pct, baseline}
    """
    from run_flow_skills_mcp.tools.get_trends import get_trends as _impl

    return _impl(days=days, metric=metric)


@mcp.tool()
def analyze_fatigue(days: int = 7) -> dict:
    """综合疲劳度评估（HRV + TSB + RPE）.

    Args:
        days: 分析天数，默认 7

    Returns:
        {prompt, fatigue_score, risk_level, main_factors, hrv_deviation, tsb}
    """
    from run_flow_skills_mcp.tools.analyze_fatigue import analyze_fatigue as _impl

    return _impl(days=days)


# ──────────────────────────────────────────
# 计划类（2 个）
# ──────────────────────────────────────────


@mcp.tool()
def generate_plan(
    goal_type: str,
    goal_time: str,
    race_date: str,
    weeks: int,
    current_vdot: float,
) -> dict:
    """生成周期化训练计划.

    Args:
        goal_type: 目标类型（5k/10k/half_marathon/full_marathon）
        goal_time: 目标时间 HH:MM:SS
        race_date: 比赛日 YYYY-MM-DD
        weeks: 训练周数
        current_vdot: 当前 VDOT

    Returns:
        {prompt, plan_id, phases, pace_zones, target_vdot, vdot_gap}
    """
    from run_flow_skills_mcp.tools.generate_plan import generate_plan as _impl

    return _impl(
        goal_type=goal_type,
        goal_time=goal_time,
        race_date=race_date,
        weeks=weeks,
        current_vdot=current_vdot,
    )


@mcp.tool()
def query_plan(plan_id: str = "") -> dict:
    """查询训练计划 + 执行忠实度.

    Args:
        plan_id: 计划 ID（空字符串返回最新计划）

    Returns:
        {prompt, plan, fidelity}
    """
    from run_flow_skills_mcp.tools.query_plan import query_plan as _impl

    return _impl(plan_id=plan_id or None)


# ──────────────────────────────────────────
# 复盘教练类（3 个）
# ──────────────────────────────────────────


@mcp.tool()
def get_period_summary(period: str = "week", date_ref: str = "") -> dict:
    """聚合周期训练数据（周/月/季/年）.

    Args:
        period: 周期类型（week/month/season/year），默认 week
        date_ref: 参考日期 YYYY-MM-DD（空字符串=今天）

    Returns:
        {prompt, total_distance, total_tss, avg_vdot,
         load_change, sessions_count, vdot_trend, hrv_trend}
    """
    from run_flow_skills_mcp.tools.get_period_summary import get_period_summary as _impl

    return _impl(period=period, date_ref=date_ref or None)


@mcp.tool()
def read_body_signals(date: str = "") -> dict:
    """读取今日身体信号 + 计算就绪状态.

    Args:
        date: 日期 YYYY-MM-DD（空字符串=今天）

    Returns:
        {prompt, hrv, resting_hr, sleep, rpe, baseline,
         deviation_pct, readiness_level, yesterday_session, recent_high_intensity}
    """
    from run_flow_skills_mcp.tools.read_body_signals import read_body_signals as _impl

    return _impl(date=date or None)


@mcp.tool()
def save_decision_log(
    decision_type: str,
    inputs: dict,
    reasoning: str,
    recommendation: str,
    confidence: float,
    trace_chain: list,
    related_session_ids: list = None,
) -> dict:
    """保存 AI 决策记录（含溯源链）.

    Args:
        decision_type: 决策类型（coach/plan/review/analyze）
        inputs: 决策输入数据
        reasoning: AI 推理过程
        recommendation: AI 最终建议
        confidence: 置信度（0-1）
        trace_chain: 溯源链步骤列表
        related_session_ids: 关联 session_id 列表（可选）

    Returns:
        {prompt, decision_id, saved}
    """
    from run_flow_skills_mcp.tools.save_decision_log import save_decision_log as _impl

    return _impl(
        decision_type=decision_type,
        inputs=inputs,
        reasoning=reasoning,
        recommendation=recommendation,
        confidence=confidence,
        trace_chain=trace_chain,
        related_session_ids=related_session_ids,
    )


# ──────────────────────────────────────────
# 统计导出类（3 个）
# ──────────────────────────────────────────


@mcp.tool()
def get_decision_trace(decision_id: str) -> dict:
    """查询决策溯源链.

    Args:
        decision_id: 决策 ID（dec_YYYYMMDD_NNN）

    Returns:
        {prompt, decision_id, found, trace?}
    """
    from run_flow_skills_mcp.tools.get_decision_trace import get_decision_trace as _impl

    return _impl(decision_id=decision_id)


@mcp.tool()
def get_statistics(
    dimension: str,
    date_from: str = "",
    date_to: str = "",
) -> dict:
    """按维度分组统计.

    Args:
        dimension: 分组维度（by_source/by_week/by_month/by_year/by_pace_zone/by_distance_range）
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）

    Returns:
        {prompt, groups, dimension}
    """
    from run_flow_skills_mcp.tools.get_statistics import get_statistics as _impl

    return _impl(
        dimension=dimension,
        date_from=date_from or None,
        date_to=date_to or None,
    )


@mcp.tool()
def export_data(
    export_format: str,
    filters: dict = None,
    include_ai_logs: bool = False,
) -> dict:
    """导出训练数据.

    Args:
        export_format: 导出格式（csv/json/parquet/md）
        filters: 过滤条件 {date_from?, date_to?, source?}（可选）
        include_ai_logs: 是否包含决策日志（默认 False）

    Returns:
        {prompt, file_path, rows_count, format} 或 {prompt, error}
    """
    from run_flow_skills_mcp.tools.export_data import export_data as _impl

    return _impl(format=export_format, filters=filters, include_ai_logs=include_ai_logs)


def main() -> None:
    """启动 MCP Server（stdio 传输模式）."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
