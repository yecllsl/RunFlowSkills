# 部署指南

## 系统要求

| 组件 | 要求 | 说明 |
|------|------|------|
| 操作系统 | Windows 10+ / macOS 12+ / Ubuntu 20+ | |
| Python | 3.12+ | `python --version` 验证 |
| uv | latest | 包管理器 |
| Agent 平台 | 任选其一 | 见下表 |

| 平台 | 规则入口 | Skills | MCP 配置 | 状态 |
|------|----------|--------|----------|------|
| Trae IDE CN | `.trae/` | ✅ | `.trae/mcp.json` | ✅ 默认 |
| Claude Code | `CLAUDE.md` | ✅ | `.mcp.json` | 🟡 镜像已入库 |
| Cursor | `.cursor/rules/` | ✅（.mdc） | `.cursor/mcp.json` | 🟡 镜像已入库 |
| Windsurf | `.windsurfrules` | ✅（合并） | `mcp_config.json` | 🟡 镜像已入库 |
| Continue | `.continue/config.json` | ✅（索引） | 同配置 | 🟡 镜像已入库 |
| OpenCode | `AGENTS.md`（自动） | ✅ | `opencode.json` | 🟡 镜像已入库 |
| WorkBuddy | `AGENTS.md`（自动） | ❌ Early | `.workbuddy/mcp.json` | 🟡 镜像已入库 |

> 所有平台镜像已入库，开箱即用。详见 [PLATFORMS.md](PLATFORMS.md)。

## 安装方式

### 方式 1：安装脚本（推荐）

```powershell
# Windows
.\install.ps1

# Linux/macOS
bash install.sh
```

脚本执行步骤：
1. 检查 Python 3.12+
2. 检查/提示安装 uv
3. `cd run-flow-skills-mcp && uv sync`
4. 验证 MCP Server 入口可用
5. 提示在目标平台中打开项目

### 方式 2：手动安装

```bash
# 1. 确保 uv 已安装
pip install uv

# 2. 安装依赖
cd run-flow-skills-mcp
uv sync

# 3. 验证
uv run run-flow-skills-mcp --help
```

## 配置 MCP（各平台详细说明）

### Trae IDE CN

1. 打开 Trae → 文件 → 打开文件夹 → 选择 `RunFlowSkills`
2. 设置 → MCP → 打开「启用项目级 MCP」
3. 重启 Trae

Trae 自动加载 `.trae/mcp.json`：
```json
{
  "mcpServers": {
    "run-flow-skills-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "${workspaceFolder}/run-flow-skills-mcp", "run-flow-skills-mcp"]
    }
  }
}
```

> 如果 Trae 版本不支持 `${workspaceFolder}`，运行 `.\install.ps1 -FixPath` 替换为绝对路径。

### Claude Code

1. 安装 Claude Code CLI：`npm install -g @anthropic-ai/claude-code`
2. 在项目目录运行：`claude /open .`

Claude Code 自动读取根目录 `.mcp.json`：
```json
{
  "mcpServers": {
    "run-flow-skills-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "D:/yecll/Documents/LocalCode/RunFlowSkills/run-flow-skills-mcp", "run-flow-skills-mcp"]
    }
  }
}
```

> `.mcp.json` 使用绝对路径（Claude Code 不支持 `${workspaceFolder}`）。

### Cursor

1. 打开 Cursor → 文件 → 打开文件夹 → 选择 `RunFlowSkills`
2. 设置 → MCP → 确认项目级 MCP 已启用

Cursor 自动读取 `.cursor/mcp.json` + `.cursor/rules/*.mdc`：
- `runflow-agents.mdc`：包含 AGENTS.md 全文（Cursor 规则格式）
- `runflow-<skill>.mdc`：6 个 Skill 定义（Cursor 规则格式）
- `mcp.json`：MCP Server 配置（绝对路径）

### Windsurf

1. 打开 Windsurf → 文件 → 打开文件夹 → 选择 `RunFlowSkills`

Windsurf 自动读取：
- `.windsurfrules`：包含 AGENTS.md 全文（Windsurf 单文件规则）
- `mcp_config.json`：MCP Server 配置（项目根目录，绝对路径）

### Continue

1. 安装 Continue 插件（VSCode 或 JetBrains）
2. 打开项目文件夹

Continue 自动读取 `.continue/config.json`，其中包含：
- `rules`：引用 `AGENTS.md`
- `skills`：6 个 Skill 索引
- `mcp.servers`：MCP Server 配置

### OpenCode

1. 安装 OpenCode CLI（[opencode.ai](https://opencode.ai)）
2. 在项目目录运行：`opencode`

OpenCode 自动读取：
- `opencode.json`：MCP Server 配置（OpenCode 专用结构 `{type: "local", command: [...], enabled: true}`）
- `.opencode/skills/`：6 个 Skill 定义
- `AGENTS.md`：规则（OpenCode 自动读取）

> OpenCode 不支持 `${workspaceFolder}` 变量，`opencode.json` 使用绝对路径。

### WorkBuddy

1. 打开 WorkBuddy → 文件 → 打开文件夹 → 选择 `RunFlowSkills`

WorkBuddy 自动读取：
- `.workbuddy/mcp.json`：MCP Server 配置
- `AGENTS.md`：规则（WorkBuddy 自动读取）

> WorkBuddy 处于 Early Support 阶段，**仅支持 MCP，不支持原生 Skills**。规则通过 `AGENTS.md` 传递。

## 重新同步镜像

修改 `AGENTS.md` 或 `.trae/skills/` 后，需重新同步各平台镜像：

```powershell
# 全平台同步
.\scripts\sync-platforms.ps1

# 仅同步指定平台
.\scripts\sync-platforms.ps1 -Platforms claude-code,cursor

# 预演（不实际写文件）
.\scripts\sync-platforms.ps1 -DryRun
```

或按需生成单个平台 MCP 配置：

```powershell
.\scripts\generate-mcp-config.ps1 -Platform opencode
.\scripts\generate-mcp-config.ps1 -Platform workbuddy -PythonRunner python
```

## Web 可视化

### 首次启动

```bash
cd run-flow-skills-mcp

# 下载静态资源（HTMX/Alpine/ECharts，约 1MB）
pwsh src/run_flow_skills_mcp/web/static/download_static.ps1   # Windows
bash src/run_flow_skills_mcp/web/static/download_static.sh    # Linux/macOS

# 启动 Web 服务
uv run run-flow-skills-web
```

### 访问

浏览器打开 http://127.0.0.1:8002

| 页面 | 路径 | 功能 |
|------|------|------|
| 仪表盘 | `/` | CTL/ATL/TSB/VDOT + 负荷趋势图 |
| 活动列表 | `/activities` | 训练记录表格 + 筛选 + 详情 |
| 数据导入 | `/import` | 拖拽批量上传 + 手动录入 |
| 设置 | `/settings` | 个人参数配置（最大心率等） |

> Web 仅绑定 127.0.0.1，无外部访问。端口 8002（DeepReview 用 8001，避免冲突）。

## 数据存储

所有数据存储在 `data/` 目录：

| 子目录 | 格式 | 内容 |
|--------|------|------|
| `sessions/` | Parquet | 跑步记录（按年分片） |
| `metrics/` | Parquet | 训练指标（按年分片） |
| `load/` | JSON | 训练负荷（日聚合） |
| `body_signals/` | JSON | 身体信号（按月） |
| `decisions/` | JSON | AI 决策日志（按月） |
| `plans/` | JSON | 训练计划 |
| `config.json` | JSON | 用户配置 |

> `data/` 已在 `.gitignore` 中，不会上传到 Git。

## 升级

```bash
# 拉取最新代码
git pull

# 更新依赖
cd run-flow-skills-mcp
uv sync

# 重新同步平台镜像（如有变更）
cd ..
.\scripts\sync-platforms.ps1
```

## 故障排查

### MCP Server 未启动

```bash
# 手动验证
cd run-flow-skills-mcp
uv run run-flow-skills-mcp
```

### Web 无法访问

1. 确认端口 8002 未被占用：`netstat -ano | findstr 8002`
2. 确认静态资源已下载（`ls src/run_flow_skills_mcp/web/static/*.js`）
3. 查看终端错误日志

### 导入失败

- FIT 文件损坏：尝试用 Garmin Connect 重新导出
- 不支持的格式：仅支持 .fit .gpx .csv .tcx .xml
- 重复导入：加 `--force` 覆盖

### 平台无法识别项目

1. 确认对应平台的配置文件存在（见上方各平台说明）
2. 运行 `.\scripts\sync-platforms.ps1` 重新生成镜像
3. 确认 MCP 配置中的路径为绝对路径（非 `${workspaceFolder}`）

## 卸载

删除 `RunFlowSkills` 文件夹即可。所有数据（含 `data/`）均在文件夹内，无系统级残留。
