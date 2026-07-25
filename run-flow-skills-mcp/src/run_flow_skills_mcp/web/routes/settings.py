"""settings 路由 — 设置页（spec 9.2 页面 4，M-3 评审修正）.

读写 data/config.json，覆盖 constants.py 默认值。
calc_metrics 读取顺序：data/config.json → constants.py 默认值。

config 路径通过 services.json_store.data_dir 动态获取，
保证与 services 容器（测试时为 tmp_data_dir）一致。
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from run_flow_skills_mcp.constants import (
    DEFAULT_AGE,
    DEFAULT_HEIGHT_CM,
    DEFAULT_LTHR,
    DEFAULT_MAX_HR,
    DEFAULT_RESTING_HR,
    DEFAULT_WEIGHT_KG,
)
from run_flow_skills_mcp.web.app import templates
from run_flow_skills_mcp.web.deps import get_services
from run_flow_skills_mcp.web.schemas import ConfigUpdateRequest

router = APIRouter()

# 默认值映射（供前端占位符提示）
_DEFAULTS = {
    "max_hr": DEFAULT_MAX_HR,
    "lthr": DEFAULT_LTHR,
    "resting_hr": DEFAULT_RESTING_HR,
    "age": DEFAULT_AGE,
    "weight_kg": DEFAULT_WEIGHT_KG,
    "height_cm": DEFAULT_HEIGHT_CM,
}


def _config_path() -> Path:
    """获取 config.json 路径（通过 services 容器，保证 data_dir 一致）."""
    svc = get_services()
    return svc.json_store.data_dir / "config.json"


def _load_config() -> dict:
    """读取 data/config.json，不存在返回空 dict."""
    path = _config_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_config(cfg: dict) -> None:
    """写入 data/config.json."""
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@router.get("/partials/settings", response_class=HTMLResponse)
async def settings_partial(request: Request):
    """返回设置页片段."""
    current = _load_config()
    return templates.TemplateResponse(
        request,
        "partials/settings.html",
        {"current": current, "defaults": _DEFAULTS},
    )


@router.get("/api/config")
async def get_config():
    """读取当前配置 + 默认值."""
    current = _load_config()
    return {**{k: None for k in _DEFAULTS}, **current, "defaults": _DEFAULTS}


@router.put("/api/config")
async def update_config(req: ConfigUpdateRequest):
    """部分更新配置，合并写入 data/config.json.

    传 null 表示重置该字段为 null（回退到 constants.py 默认值）。
    """
    current = _load_config()
    # 合并：只更新请求中明确传入的字段（包括 null）
    update_data = req.model_dump(exclude_unset=True)
    current.update(update_data)
    current["updated_at"] = datetime.now(timezone.utc).isoformat()

    _save_config(current)

    return {**{k: None for k in _DEFAULTS}, **current, "defaults": _DEFAULTS}
