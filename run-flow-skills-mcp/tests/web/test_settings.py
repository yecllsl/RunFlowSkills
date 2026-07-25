"""settings 路由测试."""

import json
from pathlib import Path

from tests.web.conftest import seed_config


def test_settings_partial(client):
    """设置页片段返回 200，包含 7 个字段."""
    resp = client.get("/partials/settings")
    assert resp.status_code == 200
    assert "最大心率" in resp.text
    assert "乳酸阈值心率" in resp.text
    assert "年龄" in resp.text


def test_get_config_empty(client, tmp_data_dir: Path):
    """无 config.json 时返回默认值."""
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_hr"] is None  # 未设置
    assert data["defaults"]["max_hr"] == 190  # 默认值


def test_get_config_with_existing(client, tmp_data_dir: Path):
    """有 config.json 时返回已保存配置."""
    seed_config(tmp_data_dir, {"max_hr": 185, "age": 35})
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_hr"] == 185
    assert data["age"] == 35


def test_put_config_partial_update(client, tmp_data_dir: Path):
    """部分更新：只传 max_hr."""
    resp = client.put("/api/config", json={"max_hr": 180})
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_hr"] == 180

    # 验证写入文件
    cfg = json.loads((tmp_data_dir / "config.json").read_text())
    assert cfg["max_hr"] == 180
    assert "updated_at" in cfg


def test_put_config_merge_existing(client, tmp_data_dir: Path):
    """更新时合并已有配置."""
    seed_config(tmp_data_dir, {"max_hr": 185, "age": 35})
    resp = client.put("/api/config", json={"lthr": 160})
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_hr"] == 185  # 保留
    assert data["age"] == 35  # 保留
    assert data["lthr"] == 160  # 新增


def test_put_config_invalid_value(client):
    """无效值校验失败."""
    resp = client.put("/api/config", json={"max_hr": 300})
    assert resp.status_code == 422


def test_put_config_reset_field(client, tmp_data_dir: Path):
    """传 null 重置字段."""
    seed_config(tmp_data_dir, {"max_hr": 185})
    resp = client.put("/api/config", json={"max_hr": None})
    assert resp.status_code == 200
    # config.json 中 max_hr 应为 null 或不存在
    cfg = json.loads((tmp_data_dir / "config.json").read_text())
    assert cfg.get("max_hr") is None
