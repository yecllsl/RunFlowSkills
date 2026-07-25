"""Pytest 公共 fixture."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_data_dir() -> Path:
    """提供临时 data/ 目录，测试结束自动清理."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "data"
        path.mkdir()
        (path / "sessions").mkdir()
        (path / "metrics").mkdir()
        (path / "load").mkdir()
        (path / "body_signals").mkdir()
        (path / "decisions").mkdir()
        (path / "plans").mkdir()
        yield path
