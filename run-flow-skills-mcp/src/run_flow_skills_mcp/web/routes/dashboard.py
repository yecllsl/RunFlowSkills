"""dashboard 路由 — 仪表盘概览页（spec 9.2 页面 1）.

提供仪表盘 HTML 片段和概览数据 API。
复用 analysis_service.calc_metrics + get_trends + review_service.get_period_summary。
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from run_flow_skills_mcp.web.app import templates
from run_flow_skills_mcp.web.deps import get_services

router = APIRouter()


def _build_dashboard_summary() -> dict:
    """组装仪表盘数据：KPI + 负荷趋势 + 本周摘要."""
    svc = get_services()
    today = datetime.now(UTC)
    date_to = today.strftime("%Y-%m-%d")
    date_from = (today - timedelta(days=42)).strftime("%Y-%m-%d")  # CTL 窗口

    # KPI：CTL/ATL/TSB/VDOT
    metrics = svc.analysis_service.calc_metrics(date_from, date_to)
    vdot_trend = metrics.get("vdot_trend", [])
    latest_vdot = vdot_trend[-1]["vdot"] if vdot_trend else None

    # 30 天负荷趋势
    load_trends = svc.analysis_service.get_trends(days=30, metric="load")
    load_series = load_trends.get("series", [])

    # 本周训练摘要
    weekly = svc.review_service.get_period_summary(period="week")

    return {
        "ctl": round(metrics.get("ctl", 0), 1),
        "atl": round(metrics.get("atl", 0), 1),
        "tsb": round(metrics.get("tsb", 0), 1),
        "vdot": round(latest_vdot, 1) if latest_vdot else None,
        "load_series": load_series,
        "weekly_summary": {
            "total_distance_km": round(weekly.get("total_distance", 0), 1),
            "total_tss": round(weekly.get("total_tss", 0), 1),
            "avg_vdot": round(weekly["avg_vdot"], 1) if weekly.get("avg_vdot") else None,
            "sessions_count": weekly.get("sessions_count", 0),
        },
    }


@router.get("/partials/dashboard", response_class=HTMLResponse)
async def dashboard_partial(request: Request):
    """返回仪表盘片段 HTML."""
    summary = _build_dashboard_summary()
    return templates.TemplateResponse(
        request,
        "partials/dashboard.html",
        {"summary": summary},
    )


@router.get("/api/dashboard/summary")
async def dashboard_summary_api():
    """返回仪表盘概览 JSON（图表用）."""
    return _build_dashboard_summary()
