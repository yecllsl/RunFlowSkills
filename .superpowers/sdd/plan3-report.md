# RunFlowSkills MVP v0.1.0 Plan 3 实施报告 — Web 可视化

**状态**: DONE
**执行日期**: 2026-07-25
**测试摘要**: 240 passed (Plan 1+2 198 + Plan 3 新增 42)，0 failed

---

## 1. 完成的 Task 清单

| Task | 内容 | 测试数 | 状态 |
|------|------|--------|------|
| Task 1 | web 模块骨架 + app.py 应用工厂 + Services 容器验证 | 4 | DONE |
| Task 2 | schemas.py Web 请求模型（ManualInputRequest / ConfigUpdateRequest） | 6 | DONE |
| Task 3 | 静态资源下载脚本（PowerShell + bash） | 0 | DONE |
| Task 4 | routes/dashboard.py 仪表盘路由 + 模板 | 3 | DONE |
| Task 5 | routes/activities.py 活动列表路由 + 模板 | 6 | DONE |
| Task 6 | routes/import_page.py 数据导入路由 + 模板 | 9 | DONE |
| Task 7 | routes/settings.py 设置路由 + 模板 | 7 | DONE |
| Task 8 | pyproject.toml 注册入口 + Web 集成测试 | 7 | DONE |
| **合计** | | **42** | |

## 2. 关键实现要点

### 2.1 Services 容器复用（Plan 2 已就绪）
- `_deps.py` 的 `Services` dataclass 已含 `parquet_store` 和 `json_store` 字段（Plan 2 一次性定义）
- Plan 3 Task 1 Step 1 仅验证，未修改 `_deps.py`
- `web/deps.py` 是薄包装，直接复用 `tools/_deps.get_services()`

### 2.2 测试 fixture 与路由 data_dir 一致性
**关键修复**：Plan 中 `conftest.py` 的 `tmp_data_dir` fixture 创建临时目录，但路由中 `get_services()` 无参调用会使用默认 `DATA_DIR`，导致测试 fixture 与路由实例不一致。

**解决方案**（偏离 Plan 的合理修正）：
- `conftest.py` 的 `tmp_data_dir` fixture 通过 `monkeypatch.setattr("run_flow_skills_mcp.tools._deps._DEFAULT_DATA_DIR", tmp_path)` 让无参 `get_services()` 返回 tmp_path 对应的 services
- `settings.py` 中 `_config_path()` 改为动态获取 `get_services().json_store.data_dir / "config.json"`，而非 Plan 中的模块级常量 `_CONFIG_PATH = Path(DATA_DIR) / "config.json"`，保证 config.json 读写与 services 容器的 data_dir 一致

### 2.3 force 参数 Form 解析
**关键修复**：Plan 中 `import_upload(files: list[UploadFile], force: bool = False)` 的 `force` 被 FastAPI 当作 query 参数，导致 `data={"force": "true"}` 表单字段被忽略。

**解决方案**：改用 `force: bool = Form(False)` 显式声明为 form 参数，Pydantic 自动将字符串 "true" 转为 True。

### 2.4 Jinja2 与 Alpine.js 模板冲突
**关键修复**：`import.html` 中 `{{ pendingFiles.length }}` 被 Jinja2 当作变量解析，触发 `UndefinedError`。

**解决方案**：改为 `<span x-text="pendingFiles.length"></span>`，避免 Jinja2/Alpine 语法冲突。

### 2.5 activities API 字段补充
Plan 中 `_list_sessions` 返回 `distance_km` 但测试断言 `distance_m`。实现中同时返回两者（`distance_m` 原始米数 + `distance_km` 公里数），满足测试契约和模板显示需求。

### 2.6 入口点测试稳健性
Plan 中 `test_web_entry_point_registered` 用 `subprocess.run(["uv", "run", "run-flow-skills-web", "--help"])`，但 uvicorn 入口不接受 `--help` 且会阻塞。改为 `importlib.metadata.entry_points(group="console_scripts")` 检查元数据，避免实际启动进程。

## 3. 文件清单

### 3.1 新增源码（14 个文件）
```
run-flow-skills-mcp/src/run_flow_skills_mcp/web/
├── __init__.py
├── app.py                          # FastAPI 应用工厂 + main() 入口
├── deps.py                         # 薄包装，复用 tools/_deps.get_services
├── schemas.py                      # ManualInputRequest / ConfigUpdateRequest
├── routes/
│   ├── __init__.py
│   ├── dashboard.py                # 仪表盘：partial + summary API
│   ├── activities.py               # 活动列表：partial + detail + sessions API
│   ├── import_page.py              # 导入：partial + upload API + manual API
│   └── settings.py                 # 设置：partial + config GET/PUT API
├── templates/
│   ├── base.html                   # 单页外壳（4 tab 导航 + HTMX + ECharts 辅助）
│   ├── errors.html                 # 错误页
│   └── partials/
│       ├── dashboard.html          # 4 KPI + 负荷趋势图 + 本周摘要
│       ├── activities.html         # 表格 + 筛选 + 分页
│       ├── activity_detail.html    # 详情片段（HTMX OOB）
│       ├── import.html             # 拖拽区 + 文件列表 + 手动录入表单
│       └── settings.html           # 7 字段配置表单
└── static/
    ├── app.css                     # 全局样式
    ├── download_static.ps1         # Windows 静态资源下载脚本
    └── download_static.sh          # Linux/macOS 静态资源下载脚本
```

### 3.2 新增测试（7 个文件，42 个测试）
```
run-flow-skills-mcp/tests/web/
├── __init__.py
├── conftest.py                     # TestClient fixture + monkeypatch _DEFAULT_DATA_DIR
├── test_app.py                     # 4 测试
├── test_schemas.py                 # 6 测试
├── test_dashboard.py               # 3 测试
├── test_activities.py              # 6 测试
├── test_import_page.py             # 9 测试
├── test_settings.py                # 7 测试
└── test_web_integration.py         # 7 测试
```

### 3.3 修改的已有文件
- `run-flow-skills-mcp/pyproject.toml`：新增 `[project.scripts]` 段，注册 `run-flow-skills-mcp` 和 `run-flow-skills-web` 两个入口点
- `run-flow-skills-mcp/.gitignore`：追加排除 `htmx.min.js / alpine.min.js / echarts.min.js`（由脚本下载）

## 4. 路由清单

| 路由 | 方法 | 用途 | 复用 Service |
|------|------|------|-------------|
| `/` | GET | 单页外壳 base.html | - |
| `/static/{file}` | GET | 静态资源（CSS/JS） | - |
| `/partials/dashboard` | GET | 仪表盘 HTML 片段 | analysis_service + review_service |
| `/api/dashboard/summary` | GET | 仪表盘 JSON（KPI + 趋势） | analysis_service + review_service |
| `/partials/activities` | GET | 活动列表 HTML 片段 | parquet_store |
| `/partials/activities/{id}` | GET | 活动详情 HTML 片段 | parquet_store |
| `/api/sessions` | GET | 活动列表 JSON | parquet_store |
| `/partials/import` | GET | 导入页 HTML 片段 | - |
| `/api/import/upload` | POST | 批量上传导入（multipart） | import_service |
| `/api/import/manual` | POST | 手动录入（JSON） | import_service |
| `/partials/settings` | GET | 设置页 HTML 片段 | - |
| `/api/config` | GET | 读取配置 JSON | json_store.data_dir |
| `/api/config` | PUT | 部分更新配置 | json_store.data_dir |

## 5. 安全约束遵守

- 绑定 `127.0.0.1:8002`（constants.WEB_HOST/WEB_PORT），仅本机访问
- 文件类型白名单：`.fit .gpx .csv .tcx .xml`（constants.SUPPORTED_IMPORT_EXT）
- 单文件大小限制：100MB（constants.MAX_UPLOAD_FILE_SIZE_MB）
- 批量上传上限：100 文件/次（constants.MAX_BATCH_UPLOAD_FILES）
- 所有数据不出 `data/` 目录（config.json + sessions/metrics parquet）
- Tool 不调 LLM，Web 也不调 LLM

## 6. 编码规范遵守

- 无 `# type: ignore`
- 无 `Dict[str, Any]`（用 `dict` 或具体类型）
- 无裸 `Exception`
- 函数/变量 snake_case，类名 PascalCase
- 中文注释解释意图

## 7. Git 提交记录

```
839c692 feat(web): register web entry point and add end-to-end integration tests
51d4db3 feat(web): add settings page for user config read/write with defaults
a6d19ae feat(web): add import page with drag-drop upload, whitelist, and manual form
80a02a0 feat(web): add activities list route and templates with filter and pagination
bd99c91 feat(web): add dashboard route and template with KPI cards and load trend chart
4c748d6 chore(web): add static asset download scripts for htmx/alpine/echarts
921bb59 feat(web): add request schemas for manual import and config update
d6a8ae4 feat(web): add FastAPI app factory, base template, and Services container extension
```

## 8. 冒烟测试说明

静态资源（htmx/alpine/echarts JS）未下载到 `static/` 目录，因为：
- 体积较大（合计约 1MB），按 `.gitignore` 排除
- TestClient 测试不依赖 JS 执行，全部通过
- 用户启动 Web 服务前需手动运行：
  ```powershell
  pwsh run-flow-skills-mcp/src/run_flow_skills_mcp/web/static/download_static.ps1
  ```
- 未下载时 `base.html` 的 `<script>` 标签会 404，但 HTML 仍可渲染

启动 Web 服务：
```bash
cd run-flow-skills-mcp
uv run run-flow-skills-web
# 浏览器访问 http://127.0.0.1:8002
```

## 9. 偏离 Plan 的修正汇总

| 位置 | Plan 原文 | 实际实现 | 原因 |
|------|----------|----------|------|
| `tests/web/conftest.py` | 无 monkeypatch | `monkeypatch.setattr("_DEFAULT_DATA_DIR", tmp_path)` | 让路由无参 `get_services()` 返回 tmp_path 对应实例 |
| `routes/settings.py` | `_CONFIG_PATH = Path(DATA_DIR) / "config.json"` 模块级常量 | `_config_path()` 函数动态获取 `get_services().json_store.data_dir` | 避免模块级常量绑定默认 DATA_DIR，测试中不跟随 tmp_data_dir |
| `routes/import_page.py` | `force: bool = False` | `force: bool = Form(False)` | FastAPI 默认把非 UploadFile 参数当 query 参数，需 `Form()` 显式声明为 form 参数 |
| `templates/partials/import.html` | `导入 {{ pendingFiles.length }} 个文件` | `导入 <span x-text="pendingFiles.length"></span> 个文件` | 避免 Jinja2 把 Alpine.js 的 `{{ }}` 当变量解析 |
| `routes/activities.py` | session dict 只有 `distance_km` | 同时返回 `distance_m` 和 `distance_km` | 测试断言 `distance_m`，模板用 `distance_km`，两者都需要 |
| `tests/web/test_web_integration.py::test_web_entry_point_registered` | `subprocess.run(["uv", "run", "run-flow-skills-web", "--help"])` | `importlib.metadata.entry_points(group="console_scripts")` | uvicorn 入口不接受 `--help` 且会阻塞，改用元数据检查 |

所有偏离均为合理修正，未改变 Plan 的设计意图和接口契约。
