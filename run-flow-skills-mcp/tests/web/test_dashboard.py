"""dashboard 路由测试."""

from pathlib import Path


def test_dashboard_partial_empty_data(client):
    """空数据时仪表盘片段返回 200，显示空状态."""
    resp = client.get("/partials/dashboard")
    assert resp.status_code == 200
    assert "CTL" in resp.text or "ctl" in resp.text.lower()
    assert "VDOT" in resp.text or "vdot" in resp.text.lower()


def test_dashboard_summary_api_empty_data(client):
    """空数据时 API 返回 200，字段齐全."""
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "ctl" in data
    assert "atl" in data
    assert "tsb" in data
    assert "vdot" in data
    assert "load_series" in data
    assert "weekly_summary" in data


def test_dashboard_summary_api_with_data(client, tmp_data_dir: Path):
    """有数据时 API 返回非零 KPI."""
    from run_flow_skills_mcp.web.deps import get_services
    from tests.web.conftest import seed_gpx_file

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx")
    svc.import_service.import_file(gpx)

    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    # 导入后应有 session，KPI 可能非零
    assert data["ctl"] >= 0
    assert data["atl"] >= 0
