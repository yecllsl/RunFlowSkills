"""activities 路由测试."""

from pathlib import Path


def test_activities_partial_empty(client):
    """空数据时活动列表返回 200，显示空状态."""
    resp = client.get("/partials/activities")
    assert resp.status_code == 200
    assert "暂无" in resp.text or "empty" in resp.text.lower() or "没有" in resp.text


def test_activities_api_empty(client):
    """空数据时 API 返回空列表."""
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["sessions"] == []


def test_activities_partial_with_data(client, tmp_data_dir: Path):
    """有数据时列表显示活动."""
    from run_flow_skills_mcp.tools._deps import get_services
    from tests.web.conftest import seed_gpx_file

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx", date="2026-07-20")
    svc.import_service.import_file(gpx)

    resp = client.get("/partials/activities")
    assert resp.status_code == 200
    assert "2026-07-20" in resp.text


def test_activities_api_with_data(client, tmp_data_dir: Path):
    """有数据时 API 返回 session 列表."""
    from run_flow_skills_mcp.tools._deps import get_services
    from tests.web.conftest import seed_gpx_file

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx", date="2026-07-20")
    svc.import_service.import_file(gpx)

    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["sessions"]) >= 1
    s = data["sessions"][0]
    assert "session_id" in s
    assert "activity_date" in s
    assert "distance_m" in s


def test_activity_detail_partial(client, tmp_data_dir: Path):
    """详情片段返回 session 详情."""
    from run_flow_skills_mcp.tools._deps import get_services
    from tests.web.conftest import seed_gpx_file

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx", date="2026-07-20")
    result = svc.import_service.import_file(gpx)
    session_id = result["session_id"]

    resp = client.get(f"/partials/activities/{session_id}")
    assert resp.status_code == 200
    assert session_id in resp.text


def test_activity_detail_not_found(client):
    """不存在的 session_id 返回 404."""
    resp = client.get("/partials/activities/sess_nonexistent_001")
    assert resp.status_code == 404
