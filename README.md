# RunFlowSkills — 深度跑步分析 Skills 套件

> **文件夹即产品**：下载解压后在 Trae IDE CN / WorkBuddy / OpenCode 中打开即可使用，无需 Web 服务或桌面 App。

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

### 2. 在 Trae 中打开

用 Trae IDE CN 打开此文件夹 → 设置 → MCP → 启用「项目级 MCP」→ 重启 Trae。

### 3. 开始使用

```
/import  导入训练文件
/analyze 分析训练数据
/coach   今日训练建议
```

## 技术架构

```
用户 → Trae（宿主 AI）→ Skills 编排 → MCP Tools → Services → Storage（Parquet/JSON）
                      ↓
                   Rules 约束
                      ↓
                Web 可视化（FastAPI + HTMX）
```

详见 [设计规格说明书](docs/superpowers/specs/2026-07-25-runflow-skills-design.md)。

## 项目结构

```
RunFlowSkills/
├── .trae/skills/          # 6 个 Skill 工作流
├── .trae/rules/           # 5 个规则文件
├── .trae/mcp.json         # MCP 配置
├── run-flow-skills-mcp/   # MCP Server + Web（Python）
├── data/                  # 运行时数据（.gitignore）
├── install.ps1 / .sh      # 安装脚本
├── QUICKSTART.md          # 5 分钟上手
└── DEPLOY.md              # 详细部署
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
