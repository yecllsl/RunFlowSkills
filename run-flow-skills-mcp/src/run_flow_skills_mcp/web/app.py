"""FastAPI 应用工厂与启动入口（spec 9.1）.

创建 FastAPI 应用实例，挂载静态文件，注册 4 个路由模块。
提供 main() 作为 CLI 入口，绑定 127.0.0.1:8002 启动 uvicorn。
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# web 模块根目录，用于定位 templates 和 static
_WEB_DIR = Path(__file__).parent
_TEMPLATES_DIR = _WEB_DIR / "templates"
_STATIC_DIR = _WEB_DIR / "static"

# 全局模板实例，供路由模块复用
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例.

    配置 Jinja2 模板引擎、挂载静态文件目录、注册所有路由模块。
    绑定 127.0.0.1 保证仅本机访问，符合数据安全规则。
    """
    app = FastAPI(
        title="RunFlowSkills 可视化",
        description="深度跑步分析本地可视化应用",
        version="0.1.1",
    )

    # 挂载静态文件（JS库、CSS）
    _STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # 根路由：返回单页外壳
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """返回单页外壳 base.html"""
        return templates.TemplateResponse(request, "base.html", {})

    # 注册路由模块（懒导入避免循环依赖）
    from run_flow_skills_mcp.web.routes import (
        activities,
        dashboard,
        import_page,
        settings,
    )

    app.include_router(dashboard.router)
    app.include_router(activities.router)
    app.include_router(import_page.router)
    app.include_router(settings.router)

    return app


def main():
    """CLI 入口：启动 uvicorn 服务.

    绑定 127.0.0.1:8002，仅本机访问。
    """
    import uvicorn

    from run_flow_skills_mcp.constants import WEB_HOST, WEB_PORT

    uvicorn.run(
        "run_flow_skills_mcp.web.app:create_app",
        factory=True,
        host=WEB_HOST,
        port=WEB_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
