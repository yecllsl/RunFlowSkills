# 5 分钟快速上手

## 前置要求

- Python 3.12+
- uv 包管理器（[安装指南](https://docs.astral.sh/uv/getting-started/install/)）
- 任一支持的 Agent 平台（见下表）

| 平台 | 获取方式 |
|------|----------|
| Trae IDE CN | [trae.ai](https://www.trae.ai) |
| Claude Code | `npm install -g @anthropic-ai/claude-code` |
| Cursor | [cursor.com](https://cursor.com) |
| Windsurf | [codeium.com/windsurf](https://codeium.com/windsurf) |
| Continue | VSCode/JetBrains 插件 |
| OpenCode | [opencode.ai](https://opencode.ai) |
| WorkBuddy | 字节跳动内网 |

## Step 1: 安装依赖（1 分钟）

### Windows

```powershell
.\install.ps1
```

### Linux/macOS

```bash
bash install.sh
```

脚本会自动检查 Python、uv，并运行 `uv sync` 安装依赖。

## Step 2: 在 Agent 平台中打开项目（1 分钟）

> 所有平台的配置镜像已入库，无需额外同步即可使用。

| 平台 | 打开方式 |
|------|----------|
| **Trae IDE CN** | 文件 → 打开文件夹 → 设置 → MCP → 启用「项目级 MCP」→ 重启 |
| **Claude Code** | `claude /open <项目路径>`（自动读取 `.mcp.json`） |
| **Cursor** | 打开文件夹（自动读取 `.cursor/mcp.json` + `.cursor/rules/`） |
| **Windsurf** | 打开文件夹（自动读取 `mcp_config.json` + `.windsurfrules`） |
| **Continue** | 打开文件夹（自动读取 `.continue/config.json`） |
| **OpenCode** | 在项目目录运行 `opencode`（自动读取 `opencode.json`） |
| **WorkBuddy** | 打开文件夹（自动读取 `.workbuddy/mcp.json`） |

> 如需重新同步镜像（修改 AGENTS.md 或 SKILL.md 后）：`.\scripts\sync-platforms.ps1`

## Step 3: 导入第一条训练数据（1 分钟）

在 Agent 对话框中输入：

```
/import D:\runs\2026-07-20-morning-run.fit
```

或手动录入：

```
帮我手动录入一条跑步记录：日期 2026-07-20，距离 10km，时长 50 分钟，平均心率 150
```

AI 会调用 `import_file` 或 `import_manual` tool，解析文件、计算 VDOT/TSS、存储到 `data/`。

## Step 4: 分析训练（1 分钟）

```
/analyze
```

AI 会并行调用 `calc_metrics` + `get_trends` + `analyze_fatigue`，生成数据驱动的分析报告。

## Step 5: 获取教练建议（1 分钟）

```
/coach 今天能跑间歇吗？
```

AI 会读取身体信号 + 训练负荷 + 当前计划，综合判断后给出具体可执行的建议（含配速区间 + 替代方案 + 置信度）。

## 可选：启动 Web 可视化

```bash
cd run-flow-skills-mcp
# 首次需下载静态资源
pwsh src/run_flow_skills_mcp/web/static/download_static.ps1   # Windows
bash src/run_flow_skills_mcp/web/static/download_static.sh    # Linux/macOS
# 启动 Web 服务
uv run run-flow-skills-web
```

浏览器访问 http://127.0.0.1:8002

## 下一步

- 试用所有 6 个命令：`/import` `/analyze` `/plan` `/review` `/coach` `/stats`
- 在 Web 设置页配置个人参数（最大心率/乳酸阈值心率等）
- 详见 [DEPLOY.md](DEPLOY.md)、[PLATFORMS.md](PLATFORMS.md) 和 [设计规格说明书](docs/superpowers/specs/2026-07-25-runflow-skills-design.md)
