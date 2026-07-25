"""web/app.py 应用工厂测试."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_create_app_returns_fastapi_instance():
    """create_app 返回 FastAPI 实例."""
    from run_flow_skills_mcp.web.app import create_app

    app = create_app()
    assert isinstance(app, FastAPI)


def test_root_route_returns_html_with_nav():
    """根路由 / 返回 HTML，包含 4 个导航 tab."""
    from run_flow_skills_mcp.web.app import create_app

    client = TestClient(create_app())
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    # 4 个导航 tab
    assert "仪表盘" in resp.text
    assert "活动" in resp.text
    assert "导入" in resp.text
    assert "设置" in resp.text


def test_static_files_mounted():
    """静态文件路径已挂载（/static/app.css 可访问或 404，不报 500）."""
    from run_flow_skills_mcp.web.app import create_app

    client = TestClient(create_app())
    # app.css 应存在（本 Task 创建）
    resp = client.get("/static/app.css")
    assert resp.status_code == 200


def test_services_container_has_parquet_store(tmp_path: Path):
    """Services 容器包含 parquet_store 和 json_store 字段."""
    from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

    reset_services_cache()
    svc = get_services(tmp_path)
    assert hasattr(svc, "parquet_store")
    assert hasattr(svc, "json_store")
    assert svc.parquet_store is not None
    assert svc.json_store is not None
    reset_services_cache()
