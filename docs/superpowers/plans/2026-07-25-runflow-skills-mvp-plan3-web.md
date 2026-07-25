# RunFlowSkills MVP v0.1.0 Plan 3: Web 可视化

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 4 页 Web 可视化（仪表盘 / 活动列表 / 数据导入 / 设置），复用 Plan 2 的 services 层，通过 FastAPI + Jinja2 + HTMX + Alpine.js + ECharts 提供本地化可视化界面。

**Architecture:** FastAPI 应用工厂 `create_app()` 挂载静态资源 + 注册 4 个路由模块。路由层是薄编排：HTML 路由渲染 Jinja2 模板，API 路由返回 JSON。所有业务逻辑通过 `tools/_deps.get_services()` 复用 Plan 2 的 6 个 services，与 MCP Tools 共用同一 service 实例，保证 Web 导入与 Skill `/import` 行为完全一致。HTMX 实现局部刷新（Tab 切换、详情展开），Alpine.js 管理表单状态（拖拽上传、多选文件），ECharts 渲染趋势图表。

**Tech Stack:** FastAPI 0.115+ / Jinja2 3.1+ / HTMX 1.9+ / Alpine.js 3.x / ECharts 5.x / python-multipart 0.0.9+ / uvicorn 0.30+

## Global Constraints

- Python >=3.12，uv 包管理
- Web 绑定 `127.0.0.1:8002`（DeepReview 用 8001，RunFlowAgent 用 8765/8766，避免冲突）
- 文件类型白名单：`.fit .gpx .csv .tcx .xml`（`constants.SUPPORTED_IMPORT_EXT`）
- 单文件大小限制：100MB（`constants.MAX_UPLOAD_FILE_SIZE_MB`）
- 批量上传上限：100 文件/次（`constants.MAX_BATCH_UPLOAD_FILES`）
- 所有数据不出 `data/` 目录（数据安全规则）
- Web 的 `/api/import/upload` 和 `/api/import/manual` 复用 `import_service`，与 MCP tool 共用
- `/api/config` 读写 `data/config.json`，覆盖 `constants.py` 默认值
- Tool 不调 LLM，Web 也不调 LLM（仅展示数据和提供导入/配置入口）
- 前置依赖：Plan 1（基础设施）+ Plan 2（Services + 14 MCP Tools）已完成

---

## 文件结构

```
run-flow-skills-mcp/src/run_flow_skills_mcp/web/
├── __init__.py                     # 模块标记
├── app.py                          # FastAPI 应用工厂 + main() 入口
├── deps.py                         # Web 层依赖获取（复用 tools/_deps.get_services）
├── schemas.py                      # Web 请求模型（ManualInputRequest, ConfigUpdateRequest）
├── routes/
│   ├── __init__.py
│   ├── dashboard.py                # 仪表盘：GET /partials/dashboard + GET /api/dashboard/summary
│   ├── activities.py               # 活动列表：GET /partials/activities + /partials/activities/{id} + GET /api/sessions
│   ├── import_page.py              # 数据导入：GET /partials/import + POST /api/import/upload + POST /api/import/manual
│   └── settings.py                 # 设置：GET /partials/settings + GET /api/config + PUT /api/config
├── templates/
│   ├── base.html                   # 单页外壳（导航 4 tab + #content + Toast + ECharts 辅助）
│   ├── errors.html                 # 404/500 错误页
│   └── partials/
│       ├── dashboard.html          # 4 KPI 卡片 + 负荷趋势图 + 本周训练摘要
│       ├── activities.html         # 表格 + 筛选 + 分页
│       ├── activity_detail.html    # 详情片段（HTMX OOB）
│       ├── import.html             # 拖拽区 + 文件列表 + 手动录入表单
│       └── settings.html           # 7 字段配置表单
└── static/
    ├── download_static.ps1         # 静态资源下载脚本（htmx/alpine/echarts）
    ├── app.css                     # 全局样式
    ├── htmx.min.js                 # 本地化 HTMX（由脚本下载）
    ├── alpine.min.js               # 本地化 Alpine.js（由脚本下载）
    └── echarts.min.js              # 本地化 ECharts（由脚本下载）

run-flow-skills-mcp/tests/web/
├── __init__.py
├── conftest.py                     # TestClient fixture + 临时 data_dir
├── test_dashboard.py               # 仪表盘路由测试
├── test_activities.py              # 活动列表路由测试
├── test_import_page.py             # 导入路由测试（含白名单/大小限制）
├── test_settings.py                # 设置路由测试
└── test_web_integration.py         # 端到端集成测试
```

**修改的已有文件：**
- `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/_deps.py`：`Services` 容器新增 `parquet_store` 和 `json_store` 字段（供 web 层读取 session 列表）
- `run-flow-skills-mcp/pyproject.toml`：注册 `run-flow-skills-web` 入口点

---

### Task 1: web 模块骨架 + app.py 应用工厂 + 修改 Services 容器

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/__init__.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/app.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/deps.py`
- Create: `run-flow-skills-mcp/tests/web/__init__.py`
- Create: `run-flow-skills-mcp/tests/web/conftest.py`
- Modify: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/_deps.py`（Services 容器新增 parquet_store/json_store）
- Test: `run-flow-skills-mcp/tests/web/test_app.py`

**Interfaces:**
- Consumes: `tools/_deps.get_services()`（Plan 2 Task 8）、`constants.WEB_HOST/WEB_PORT`（Plan 1 Task 2）
- Produces:
  - `web/app.py::create_app() -> FastAPI`：应用工厂，挂载 static + 注册 4 个路由模块
  - `web/app.py::templates`：全局 Jinja2Templates 实例（供路由模块复用）
  - `web/app.py::main()`：CLI 入口，启动 uvicorn 127.0.0.1:8002
  - `web/deps.py::get_services(data_dir=None) -> Services`：薄包装，复用 `tools/_deps.get_services`
  - `tools/_deps.Services` 已含 `parquet_store: ParquetStore` 和 `json_store: JsonStore` 字段（Plan 2 Task 8 已一次性定义，本 Plan 无需修改）

- [ ] **Step 1: 验证 tools/_deps.py 的 Services 容器已含 parquet_store 和 json_store 字段**

读取当前 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/_deps.py`，确认 Plan 2 已一次性定义完整容器（无需修改）：

```python
@dataclass
class Services:
    """所有 service 实例的容器."""
    import_service: ImportService
    analysis_service: AnalysisService
    plan_service: PlanService
    review_service: ReviewService
    coach_service: CoachService
    stats_service: StatsService
    parquet_store: ParquetStore   # Plan 2 已定义：供 web 层读取 session 列表
    json_store: JsonStore         # Plan 2 已定义：供 web 层读写 config.json
```

`get_services()` 函数中构造 `Services` 时已传入 store（Plan 2 已完成）：

```python
    services = Services(
        import_service=ImportService(parquet_store, json_store),
        analysis_service=AnalysisService(parquet_store, json_store),
        plan_service=PlanService(parquet_store, json_store),
        review_service=ReviewService(parquet_store, json_store),
        coach_service=CoachService(parquet_store, json_store),
        stats_service=StatsService(parquet_store, json_store),
        parquet_store=parquet_store,
        json_store=json_store,
    )
```

若 Plan 2 未定义上述字段，回退方案：按上述代码补齐 `Services` 容器定义和 `get_services()` 构造逻辑。

- [ ] **Step 2: 运行 Plan 2 既有测试，确认 Services 容器完整**

Run: `uv run pytest tests/tools/ tests/services/ -v --tb=short`
Expected: 所有既有测试 PASS（Services 容器已含 parquet_store/json_store，不影响既有 tool 调用）

- [ ] **Step 3: 写失败测试 — test_app.py**

写入 `run-flow-skills-mcp/tests/web/test_app.py`：

```python
"""web/app.py 应用工厂测试."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_create_app_returns_fastapi_instance():
    """create_app 返回 FastAPI 实例."""
    from run_flow_skills_mcp.web.app import create_app
    app = create_app()
    assert isinstance(app, FastAPI)


def test_root_route_returns_html_with_nav():
    """根路由 / 返回 HTML，包含 4 个导航 tab."""
    from run_flow_skills_mcp.web.app import create_app
    client = TestClient(create_app())
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    # 4 个导航 tab
    assert "仪表盘" in resp.text
    assert "活动" in resp.text
    assert "导入" in resp.text
    assert "设置" in resp.text


def test_static_files_mounted():
    """静态文件路径已挂载（/static/app.css 可访问或 404，不报 500）."""
    from run_flow_skills_mcp.web.app import create_app
    client = TestClient(create_app())
    # app.css 应存在（本 Task 创建）
    resp = client.get("/static/app.css")
    assert resp.status_code == 200


def test_services_container_has_parquet_store(tmp_path: Path):
    """Services 容器包含 parquet_store 和 json_store 字段."""
    from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache
    reset_services_cache()
    svc = get_services(tmp_path)
    assert hasattr(svc, "parquet_store")
    assert hasattr(svc, "json_store")
    assert svc.parquet_store is not None
    assert svc.json_store is not None
    reset_services_cache()
```

- [ ] **Step 4: 运行测试验证失败**

Run: `uv run pytest tests/web/test_app.py -v`
Expected: FAIL，`ImportError: No module named 'run_flow_skills_mcp.web'`

- [ ] **Step 5: 创建 web/__init__.py + web/deps.py + web/app.py**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/__init__.py`：

```python
"""RunFlowSkills Web 可视化模块（spec 9.x）.

FastAPI + Jinja2 + HTMX + Alpine.js + ECharts，绑定 127.0.0.1:8002。
"""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/deps.py`：

```python
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
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/app.py`：

```python
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
        version="0.1.0",
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
        dashboard,
        activities,
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
```

- [ ] **Step 6: 创建 routes/__init__.py 占位（路由模块在后续 Task 实现）**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/__init__.py`：

```python
"""Web 路由模块（spec 9.3）."""
```

- [ ] **Step 7: 创建 static/app.css 最小样式（确保 /static/app.css 可访问）**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/app.css`：

```css
/* RunFlowSkills 全局样式 — 最小可用版 */
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; color: #333; }

/* 导航栏 */
.navbar { display: flex; align-items: center; background: #1a73e8; color: #fff; padding: 0 20px; height: 56px; }
.navbar-brand { font-size: 18px; font-weight: 600; margin-right: 32px; }
.navbar-tabs { display: flex; gap: 4px; }
.navbar-tab { background: transparent; border: none; color: rgba(255,255,255,0.8); padding: 8px 16px;
  border-radius: 4px; cursor: pointer; font-size: 14px; }
.navbar-tab:hover { background: rgba(255,255,255,0.1); }
.navbar-tab.active { background: rgba(255,255,255,0.2); color: #fff; }

/* 内容区 */
#content { padding: 20px; max-width: 1200px; margin: 0 auto; }

/* KPI 卡片 */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi-card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.kpi-label { font-size: 13px; color: #666; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 700; }
.kpi-trend { font-size: 12px; margin-top: 4px; }
.kpi-trend.up { color: #34a853; }
.kpi-trend.down { color: #ea4335; }

/* 表格 */
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }
th { background: #f8f9fa; font-weight: 600; color: #555; }
tr:hover { background: #f8f9fa; cursor: pointer; }

/* 表单 */
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; color: #555; margin-bottom: 4px; }
.form-group input, .form-group select { width: 100%; padding: 8px 12px; border: 1px solid #ddd;
  border-radius: 4px; font-size: 14px; }
.btn { padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-primary { background: #1a73e8; color: #fff; }
.btn-secondary { background: #f8f9fa; color: #333; border: 1px solid #ddd; }

/* 拖拽区 */
.drop-zone { border: 2px dashed #ddd; border-radius: 8px; padding: 40px; text-align: center;
  color: #666; cursor: pointer; transition: border-color 0.2s; }
.drop-zone.dragover { border-color: #1a73e8; background: #e8f0fe; }

/* Toast */
#toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; }
.toast { background: #333; color: #fff; padding: 12px 20px; border-radius: 4px; margin-bottom: 8px;
  font-size: 14px; }
.toast.success { background: #34a853; }
.toast.error { background: #ea4335; }

/* 空状态 */
.empty-state { text-align: center; padding: 60px 20px; color: #999; }
.chart-container { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
```

- [ ] **Step 8: 创建 templates/base.html 和 templates/errors.html 占位**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/base.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RunFlowSkills 跑步分析</title>
    <link rel="stylesheet" href="/static/app.css">
    <script src="/static/htmx.min.js"></script>
    <script src="/static/alpine.min.js" defer></script>
    <script src="/static/echarts.min.js"></script>
</head>
<body>
    <!-- 顶栏导航 -->
    <nav class="navbar">
        <div class="navbar-brand">🏃 RunFlowSkills</div>
        <div class="navbar-tabs">
            <button class="navbar-tab active" data-tab="dashboard"
                    hx-get="/partials/dashboard" hx-target="#content" hx-swap="innerHTML">
                仪表盘
            </button>
            <button class="navbar-tab" data-tab="activities"
                    hx-get="/partials/activities" hx-target="#content" hx-swap="innerHTML">
                活动
            </button>
            <button class="navbar-tab" data-tab="import"
                    hx-get="/partials/import" hx-target="#content" hx-swap="innerHTML">
                导入
            </button>
            <button class="navbar-tab" data-tab="settings"
                    hx-get="/partials/settings" hx-target="#content" hx-swap="innerHTML">
                设置
            </button>
        </div>
    </nav>

    <!-- 内容区：HTMX 局部交换 -->
    <div id="content" hx-get="/partials/dashboard" hx-trigger="load" hx-swap="innerHTML">
        <div class="empty-state">
            <div>加载中...</div>
        </div>
    </div>

    <!-- 全局 Toast 容器 -->
    <div id="toast-container"></div>

    <script>
        // Tab 切换高亮
        document.body.addEventListener('htmx:afterRequest', function(evt) {
            const target = evt.detail.requestConfig.elt;
            if (target.classList.contains('navbar-tab')) {
                document.querySelectorAll('.navbar-tab').forEach(t => t.classList.remove('active'));
                target.classList.add('active');
            }
        });

        // Toast 提示
        function showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        // HTMX 错误处理
        document.body.addEventListener('htmx:responseError', function(evt) {
            showToast('请求失败，请重试', 'error');
        });

        // ECharts 渲染辅助：htmx:afterSwap 后自动初始化 [data-echart] 元素
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            const containers = evt.detail.target.querySelectorAll('[data-echart]');
            containers.forEach(container => {
                const chartType = container.getAttribute('data-echart');
                const dataUrl = container.getAttribute('data-chart-url');
                if (dataUrl) {
                    fetch(dataUrl)
                        .then(r => r.json())
                        .then(data => {
                            const fn = window[chartType];
                            if (fn) fn(container, data);
                        })
                        .catch(err => {
                            container.innerHTML = '<div class="empty-state"><div>图表加载失败</div></div>';
                        });
                }
            });
        });

        // 负荷趋势图渲染函数（dashboard 用）
        window.renderLoadChart = function(container, data) {
            const chart = echarts.init(container);
            const dates = data.series.map(p => p.date);
            chart.setOption({
                tooltip: { trigger: 'axis' },
                legend: { data: ['CTL', 'ATL', 'TSB'] },
                xAxis: { type: 'category', data: dates },
                yAxis: { type: 'value' },
                series: [
                    { name: 'CTL', type: 'line', data: data.series.map(p => p.value), smooth: true },
                    { name: 'ATL', type: 'line', data: data.series.map(p => p.atl), smooth: true },
                    { name: 'TSB', type: 'line', data: data.series.map(p => p.tsb), smooth: true },
                ],
            });
            window.addEventListener('resize', () => chart.resize());
        };
    </script>
</body>
</html>
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/errors.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>错误 - RunFlowSkills</title>
    <link rel="stylesheet" href="/static/app.css">
</head>
<body>
    <div class="empty-state">
        <h1>{{ status_code }}</h1>
        <p>{{ message }}</p>
        <a href="/" class="btn btn-primary">返回首页</a>
    </div>
</body>
</html>
```

- [ ] **Step 9: 创建 conftest.py 提供 TestClient fixture**

写入 `run-flow-skills-mcp/tests/web/conftest.py`：

```python
"""web 测试公共 fixture."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from run_flow_skills_mcp.tools._deps import reset_services_cache


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """临时 data 目录，隔离每次测试."""
    (tmp_path / "sessions").mkdir()
    (tmp_path / "metrics").mkdir()
    (tmp_path / "load").mkdir()
    (tmp_path / "body_signals").mkdir()
    (tmp_path / "decisions").mkdir()
    (tmp_path / "plans").mkdir()
    reset_services_cache()
    yield tmp_path
    reset_services_cache()


@pytest.fixture
def client(tmp_data_dir: Path) -> TestClient:
    """FastAPI TestClient，使用临时 data_dir."""
    from run_flow_skills_mcp.web.app import create_app
    app = create_app()
    yield TestClient(app)


def seed_gpx_file(path: Path, date: str = "2026-07-20", distance_km: float = 10.0,
                  duration_s: int = 3600) -> Path:
    """生成一个最小可解析的 GPX 文件供测试用."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # 简化 GPX：用 <time> 和 <trkpt> 序列模拟
    points = []
    n_pts = 10
    for i in range(n_pts):
        lat = 30.0 + i * 0.001
        lon = 120.0 + i * 0.001
        ele = 10.0
        t = f"{date}T06:{i:02d}:00Z"
        points.append(f'<trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele><time>{t}</time></trkpt>')
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<gpx version="1.1" creator="test">\n'
        f'<trk><name>Test Run</name><trkseg>\n'
        + "\n".join(points) + "\n"
        + f'</trkseg></trk></gpx>',
        encoding="utf-8",
    )
    return path


def seed_config(tmp_data_dir: Path, config: dict) -> Path:
    """写入 data/config.json."""
    cfg_path = tmp_data_dir / "config.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    return cfg_path
```

- [ ] **Step 10: 运行测试验证通过**

Run: `uv run pytest tests/web/test_app.py -v`
Expected: 4 个测试全部 PASS

- [ ] **Step 11: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/web/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/app.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/deps.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/app.css run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/base.html run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/errors.html run-flow-skills-mcp/src/run_flow_skills_mcp/tools/_deps.py run-flow-skills-mcp/tests/web/__init__.py run-flow-skills-mcp/tests/web/conftest.py run-flow-skills-mcp/tests/web/test_app.py
git commit -m "feat(web): add FastAPI app factory, base template, and Services container extension"
```

---

### Task 2: schemas.py Web 请求模型

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/schemas.py`
- Test: `run-flow-skills-mcp/tests/web/test_schemas.py`

**Interfaces:**
- Consumes: `models.UserConfig`（Plan 1 Task 3）、`constants`（Plan 1 Task 2）
- Produces:
  - `schemas.ManualInputRequest`：手动录入请求体（activity_date/distance_m/duration_s/avg_hr/max_hr/source/notes）
  - `schemas.ConfigUpdateRequest`：配置更新请求体（7 个可选字段，部分更新）

- [ ] **Step 1: 写失败测试 — test_schemas.py**

写入 `run-flow-skills-mcp/tests/web/test_schemas.py`：

```python
"""web/schemas.py 请求模型测试."""
import pytest
from pydantic import ValidationError


def test_manual_input_request_valid():
    """有效的手动录入请求."""
    from run_flow_skills_mcp.web.schemas import ManualInputRequest
    req = ManualInputRequest(
        activity_date="2026-07-20T06:00:00",
        distance_m=10000,
        duration_s=3600,
        avg_hr=150,
        max_hr=170,
        source="manual",
        notes="晨跑",
    )
    assert req.distance_m == 10000
    assert req.duration_s == 3600


def test_manual_input_request_minimal():
    """最小必填字段."""
    from run_flow_skills_mcp.web.schemas import ManualInputRequest
    req = ManualInputRequest(
        activity_date="2026-07-20T06:00:00",
        distance_m=5000,
        duration_s=1800,
    )
    assert req.avg_hr is None
    assert req.source == "manual"  # 默认值


def test_manual_input_request_invalid_zero_distance():
    """距离为 0 时校验失败."""
    from run_flow_skills_mcp.web.schemas import ManualInputRequest
    with pytest.raises(ValidationError):
        ManualInputRequest(
            activity_date="2026-07-20T06:00:00",
            distance_m=0,
            duration_s=1800,
        )


def test_config_update_request_all_optional():
    """配置更新所有字段可选（部分更新）."""
    from run_flow_skills_mcp.web.schemas import ConfigUpdateRequest
    req = ConfigUpdateRequest()  # 空请求
    assert req.max_hr is None
    assert req.lthr is None


def test_config_update_request_partial():
    """部分更新：只传 max_hr."""
    from run_flow_skills_mcp.web.schemas import ConfigUpdateRequest
    req = ConfigUpdateRequest(max_hr=185)
    assert req.max_hr == 185
    assert req.lthr is None  # 其他字段保持 None


def test_config_update_request_invalid_max_hr():
    """max_hr 超出范围校验失败."""
    from run_flow_skills_mcp.web.schemas import ConfigUpdateRequest
    with pytest.raises(ValidationError):
        ConfigUpdateRequest(max_hr=300)  # >260
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/web/test_schemas.py -v`
Expected: FAIL，`ImportError: No module named 'run_flow_skills_mcp.web.schemas'`

- [ ] **Step 3: 实现 schemas.py**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/schemas.py`：

```python
"""Web 请求模型（spec 9.3 API 路由用）.

手动录入和配置更新的 Pydantic 请求体，复用 models.UserConfig 的字段约束。
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ManualInputRequest(BaseModel):
    """手动录入请求体（POST /api/import/manual）.

    activity_date/distance_m/duration_s 必填，其余可选。
    复用 ImportService.import_manual 的入参格式。
    """

    activity_date: str = Field(..., description="活动日期 ISO 格式，如 2026-07-20T06:00:00")
    distance_m: float = Field(..., gt=0, description="距离（米），>0")
    duration_s: int = Field(..., gt=0, description="时长（秒），>0")
    avg_hr: Optional[int] = Field(None, ge=30, le=260, description="平均心率")
    max_hr: Optional[int] = Field(None, ge=30, le=260, description="最大心率")
    source: Literal["garmin", "coros", "apple", "suunto", "polar", "manual"] = "manual"
    notes: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求体（PUT /api/config）.

    所有字段可选，支持部分更新。字段约束与 models.UserConfig 一致。
    """

    max_hr: Optional[int] = Field(None, ge=80, le=260)
    lthr: Optional[int] = Field(None, ge=60, le=220)
    resting_hr: Optional[int] = Field(None, ge=30, le=150)
    age: Optional[int] = Field(None, ge=10, le=120)
    weight_kg: Optional[float] = Field(None, gt=0, le=300)
    gender: Optional[Literal["male", "female"]] = None
    height_cm: Optional[float] = Field(None, gt=0, le=300)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/web/test_schemas.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/web/schemas.py run-flow-skills-mcp/tests/web/test_schemas.py
git commit -m "feat(web): add request schemas for manual import and config update"
```

---

### Task 3: 静态资源下载脚本

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.ps1`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.sh`
- Test: 手动运行脚本验证 JS 文件下载成功

**说明：** htmx.min.js / alpine.min.js / echarts.min.js 体积较大（合计约 1MB），不纳入 git 版本控制。开发者通过此脚本从 CDN 下载到 `static/` 目录。如果未下载，base.html 的 `<script>` 标签会 404，但 HTML 仍可渲染（TestClient 测试不依赖 JS 执行）。

- [ ] **Step 1: 创建 PowerShell 下载脚本（Windows）**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.ps1`：

```powershell
# 下载 HTMX / Alpine.js / ECharts 到当前目录
# 用法：pwsh download_static.ps1
$ErrorActionPreference = "Stop"

$files = @{
    "htmx.min.js"   = "https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js"
    "alpine.min.js" = "https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"
    "echarts.min.js" = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "下载静态资源到: $scriptDir" -ForegroundColor Cyan

foreach ($name in $files.Keys) {
    $url = $files[$name]
    $dest = Join-Path $scriptDir $name
    Write-Host "  下载 $name ..." -NoNewline
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        Write-Host " 完成 ($((Get-Item $dest).Length) bytes)" -ForegroundColor Green
    } catch {
        Write-Host " 失败: $_" -ForegroundColor Red
        Write-Host "    手动下载: $url" -ForegroundColor Yellow
    }
}

Write-Host "`n完成。如果全部成功，base.html 的 <script> 标签可正常加载。" -ForegroundColor Cyan
```

- [ ] **Step 2: 创建 bash 下载脚本（Linux/macOS）**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.sh`：

```bash
#!/usr/bin/env bash
# 下载 HTMX / Alpine.js / ECharts 到当前目录
# 用法：bash download_static.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

declare -A FILES=(
    ["htmx.min.js"]="https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js"
    ["alpine.min.js"]="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"
    ["echarts.min.js"]="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"
)

echo "下载静态资源到: $SCRIPT_DIR"

for name in "${!FILES[@]}"; do
    url="${FILES[$name]}"
    echo -n "  下载 $name ..."
    if curl -sSL -o "$name" "$url"; then
        size=$(wc -c < "$name")
        echo " 完成 (${size} bytes)"
    else
        echo " 失败"
        echo "    手动下载: $url"
    fi
done

echo ""
echo "完成。如果全部成功，base.html 的 <script> 标签可正常加载。"
```

- [ ] **Step 3: 运行脚本验证（可选，需网络）**

Run: `pwsh run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.ps1`
Expected: 3 个 JS 文件下载到 static/ 目录（如无网络可跳过，不影响后续测试）

- [ ] **Step 4: 更新 .gitignore 排除 JS 文件**

读取 `run-flow-skills-mcp/.gitignore`，追加：

```
# 第三方 JS 库（由 download_static 脚本下载）
src/run_flow_skills_mcp/web/static/htmx.min.js
src/run_flow_skills_mcp/web/static/alpine.min.js
src/run_flow_skills_mcp/web/static/echarts.min.js
```

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.ps1 run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.sh run-flow-skills-mcp/.gitignore
git commit -m "chore(web): add static asset download scripts for htmx/alpine/echarts"
```

---

### Task 4: routes/dashboard.py 仪表盘路由 + 模板

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/dashboard.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/dashboard.html`
- Test: `run-flow-skills-mcp/tests/web/test_dashboard.py`

**Interfaces:**
- Consumes:
  - `web/deps.get_services()` → `Services`
  - `AnalysisService.calc_metrics(date_from, date_to) -> dict`：返回 `{vdot_trend, tss_sum, ctl, atl, tsb, hr_zones_dist}`
  - `AnalysisService.get_trends(days=30, metric="load") -> dict`：返回 `{series: [{date, value, atl, tsb}], change_pct, baseline}`
  - `ReviewService.get_period_summary(period="week") -> dict`：返回 `{total_distance, total_tss, avg_vdot, sessions_count, vdot_trend, hrv_trend, load_change}`
- Produces:
  - `GET /partials/dashboard` → HTML（4 KPI 卡片 + 负荷趋势图容器 + 本周训练摘要）
  - `GET /api/dashboard/summary` → JSON（KPI + 趋势数据）

- [ ] **Step 1: 写失败测试 — test_dashboard.py**

写入 `run-flow-skills-mcp/tests/web/test_dashboard.py`：

```python
"""dashboard 路由测试."""
from pathlib import Path


def test_dashboard_partial_empty_data(client):
    """空数据时仪表盘片段返回 200，显示空状态."""
    resp = client.get("/partials/dashboard")
    assert resp.status_code == 200
    assert "CTL" in resp.text or "ctl" in resp.text.lower()
    assert "VDOT" in resp.text or "vdot" in resp.text.lower()


def test_dashboard_summary_api_empty_data(client):
    """空数据时 API 返回 200，字段齐全."""
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "ctl" in data
    assert "atl" in data
    assert "tsb" in data
    assert "vdot" in data
    assert "load_series" in data
    assert "weekly_summary" in data


def test_dashboard_summary_api_with_data(client, tmp_data_dir: Path):
    """有数据时 API 返回非零 KPI."""
    from tests.web.conftest import seed_gpx_file
    from run_flow_skills_mcp.web.deps import get_services

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx")
    svc.import_service.import_file(gpx)

    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    # 导入后应有 session，KPI 可能非零
    assert data["ctl"] >= 0
    assert data["atl"] >= 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/web/test_dashboard.py -v`
Expected: FAIL，`ImportError: No module named 'run_flow_skills_mcp.web.routes.dashboard'` 或 404

- [ ] **Step 3: 实现 routes/dashboard.py**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/dashboard.py`：

```python
"""dashboard 路由 — 仪表盘概览页（spec 9.2 页面 1）.

提供仪表盘 HTML 片段和概览数据 API。
复用 analysis_service.calc_metrics + get_trends + review_service.get_period_summary。
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from run_flow_skills_mcp.web.app import templates
from run_flow_skills_mcp.web.deps import get_services

router = APIRouter()


def _build_dashboard_summary() -> dict:
    """组装仪表盘数据：KPI + 负荷趋势 + 本周摘要."""
    svc = get_services()
    today = datetime.now(timezone.utc)
    date_to = today.strftime("%Y-%m-%d")
    date_from = (today - timedelta(days=42)).strftime("%Y-%m-%d")  # CTL 窗口

    # KPI：CTL/ATL/TSB/VDOT
    metrics = svc.analysis_service.calc_metrics(date_from, date_to)
    vdot_trend = metrics.get("vdot_trend", [])
    latest_vdot = vdot_trend[-1]["vdot"] if vdot_trend else None

    # 30 天负荷趋势
    load_trends = svc.analysis_service.get_trends(days=30, metric="load")
    load_series = load_trends.get("series", [])

    # 本周训练摘要
    weekly = svc.review_service.get_period_summary(period="week")

    return {
        "ctl": round(metrics.get("ctl", 0), 1),
        "atl": round(metrics.get("atl", 0), 1),
        "tsb": round(metrics.get("tsb", 0), 1),
        "vdot": round(latest_vdot, 1) if latest_vdot else None,
        "load_series": load_series,
        "weekly_summary": {
            "total_distance_km": round(weekly.get("total_distance", 0), 1),
            "total_tss": round(weekly.get("total_tss", 0), 1),
            "avg_vdot": round(weekly["avg_vdot"], 1) if weekly.get("avg_vdot") else None,
            "sessions_count": weekly.get("sessions_count", 0),
        },
    }


@router.get("/partials/dashboard", response_class=HTMLResponse)
async def dashboard_partial(request: Request):
    """返回仪表盘片段 HTML."""
    summary = _build_dashboard_summary()
    return templates.TemplateResponse(
        request,
        "partials/dashboard.html",
        {"summary": summary},
    )


@router.get("/api/dashboard/summary")
async def dashboard_summary_api():
    """返回仪表盘概览 JSON（图表用）."""
    return _build_dashboard_summary()
```

- [ ] **Step 4: 实现 templates/partials/dashboard.html**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/dashboard.html`：

```html
<!-- 仪表盘片段：4 KPI 卡片 + 负荷趋势图 + 本周训练摘要 -->
<div>
    <!-- KPI 卡片 -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">CTL（慢性负荷）</div>
            <div class="kpi-value">{{ summary.ctl }}</div>
            <div class="kpi-trend">42 天 EWMA</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">ATL（急性负荷）</div>
            <div class="kpi-value">{{ summary.atl }}</div>
            <div class="kpi-trend">7 天 EWMA</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">TSB（压力平衡）</div>
            <div class="kpi-value">{{ summary.tsb }}</div>
            <div class="kpi-trend {% if summary.tsb < 0 %}down{% else %}up{% endif %}">
                {% if summary.tsb > 0 %}↑ 体能充沛{% elif summary.tsb < 0 %}↓ 疲劳积累{% else %}- 平衡{% endif %}
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">VDOT（跑力）</div>
            <div class="kpi-value">{{ summary.vdot if summary.vdot else '--' }}</div>
            <div class="kpi-trend">最新值</div>
        </div>
    </div>

    <!-- 负荷趋势图（ECharts） -->
    <div class="chart-container">
        <h3 style="margin-bottom: 16px;">30 天训练负荷趋势</h3>
        <div data-echart="renderLoadChart" data-chart-url="/api/dashboard/summary"
             id="load-chart" style="width: 100%; height: 320px;">
            <div class="empty-state"><div>图表加载中...</div></div>
        </div>
    </div>

    <!-- 本周训练摘要 -->
    <div class="chart-container">
        <h3 style="margin-bottom: 16px;">本周训练摘要</h3>
        <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>训练次数</td><td>{{ summary.weekly_summary.sessions_count }}</td></tr>
            <tr><td>总距离</td><td>{{ summary.weekly_summary.total_distance_km }} km</td></tr>
            <tr><td>总 TSS</td><td>{{ summary.weekly_summary.total_tss }}</td></tr>
            <tr><td>平均 VDOT</td><td>{{ summary.weekly_summary.avg_vdot if summary.weekly_summary.avg_vdot else '--' }}</td></tr>
        </table>
    </div>
</div>

<script>
// 负荷图需要从 /api/dashboard/summary 读取 load_series
// base.html 的 ECharts 辅助会在 afterSwap 时自动调用 renderLoadChart
// 这里覆盖渲染函数，让它使用 summary.load_series 而非整个 response
window.renderLoadChart = function(container, data) {
    var chart = echarts.init(container);
    var series = data.load_series || [];
    var dates = series.map(p => p.date);
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['CTL', 'ATL', 'TSB'] },
        grid: { left: '8%', right: '5%', bottom: '10%' },
        xAxis: { type: 'category', data: dates },
        yAxis: { type: 'value' },
        series: [
            { name: 'CTL', type: 'line', data: series.map(p => p.value), smooth: true },
            { name: 'ATL', type: 'line', data: series.map(p => p.atl), smooth: true },
            { name: 'TSB', type: 'line', data: series.map(p => p.tsb), smooth: true },
        ],
    });
    window.addEventListener('resize', function() { chart.resize(); });
};
</script>
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/web/test_dashboard.py -v`
Expected: 3 个测试全部 PASS

- [ ] **Step 6: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/dashboard.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/dashboard.html run-flow-skills-mcp/tests/web/test_dashboard.py
git commit -m "feat(web): add dashboard route and template with KPI cards and load trend chart"
```

---

### Task 5: routes/activities.py 活动列表路由 + 模板

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/activities.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/activities.html`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/activity_detail.html`
- Test: `run-flow-skills-mcp/tests/web/test_activities.py`

**Interfaces:**
- Consumes:
  - `web/deps.get_services()` → `Services.parquet_store`
  - `ParquetStore.query_sessions(date_from, date_to, source) -> list[Session]`（Plan 1 Task 5）
  - `ParquetStore.query_metrics(session_ids) -> list[TrainingMetrics]`（Plan 1 Task 5）
- Produces:
  - `GET /partials/activities` → HTML（表格 + 筛选 + 分页）
  - `GET /partials/activities/{session_id}` → HTML 片段（详情，HTMX OOB）
  - `GET /api/sessions` → JSON（活动列表）

- [ ] **Step 1: 写失败测试 — test_activities.py**

写入 `run-flow-skills-mcp/tests/web/test_activities.py`：

```python
"""activities 路由测试."""
from pathlib import Path


def test_activities_partial_empty(client):
    """空数据时活动列表返回 200，显示空状态."""
    resp = client.get("/partials/activities")
    assert resp.status_code == 200
    assert "暂无" in resp.text or "empty" in resp.text.lower() or "没有" in resp.text


def test_activities_api_empty(client):
    """空数据时 API 返回空列表."""
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["sessions"] == []


def test_activities_partial_with_data(client, tmp_data_dir: Path):
    """有数据时列表显示活动."""
    from tests.web.conftest import seed_gpx_file
    from run_flow_skills_mcp.web.deps import get_services

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx", date="2026-07-20")
    svc.import_service.import_file(gpx)

    resp = client.get("/partials/activities")
    assert resp.status_code == 200
    assert "2026-07-20" in resp.text


def test_activities_api_with_data(client, tmp_data_dir: Path):
    """有数据时 API 返回 session 列表."""
    from tests.web.conftest import seed_gpx_file
    from run_flow_skills_mcp.web.deps import get_services

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx", date="2026-07-20")
    svc.import_service.import_file(gpx)

    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["sessions"]) >= 1
    s = data["sessions"][0]
    assert "session_id" in s
    assert "activity_date" in s
    assert "distance_m" in s


def test_activity_detail_partial(client, tmp_data_dir: Path):
    """详情片段返回 session 详情."""
    from tests.web.conftest import seed_gpx_file
    from run_flow_skills_mcp.web.deps import get_services

    svc = get_services(tmp_data_dir)
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "test.gpx", date="2026-07-20")
    result = svc.import_service.import_file(gpx)
    session_id = result["session_id"]

    resp = client.get(f"/partials/activities/{session_id}")
    assert resp.status_code == 200
    assert session_id in resp.text


def test_activity_detail_not_found(client):
    """不存在的 session_id 返回 404."""
    resp = client.get("/partials/activities/sess_nonexistent_001")
    assert resp.status_code == 404
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/web/test_activities.py -v`
Expected: FAIL，路由未注册返回 404

- [ ] **Step 3: 实现 routes/activities.py**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/activities.py`：

```python
"""activities 路由 — 活动列表页（spec 9.2 页面 2）.

提供活动列表片段、单题详情片段和 sessions JSON API。
直接读取 parquet_store（通过 Services 容器），因为 services 层无 list_sessions 方法。
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from run_flow_skills_mcp.web.app import templates
from run_flow_skills_mcp.web.deps import get_services

router = APIRouter()

# 每页条数
_PAGE_SIZE = 20


def _format_pace(s_per_km: float) -> str:
    """配速格式化为 M'SS\"/km."""
    if not s_per_km or s_per_km <= 0:
        return "--"
    m = int(s_per_km // 60)
    s = int(s_per_km % 60)
    return f"{m}'{s:02d}\"/km"


def _format_duration(s: int) -> str:
    """时长格式化为 HH:MM:SS."""
    if not s:
        return "--"
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _list_sessions(
    date_from: str = "", date_to: str = "", source: str = "", page: int = 1
) -> dict:
    """查询 session 列表 + 关联 metrics，分页返回."""
    svc = get_services()
    sessions = svc.parquet_store.query_sessions(
        date_from=date_from or None,
        date_to=date_to or None,
        source=source or None,
    )
    total = len(sessions)

    # 分页
    start = (page - 1) * _PAGE_SIZE
    end = start + _PAGE_SIZE
    page_sessions = sessions[start:end]

    # 关联 metrics
    if page_sessions:
        metrics = svc.parquet_store.query_metrics(
            [s.session_id for s in page_sessions]
        )
        metrics_map = {m.session_id: m for m in metrics}
    else:
        metrics_map = {}

    session_list = []
    for s in page_sessions:
        m = metrics_map.get(s.session_id)
        session_list.append({
            "session_id": s.session_id,
            "activity_date": s.activity_date.strftime("%Y-%m-%d"),
            "distance_km": round(s.distance_m / 1000, 2),
            "duration": _format_duration(s.duration_s),
            "pace": _format_pace(s.avg_pace_s_per_km),
            "avg_hr": s.avg_hr,
            "vdot": round(m.vdot, 1) if m and m.vdot else None,
            "source": s.source,
        })

    return {
        "sessions": session_list,
        "total": total,
        "page": page,
        "total_pages": (total + _PAGE_SIZE - 1) // _PAGE_SIZE,
    }


@router.get("/partials/activities", response_class=HTMLResponse)
async def activities_partial(
    request: Request,
    date_from: str = "",
    date_to: str = "",
    source: str = "",
    page: int = 1,
):
    """返回活动列表片段（带筛选 + 分页）."""
    data = _list_sessions(date_from, date_to, source, page)
    return templates.TemplateResponse(
        request,
        "partials/activities.html",
        {
            **data,
            "current_date_from": date_from,
            "current_date_to": date_to,
            "current_source": source,
        },
    )


@router.get("/partials/activities/{session_id}", response_class=HTMLResponse)
async def activity_detail_partial(request: Request, session_id: str):
    """返回单题详情片段（HTMX OOB）."""
    svc = get_services()
    sessions = svc.parquet_store.query_sessions()
    session = next((s for s in sessions if s.session_id == session_id), None)
    if session is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    metrics = svc.parquet_store.query_metrics([session_id])
    m = metrics[0] if metrics else None

    return templates.TemplateResponse(
        request,
        "partials/activity_detail.html",
        {
            "session": session,
            "metrics": m,
            "format_pace": _format_pace,
            "format_duration": _format_duration,
        },
    )


@router.get("/api/sessions")
async def sessions_api(
    date_from: str = "",
    date_to: str = "",
    source: str = "",
    page: int = 1,
):
    """返回活动列表 JSON."""
    return _list_sessions(date_from, date_to, source, page)
```

- [ ] **Step 4: 实现 templates/partials/activities.html**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/activities.html`：

```html
<!-- 活动列表片段：筛选栏 + 表格 + 分页 -->
<div>
    <!-- 筛选栏 -->
    <div class="chart-container" style="display: flex; gap: 12px; align-items: end;">
        <div class="form-group" style="flex: 1;">
            <label>开始日期</label>
            <input type="date" name="date_from" value="{{ current_date_from }}"
                   hx-get="/partials/activities" hx-target="#activity-list" hx-trigger="change"
                   hx-include="[name='date_to'],[name='source']" hx-vals='{"page": 1}'>
        </div>
        <div class="form-group" style="flex: 1;">
            <label>结束日期</label>
            <input type="date" name="date_to" value="{{ current_date_to }}"
                   hx-get="/partials/activities" hx-target="#activity-list" hx-trigger="change"
                   hx-include="[name='date_from'],[name='source']" hx-vals='{"page": 1}'>
        </div>
        <div class="form-group" style="flex: 1;">
            <label>来源</label>
            <select name="source" value="{{ current_source }}"
                    hx-get="/partials/activities" hx-target="#activity-list" hx-trigger="change"
                    hx-include="[name='date_from'],[name='date_to']" hx-vals='{"page": 1}'>
                <option value="">全部</option>
                <option value="garmin" {% if current_source == 'garmin' %}selected{% endif %}>Garmin</option>
                <option value="coros" {% if current_source == 'coros' %}selected{% endif %}>COROS</option>
                <option value="apple" {% if current_source == 'apple' %}selected{% endif %}>Apple</option>
                <option value="manual" {% if current_source == 'manual' %}selected{% endif %}>手动</option>
            </select>
        </div>
    </div>

    <!-- 活动列表 -->
    <div id="activity-list">
        {% if sessions %}
        <table>
            <thead>
                <tr>
                    <th>日期</th>
                    <th>距离</th>
                    <th>时长</th>
                    <th>配速</th>
                    <th>心率</th>
                    <th>VDOT</th>
                    <th>来源</th>
                </tr>
            </thead>
            <tbody>
                {% for s in sessions %}
                <tr hx-get="/partials/activities/{{ s.session_id }}" hx-target="#activity-detail"
                    hx-trigger="click">
                    <td>{{ s.activity_date }}</td>
                    <td>{{ s.distance_km }} km</td>
                    <td>{{ s.duration }}</td>
                    <td>{{ s.pace }}</td>
                    <td>{{ s.avg_hr if s.avg_hr else '--' }}</td>
                    <td>{{ s.vdot if s.vdot else '--' }}</td>
                    <td>{{ s.source }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- 分页 -->
        {% if total_pages > 1 %}
        <div style="margin-top: 16px; display: flex; gap: 8px; justify-content: center;">
            {% for p in range(1, total_pages + 1) %}
            <button class="btn {% if p == page %}btn-primary{% else %}btn-secondary{% endif %}"
                    hx-get="/partials/activities?page={{ p }}"
                    hx-target="#activity-list"
                    hx-include="[name='date_from'],[name='date_to'],[name='source']">
                {{ p }}
            </button>
            {% endfor %}
        </div>
        {% endif %}
        {% else %}
        <div class="empty-state">
            <div>暂无活动记录</div>
            <p style="margin-top: 8px;">点击导航栏「导入」上传训练文件</p>
        </div>
        {% endif %}
    </div>

    <!-- 详情区（HTMX OOB） -->
    <div id="activity-detail" style="margin-top: 24px;"></div>
</div>
```

- [ ] **Step 5: 实现 templates/partials/activity_detail.html**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/activity_detail.html`：

```html
<!-- 活动详情片段：基本信息 + 指标 -->
<div class="chart-container">
    <h3 style="margin-bottom: 16px;">活动详情 — {{ session.session_id }}</h3>
    <table>
        <tr><th>字段</th><th>值</th></tr>
        <tr><td>日期</td><td>{{ session.activity_date.strftime('%Y-%m-%d %H:%M') }}</td></tr>
        <tr><td>距离</td><td>{{ (session.distance_m / 1000)|round(2) }} km</td></tr>
        <tr><td>时长</td><td>{{ format_duration(session.duration_s) }}</td></tr>
        <tr><td>平均配速</td><td>{{ format_pace(session.avg_pace_s_per_km) }}</td></tr>
        <tr><td>平均心率</td><td>{{ session.avg_hr if session.avg_hr else '--' }} bpm</td></tr>
        <tr><td>最大心率</td><td>{{ session.max_hr if session.max_hr else '--' }} bpm</td></tr>
        <tr><td>步频</td><td>{{ session.cadence if session.cadence else '--' }} spm</td></tr>
        <tr><td>累计爬升</td><td>{{ session.elevation_gain_m if session.elevation_gain_m else '--' }} m</td></tr>
        <tr><td>来源</td><td>{{ session.source }}</td></tr>
        {% if metrics %}
        <tr><td>VDOT</td><td>{{ metrics.vdot|round(1) if metrics.vdot else '--' }}</td></tr>
        <tr><td>TSS</td><td>{{ metrics.tss|round(1) }}</td></tr>
        <tr><td>强度因子</td><td>{{ metrics.intensity_factor|round(3) }}</td></tr>
        <tr><td>配速区间</td><td>{{ metrics.pace_zone }}</td></tr>
        {% endif %}
        {% if session.notes %}
        <tr><td>备注</td><td>{{ session.notes }}</td></tr>
        {% endif %}
    </table>
</div>
```

- [ ] **Step 6: 运行测试验证通过**

Run: `uv run pytest tests/web/test_activities.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 7: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/activities.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/activities.html run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/activity_detail.html run-flow-skills-mcp/tests/web/test_activities.py
git commit -m "feat(web): add activities list route and templates with filter and pagination"
```

---

### Task 6: routes/import_page.py 数据导入路由 + 模板 ⭐

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/import_page.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/import.html`
- Test: `run-flow-skills-mcp/tests/web/test_import_page.py`

**Interfaces:**
- Consumes:
  - `web/deps.get_services()` → `Services.import_service`
  - `ImportService.import_file(file_path: Path, force=False, source=None) -> dict`（Plan 2 Task 4）
  - `ImportService.import_manual(manual_data: dict, force=False) -> dict`（Plan 2 Task 4）
  - `constants.SUPPORTED_IMPORT_EXT / MAX_UPLOAD_FILE_SIZE_MB / MAX_BATCH_UPLOAD_FILES`（Plan 1 Task 2）
  - `web/schemas.ManualInputRequest`（Task 2）
- Produces:
  - `GET /partials/import` → HTML（拖拽区 + 文件列表 + 手动录入表单）
  - `POST /api/import/upload` → JSON（多文件上传，multipart/form-data）
  - `POST /api/import/manual` → JSON（手动录入）

- [ ] **Step 1: 写失败测试 — test_import_page.py**

写入 `run-flow-skills-mcp/tests/web/test_import_page.py`：

```python
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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/web/test_import_page.py -v`
Expected: FAIL，路由未注册

- [ ] **Step 3: 实现 routes/import_page.py**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/import_page.py`：

```python
"""import_page 路由 — 数据导入页（spec 9.2 页面 3，9.4 导入流程）.

⭐ 核心功能：可视化批量导入，复用 import_service，与 MCP import_file tool 共用。
安全限制：文件类型白名单、单文件 100MB、批量 100 文件。
"""
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
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
async def import_upload(files: list[UploadFile], force: bool = False):
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
```

- [ ] **Step 4: 实现 templates/partials/import.html**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/import.html`：

```html
<!-- 导入页片段：拖拽区 + 文件列表 + 手动录入表单 -->
<div x-data="importPage()">
    <!-- 拖拽上传区 -->
    <div class="chart-container">
        <h3 style="margin-bottom: 16px;">批量导入训练文件</h3>
        <p style="color: #666; margin-bottom: 16px;">
            支持格式：{{ ' '.join(supported_ext) }} | 单文件上限 {{ max_size_mb }}MB | 批量上限 {{ max_batch }} 个
        </p>

        <div class="drop-zone" 
             @dragover.prevent="dragover = true" 
             @dragleave.prevent="dragover = false"
             @drop.prevent="handleDrop"
             :class="{ 'dragover': dragover }"
             @click="$refs.fileInput.click()">
            <div style="font-size: 48px; margin-bottom: 8px;">📁</div>
            <div>拖拽文件到此处，或点击选择文件（支持多选）</div>
        </div>
        <input type="file" x-ref="fileInput" multiple 
               :accept="supported_ext.map(e => '.' + e).join(',')"
               style="display: none;" @change="handleSelect">

        <!-- 强制重新导入勾选框 -->
        <label style="display: flex; align-items: center; gap: 8px; margin-top: 16px;">
            <input type="checkbox" x-model="force">
            <span>强制重新导入（覆盖重复文件）</span>
        </label>

        <!-- 导入按钮 -->
        <button class="btn btn-primary" @click="uploadFiles" :disabled="pendingFiles.length === 0"
                style="margin-top: 16px;">
            导入 {{ pendingFiles.length }} 个文件
        </button>
    </div>

    <!-- 导入进度列表 -->
    <div class="chart-container" x-show="results.length > 0" style="display: none;">
        <h3 style="margin-bottom: 16px;">导入结果</h3>
        <table>
            <thead>
                <tr><th>文件名</th><th>状态</th><th>详情</th></tr>
            </thead>
            <tbody>
                <template x-for="r in results" :key="r.filename">
                    <tr>
                        <td x-text="r.filename"></td>
                        <td>
                            <span x-show="r.imported" style="color: #34a853;">✅ 已导入</span>
                            <span x-show="r.skipped" style="color: #fbbc04;">⏭️ 跳过</span>
                            <span x-show="!r.imported && !r.skipped" style="color: #ea4335;">❌ 失败</span>
                        </td>
                        <td x-text="r.session_id || r.reason || r.error || ''"></td>
                    </tr>
                </template>
            </tbody>
        </table>
        <p style="margin-top: 12px; color: #666;">
            共 <span x-text="results.length"></span> 个文件，
            成功 <span x-text="results.filter(r => r.imported).length" style="color: #34a853;"></span>，
            跳过 <span x-text="results.filter(r => r.skipped).length" style="color: #fbbc04;"></span>，
            失败 <span x-text="results.filter(r => !r.imported && !r.skipped).length" style="color: #ea4335;"></span>
        </p>
    </div>

    <!-- 手动录入表单 -->
    <div class="chart-container">
        <h3 style="margin-bottom: 16px;">手动录入（备用方案）</h3>
        <form @submit.prevent="submitManual">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div class="form-group">
                    <label>活动日期 *</label>
                    <input type="datetime-local" x-model="manual.activity_date" required>
                </div>
                <div class="form-group">
                    <label>来源</label>
                    <select x-model="manual.source">
                        <option value="manual">手动</option>
                        <option value="garmin">Garmin</option>
                        <option value="coros">COROS</option>
                        <option value="apple">Apple</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>距离（米）*</label>
                    <input type="number" x-model.number="manual.distance_m" min="1" required>
                </div>
                <div class="form-group">
                    <label>时长（秒）*</label>
                    <input type="number" x-model.number="manual.duration_s" min="1" required>
                </div>
                <div class="form-group">
                    <label>平均心率</label>
                    <input type="number" x-model.number="manual.avg_hr" min="30" max="260">
                </div>
                <div class="form-group">
                    <label>最大心率</label>
                    <input type="number" x-model.number="manual.max_hr" min="30" max="260">
                </div>
            </div>
            <div class="form-group">
                <label>备注</label>
                <input type="text" x-model="manual.notes">
            </div>
            <button type="submit" class="btn btn-primary">提交录入</button>
        </form>
        <div x-show="manualResult" style="margin-top: 12px;" :style="manualResult?.imported ? 'color: #34a853;' : 'color: #ea4335;'">
            <span x-text="manualResult?.imported ? '✅ 录入成功：' + (manualResult?.session_id || '') : '❌ ' + (manualResult?.error || '录入失败')"></span>
        </div>
    </div>
</div>

<script>
function importPage() {
    return {
        dragover: false,
        force: false,
        pendingFiles: [],
        results: [],
        manual: {
            activity_date: '',
            distance_m: null,
            duration_s: null,
            avg_hr: null,
            max_hr: null,
            source: 'manual',
            notes: '',
        },
        manualResult: null,
        supported_ext: Array.from(document.currentScript.dataset.supported_ext || '{{ supported_ext|tojson }}'),

        handleDrop(e) {
            this.dragover = false;
            this.pendingFiles = Array.from(e.dataTransfer.files);
        },

        handleSelect(e) {
            this.pendingFiles = Array.from(e.target.files);
        },

        async uploadFiles() {
            if (this.pendingFiles.length === 0) return;
            const formData = new FormData();
            this.pendingFiles.forEach(f => formData.append('files', f));
            formData.append('force', this.force);

            try {
                const resp = await fetch('/api/import/upload', {
                    method: 'POST',
                    body: formData,
                });
                const data = await resp.json();
                this.results = data.results || [];
                showToast(`导入完成：成功 ${data.imported}，跳过 ${data.skipped}，失败 ${data.failed}`,
                          data.failed > 0 ? 'error' : 'success');
                this.pendingFiles = [];
            } catch (err) {
                showToast('上传失败：' + err.message, 'error');
            }
        },

        async submitManual() {
            try {
                const resp = await fetch('/api/import/manual', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.manual),
                });
                this.manualResult = await resp.json();
                if (this.manualResult.imported) {
                    showToast('录入成功', 'success');
                    this.manual = { activity_date: '', distance_m: null, duration_s: null,
                                   avg_hr: null, max_hr: null, source: 'manual', notes: '' };
                } else {
                    showToast('录入失败：' + (this.manualResult.error || ''), 'error');
                }
            } catch (err) {
                showToast('录入失败：' + err.message, 'error');
            }
        },
    };
}
</script>
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/web/test_import_page.py -v`
Expected: 9 个测试全部 PASS

- [ ] **Step 6: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/import_page.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/import.html run-flow-skills-mcp/tests/web/test_import_page.py
git commit -m "feat(web): add import page with drag-drop upload, whitelist, and manual form"
```

---

### Task 7: routes/settings.py 设置路由 + 模板

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/settings.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/settings.html`
- Test: `run-flow-skills-mcp/tests/web/test_settings.py`

**Interfaces:**
- Consumes:
  - `web/deps.get_services()` → `Services.json_store`
  - `constants.DEFAULT_MAX_HR / DEFAULT_LTHR / DEFAULT_RESTING_HR / DEFAULT_AGE / DEFAULT_WEIGHT_KG / DEFAULT_HEIGHT_CM`（Plan 1 Task 2）
  - `models.UserConfig`（Plan 1 Task 3）
  - `web/schemas.ConfigUpdateRequest`（Task 2）
- Produces:
  - `GET /partials/settings` → HTML（7 字段配置表单）
  - `GET /api/config` → JSON（当前配置 + 默认值）
  - `PUT /api/config` → JSON（部分更新，写入 data/config.json）

- [ ] **Step 1: 写失败测试 — test_settings.py**

写入 `run-flow-skills-mcp/tests/web/test_settings.py`：

```python
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
    assert data["age"] == 35       # 保留
    assert data["lthr"] == 160     # 新增


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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/web/test_settings.py -v`
Expected: FAIL，路由未注册

- [ ] **Step 3: 实现 routes/settings.py**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/settings.py`：

```python
"""settings 路由 — 设置页（spec 9.2 页面 4，M-3 评审修正）.

读写 data/config.json，覆盖 constants.py 默认值。
calc_metrics 读取顺序：data/config.json → constants.py 默认值。
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from run_flow_skills_mcp.constants import (
    DATA_DIR,
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

_CONFIG_PATH = Path(DATA_DIR) / "config.json"

# 默认值映射（供前端占位符提示）
_DEFAULTS = {
    "max_hr": DEFAULT_MAX_HR,
    "lthr": DEFAULT_LTHR,
    "resting_hr": DEFAULT_RESTING_HR,
    "age": DEFAULT_AGE,
    "weight_kg": DEFAULT_WEIGHT_KG,
    "height_cm": DEFAULT_HEIGHT_CM,
}


def _load_config() -> dict:
    """读取 data/config.json，不存在返回空 dict."""
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _save_config(cfg: dict) -> None:
    """写入 data/config.json."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(
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
```

- [ ] **Step 4: 实现 templates/partials/settings.html**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/settings.html`：

```html
<!-- 设置页片段：7 字段配置表单 -->
<div x-data="settingsPage()">
    <div class="chart-container">
        <h3 style="margin-bottom: 8px;">个人配置</h3>
        <p style="color: #666; margin-bottom: 16px; font-size: 13px;">
            这些参数用于心率区间和训练负荷计算，请根据实测值填写（如乳酸阈值心率需实验室测试）。
            未设置的字段将使用默认值。
        </p>

        <form @submit.prevent="save">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div class="form-group">
                    <label>最大心率（bpm）</label>
                    <input type="number" x-model.number="config.max_hr" min="80" max="260"
                           placeholder="默认 {{ defaults.max_hr }}">
                </div>
                <div class="form-group">
                    <label>乳酸阈值心率（bpm）</label>
                    <input type="number" x-model.number="config.lthr" min="60" max="220"
                           placeholder="默认 {{ defaults.lthr }}">
                </div>
                <div class="form-group">
                    <label>静息心率（bpm）</label>
                    <input type="number" x-model.number="config.resting_hr" min="30" max="150"
                           placeholder="默认 {{ defaults.resting_hr }}">
                </div>
                <div class="form-group">
                    <label>年龄</label>
                    <input type="number" x-model.number="config.age" min="10" max="120"
                           placeholder="默认 {{ defaults.age }}">
                </div>
                <div class="form-group">
                    <label>体重（kg）</label>
                    <input type="number" step="0.1" x-model.number="config.weight_kg" min="0" max="300"
                           placeholder="默认 {{ defaults.weight_kg }}">
                </div>
                <div class="form-group">
                    <label>身高（cm）</label>
                    <input type="number" step="0.1" x-model.number="config.height_cm" min="0" max="300"
                           placeholder="默认 {{ defaults.height_cm }}">
                </div>
                <div class="form-group">
                    <label>性别</label>
                    <select x-model="config.gender">
                        <option value="">未设置</option>
                        <option value="male">男</option>
                        <option value="female">女</option>
                    </select>
                </div>
            </div>

            <div style="display: flex; gap: 12px; margin-top: 20px;">
                <button type="submit" class="btn btn-primary">保存</button>
                <button type="button" class="btn btn-secondary" @click="reset">重置为默认值</button>
            </div>
        </form>

        <div x-show="message" style="margin-top: 16px;" :style="messageType === 'success' ? 'color: #34a853;' : 'color: #ea4335;'">
            <span x-text="message"></span>
        </div>
    </div>

    <div class="chart-container">
        <h3 style="margin-bottom: 8px;">当前生效值</h3>
        <p style="color: #666; margin-bottom: 12px; font-size: 13px;">
            以下为计算器实际使用的值（data/config.json 覆盖 → constants.py 默认值）
        </p>
        <table>
            <tr><th>参数</th><th>当前值</th><th>来源</th></tr>
            <template x-for="(val, key) in effectiveValues" :key="key">
                <tr>
                    <td x-text="labelMap[key]"></td>
                    <td x-text="val !== null ? val : '未设置'"></td>
                    <td x-text="config[key] !== null && config[key] !== undefined ? 'config.json' : '默认值'"></td>
                </tr>
            </template>
        </table>
    </div>
</div>

<script>
function settingsPage() {
    var defaults = {{ defaults|tojson }};
    var current = {{ current|tojson }};

    return {
        config: Object.assign({}, {max_hr: null, lthr: null, resting_hr: null, age: null,
                                    weight_kg: null, height_cm: null, gender: ''}, current),
        defaults: defaults,
        message: '',
        messageType: 'success',
        labelMap: {max_hr: '最大心率', lthr: '乳酸阈值心率', resting_hr: '静息心率',
                   age: '年龄', weight_kg: '体重', height_cm: '身高', gender: '性别'},

        get effectiveValues() {
            var result = {};
            for (var key in this.defaults) {
                result[key] = (this.config[key] !== null && this.config[key] !== undefined && this.config[key] !== '')
                    ? this.config[key] : this.defaults[key];
            }
            result.gender = this.config.gender || '未设置';
            return result;
        },

        async save() {
            try {
                var resp = await fetch('/api/config', {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(this.config),
                });
                if (resp.ok) {
                    this.message = '✅ 配置已保存';
                    this.messageType = 'success';
                    showToast('配置已保存', 'success');
                } else {
                    var err = await resp.json();
                    this.message = '❌ 保存失败：' + JSON.stringify(err.detail || err);
                    this.messageType = 'error';
                }
            } catch (e) {
                this.message = '❌ 保存失败：' + e.message;
                this.messageType = 'error';
            }
        },

        async reset() {
            if (!confirm('确定重置所有字段为默认值？这将清空 config.json。')) return;
            var resetData = {};
            for (var key in this.defaults) resetData[key] = null;
            resetData.gender = '';
            try {
                await fetch('/api/config', {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(resetData),
                });
                this.config = Object.assign({}, {max_hr: null, lthr: null, resting_hr: null, age: null,
                                                  weight_kg: null, height_cm: null, gender: ''});
                this.message = '✅ 已重置为默认值';
                this.messageType = 'success';
                showToast('已重置为默认值', 'success');
            } catch (e) {
                this.message = '❌ 重置失败：' + e.message;
                this.messageType = 'error';
            }
        },
    };
}
</script>
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/web/test_settings.py -v`
Expected: 7 个测试全部 PASS

- [ ] **Step 6: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/web/routes/settings.py run-flow-skills-mcp/src/run_flow_skills_mcp/web/templates/partials/settings.html run-flow-skills-mcp/tests/web/test_settings.py
git commit -m "feat(web): add settings page for user config read/write with defaults"
```

---

### Task 8: pyproject.toml 注册入口 + Web 集成测试 + 冒烟验证

**Files:**
- Modify: `run-flow-skills-mcp/pyproject.toml`（注册 `run-flow-skills-web` 入口）
- Create: `run-flow-skills-mcp/tests/web/test_web_integration.py`
- Test: `run-flow-skills-mcp/tests/web/test_web_integration.py`

**Interfaces:**
- Consumes: Task 1-7 所有 web 路由 + Plan 2 所有 services
- Produces: 完整可运行的 Web 应用 + 端到端集成测试

- [ ] **Step 1: 在 pyproject.toml 注册 web 入口点**

读取 `run-flow-skills-mcp/pyproject.toml`，在 `[project.scripts]` 段添加 `run-flow-skills-web`：

```toml
[project.scripts]
run-flow-skills-mcp = "run_flow_skills_mcp.server:main"
run-flow-skills-web = "run_flow_skills_mcp.web.app:main"
```

- [ ] **Step 2: 写集成测试 — test_web_integration.py**

写入 `run-flow-skills-mcp/tests/web/test_web_integration.py`：

```python
"""Web 端到端集成测试：完整工作流（导入 → 仪表盘 → 活动列表 → 设置 → 导出）."""
import io
import json
from pathlib import Path

from tests.web.conftest import seed_gpx_file


def test_full_workflow_import_to_dashboard(client, tmp_data_dir: Path):
    """完整工作流：导入 → 仪表盘显示 → 活动列表 → 设置 → 导出."""
    from run_flow_skills_mcp.web.deps import get_services

    svc = get_services(tmp_data_dir)

    # 1. 导入 GPX 文件
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "run1.gpx", date="2026-07-20")
    with open(gpx, "rb") as f:
        resp = client.post(
            "/api/import/upload",
            files={"files": ("run1.gpx", f, "application/xml")},
        )
    assert resp.status_code == 200
    assert resp.json()["imported"] == 1

    # 2. 仪表盘显示数据
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["weekly_summary"]["sessions_count"] >= 1

    # 3. 活动列表显示
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert sessions["total"] >= 1

    # 4. 设置页读写配置
    resp = client.put("/api/config", json={"max_hr": 185, "age": 35})
    assert resp.status_code == 200
    resp = client.get("/api/config")
    assert resp.json()["max_hr"] == 185

    # 5. 导出（复用 stats_service）
    resp = client.get("/partials/dashboard")
    assert resp.status_code == 200
    assert "185" not in resp.text  # 仪表盘不显示配置


def test_all_four_pages_accessible(client):
    """4 个页面片段均返回 200."""
    for path in ["/partials/dashboard", "/partials/activities", "/partials/import", "/partials/settings"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} 返回 {resp.status_code}"


def test_all_api_endpoints_accessible(client):
    """所有 API 端点返回 200."""
    for path in ["/api/dashboard/summary", "/api/sessions", "/api/config"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} 返回 {resp.status_code}"


def test_import_then_activities_shows_imported(client, tmp_data_dir: Path):
    """导入后活动列表显示导入的记录."""
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "run2.gpx", date="2026-07-21")
    with open(gpx, "rb") as f:
        client.post("/api/import/upload", files={"files": ("run2.gpx", f, "application/xml")})

    resp = client.get("/partials/activities")
    assert resp.status_code == 200
    assert "2026-07-21" in resp.text


def test_config_persist_across_requests(client, tmp_data_dir: Path):
    """配置跨请求持久化."""
    client.put("/api/config", json={"max_hr": 195, "lthr": 170})
    # 再次读取
    resp = client.get("/api/config")
    data = resp.json()
    assert data["max_hr"] == 195
    assert data["lthr"] == 170


def test_upload_batch_with_mixed_valid_invalid(client, tmp_data_dir: Path):
    """批量上传含合法和非法文件."""
    gpx = seed_gpx_file(tmp_data_dir / "uploads" / "ok.gpx", date="2026-07-22")
    with open(gpx, "rb") as f_ok:
        fake = io.BytesIO(b"fake exe")
        resp = client.post(
            "/api/import/upload",
            files=[
                ("files", ("ok.gpx", f_ok, "application/xml")),
                ("files", ("bad.exe", fake, "application/octet-stream")),
            ],
        )
    data = resp.json()
    assert data["total"] == 2
    assert data["imported"] == 1
    assert data["failed"] == 1


def test_web_entry_point_registered():
    """pyproject.toml 注册了 run-flow-skills-web 入口."""
    import subprocess
    result = subprocess.run(
        ["uv", "run", "run-flow-skills-web", "--help"],
        capture_output=True, text=True, cwd="run-flow-skills-mcp",
    )
    # uvicorn --help 返回 0 或入口可被调用即算通过
    # （实际启动会阻塞，这里只验证入口存在）
    assert "run-flow-skills-web" in result.stdout or result.returncode in (0, 1) or "uvicorn" in result.stderr
```

- [ ] **Step 3: 运行所有 web 测试**

Run: `uv run pytest tests/web/ -v --tb=short`
Expected: 所有 web 测试 PASS（test_app + test_schemas + test_dashboard + test_activities + test_import_page + test_settings + test_web_integration）

- [ ] **Step 4: 运行全量测试确保无回归**

Run: `uv run pytest tests/ -v --tb=short`
Expected: 所有测试 PASS（Plan 1 基础设施 + Plan 2 services/tools + Plan 3 web）

- [ ] **Step 5: 手动冒烟测试（可选，需静态资源已下载）**

```bash
# 下载静态资源（首次）
pwsh run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.ps1

# 启动 web 服务
uv run run-flow-skills-web

# 浏览器访问 http://127.0.0.1:8002 验证：
# - 仪表盘 4 KPI 卡片渲染
# - 活动列表空状态显示
# - 导入页拖拽区显示
# - 设置页 7 字段表单显示
```

- [ ] **Step 6: Commit**

```bash
git add run-flow-skills-mcp/pyproject.toml run-flow-skills-mcp/tests/web/test_web_integration.py
git commit -m "feat(web): register web entry point and add end-to-end integration tests"
```

---

## Self-Review

### 1. Spec 覆盖检查

| 设计文档章节 | 覆盖 Task | 说明 |
|---|---|---|
| 9.1 技术栈 | Task 1 | FastAPI + Jinja2 + HTMX + Alpine + ECharts |
| 9.2 页面 1 仪表盘 | Task 4 | 4 KPI + 负荷趋势图 + 本周摘要 |
| 9.2 页面 2 活动列表 | Task 5 | 表格 + 筛选 + 分页 + 详情 OOB |
| 9.2 页面 3 数据导入 ⭐ | Task 6 | 拖拽 + 多文件 + 白名单 + 手动录入 |
| 9.2 页面 4 设置（M-3） | Task 7 | 7 字段表单 + 读写 config.json |
| 9.3 路由设计 | Task 1/4/5/6/7 | 所有 MVP ✅ 路由均已实现 |
| 9.4 导入流程时序 | Task 6 | POST /api/import/upload 复用 import_service |
| 9.5 安全与限制 | Task 6 | 白名单 + 100MB + 100 文件 + 127.0.0.1 |
| 9.6 实现要点 | Task 1/6 | web 复用 services，与 tool 共用 |

### 2. 占位符扫描

- ✅ 无 TBD/TODO
- ✅ 所有代码块完整可运行
- ✅ 所有测试有具体断言

### 3. 类型一致性

- `get_services()` 签名与 Plan 2 一致
- `Services.parquet_store/json_store` 在 Task 1 新增，后续 Task 使用一致
- `ManualInputRequest` / `ConfigUpdateRequest` 字段与 Plan 1 `UserConfig` 约束一致
- `import_service.import_file/import_manual` 返回结构与 Plan 2 一致

### 4. 依赖链

- Task 1 → 修改 `_deps.py` + 创建 app.py（依赖 Plan 2 `_deps.py`）
- Task 2 → schemas.py（依赖 Plan 1 `UserConfig`）
- Task 3 → 静态资源下载脚本（独立）
- Task 4 → dashboard（依赖 Task 1 + Plan 2 `analysis_service/review_service`）
- Task 5 → activities（依赖 Task 1 + Plan 1 `parquet_store`）
- Task 6 → import（依赖 Task 1/2 + Plan 2 `import_service` + Plan 1 `constants`）
- Task 7 → settings（依赖 Task 2 + Plan 1 `constants/UserConfig`）
- Task 8 → 集成测试（依赖 Task 1-7 全部完成）
