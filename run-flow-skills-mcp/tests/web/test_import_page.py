"""import_page 路由测试."""
from pathlib import Path

from tests.web.conftest import seed_gpx_file


def test_import_partial_empty(client):
    """导入页片段返回 200，包含拖拽区."""
    resp = client.get("/partials/import")
    assert resp.status_code == 200
    assert "拖拽" in resp.text or "drop" in resp.text.lower() or "选择" in resp.text
    assert ".fit" in resp.text or ".gpx" in resp.text  # 白名单提示


def test_import_upload_single_gpx(client, tmp_data_dir: Path):
    """上传单个 GPX 文件成功导入."""
    gpx_path = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx", date="2026-07-20")
    with open(gpx_path, "rb") as f:
        resp = client.post(
            "/api/import/upload",
            files={"files": ("test.gpx", f, "application/xml")},
            data={"force": "false"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["results"][0]["imported"] is True


def test_import_upload_multiple_files(client, tmp_data_dir: Path):
    """上传多个文件."""
    gpx1 = seed_gpx_file(tmp_data_dir / "uploads" / "a.gpx", date="2026-07-18")
    gpx2 = seed_gpx_file(tmp_data_dir / "uploads" / "b.gpx", date="2026-07-19")
    with open(gpx1, "rb") as f1, open(gpx2, "rb") as f2:
        resp = client.post(
            "/api/import/upload",
            files=[
                ("files", ("a.gpx", f1, "application/xml")),
                ("files", ("b.gpx", f2, "application/xml")),
            ],
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert sum(1 for r in data["results"] if r["imported"]) == 2


def test_import_upload_duplicate_skipped(client, tmp_data_dir: Path):
    """重复上传同一文件被跳过."""
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "dup.gpx", date="2026-07-20")
    # 第一次
    with open(gpx, "rb") as f:
        client.post("/api/import/upload", files={"files": ("dup.gpx", f, "application/xml")})
    # 第二次（同 hash）
    with open(gpx, "rb") as f:
        resp = client.post(
            "/api/import/upload",
            files={"files": ("dup.gpx", f, "application/xml")},
        )
    data = resp.json()
    assert data["results"][0]["imported"] is False
    assert data["results"][0].get("skipped") is True


def test_import_upload_force_overrides_duplicate(client, tmp_data_dir: Path):
    """force=true 覆盖重复."""
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "dup.gpx", date="2026-07-20")
    with open(gpx, "rb") as f:
        client.post("/api/import/upload", files={"files": ("dup.gpx", f, "application/xml")})
    with open(gpx, "rb") as f:
        resp = client.post(
            "/api/import/upload",
            files={"files": ("dup.gpx", f, "application/xml")},
            data={"force": "true"},
        )
    data = resp.json()
    assert data["results"][0]["imported"] is True


def test_import_upload_unsupported_extension_rejected(client):
    """不支持的文件类型被拒绝."""
    import io
    fake = io.BytesIO(b"fake content")
    resp = client.post(
        "/api/import/upload",
        files={"files": ("malware.exe", fake, "application/octet-stream")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["imported"] is False
    assert "error" in data["results"][0]


def test_import_upload_too_many_files_rejected(client):
    """超过 100 文件上限被拒绝."""
    from run_flow_skills_mcp.constants import MAX_BATCH_UPLOAD_FILES
    import io
    files = []
    for i in range(MAX_BATCH_UPLOAD_FILES + 1):
        files.append(("files", (f"f{i}.gpx", io.BytesIO(b"<gpx></gpx>"), "application/xml")))
    resp = client.post("/api/import/upload", files=files)
    assert resp.status_code == 400
    assert "超过" in resp.json()["detail"] or "exceed" in resp.json()["detail"].lower()


def test_import_manual_success(client, tmp_data_dir: Path):
    """手动录入成功."""
    resp = client.post(
        "/api/import/manual",
        json={
            "activity_date": "2026-07-20T06:00:00",
            "distance_m": 10000,
            "duration_s": 3600,
            "avg_hr": 150,
            "source": "manual",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] is True
    assert "session_id" in data


def test_import_manual_invalid_data(client):
    """无效数据（距离为 0）返回 422."""
    resp = client.post(
        "/api/import/manual",
        json={"activity_date": "2026-07-20T06:00:00", "distance_m": 0, "duration_s": 3600},
    )
    assert resp.status_code == 422
