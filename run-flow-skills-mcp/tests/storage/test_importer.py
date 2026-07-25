"""导入器测试（spec FR-IMPORT-01/02/03, M-1 评审修正 GPX）."""
import hashlib
from pathlib import Path

import pytest

from run_flow_skills_mcp.storage.importer import (
    ImportParseError,
    compute_file_hash,
    parse_file,
    parse_gpx,
)


def _write_gpx(path: Path) -> None:
    """生成合成 GPX 测试文件."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <time>2026-07-25T06:00:00Z</time>
  </metadata>
  <trk>
    <name>Morning Run</name>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>50.0</ele>
        <time>2026-07-25T06:00:00Z</time>
      </trkpt>
      <trkpt lat="39.9050" lon="116.4080">
        <ele>51.0</ele>
        <time>2026-07-25T06:00:01Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    path.write_text(gpx_content, encoding="utf-8")


def test_compute_file_hash_stable(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("hello", encoding="utf-8")
    h1 = compute_file_hash(f)
    h2 = compute_file_hash(f)
    assert h1 == h2
    assert h1 == hashlib.sha256(b"hello").hexdigest()


def test_parse_gpx_basic(tmp_path: Path):
    """M-1 评审修正：GPX 解析必须支持."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_gpx(gpx_path)
    assert session.source == "garmin"  # GPX 默认归 garmin（可在 parse_file 覆盖）
    assert session.activity_date is not None
    assert session.duration_s >= 0


def test_parse_file_dispatches_by_extension(tmp_path: Path):
    """parse_file 根据扩展名分发."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_file(gpx_path)
    assert session is not None


def test_parse_file_unsupported_extension_raises(tmp_path: Path):
    """不支持的扩展名应抛 ImportParseError."""
    bad_path = tmp_path / "test.txt"
    bad_path.write_text("invalid", encoding="utf-8")

    with pytest.raises(ImportParseError):
        parse_file(bad_path)


def test_parse_file_sets_raw_file_hash(tmp_path: Path):
    """解析后应填充 raw_file_hash（去重键）."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_file(gpx_path)
    assert session.raw_file_hash is not None
    assert session.raw_file_hash == compute_file_hash(gpx_path)


def test_parse_file_sets_raw_file_path(tmp_path: Path):
    """解析后应填充 raw_file_path（追溯）."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_file(gpx_path)
    assert session.raw_file_path == "test.gpx"


def test_parse_file_corrupt_gpx_raises(tmp_path: Path):
    """损坏的 GPX 应抛 ImportParseError."""
    gpx_path = tmp_path / "test.gpx"
    gpx_path.write_text("not valid xml <<<", encoding="utf-8")

    with pytest.raises(ImportParseError):
        parse_file(gpx_path)
