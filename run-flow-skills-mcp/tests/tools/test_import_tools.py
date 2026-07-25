"""import_file / import_manual tool 测试（spec FR-IMPORT-01/05, 6.2）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.import_file import import_file
from run_flow_skills_mcp.tools.import_manual import import_manual


@pytest.fixture(autouse=True)
def reset_cache():
    """每个测试后重置 services 单例，避免污染."""
    yield
    _deps.reset_services_cache()


def _write_gpx(path: Path) -> None:
    gpx = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><time>2026-07-25T06:00:00Z</time></metadata>
  <trk><name>Morning Run</name><trkseg>
    <trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2026-07-25T06:00:00Z</time></trkpt>
    <trkpt lat="39.9142" lon="116.4174"><ele>51.0</ele><time>2026-07-25T06:30:00Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""
    path.write_text(gpx, encoding="utf-8")


def test_import_file_returns_prompt_and_data(tmp_path: Path):
    """tool 必须返回 {prompt, ...data}（spec 10.2）."""
    # 替换 DATA_DIR 到 tmp_path
    _deps.reset_services_cache()
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    result = import_file(str(gpx), _data_dir=tmp_path)
    assert "prompt" in result
    assert result["imported"] is True
    assert "session_id" in result
    assert "metrics_summary" in result


def test_import_file_duplicate_returns_skipped(tmp_path: Path):
    """重复导入返回 skipped=True."""
    _deps.reset_services_cache()
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    first = import_file(str(gpx), _data_dir=tmp_path)
    assert first["imported"] is True

    second = import_file(str(gpx), _data_dir=tmp_path)
    assert second["imported"] is False
    assert second["skipped"] is True
    assert "prompt" in second  # 即使跳过也附 prompt


def test_import_file_unsupported_returns_error_with_prompt(tmp_path: Path):
    """不支持的文件：返回 error + prompt（interaction-rules.md 降级方案）."""
    _deps.reset_services_cache()
    bad = tmp_path / "test.txt"
    bad.write_text("invalid", encoding="utf-8")

    result = import_file(str(bad), _data_dir=tmp_path)
    assert result["imported"] is False
    assert "error" in result
    assert "prompt" in result


def test_import_manual_returns_prompt_and_data(tmp_path: Path):
    """手动录入 tool 返回 {prompt, ...data}."""
    _deps.reset_services_cache()
    manual_data = {
        "activity_date": "2026-07-25T06:00:00",
        "distance_m": 10000.0,
        "duration_s": 3600,
        "source": "manual",
    }
    result = import_manual(manual_data, _data_dir=tmp_path)
    assert result["imported"] is True
    assert "prompt" in result
    assert result["metrics_summary"]["tss"] > 0


def test_import_manual_invalid_returns_error_with_prompt(tmp_path: Path):
    """无效数据返回 error + prompt."""
    _deps.reset_services_cache()
    result = import_manual(
        {"distance_m": 0, "duration_s": 3600, "source": "manual"},
        _data_dir=tmp_path,
    )
    assert result["imported"] is False
    assert "error" in result
    assert "prompt" in result
