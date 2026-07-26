# RunFlowSkills — 深度跑步分析 Skills 套件

> **文件夹即产品**：下载解压后在 Trae IDE CN / Claude Code / Cursor / Windsurf / Continue / OpenCode / WorkBuddy 中打开即可使用，无需 Web 服务或桌面 App。
> 跨平台规范见 [AGENTS.md](AGENTS.md)，平台兼容性矩阵见 [PLATFORMS.md](PLATFORMS.md)。

## 简介

RunFlowSkills 是一套基于 MCP（Model Context Protocol）的跑步数据分析 Skills，提供 6 个核心能力：

| 命令 | 功能 | 示例 |
|------|------|------|
| `/import` | 导入训练数据（FIT/GPX/CSV/TCX/XML + 手动录入） | "导入今天的跑步文件" |
| `/analyze` | 分析训练负荷/VDOT/HRV/疲劳 | "分析最近 30 天的训练" |
| `/plan` | 生成周期化训练计划 | "帮我制定全马破 4 的 12 周计划" |
| `/review` | 复盘周/月/赛季训练 | "复盘本周训练" |
| `/coach` | AI 教练建议（差异化核心） | "今天能跑间歇吗？" |
| `/stats` | 统计分布与数据导出 | "按周统计跑量" |

## 核心特性

- 🔒 **全本地**：数据不出 `data/` 目录，无云端上传
- 🧠 **AI 决策溯源**：每条建议附溯源链 + 置信度
- 📊 **Web 可视化**：4 页仪表盘（127.0.0.1:8002）
- 🏃 **跨平台去重**：SHA256 + 时间/距离匹配，多设备导入不重复
- 📐 **专业计算**：VDOT（Powers 方法）/ TSS / CTL / ATL / HRV

## 快速开始

详见 [QUICKSTART.md](QUICKSTART.md)，5 分钟上手。

### 1. 安装

```powershell
# Windows
.\install.ps1

# Linux/macOS
bash install.sh
```

### 2. 在支持 MCP 的 Agent 平台中打开

- **Trae IDE CN**：打开此文件夹 → 设置 → MCP → 启用「项目级 MCP」→ 重启 Trae
- **Claude Code**：`claude /open <项目路径>`（自动读取 `.mcp.json`，镜像已入库）
- **Cursor / Windsurf / Continue**：镜像已入库，直接打开即可
- **OpenCode**：在项目目录运行 `opencode`（自动读取 `opencode.json` 与 `AGENTS.md`）
- **WorkBuddy**：打开此文件夹（自动读取 `.workbuddy/mcp.json` 与 `AGENTS.md`）

> 各平台镜像已通过 `scripts\sync-platforms.ps1` 生成并入库，开箱即用。
> 如需重新同步（修改 AGENTS.md 或 SKILL.md 后）：
> ```powershell
> .\scripts\sync-platforms.ps1  # 全平台同步
> ```

### 3. 开始使用

```
/import  导入训练文件
/analyze 分析训练数据
/coach   今日训练建议
```

## 技术架构

```
用户 → Agent 平台（Trae/Claude Code/Cursor/Windsurf/Continue/OpenCode/WorkBuddy）
         ↓
      Skills 编排（6 个 Skill）
         ↓
      MCP Tools（14 个）→ Services → Storage（Parquet/JSON）
         ↓
      AGENTS.md 规则约束
         ↓
      Web 可视化（FastAPI + HTMX，127.0.0.1:8002）
```

详见 [设计规格说明书](docs/superpowers/specs/2026-07-25-runflow-skills-design.md)。

## 项目结构

```
RunFlowSkills/
├── AGENTS.md                # 跨平台 Agent 统一规范（规则单一事实源）
├── PLATFORMS.md             # 平台兼容性矩阵
├── CLAUDE.md                # Claude Code 规则镜像
├── .mcp.json                # Claude Code MCP 配置
├── opencode.json            # OpenCode MCP 配置
├── .windsurfrules           # Windsurf 规则镜像
├── .trae/                   # Trae IDE 平台目录（默认源）
│   ├── skills/              # 6 个 Skill 工作流（单一事实源）
│   └── mcp.json             # Trae MCP 配置
├── .claude/skills/          # Claude Code Skills 镜像
├── .cursor/                 # Cursor 镜像
│   ├── rules/               # .mdc 规则文件
│   └── mcp.json             # Cursor MCP 配置
├── .opencode/skills/        # OpenCode Skills 镜像
├── .workbuddy/mcp.json      # WorkBuddy MCP 配置
├── .continue/config.json    # Continue 配置镜像
├── run-flow-skills-mcp/     # MCP Server + Web（Python）
│   ├── src/                 # 源代码（tools/services/models/calculators/web）
│   └── tests/               # 测试套件（348 用例）
├── scripts/
│   ├── sync-platforms.ps1         # 跨平台镜像同步脚本
│   ├── generate-mcp-config.ps1    # 按平台生成 MCP 配置
│   ├── build-release.ps1          # 构建发布包（Windows）
│   └── build-release.sh           # 构建发布包（Linux/macOS）
├── data/                    # 运行时数据（.gitignore）
├── install.ps1 / .sh        # 安装脚本
├── QUICKSTART.md            # 5 分钟上手
└── DEPLOY.md                # 详细部署
```

### 跨平台兼容

本项目支持 7 个桌面 Agent 平台，镜像已入库，开箱即用。详见 [PLATFORMS.md](PLATFORMS.md)。

| 平台 | 规则入口 | Skills | MCP |
|------|----------|--------|-----|
| Trae IDE CN | `.trae/` | ✅ | ✅ |
| Claude Code | `CLAUDE.md` + `.mcp.json` | ✅ | ✅ |
| Cursor | `.cursor/rules/` | ✅（转 .mdc） | ✅ |
| Windsurf | `.windsurfrules` | ✅（合并） | ✅ |
| Continue | `.continue/config.json` | ✅（索引） | ✅ |
| OpenCode | `opencode.json` | ✅ | ✅ |
| WorkBuddy | `.workbuddy/mcp.json` | ❌ Early | ✅ |

重新同步镜像（修改 AGENTS.md 或 SKILL.md 后）：
```powershell
.\scripts\sync-platforms.ps1                       # 全平台同步
.\scripts\sync-platforms.ps1 -Platforms claude-code,cursor -DryRun  # 预演
```

## 开发

```bash
cd run-flow-skills-mcp
uv sync --extra dev
uv run pytest tests/
uv run ruff check src/ tests/
```

## 许可证

MIT
