# 部署指南

## 系统要求

| 组件 | 要求 | 说明 |
|------|------|------|
| 操作系统 | Windows 10+ / macOS 12+ / Ubuntu 20+ | |
| Python | 3.12+ | `python --version` 验证 |
| uv | latest | 包管理器 |
| Trae IDE CN | latest | 宿主平台（或 WorkBuddy / OpenCode） |

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
5. 提示在 Trae 中打开项目

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

## 配置 MCP

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

### WorkBuddy / OpenCode

将 `.trae/mcp.json` 内容复制到对应平台的 MCP 配置中，手动替换 `${workspaceFolder}` 为项目绝对路径。

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

## 卸载

删除 `RunFlowSkills` 文件夹即可。所有数据（含 `data/`）均在文件夹内，无系统级残留。
