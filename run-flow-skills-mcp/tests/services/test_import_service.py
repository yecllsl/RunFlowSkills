"""import_service 测试（spec 5.4, FR-IMPORT-01/05）."""
from datetime import datetime
from pathlib import Path

import pytest

from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> ImportService:
    return ImportService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


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


def test_import_file_new_gpx(service: ImportService, tmp_path: Path):
    """导入新 GPX 文件：imported=True + metrics_summary."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    result = service.import_file(gpx)
    assert result["imported"] is True
    assert "session_id" in result
    assert "metrics_summary" in result
    assert result["metrics_summary"]["pace_zone"] in ("E", "M", "T", "I", "R")


def test_import_file_duplicate_hash_skipped(service: ImportService, tmp_path: Path):
    """同文件二次导入：skipped=True + reason=duplicate_hash（spec 5.3）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    first = service.import_file(gpx)
    assert first["imported"] is True

    second = service.import_file(gpx)
    assert second["imported"] is False
    assert second["skipped"] is True
    assert second["reason"] == "duplicate_hash"


def test_import_file_force_overrides_duplicate(service: ImportService, tmp_path: Path):
    """--force 覆盖去重（spec 5.3）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    service.import_file(gpx)
    result = service.import_file(gpx, force=True)
    assert result["imported"] is True


def test_import_file_unsupported_extension_returns_error(service: ImportService, tmp_path: Path):
    """不支持的扩展名：返回 error，不抛异常（interaction-rules.md 降级方案）."""
    bad = tmp_path / "test.txt"
    bad.write_text("invalid", encoding="utf-8")

    result = service.import_file(bad)
    assert result["imported"] is False
    assert "error" in result


def test_import_manual_basic(service: ImportService):
    """手动录入：activity_date/distance_m/duration_s."""
    manual_data = {
        "activity_date": "2026-07-25T06:00:00",
        "distance_m": 10000.0,
        "duration_s": 3600,
        "source": "manual",
    }
    result = service.import_manual(manual_data)
    assert result["imported"] is True
    assert "session_id" in result
    assert result["metrics_summary"]["tss"] > 0


def test_import_manual_invalid_data_returns_error(service: ImportService):
    """无效数据（distance<=0）：返回 error."""
    result = service.import_manual({"distance_m": 0, "duration_s": 3600, "source": "manual"})
    assert result["imported"] is False
    assert "error" in result


def test_import_writes_metrics_to_parquet(service: ImportService, tmp_path: Path):
    """导入后 metrics 应写入 parquet（spec 5.4）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    result = service.import_file(gpx)
    session_id = result["session_id"]
    metrics = service.parquet_store.query_metrics([session_id])
    assert len(metrics) == 1
    assert metrics[0].tss > 0


def test_import_recomputes_training_load(service: ImportService, tmp_path: Path):
    """导入后 TrainingLoad 应被重算并写入 JSON（spec 5.4）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    service.import_file(gpx)
    loads = service.json_store.query_load()
    assert len(loads) > 0
    # 当日应有 TrainingLoad 记录
    today_load = [l for l in loads if l.date == "2026-07-25"]
    assert len(today_load) == 1
