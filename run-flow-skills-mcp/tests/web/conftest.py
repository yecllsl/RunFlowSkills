"""web 测试公共 fixture."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from run_flow_skills_mcp.tools._deps import reset_services_cache


@pytest.fixture
def tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """临时 data 目录，隔离每次测试.

    通过 monkeypatch 替换 _deps._DEFAULT_DATA_DIR，让路由中无参 get_services()
    也使用 tmp_path，保证 TestClient 与测试代码共用同一 services 实例。
    """
    (tmp_path / "sessions").mkdir()
    (tmp_path / "metrics").mkdir()
    (tmp_path / "load").mkdir()
    (tmp_path / "body_signals").mkdir()
    (tmp_path / "decisions").mkdir()
    (tmp_path / "plans").mkdir()
    # 关键：让无参 get_services() 使用 tmp_path
    monkeypatch.setattr(
        "run_flow_skills_mcp.tools._deps._DEFAULT_DATA_DIR",
        tmp_path,
    )
    reset_services_cache()
    yield tmp_path
    reset_services_cache()


@pytest.fixture
def client(tmp_data_dir: Path) -> TestClient:
    """FastAPI TestClient，使用临时 data_dir."""
    from run_flow_skills_mcp.web.app import create_app

    app = create_app()
    yield TestClient(app)


def seed_gpx_file(
    path: Path, date: str = "2026-07-20", distance_km: float = 10.0, duration_s: int = 3600
) -> Path:
    """生成一个最小可解析的 GPX 文件供测试用."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # 简化 GPX：用 <time> 和 <trkpt> 序列模拟
    points = []
    n_pts = 10
    for i in range(n_pts):
        lat = 30.0 + i * 0.001
        lon = 120.0 + i * 0.001
        ele = 10.0
        t = f"{date}T06:{i:02d}:00Z"
        points.append(f'<trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele><time>{t}</time></trkpt>')
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="test">\n'
        "<trk><name>Test Run</name><trkseg>\n" + "\n".join(points) + "\n" + "</trkseg></trk></gpx>",
        encoding="utf-8",
    )
    return path


def seed_config(tmp_data_dir: Path, config: dict) -> Path:
    """写入 data/config.json."""
    cfg_path = tmp_data_dir / "config.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    return cfg_path
