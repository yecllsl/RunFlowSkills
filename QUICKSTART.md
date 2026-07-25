# 5 分钟快速上手

## 前置要求

- Python 3.12+
- uv 包管理器（[安装指南](https://docs.astral.sh/uv/getting-started/install/)）
- Trae IDE CN / WorkBuddy / OpenCode（任选其一）

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

## Step 2: 在 Trae 中打开项目（1 分钟）

1. 打开 Trae IDE CN
2. 文件 → 打开文件夹 → 选择 `RunFlowSkills`
3. 设置 → MCP → 打开「启用项目级 MCP」开关
4. 重启 Trae

> Trae 会自动加载 `.trae/mcp.json`，注册 `run-flow-skills-mcp` server。

## Step 3: 导入第一条训练数据（1 分钟）

在 Trae 对话框中输入：

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
pwsh src/run_flow_skills_mcp/web/static/download_static.ps1
# 启动 Web 服务
uv run run-flow-skills-web
```

浏览器访问 http://127.0.0.1:8002

## 下一步

- 试用所有 6 个命令：`/import` `/analyze` `/plan` `/review` `/coach` `/stats`
- 在 Web 设置页配置个人参数（最大心率/乳酸阈值心率等）
- 详见 [DEPLOY.md](DEPLOY.md) 和 [设计规格说明书](docs/superpowers/specs/2026-07-25-runflow-skills-design.md)
