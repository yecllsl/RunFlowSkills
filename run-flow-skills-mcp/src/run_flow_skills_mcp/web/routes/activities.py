"""activities 路由 — 活动列表页（spec 9.2 页面 2）.

提供活动列表片段、单题详情片段和 sessions JSON API。
直接读取 parquet_store（通过 Services 容器），因为 services 层无 list_sessions 方法。
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from run_flow_skills_mcp.tools._deps import get_services
from run_flow_skills_mcp.web.app import templates

router = APIRouter()

# 每页条数
_PAGE_SIZE = 20


def _format_pace(s_per_km: float) -> str:
    """配速格式化为 M'SS\"/km."""
    if not s_per_km or s_per_km <= 0:
        return "--"
    m = int(s_per_km // 60)
    s = int(s_per_km % 60)
    return f"{m}'{s:02d}\"/km"


def _format_duration(s: int) -> str:
    """时长格式化为 HH:MM:SS."""
    if not s:
        return "--"
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _list_sessions(date_from: str = "", date_to: str = "", source: str = "", page: int = 1) -> dict:
    """查询 session 列表 + 关联 metrics，分页返回."""
    svc = get_services()
    sessions = svc.parquet_store.query_sessions(
        date_from=date_from or None,
        date_to=date_to or None,
        source=source or None,
    )
    total = len(sessions)

    # 分页
    start = (page - 1) * _PAGE_SIZE
    end = start + _PAGE_SIZE
    page_sessions = sessions[start:end]

    # 关联 metrics
    if page_sessions:
        metrics = svc.parquet_store.query_metrics([s.session_id for s in page_sessions])
        metrics_map = {m.session_id: m for m in metrics}
    else:
        metrics_map = {}

    session_list = []
    for s in page_sessions:
        m = metrics_map.get(s.session_id)
        session_list.append(
            {
                "session_id": s.session_id,
                "activity_date": s.activity_date.strftime("%Y-%m-%d"),
                "distance_m": s.distance_m,
                "distance_km": round(s.distance_m / 1000, 2),
                "duration": _format_duration(s.duration_s),
                "pace": _format_pace(s.avg_pace_s_per_km),
                "avg_hr": s.avg_hr,
                "vdot": round(m.vdot, 1) if m and m.vdot else None,
                "source": s.source,
            }
        )

    return {
        "sessions": session_list,
        "total": total,
        "page": page,
        "total_pages": (total + _PAGE_SIZE - 1) // _PAGE_SIZE,
    }


@router.get("/partials/activities", response_class=HTMLResponse)
async def activities_partial(
    request: Request,
    date_from: str = "",
    date_to: str = "",
    source: str = "",
    page: int = 1,
):
    """返回活动列表片段（带筛选 + 分页）."""
    data = _list_sessions(date_from, date_to, source, page)
    return templates.TemplateResponse(
        request,
        "partials/activities.html",
        {
            **data,
            "current_date_from": date_from,
            "current_date_to": date_to,
            "current_source": source,
        },
    )


@router.get("/partials/activities/{session_id}", response_class=HTMLResponse)
async def activity_detail_partial(request: Request, session_id: str):
    """返回单题详情片段（HTMX OOB）."""
    svc = get_services()
    sessions = svc.parquet_store.query_sessions()
    session = next((s for s in sessions if s.session_id == session_id), None)
    if session is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    metrics = svc.parquet_store.query_metrics([session_id])
    m = metrics[0] if metrics else None

    return templates.TemplateResponse(
        request,
        "partials/activity_detail.html",
        {
            "session": session,
            "metrics": m,
            "format_pace": _format_pace,
            "format_duration": _format_duration,
        },
    )


@router.get("/api/sessions")
async def sessions_api(
    date_from: str = "",
    date_to: str = "",
    source: str = "",
    page: int = 1,
):
    """返回活动列表 JSON."""
    return _list_sessions(date_from, date_to, source, page)
