"""Web 层依赖获取 — 复用 tools/_deps.get_services.

所有 web 路由通过本模块获取 service 实例，测试可 monkeypatch。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import Services, get_services as _get_services


def get_services(data_dir: Optional[Path] = None) -> Services:
    """获取 services 实例（复用 tools/_deps 单例工厂）."""
    return _get_services(data_dir)
