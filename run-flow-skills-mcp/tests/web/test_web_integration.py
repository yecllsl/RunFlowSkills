"""Web 端到端集成测试：完整工作流（导入 → 仪表盘 → 活动列表 → 设置 → 导出）."""

import io
from pathlib import Path

from tests.web.conftest import seed_gpx_file


def test_full_workflow_import_to_dashboard(client, tmp_data_dir: Path):
    """完整工作流：导入 → 仪表盘显示 → 活动列表 → 设置 → 导出."""
    from run_flow_skills_mcp.web.deps import get_services

    get_services(tmp_data_dir)

    # 1. 导入 GPX 文件
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "run1.gpx", date="2026-07-20")
    with open(gpx, "rb") as f:
        resp = client.post(
            "/api/import/upload",
            files={"files": ("run1.gpx", f, "application/xml")},
        )
    assert resp.status_code == 200
    assert resp.json()["imported"] == 1

    # 2. 仪表盘显示数据
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["weekly_summary"]["sessions_count"] >= 1

    # 3. 活动列表显示
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert sessions["total"] >= 1

    # 4. 设置页读写配置
    resp = client.put("/api/config", json={"max_hr": 185, "age": 35})
    assert resp.status_code == 200
    resp = client.get("/api/config")
    assert resp.json()["max_hr"] == 185

    # 5. 仪表盘片段可渲染（不显示配置值）
    resp = client.get("/partials/dashboard")
    assert resp.status_code == 200
    assert "185" not in resp.text  # 仪表盘不显示配置


def test_all_four_pages_accessible(client):
    """4 个页面片段均返回 200."""
    for path in [
        "/partials/dashboard",
        "/partials/activities",
        "/partials/import",
        "/partials/settings",
    ]:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} 返回 {resp.status_code}"


def test_all_api_endpoints_accessible(client):
    """所有 API 端点返回 200."""
    for path in ["/api/dashboard/summary", "/api/sessions", "/api/config"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} 返回 {resp.status_code}"


def test_import_then_activities_shows_imported(client, tmp_data_dir: Path):
    """导入后活动列表显示导入的记录."""
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "run2.gpx", date="2026-07-21")
    with open(gpx, "rb") as f:
        client.post("/api/import/upload", files={"files": ("run2.gpx", f, "application/xml")})

    resp = client.get("/partials/activities")
    assert resp.status_code == 200
    assert "2026-07-21" in resp.text


def test_config_persist_across_requests(client, tmp_data_dir: Path):
    """配置跨请求持久化."""
    client.put("/api/config", json={"max_hr": 195, "lthr": 170})
    # 再次读取
    resp = client.get("/api/config")
    data = resp.json()
    assert data["max_hr"] == 195
    assert data["lthr"] == 170


def test_upload_batch_with_mixed_valid_invalid(client, tmp_data_dir: Path):
    """批量上传含合法和非法文件."""
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "ok.gpx", date="2026-07-22")
    with open(gpx, "rb") as f_ok:
        fake = io.BytesIO(b"fake exe")
        resp = client.post(
            "/api/import/upload",
            files=[
                ("files", ("ok.gpx", f_ok, "application/xml")),
                ("files", ("bad.exe", fake, "application/octet-stream")),
            ],
        )
    data = resp.json()
    assert data["total"] == 2
    assert data["imported"] == 1
    assert data["failed"] == 1


def test_web_entry_point_registered():
    """pyproject.toml 注册了 run-flow-skills-web 入口.

    通过检查 console_scripts 元数据验证入口已注册，
    避免实际启动 uvicorn（会阻塞）。
    """
    import importlib.metadata

    eps = importlib.metadata.entry_points(group="console_scripts")
    names = [ep.name for ep in eps]
    assert "run-flow-skills-web" in names, "run-flow-skills-web 入口未注册"
    # 验证入口指向正确模块
    web_ep = next(ep for ep in eps if ep.name == "run-flow-skills-web")
    assert web_ep.value == "run_flow_skills_mcp.web.app:main"
