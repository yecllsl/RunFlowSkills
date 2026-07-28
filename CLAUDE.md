---
project: RunFlowSkills
version: 1.2.0
last_updated: 2026-07-28
applies_to:
  - trae
  - claude-code
  - cursor
  - windsurf
  - continue
  - opencode
  - workbuddy
enforcement: hard
---

# AGENTS.md — RunFlowSkills 跨平台 Agent 统一规范

> 本文件是项目对所有 AI Coding Agent 的统一入口规范。
> Trae / Claude Code / Cursor / Windsurf / Continue / Aider 等平台在加载项目时应优先读取本文件。

---

## 1. 项目能力声明（Capabilities）

RunFlowSkills 是一套基于 MCP（Model Context Protocol）的深度跑步数据分析 Skills 套件。

| 命令 | Skill | 功能 | 示例 |
|------|-------|------|------|
| `/import` | runflow-import | 导入训练数据（FIT/GPX/CSV/TCX/XML + 手动录入） | "导入今天的跑步文件" |
| `/analyze` | runflow-analyze | 分析训练负荷/VDOT/HRV/疲劳 | "分析最近 30 天的训练" |
| `/plan` | runflow-plan | 生成周期化训练计划 | "帮我制定全马破 4 的 12 周计划" |
| `/review` | runflow-review | 复盘周/月/赛季训练 | "复盘本周训练" |
| `/coach` | runflow-coach | AI 教练建议（差异化核心） | "今天能跑间歇吗？" |
| `/stats` | runflow-stats | 统计分布与数据导出 | "按周统计跑量" |

**技术栈**：
- MCP Server：14 个 Tool（详见 `.trae/mcp.json` 或平台对应配置）
- Web 可视化：FastAPI + HTMX，绑定 127.0.0.1:8002
- 计算：VDOT（Powers 方法）/ TSS / CTL / ATL / TSB / HRV
- 存储：Parquet（Sessions）+ JSON（计划/配置/决策日志）

---

## 2. 交互协议（Interaction Protocol）

1. **命令格式**：`/import` `/analyze` `/plan` `/review` `/coach` `/stats`
2. **自然语言关键词**：导入/分析/计划/复盘/教练/统计
3. **每次操作结果必须给出明确反馈**（成功/跳过/失败 + 原因）
4. **错误发生时提供降级方案而非直接报错**：
   - FIT 解析失败 → 提示手动录入
   - 数据不足 → 降级为趋势外推并标注
   - AI 解读异常 → 提示重试 + 提供原始数据
5. **以下场景必须用户确认**：
   - 训练计划生成后保存前
   - 数据导入去重检测到冲突时
   - AI 教练建议给出后是否采纳
   - 数据导出前
6. **命令未识别时提示可用命令清单**
7. **批量操作（如导入 100 文件）展示进度**

---

## 3. 计算规则（Calculation Rules）

> 适用 Skill：runflow-analyze / runflow-plan / runflow-coach

1. VDOT 计算必须使用 Powers 方法，距离 <1500m 时标记为 "estimated" 并降低置信度
2. TSS = 时长(秒) × IF² × 100，IF 基于乳酸阈值心率或配速
3. CTL = 42 天 EWMA，ATL = 7 天 EWMA，TSB = CTL - ATL
4. 配速格式统一 M'SS"/km（如 5'40"/km），时长统一 HH:MM:SS
5. 心率区间基于个人最大心率或乳酸阈值心率，不可使用通用公式默认值（如 220-年龄）。默认值见 `constants.py`（DEFAULT_MAX_HR / DEFAULT_LTHR），用户可经 Web `/settings` 页覆盖 `data/config.json`；计算器读取顺序：config.json → constants.py 默认值
6. 配速区间基于个人 VDOT：E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110%
7. EWMA 计算：当日值 × α + 昨日 EWMA × (1-α)，α = 2/(N+1)，N 为窗口天数
8. HRV 指标：RMSSD（主）、SDNN、pNN50，基线 = 7 天滚动均值

---

## 4. 分析规则（Analysis Rules）

> 适用 Skill：runflow-analyze / runflow-review

1. AI 分析必须具体到数据层面，禁止笼统结论（"训练不错"/"负荷合理" 不合规）
2. 趋势判断必须附数据依据（"CTL 65 较上周 +3" 而非 "负荷上升"）
3. 伤病风险评估必须列出主要风险因子，不可只给 "有风险"
4. 预测结果必须标注误差范围，禁止伪精确（"全马 3:59:30" 不合规，必须 "3:55:00–4:05:00"）
5. 数据不足时必须明确降级标注（"基于 7 天数据，置信度低"），不可静默外推
6. 同比/环比对比必须明确时间窗口（"vs 上周" / "vs 去年同期"）
7. 心率漂移分析必须基于相同配速段，不可跨配速段混合计算

---

## 5. 教练规则（Coaching Rules）

> 适用 Skill：runflow-coach

1. AI 建议必须具体可执行：类型 + 强度 + 时长 + 配速区间（"E 区间 30 分钟，配速 5'40"-6'00"/km"）
2. 建议必须附决策溯源链：输入数据 + 判断规则 + 置信度 + 替代方案
3. 就绪状态评估必须综合 HRV + TSB + RPE，单一指标不可单独决策
4. 建议不得与当前训练计划冲突（计划是休息日不可建议高强度；冲突时给"调整建议"并说明）
5. confidence < 0.6 时必须提示 "仅供参考，建议结合主观感受"
6. 建议必须考虑 24h 内的高强度训练历史（昨跑 T5 间歇 → 今日降级）
7. 用户反馈（采纳/拒绝/修改）必须记录到 DecisionLog
8. 替代方案至少 1 个（如"今日推荐 E 区间，替代方案：完全休息或 M 区间 20 分钟"）

---

## 6. 数据安全规则（Data Safety Rules）

> 适用 Skill：runflow-import / runflow-stats / runflow-coach
> **强制约束，不可绕过**

1. 所有数据仅存储在本地 `data/` 目录，禁止上传任何外部服务
2. 导出数据前需用户确认
3. 不记录用户姓名、身份证号、手机号等个人身份信息（PII）；年龄/体重/性别/身高/心率等训练参数不属 PII，存于 `data/config.json` 用于计算
4. FIT/GPX/CSV/TCX/XML 文件解析在本地完成，不调用外部 API
5. Web 可视化仅绑定 127.0.0.1，JS 库本地化（HTMX/Alpine/ECharts 无 CDN）
6. 原始文件 SHA256 哈希存储用于去重，原始文件路径可选保留
7. 导出含 AI 决策日志时二次确认（含敏感训练分析）
8. 不记录 IP 地址、设备指纹等环境信息

---

## 7. Agent 接口约定（Agent Interface Convention）

> 本项目不使用平台专有 subagent / sunagent 配置目录（如 `.trae/agents/`、`.claude/agents/`）。
> 所有能力通过 **MCP Tool + Skill** 暴露，确保跨平台通用。

### 7.1 能力暴露方式

| 层级 | 位置 | 用途 |
|------|------|------|
| 工具层 | `.trae/mcp.json` → MCP Server → 14 Tool | 结构化数据操作（CRUD + 计算） |
| 工作流层 | `.trae/skills/<name>/SKILL.md` | 多步编排 + LLM 提示词模板 |
| 规则层 | 本文件（AGENTS.md） | 跨平台统一约束 |

### 7.2 Skill 调用约定

- 每个 Skill 在 frontmatter 中显式声明 `allowed-tools`、`inputs`、`outputs`、`error_handling`、`compatibility`
- 宿主 AI 加载 Skill 时必须校验 `compatibility.mcp_server` 版本
- Skill 不直接调用其他 Skill，所有跨 Skill 协作通过共享 MCP Tool 完成

### 7.3 不引入平台专有 agent 定义

- ❌ 不创建 `.trae/agents/`、`.claude/agents/`、`.cursor/agents/` 等
- ❌ 不使用平台专有的 subagent 调度配置
- ✅ 仅通过 MCP 标准协议暴露能力，确保任何支持 MCP 的宿主均可调用

---

## 8. 跨平台兼容性矩阵（Platform Compatibility Matrix）

### 8.1 平台入口映射

| 平台 | 规则入口 | Skill 路径 | MCP 配置 | 支持状态 |
|------|----------|------------|----------|----------|
| Trae IDE CN | `AGENTS.md` + `.trae/` | `.trae/skills/` | `.trae/mcp.json` | ✅ 默认支持 |
| Claude Code | `AGENTS.md` + `CLAUDE.md` | `.claude/skills/` | `.mcp.json` | 🟡 同步脚本支持 |
| Cursor | `AGENTS.md` + `.cursor/rules/` | `.cursor/rules/`（转 rules） | `.cursor/mcp.json` | 🟡 同步脚本支持 |
| Windsurf | `AGENTS.md` + `.windsurf/rules/` | `.windsurf/rules/`（现代格式） | `.windsurf/mcp.json` | 🟡 同步脚本支持 |
| Continue | `AGENTS.md` + `.continue/config.yaml` | `.continue/config.yaml`（索引） | `.continue/mcpServers/` | 🟡 同步脚本支持 |
| OpenCode | `AGENTS.md`（自动读取） | `.opencode/skills/` | `opencode.json` | 🟡 同步脚本支持 |
| WorkBuddy | `AGENTS.md`（自动读取） | `.workbuddy/skills/` | `.workbuddy/mcp.json` | 🟡 同步脚本支持 |

### 8.2 同步与生成

- 同步脚本：`scripts/sync-platforms.ps1`（将根目录 `AGENTS.md` + `.trae/skills/` 镜像到各平台目录）
- 配置生成：`scripts/generate-mcp-config.ps1`（按平台生成对应 MCP 配置）
- 单一事实源：根目录 `AGENTS.md` + `.trae/skills/`（当前）
- 支持平台：Trae / Claude Code / Cursor / Windsurf / Continue / OpenCode / WorkBuddy
- 镜像目录入库：`.claude/`、`.cursor/`、`.windsurf/`、`.continue/`（含 `config.yaml` + `mcpServers/`）、`.opencode/`、`.workbuddy/`（含 `skills/`）、`opencode.json`、`CLAUDE.md`、`.mcp.json` 均提交到 Git，便于开箱即用

### 8.3 平台专有依赖清单

| 依赖 | 类型 | 影响 | 抽象方案 |
|------|------|------|----------|
| `.trae/` 目录命名 | Trae 专属 | Skill/Rules 路径 | 保留为默认源；其他平台由同步脚本生成镜像 |
| `${workspaceFolder}` 变量 | VSCode/Trae 风格 | mcp.json 启动命令 | 配置生成器按平台替换为绝对路径或平台变量 |
| `uv run --directory` | uv 专属 | MCP 启动 | 提供 `pip install` + `python -m` 备选 |
| Python 3.12+ | 版本约束 | 用户环境 | 评估降至 3.10+（pydantic v2 兼容） |
| OpenCode 不支持 `${workspaceFolder}` | OpenCode 专属 | opencode.json 启动命令 | 同步脚本强制写入绝对路径 |
| OpenCode MCP 结构 `{type,command[],enabled}` | OpenCode 专属 | opencode.json 字段格式 | 同步脚本生成 OpenCode 专用结构 |
| WorkBuddy Skills 目录命名 | WorkBuddy 专属 | Skill 镜像路径 | 使用 `.workbuddy/skills/`（与 `.codebuddy/skills/` 并行） |
| Windsurf 现代规则格式 | Windsurf Wave 8+ | `.windsurf/rules/` 目录 | 单文件 `.windsurfrules` 作为兼容 fallback |
| Continue config.yaml 格式 | Continue 现代标准 | `config.yaml` + `.continue/mcpServers/` | `config.json` 保留为兼容 fallback |

---

## 9. Skill 引用规则（Skill Rules Reference）

> 6 个 Skill 的"约束规则"章节应统一引用本文件章节，而非分散的 rules 文件。

| Skill | 引用章节 |
|-------|---------|
| runflow-import | §2 交互协议 / §6 数据安全 |
| runflow-analyze | §3 计算规则 / §4 分析规则 |
| runflow-plan | §2 交互协议 / §3 计算规则 |
| runflow-review | §4 分析规则 / §6 数据安全 / §2 交互协议 |
| runflow-coach | §5 教练规则 / §3 计算规则 / §2 交互协议 |
| runflow-stats | §6 数据安全 / §2 交互协议 |

---

## 10. 变更记录（Changelog）

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-07-26 | 初始版本：合并 5 个 rules 文件，新增跨平台规范与平台矩阵 |
| 1.1.0 | 2026-07-26 | 移除 GitHub Copilot / Aider 支持；新增 OpenCode / WorkBuddy 平台；镜像目录入库策略 |
| 1.2.0 | 2026-07-28 | WorkBuddy 升级为原生 Skill 支持：`.workbuddy/skills/` 目录同步；更新平台依赖清单 |
