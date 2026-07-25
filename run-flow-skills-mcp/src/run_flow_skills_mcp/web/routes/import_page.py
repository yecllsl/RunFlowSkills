"""import_page 路由 — 数据导入页（spec 9.2 页面 3，9.4 导入流程）.

核心功能：可视化批量导入，复用 import_service，与 MCP import_file tool 共用。
安全限制：文件类型白名单、单文件 100MB、批量 100 文件。
"""
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse

from run_flow_skills_mcp.constants import (
    MAX_BATCH_UPLOAD_FILES,
    MAX_UPLOAD_FILE_SIZE_MB,
    SUPPORTED_IMPORT_EXT,
)
from run_flow_skills_mcp.web.app import templates
from run_flow_skills_mcp.web.deps import get_services
from run_flow_skills_mcp.web.schemas import ManualInputRequest

router = APIRouter()


@router.get("/partials/import", response_class=HTMLResponse)
async def import_partial(request: Request):
    """返回导入页片段."""
    return templates.TemplateResponse(
        request,
        "partials/import.html",
        {
            "supported_ext": SUPPORTED_IMPORT_EXT,
            "max_size_mb": MAX_UPLOAD_FILE_SIZE_MB,
            "max_batch": MAX_BATCH_UPLOAD_FILES,
        },
    )


@router.post("/api/import/upload")
async def import_upload(files: list[UploadFile], force: bool = Form(False)):
    """批量上传导入（multipart/form-data）.

    复用 ImportService.import_file，与 MCP import_file tool 共用同一 service。
    """
    # 批量上限校验
    if len(files) > MAX_BATCH_UPLOAD_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"文件数量超过上限 {MAX_BATCH_UPLOAD_FILES} 个",
        )

    svc = get_services()
    results = []

    for f in files:
        # 文件类型白名单校验
        ext = Path(f.filename).suffix.lower() if f.filename else ""
        if ext not in SUPPORTED_IMPORT_EXT:
            results.append({
                "filename": f.filename,
                "imported": False,
                "error": f"不支持的文件类型: {ext}（仅支持 {' '.join(SUPPORTED_IMPORT_EXT)}）",
            })
            continue

        # 保存到临时文件后调 import_file
        # ponytail: 临时文件方案，导入后删除，避免内存溢出
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            content = await f.read()
            # 大小校验
            if len(content) > MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024:
                results.append({
                    "filename": f.filename,
                    "imported": False,
                    "error": f"文件超过 {MAX_UPLOAD_FILE_SIZE_MB}MB 限制",
                })
                tmp.close()
                Path(tmp.name).unlink(missing_ok=True)
                continue
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            result = svc.import_service.import_file(tmp_path, force=force)
            result["filename"] = f.filename
            results.append(result)
        finally:
            tmp_path.unlink(missing_ok=True)

    return {
        "total": len(results),
        "imported": sum(1 for r in results if r.get("imported")),
        "skipped": sum(1 for r in results if r.get("skipped")),
        "failed": sum(1 for r in results if not r.get("imported") and not r.get("skipped")),
        "results": results,
    }


@router.post("/api/import/manual")
async def import_manual(req: ManualInputRequest):
    """手动录入（JSON body）.

    复用 ImportService.import_manual，与 MCP import_manual tool 共用同一 service。
    """
    svc = get_services()
    result = svc.import_service.import_manual(
        manual_data=req.model_dump(),
        force=False,
    )
    return result
