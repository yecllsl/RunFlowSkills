# RunFlowSkills MVP v0.1.0 Plan 4: Skills + Rules + MCP 配置 + 文档

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 6 个 Skills（`.trae/skills/runflow-*/SKILL.md`）、5 个 Rules（`.trae/rules/*.md`）、MCP 配置（`.trae/mcp.json`）和用户文档（README/QUICKSTART/DEPLOY/LICENSE），完成"文件夹即产品"的编排层与约束层。

**Architecture:** Skills 编排层是纯 Markdown，每个 SKILL.md 含 frontmatter（`name + description`）+ Workflow + Quick Reference + Common Mistakes + 约束规则，由宿主平台（Trae/WorkBuddy）加载并编排 MCP Tools 调用。Rules 约束层是 Markdown 规则文件，被 Skills 引用约束 AI 行为。MCP 配置注册 `run-flow-skills-mcp` server，宿主通过 `uv run` 启动。文档保证用户 5 分钟上手。

**Tech Stack:** Markdown / YAML frontmatter / JSON（mcp.json）

## Global Constraints

- 6 个 Skill：`/import` `/analyze` `/plan` `/review` `/coach` `/stats`（不含 `/twin`，推迟 v0.2.0）
- 5 个 Rules：`calculation-rules.md` / `analysis-rules.md` / `coaching-rules.md` / `data-safety-rules.md` / `interaction-rules.md`
- SKILL.md frontmatter 必须含 `name` 和 `description`（Trae 加载要求）
- Skills 引用的 Tool 名称必须与 Plan 2 的 14 个 MCP Tools 一致：`import_file` / `import_manual` / `query_sessions` / `calc_metrics` / `get_trends` / `analyze_fatigue` / `generate_plan` / `query_plan` / `get_period_summary` / `read_body_signals` / `get_decision_trace` / `save_decision_log` / `get_statistics` / `export_data`
- MCP 配置使用 `${workspaceFolder}` 变量（Trae 自动替换）
- 文档中不硬编码绝对路径，使用相对路径或 `${workspaceFolder}`
- 前置依赖：Plan 1（基础设施）+ Plan 2（Services + 14 MCP Tools）已完成

---

## 文件结构

```
RunFlowSkills/
├── .trae/
│   ├── mcp.json                               # MCP server 注册
│   ├── skills/
│   │   ├── runflow-import/SKILL.md            # /import 工作流
│   │   ├── runflow-analyze/SKILL.md           # /analyze 工作流
│   │   ├── runflow-plan/SKILL.md              # /plan 工作流
│   │   ├── runflow-review/SKILL.md            # /review 工作流
│   │   ├── runflow-coach/SKILL.md             # /coach 工作流（差异化核心）
│   │   └── runflow-stats/SKILL.md             # /stats 工作流
│   └── rules/
│       ├── calculation-rules.md               # 计算规则
│       ├── analysis-rules.md                  # 分析规则
│       ├── coaching-rules.md                  # 教练规则
│       ├── data-safety-rules.md               # 数据安全规则
│       └── interaction-rules.md               # 交互规则
├── README.md                                  # 项目说明
├── QUICKSTART.md                              # 5 分钟快速上手
├── DEPLOY.md                                  # 详细部署指南
└── LICENSE                                    # MIT
```

**测试文件：**
- `run-flow-skills-mcp/tests/test_skills_rules.py`：验证 Skills 和 Rules 的一致性

---

### Task 1: .trae/mcp.json MCP 配置

**Files:**
- Create: `.trae/mcp.json`
- Test: `run-flow-skills-mcp/tests/test_mcp_config.py`

**Interfaces:**
- Consumes: Plan 2 `server.py` 的 `main()` 入口 + `pyproject.toml` 的 `run-flow-skills-mcp` 脚本
- Produces: `.trae/mcp.json`，Trae 加载后注册 `run-flow-skills-mcp` server

- [ ] **Step 1: 写失败测试 — test_mcp_config.py**

写入 `run-flow-skills-mcp/tests/test_mcp_config.py`：

```python
"""mcp.json 配置文件测试."""
import json
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_MCP_JSON = _PROJECT_ROOT / ".trae" / "mcp.json"


def test_mcp_json_exists():
    """mcp.json 文件存在."""
    assert _MCP_JSON.exists(), f"{_MCP_JSON} 不存在"


def test_mcp_json_valid_format():
    """mcp.json 是有效 JSON."""
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    assert "mcpServers" in data


def test_mcp_json_registers_run_flow_skills():
    """注册了 run-flow-skills-mcp server."""
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    assert "run-flow-skills-mcp" in data["mcpServers"]
    server = data["mcpServers"]["run-flow-skills-mcp"]
    assert server["command"] == "uv"
    assert "run" in server["args"]


def test_mcp_json_uses_workspace_folder():
    """使用 ${workspaceFolder} 变量（Trae 自动替换）."""
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    server = data["mcpServers"]["run-flow-skills-mcp"]
    args_str = " ".join(server["args"])
    assert "${workspaceFolder}" in args_str
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_mcp_config.py -v`
Expected: FAIL，`.trae/mcp.json` 不存在

- [ ] **Step 3: 创建 .trae/mcp.json**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/mcp.json`：

```json
{
  "mcpServers": {
    "run-flow-skills-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${workspaceFolder}/run-flow-skills-mcp",
        "run-flow-skills-mcp"
      ]
    }
  }
}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_mcp_config.py -v`
Expected: 4 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add .trae/mcp.json run-flow-skills-mcp/tests/test_mcp_config.py
git commit -m "feat(config): add mcp.json for run-flow-skills-mcp server registration"
```

---

### Task 2: 5 个 Rules 规则文件

**Files:**
- Create: `.trae/rules/calculation-rules.md`
- Create: `.trae/rules/analysis-rules.md`
- Create: `.trae/rules/coaching-rules.md`
- Create: `.trae/rules/data-safety-rules.md`
- Create: `.trae/rules/interaction-rules.md`
- Test: `run-flow-skills-mcp/tests/test_rules.py`

**Interfaces:**
- Consumes: 设计文档 8.1-8.5 节
- Produces: 5 个 Rules 规则文件，frontmatter 含 `name + scope`，被 Skills 引用

- [ ] **Step 1: 写失败测试 — test_rules.py**

写入 `run-flow-skills-mcp/tests/test_rules.py`：

```python
"""Rules 规则文件测试."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_RULES_DIR = _PROJECT_ROOT / ".trae" / "rules"

EXPECTED_RULES = {
    "calculation-rules.md": "calculation-rules",
    "analysis-rules.md": "analysis-rules",
    "coaching-rules.md": "coaching-rules",
    "data-safety-rules.md": "data-safety-rules",
    "interaction-rules.md": "interaction-rules",
}


def test_rules_dir_exists():
    """rules 目录存在."""
    assert _RULES_DIR.exists() and _RULES_DIR.is_dir()


@pytest.mark.parametrize("filename,expected_name", list(EXPECTED_RULES.items()))
def test_rule_file_exists_and_has_frontmatter(filename, expected_name):
    """每个 rule 文件存在且 frontmatter 含 name."""
    path = _RULES_DIR / filename
    assert path.exists(), f"{filename} 不存在"
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{filename} 缺少 frontmatter"
    assert f"name: {expected_name}" in content


def test_calculation_rules_content():
    """计算规则包含关键条目."""
    content = (_RULES_DIR / "calculation-rules.md").read_text(encoding="utf-8")
    assert "VDOT" in content
    assert "Powers" in content
    assert "TSS" in content
    assert "CTL" in content and "42" in content
    assert "ATL" in content and "7" in content
    assert "config.json" in content  # M-3 评审修正


def test_coaching_rules_content():
    """教练规则包含关键条目."""
    content = (_RULES_DIR / "coaching-rules.md").read_text(encoding="utf-8")
    assert "具体可执行" in content
    assert "溯源链" in content
    assert "HRV" in content and "TSB" in content and "RPE" in content
    assert "0.6" in content  # confidence 门禁
    assert "24h" in content or "24小时" in content


def test_data_safety_rules_content():
    """数据安全规则包含关键条目."""
    content = (_RULES_DIR / "data-safety-rules.md").read_text(encoding="utf-8")
    assert "127.0.0.1" in content
    assert "config.json" in content
    assert "SHA256" in content
    assert "PII" in content or "个人身份" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_rules.py -v`
Expected: FAIL，rules 文件不存在

- [ ] **Step 3: 创建 calculation-rules.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/rules/calculation-rules.md`：

```markdown
---
name: calculation-rules
scope: runflow-analyze, runflow-plan, runflow-coach
---

# 计算规则

1. VDOT 计算必须使用 Powers 方法，距离 <1500m 时标记为 "estimated" 并降低置信度
2. TSS = 时长(秒) × IF² × 100，IF 基于乳酸阈值心率或配速
3. CTL = 42 天 EWMA，ATL = 7 天 EWMA，TSB = CTL - ATL
4. 配速格式统一 M'SS"/km（如 5'40"/km），时长统一 HH:MM:SS
5. 心率区间基于个人最大心率或乳酸阈值心率，不可使用通用公式默认值（如 220-年龄）。默认值见 constants.py（DEFAULT_MAX_HR / DEFAULT_LTHR），用户可经 Web `/settings` 页覆盖 `data/config.json`；计算器读取顺序：config.json → constants.py 默认值
6. 配速区间基于个人 VDOT：E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110%
7. EWMA 计算：当日值 × α + 昨日 EWMA × (1-α)，α = 2/(N+1)，N 为窗口天数
8. HRV 指标：RMSSD（主）、SDNN、pNN50，基线 = 7 天滚动均值
```

- [ ] **Step 4: 创建 analysis-rules.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/rules/analysis-rules.md`：

```markdown
---
name: analysis-rules
scope: runflow-analyze, runflow-review
---

# 分析规则

1. AI 分析必须具体到数据层面，禁止笼统结论（"训练不错"/"负荷合理" 不合规）
2. 趋势判断必须附数据依据（"CTL 65 较上周 +3" 而非 "负荷上升"）
3. 伤病风险评估必须列出主要风险因子，不可只给 "有风险"
4. 预测结果必须标注误差范围，禁止伪精确（"全马 3:59:30" 不合规，必须 "3:55:00–4:05:00"）
5. 数据不足时必须明确降级标注（"基于 7 天数据，置信度低"），不可静默外推
6. 同比/环比对比必须明确时间窗口（"vs 上周" / "vs 去年同期"）
7. 心率漂移分析必须基于相同配速段，不可跨配速段混合计算
```

- [ ] **Step 5: 创建 coaching-rules.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/rules/coaching-rules.md`：

```markdown
---
name: coaching-rules
scope: runflow-coach
---

# 教练规则

1. AI 建议必须具体可执行：类型 + 强度 + 时长 + 配速区间（"E 区间 30 分钟，配速 5'40"-6'00"/km"）
2. 建议必须附决策溯源链：输入数据 + 判断规则 + 置信度 + 替代方案
3. 就绪状态评估必须综合 HRV + TSB + RPE，单一指标不可单独决策
4. 建议不得与当前训练计划冲突（计划是休息日不可建议高强度；冲突时给"调整建议"并说明）
5. confidence < 0.6 时必须提示 "仅供参考，建议结合主观感受"
6. 建议必须考虑 24h 内的高强度训练历史（昨跑 T5 间歇 → 今日降级）
7. 用户反馈（采纳/拒绝/修改）必须记录到 DecisionLog
8. 替代方案至少 1 个（如"今日推荐 E 区间，替代方案：完全休息或 M 区间 20 分钟"）
```

- [ ] **Step 6: 创建 data-safety-rules.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/rules/data-safety-rules.md`：

```markdown
---
name: data-safety-rules
scope: runflow-import, runflow-stats, runflow-coach
---

# 数据安全规则

1. 所有数据仅存储在本地 data/ 目录，禁止上传任何外部服务
2. 导出数据前需用户确认
3. 不记录用户姓名、身份证号、手机号等个人身份信息（PII）；年龄/体重/性别/身高/心率等训练参数不属 PII，存于 `data/config.json` 用于计算
4. FIT/GPX/CSV/TCX/XML 文件解析在本地完成，不调用外部 API
5. Web 可视化仅绑定 127.0.0.1，JS 库本地化（HTMX/Alpine/ECharts 无 CDN）
6. 原始文件 SHA256 哈希存储用于去重，原始文件路径可选保留
7. 导出含 AI 决策日志时二次确认（含敏感训练分析）
8. 不记录 IP 地址、设备指纹等环境信息
```

- [ ] **Step 7: 创建 interaction-rules.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/rules/interaction-rules.md`：

```markdown
---
name: interaction-rules
scope: runflow-import, runflow-analyze, runflow-plan, runflow-review, runflow-coach, runflow-stats
---

# 交互规则

1. 命令格式：/import /analyze /plan /review /coach /stats
2. 自然语言关键词：导入/分析/计划/复盘/教练/统计
3. 每次操作结果必须给出明确反馈（成功/跳过/失败 + 原因）
4. 错误发生时提供降级方案而非直接报错：
   - FIT 解析失败 → 提示手动录入
   - 数据不足 → 降级为趋势外推并标注
   - AI 解读异常 → 提示重试 + 提供原始数据
5. 以下场景必须用户确认：
   - 训练计划生成后保存前
   - 数据导入去重检测到冲突时
   - AI 教练建议给出后是否采纳
   - 数据导出前
6. 命令未识别时提示可用命令清单
7. 批量操作（如导入 100 文件）展示进度
```

- [ ] **Step 8: 运行测试验证通过**

Run: `uv run pytest tests/test_rules.py -v`
Expected: 所有测试 PASS

- [ ] **Step 9: Commit**

```bash
git add .trae/rules/ run-flow-skills-mcp/tests/test_rules.py
git commit -m "feat(rules): add 5 rule files for calculation, analysis, coaching, data safety, interaction"
```

---

### Task 3: /import + /analyze Skill

**Files:**
- Create: `.trae/skills/runflow-import/SKILL.md`
- Create: `.trae/skills/runflow-analyze/SKILL.md`
- Test: `run-flow-skills-mcp/tests/test_skills.py`

**Interfaces:**
- Consumes: 设计文档 7.1-7.2 节 + Plan 2 的 14 个 tool 名称
- Produces: 2 个 SKILL.md，frontmatter 含 `name + description`

- [ ] **Step 1: 写失败测试 — test_skills.py**

写入 `run-flow-skills-mcp/tests/test_skills.py`：

```python
"""Skills SKILL.md 文件测试."""
import re
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SKILLS_DIR = _PROJECT_ROOT / ".trae" / "skills"

# 14 个合法 Tool 名称（Plan 2）
VALID_TOOLS = {
    "import_file", "import_manual", "query_sessions", "calc_metrics",
    "get_trends", "analyze_fatigue", "generate_plan", "query_plan",
    "get_period_summary", "read_body_signals", "get_decision_trace",
    "save_decision_log", "get_statistics", "export_data",
}

EXPECTED_SKILLS = [
    "runflow-import",
    "runflow-analyze",
    "runflow-plan",
    "runflow-review",
    "runflow-coach",
    "runflow-stats",
]


def test_skills_dir_exists():
    """skills 目录存在."""
    assert _SKILLS_DIR.exists() and _SKILLS_DIR.is_dir()


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_skill_file_exists(skill_name):
    """每个 Skill 的 SKILL.md 存在."""
    path = _SKILLS_DIR / skill_name / "SKILL.md"
    assert path.exists(), f"{skill_name}/SKILL.md 不存在"


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_skill_has_valid_frontmatter(skill_name):
    """SKILL.md frontmatter 含 name 和 description."""
    path = _SKILLS_DIR / skill_name / "SKILL.md"
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{skill_name} 缺少 frontmatter"
    # 提取 frontmatter
    fm = content.split("---")[1]
    assert f"name: {skill_name}" in fm
    assert "description:" in fm


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_skill_referenced_tools_are_valid(skill_name):
    """SKILL.md 引用的 Tool 名称在 14 个合法 tool 范围内."""
    path = _SKILLS_DIR / skill_name / "SKILL.md"
    content = path.read_text(encoding="utf-8")
    # 提取反引号包裹的 tool 名称（如 `import_file`）
    referenced = set(re.findall(r"`(import_file|import_manual|query_sessions|calc_metrics|"
                                r"get_trends|analyze_fatigue|generate_plan|query_plan|"
                                r"get_period_summary|read_body_signals|get_decision_trace|"
                                r"save_decision_log|get_statistics|export_data)`", content))
    # 至少引用 1 个 tool
    assert len(referenced) >= 1, f"{skill_name} 未引用任何 tool"
    # 所有引用都在合法集合内（正则已保证，这里冗余检查）
    assert referenced.issubset(VALID_TOOLS)


def test_import_skill_workflow():
    """import Skill 包含关键工作流步骤."""
    content = (_SKILLS_DIR / "runflow-import" / "SKILL.md").read_text(encoding="utf-8")
    assert "import_file" in content
    assert "import_manual" in content
    assert "force" in content or "--force" in content
    assert "去重" in content or "duplicate" in content.lower()


def test_analyze_skill_workflow():
    """analyze Skill 包含关键工作流步骤."""
    content = (_SKILLS_DIR / "runflow-analyze" / "SKILL.md").read_text(encoding="utf-8")
    assert "calc_metrics" in content
    assert "get_trends" in content
    assert "analyze_fatigue" in content
    assert "save_decision_log" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_skills.py -v`
Expected: FAIL，skills 文件不存在

- [ ] **Step 3: 创建 runflow-import/SKILL.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/skills/runflow-import/SKILL.md`：

```markdown
---
name: runflow-import
description: Use when 用户想导入训练数据、上传文件、同步记录、手动录入跑步活动
---

# 训练数据导入流程

## Overview

跑步数据导入助手，负责将 FIT/GPX/CSV/TCX/XML 文件或手动录入数据转化为结构化 Session 并存储。核心流程：解析文件 → SHA256 去重 → 计算指标 → 存储 Parquet。

## When to Use

- 用户说"导入"/"上传"/"同步"/"录入"
- 用户提供 FIT/GPX/CSV/TCX/XML 文件路径
- 用户要求手动录入跑步数据
- 用户需要批量导入多个文件

## Workflow

### 1. 确定数据源

询问用户提供以下之一：
- 文件路径（FIT/GPX/CSV/TCX/XML）
- 批量文件目录
- 手动录入（日期/距离/时长/心率/来源）

### 2. 调用导入 Tool

- 文件源：调用 `import_file(file_path, force)` —— 支持单文件或循环批量
- 手动录入：调用 `import_manual(manual_data, force)`

### 3. 处理去重结果

- `imported=true`：展示 session_id + 关键指标（距离/时长/VDOT/TSS）
- `skipped=true`：告知用户重复原因（duplicate_hash / cross_platform_duplicate），询问是否 `--force` 重新导入
- `error`：给出明确错误原因（格式错误/不支持类型）

### 4. 批量导入汇总

循环调用 `import_file`，最后汇总：
```
导入完成：成功 N，跳过 M（重复），失败 K
```

## Quick Reference

| 步骤 | Tool | 降级方案 |
|------|------|----------|
| 文件导入 | `import_file` | 解析失败 → 手动录入 |
| 手动录入 | `import_manual` | 数据校验失败 → 提示修正 |
| 去重检测 | Tool 内部自动 | 重复 → 询问 --force |
| 批量导入 | 循环 `import_file` | 逐文件报告状态 |

## Common Mistakes

- **重复导入不提示 --force**：skipped=true 时必须告知用户可加 force 覆盖
- **手动录入未校验合理性**：距离/时长必须 >0，心率 30-260
- **批量导入无汇总**：必须给出成功/跳过/失败计数
- **不支持的文件类型**：仅支持 .fit .gpx .csv .tcx .xml

## 约束规则

- 遵循 data-safety-rules.md：文件本地解析，不上传外部服务
- 遵循 interaction-rules.md：去重冲突必须用户确认
- SHA256 去重 + 跨平台去重（时间±5min + 距离±2% + 时长±30s）
- 导入失败必须给明确原因，不可只报 "导入失败"
```

- [ ] **Step 4: 创建 runflow-analyze/SKILL.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/skills/runflow-analyze/SKILL.md`：

```markdown
---
name: runflow-analyze
description: Use when 用户想分析训练数据、查看负荷、VDOT趋势、HRV、疲劳度、心率漂移
---

# 训练数据分析流程

## Overview

训练数据分析助手，负责聚合区间指标、趋势分析、疲劳评估，并用 AI 生成数据驱动的解读。核心流程：确定范围 → 并行查询 → AI 解读 → 可选持久化。

## When to Use

- 用户说"分析"/"负荷"/"VDOT"/"HRV"/"疲劳"/"心率漂移"
- 用户想了解近期训练状态
- 用户需要数据支撑做训练决策

## Workflow

### 1. 确定分析范围

默认 30 天，支持 7/30/90/365 天或自定义日期范围。

### 2. 并行调用分析 Tool

- `calc_metrics(date_from, date_to)`：返回 VDOT 趋势 / TSS 累计 / CTL / ATL / TSB / 心率区间分布
- `get_trends(days, metric)`：返回时间序列（metric 可选 vdot/load/hrv）
- `analyze_fatigue(days)`：返回综合疲劳度（HRV + TSB + RPE）

### 3. AI 解读

用 Tool 返回的 `prompt` 调用宿主 LLM 生成解读：
- 必须具体到数据（"CTL 65 较上周 +3" 而非 "负荷上升"）
- 必须附数据依据
- 必须列风险因子
- 必须标注误差范围（禁止伪精确）
- 数据不足时必须降级标注

### 4. 可选持久化

用户确认后调用 `save_decision_log` 持久化分析结论。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 指标聚合 | `calc_metrics` | CTL/ATL/TSB/VDOT 趋势 |
| 趋势查询 | `get_trends` | vdot/load/hrv 时序 |
| 疲劳评估 | `analyze_fatigue` | 综合疲劳度 + 评分 |
| 决策记录 | `save_decision_log` | 可选，用户确认后 |

## Common Mistakes

- **笼统结论**："训练不错"/"负荷合理" 不合规，必须具体到数据
- **静默外推**：数据不足时必须标注 "基于 7 天数据，置信度低"
- **伪精确**："全马 3:59:30" 不合规，必须给区间 "3:55:00–4:05:00"
- **跨配速段混合**：心率漂移必须基于相同配速段

## 约束规则

- 遵循 analysis-rules.md：分析必须具体、附依据、标注误差
- 遵循 calculation-rules.md：VDOT 用 Powers 方法，TSS/CTL/ATL 公式正确
- 趋势判断必须明确时间窗口（vs 上周 / vs 去年同期）
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_skills.py -v -k "import or analyze"`
Expected: 相关测试 PASS

- [ ] **Step 6: Commit**

```bash
git add .trae/skills/runflow-import/ .trae/skills/runflow-analyze/ run-flow-skills-mcp/tests/test_skills.py
git commit -m "feat(skills): add runflow-import and runflow-analyze skills"
```

---

### Task 4: /plan + /review Skill

**Files:**
- Create: `.trae/skills/runflow-plan/SKILL.md`
- Create: `.trae/skills/runflow-review/SKILL.md`
- Test: `run-flow-skills-mcp/tests/test_skills.py`（Task 3 已创建，追加测试）

**Interfaces:**
- Consumes: 设计文档 7.3-7.4 节
- Produces: 2 个 SKILL.md

- [ ] **Step 1: 追加测试到 test_skills.py**

在 `run-flow-skills-mcp/tests/test_skills.py` 末尾追加：

```python
def test_plan_skill_workflow():
    """plan Skill 包含关键工作流步骤."""
    content = (_SKILLS_DIR / "runflow-plan" / "SKILL.md").read_text(encoding="utf-8")
    assert "generate_plan" in content
    assert "query_plan" in content
    assert "确认" in content  # 强制用户确认
    assert "save_decision_log" in content
    assert "VDOT" in content


def test_review_skill_workflow():
    """review Skill 包含关键工作流步骤."""
    content = (_SKILLS_DIR / "runflow-review" / "SKILL.md").read_text(encoding="utf-8")
    assert "get_period_summary" in content
    assert "export_data" in content
    assert "save_decision_log" in content
    assert "环比" in content or "同比" in content or "对比" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_skills.py -v -k "plan or review"`
Expected: FAIL，文件不存在

- [ ] **Step 3: 创建 runflow-plan/SKILL.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/skills/runflow-plan/SKILL.md`：

```markdown
---
name: runflow-plan
description: Use when 用户想制定训练计划、生成课表、设定目标、备赛全马/半马/破4
---

# 训练计划生成流程

## Overview

周期化训练计划生成助手，基于当前 VDOT 和目标生成结构化课表。核心流程：收集目标 → 评估能力 → 生成计划 → **用户确认** → 持久化。

## When to Use

- 用户说"计划"/"课表"/"目标"/"全马"/"破4"/"备赛"
- 用户想制定周期化训练方案
- 用户设定了比赛日期和目标成绩

## Workflow

### 1. 收集目标

必填参数：
- `goal_type`：full_marathon / half_marathon / 10k / 5k
- `goal_time`：目标完赛时间（如 "4:00:00"）
- `race_date`：比赛日期（YYYY-MM-DD）
- `weeks`：训练周期周数

### 2. 评估当前能力

调用 `query_sessions` 取近 90 天数据 → 计算当前 VDOT。
若无数据，提示用户先导入训练记录。

### 3. 生成计划

调用 `generate_plan(goal_type, goal_time, race_date, weeks, current_vdot)`：
- 返回结构化计划（phases 周期化阶段 + pace_zones 配速区间 + target_vdot）
- 返回 `plan_prompt`，用此 prompt 调用宿主 LLM 生成计划解释

### 4. 用户确认（强制）

展示完整计划 + AI 解释，**必须用户确认后才保存**。
未经确认不可保存计划。

### 5. 持久化决策

用户确认后调用 `save_decision_log` 记录计划生成决策（含 reasoning + trace_chain）。

### 6. 漏练自适应

后续 `query_plan` 自动计算 fidelity（执行忠实度），漏练检测 → 重新分配后续负荷（负荷守恒，不追加）。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 评估能力 | `query_sessions` | 取 90 天数据算 VDOT |
| 生成计划 | `generate_plan` | 结构化课表 + plan_prompt |
| 查询计划 | `query_plan` | 含 fidelity 忠实度 |
| 决策记录 | `save_decision_log` | 确认后记录 |

## Common Mistakes

- **未经确认直接保存**：计划必须用户确认后才持久化
- **漏练后追加负荷**：应重新分配，负荷守恒不追加
- **配速区间未基于个人 VDOT**：E/M/T/I/R 区间必须基于当前 VDOT
- **无数据生成计划**：当前 VDOT 未知时必须先导入数据

## 约束规则

- 遵循 interaction-rules.md：计划保存前必须用户确认
- 遵循 calculation-rules.md：配速区间基于 VDOT 比例
- 目标 VDOT 估算需标注误差范围
- 漏练自适应不追加负荷，只重新分配
```

- [ ] **Step 4: 创建 runflow-review/SKILL.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/skills/runflow-review/SKILL.md`：

```markdown
---
name: runflow-review
description: Use when 用户想复盘训练、生成总结、回顾本周/本月训练、导出报告
---

# 训练复盘流程

## Overview

训练复盘助手，负责聚合周期数据、对比历史、生成报告。核心流程：确定周期 → 聚合数据 → 对比 → AI 报告 → 可选导出。

## When to Use

- 用户说"复盘"/"总结"/"本周"/"本月"/"回顾"
- 用户想了解某段时间的训练表现
- 用户需要导出训练报告

## Workflow

### 1. 确定周期

默认本周，支持 week/month/season/year。

### 2. 聚合周期数据

调用 `get_period_summary(period, date_ref)`：
- 返回 total_distance / total_tss / avg_vdot / sessions_count
- 返回 vdot_trend / hrv_trend
- 返回 load_change（vs 上周期变化）

### 3. 对比历史

- 环比：vs 上周期（get_period_summary 已含 load_change）
- 同比：vs 去年同期（需调用两次 get_period_summary）

### 4. AI 生成报告

用 Tool 返回的 `prompt` 调用宿主 LLM 生成复盘报告：
- 跑量统计（总距离/训练次数）
- 负荷变化（CTL/ATL/TSB 趋势）
- VDOT 趋势（进步/停滞/退步）
- HRV 趋势（恢复状态）
- 伤病风险评估
- 下周建议

### 5. 可选导出

用户确认后调用 `export_data(format="md")` 导出 Markdown 报告。
**导出前必须用户确认**（data-safety-rules.md）。

### 6. 持久化决策

调用 `save_decision_log` 记录复盘结论。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 周期聚合 | `get_period_summary` | week/month/season/year |
| 导出报告 | `export_data` | md/csv/json/parquet |
| 决策记录 | `save_decision_log` | 记录复盘结论 |

## Common Mistakes

- **复盘笼统**：必须具体到数据（"本周跑量 45km，较上周 +5km"）
- **缺数据维度静默跳过**：必须明确标注 "HRV 数据缺失，未纳入分析"
- **导出前未确认**：export_data 前必须用户确认
- **同比/环比不明确**：必须标注时间窗口

## 约束规则

- 遵循 analysis-rules.md：复盘必须具体、附依据
- 遵循 data-safety-rules.md：导出前用户确认，含 AI 日志时二次确认
- 遵循 interaction-rules.md：错误时提供降级方案
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_skills.py -v -k "plan or review"`
Expected: 相关测试 PASS

- [ ] **Step 6: Commit**

```bash
git add .trae/skills/runflow-plan/ .trae/skills/runflow-review/ run-flow-skills-mcp/tests/test_skills.py
git commit -m "feat(skills): add runflow-plan and runflow-review skills"
```

---

### Task 5: /coach + /stats Skill

**Files:**
- Create: `.trae/skills/runflow-coach/SKILL.md`
- Create: `.trae/skills/runflow-stats/SKILL.md`
- Test: `run-flow-skills-mcp/tests/test_skills.py`（追加测试）

**Interfaces:**
- Consumes: 设计文档 7.5-7.6 节
- Produces: 2 个 SKILL.md

- [ ] **Step 1: 追加测试到 test_skills.py**

在 `run-flow-skills-mcp/tests/test_skills.py` 末尾追加：

```python
def test_coach_skill_workflow():
    """coach Skill 包含关键工作流步骤."""
    content = (_SKILLS_DIR / "runflow-coach" / "SKILL.md").read_text(encoding="utf-8")
    assert "read_body_signals" in content
    assert "calc_metrics" in content
    assert "query_plan" in content
    assert "save_decision_log" in content
    assert "0.6" in content  # confidence 门禁
    assert "替代方案" in content or "替代" in content


def test_stats_skill_workflow():
    """stats Skill 包含关键工作流步骤."""
    content = (_SKILLS_DIR / "runflow-stats" / "SKILL.md").read_text(encoding="utf-8")
    assert "get_statistics" in content
    assert "export_data" in content
    assert "确认" in content  # 导出前确认
    assert "by_source" in content or "by_week" in content  # 统计维度
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_skills.py -v -k "coach or stats"`
Expected: FAIL，文件不存在

- [ ] **Step 3: 创建 runflow-coach/SKILL.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/skills/runflow-coach/SKILL.md`：

```markdown
---
name: runflow-coach
description: Use when 用户询问今天能不能跑、今天怎么练、感觉累、恢复状态、训练建议
---

# AI 教练建议流程（差异化核心）

## Overview

AI 教练助手，综合身体信号、训练负荷、当前计划生成具体可执行的训练建议。核心流程：读身体信号 → 读负荷 → 读计划 → AI 综合判断 → 置信度门禁 → 用户反馈。

## When to Use

- 用户说"能不能跑"/"今天怎么练"/"感觉累"/"恢复"
- 用户询问今日训练建议
- 用户想了解身体就绪状态

## Workflow

### 1. 读取身体信号

调用 `read_body_signals(date=today)`：
- 返回 HRV / 静息心率 / 睡眠 / RPE / 基线偏离 / 就绪状态（green/yellow/red）
- readiness_level 由 Tool 内部综合 HRV + TSB + RPE 计算

### 2. 读取训练负荷

调用 `calc_metrics(date_from=<7天前日期>, date_to=<今日日期>)` 取 ATL，调用 `calc_metrics(date_from=<42天前日期>, date_to=<今日日期>)` 取 CTL/TSB。

> **注意**：`calc_metrics` 的入参是绝对日期（`YYYY-MM-DD`），不支持相对日期（如 `-7d`）。宿主 AI 需先计算具体日期后传入。

### 3. 读取当前计划

调用 `query_plan()`（无 plan_id 返回最新计划）→ 获取今日计划课表。

### 4. AI 综合判断

用 Tool 返回的 `coach_prompt` 调用宿主 LLM 生成建议：
- **类型 + 强度 + 时长 + 配速区间**（具体可执行）
- **决策溯源链**（输入数据 + 判断规则 + 置信度）
- **替代方案**（至少 1 个）

### 5. 置信度门禁

- `confidence ≥ 0.6`：直接给建议
- `confidence < 0.6`：必须提示 "仅供参考，建议结合主观感受"

### 6. 用户反馈

询问用户是否采纳：
- 采纳 → `save_decision_log` 记录 user_feedback=accepted
- 拒绝 → 记录 user_feedback=rejected
- 修改 → 记录修改内容

### 7. 历史查询（可选）

用户问"上次类似情况" → 调用 `get_decision_trace` 查询历史决策。

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 身体信号 | `read_body_signals` | HRV/RPE/就绪状态 |
| 训练负荷 | `calc_metrics` | ATL(7d)/CTL(42d)/TSB |
| 当前计划 | `query_plan` | 今日课表 + fidelity |
| 决策记录 | `save_decision_log` | 含 user_feedback |
| 历史溯源 | `get_decision_trace` | 可选，查类似决策 |

## Common Mistakes

- **建议不具体**："轻松跑一会儿" 不合规，必须 "E 区间 30 分钟，配速 5'40"-6'00"/km"
- **单一指标决策**：必须综合 HRV + TSB + RPE
- **与计划冲突**：计划是休息日不可建议高强度；冲突时给调整建议
- **confidence < 0.6 未提示**：必须加 "仅供参考" 声明
- **未考虑昨日高强度**：24h 内有 T5 间歇 → 今日必须降级
- **无替代方案**：至少给 1 个替代

## 约束规则

- 遵循 coaching-rules.md：建议具体可执行 + 溯源链 + 替代方案
- 遵循 calculation-rules.md：配速区间基于个人 VDOT
- 遵循 interaction-rules.md：建议给出后必须询问采纳
- confidence ≥ 0.6 直接建议；< 0.6 标注 "仅供参考"
- 用户反馈必须记录到 DecisionLog
```

- [ ] **Step 4: 创建 runflow-stats/SKILL.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.trae/skills/runflow-stats/SKILL.md`：

```markdown
---
name: runflow-stats
description: Use when 用户想查看统计、分布、导出数据、趋势汇总、按维度分组
---

# 训练统计与导出流程

## Overview

训练统计助手，按维度分组聚合数据并支持导出。核心流程：确定维度 → 查询统计 → 展示 → 可选导出。

## When to Use

- 用户说"统计"/"分布"/"导出"/"趋势"
- 用户想按来源/周/月/年/配速区间/距离范围分组
- 用户需要导出训练数据

## Workflow

### 1. 确定统计维度

支持维度：
- `by_source`：按数据来源（garmin/coros/apple/manual）
- `by_week`：按周
- `by_month`：按月
- `by_year`：按年
- `by_pace_zone`：按配速区间（E/M/T/I/R）
- `by_distance_range`：按距离范围（<5k/5-10k/10-21k/21-42k/>=42k）

### 2. 调用统计 Tool

调用 `get_statistics(dimension, date_from, date_to)`：
- 返回 groups（每组含 count/total_distance_km/total_duration_s/avg_pace/total_tss/avg_vdot）

### 3. 展示统计

以表格 + 简要文字展示，**不调 LLM**（统计是纯数据展示）。

### 4. 可选导出

用户要求导出时调用 `export_data(format, include_ai_logs)`：
- format：csv / json / parquet / md
- include_ai_logs：是否含 AI 决策日志（含时二次确认）
- **导出前必须用户确认**（data-safety-rules.md）

## Quick Reference

| 步骤 | Tool | 说明 |
|------|------|------|
| 分组统计 | `get_statistics` | 7 种维度 |
| 导出数据 | `export_data` | csv/json/parquet/md |

## Common Mistakes

- **导出前未确认**：export_data 前必须用户确认
- **全量导出未含 AI 日志**：询问是否包含 AI 决策记录
- **统计维度不合法**：仅支持 7 种维度，非法维度返回空
- **统计调 LLM**：统计是纯数据展示，不调 LLM

## 约束规则

- 遵循 data-safety-rules.md：导出前用户确认，含 AI 日志时二次确认
- 遵循 interaction-rules.md：批量操作展示进度
- 统计结果以表格展示，不调 LLM 生成解读
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_skills.py -v`
Expected: 所有 Skills 测试 PASS

- [ ] **Step 6: Commit**

```bash
git add .trae/skills/runflow-coach/ .trae/skills/runflow-stats/ run-flow-skills-mcp/tests/test_skills.py
git commit -m "feat(skills): add runflow-coach and runflow-stats skills"
```

---

### Task 6: 文档（README + QUICKSTART + DEPLOY + LICENSE）

**Files:**
- Create: `README.md`
- Create: `QUICKSTART.md`
- Create: `DEPLOY.md`
- Create: `LICENSE`
- Test: `run-flow-skills-mcp/tests/test_docs.py`

**Interfaces:**
- Consumes: 所有前置 Plan 的产出
- Produces: 用户文档，保证 5 分钟上手

- [ ] **Step 1: 写失败测试 — test_docs.py**

写入 `run-flow-skills-mcp/tests/test_docs.py`：

```python
"""文档文件测试."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.mark.parametrize("filename", ["README.md", "QUICKSTART.md", "DEPLOY.md", "LICENSE"])
def test_doc_file_exists(filename):
    """文档文件存在."""
    path = _PROJECT_ROOT / filename
    assert path.exists(), f"{filename} 不存在"
    assert path.stat().st_size > 0, f"{filename} 为空"


def test_readme_contains_key_sections():
    """README 包含关键章节."""
    content = (_PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "安装" in content or "Install" in content
    assert "Skill" in content or "技能" in content
    assert "/import" in content
    assert "/coach" in content


def test_quickstart_contains_steps():
    """QUICKSTART 包含步骤."""
    content = (_PROJECT_ROOT / "QUICKSTART.md").read_text(encoding="utf-8")
    assert "uv" in content
    assert "Trae" in content or "trae" in content
    assert "mcp" in content.lower()


def test_license_is_mit():
    """LICENSE 是 MIT 协议."""
    content = (_PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT" in content
    assert "Copyright" in content


def test_deploy_contains_web_instructions():
    """DEPLOY 包含 Web 启动说明."""
    content = (_PROJECT_ROOT / "DEPLOY.md").read_text(encoding="utf-8")
    assert "8002" in content or "web" in content.lower()
    assert "uv" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_docs.py -v`
Expected: FAIL，文档不存在

- [ ] **Step 3: 创建 LICENSE**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/LICENSE`：

```
MIT License

Copyright (c) 2026 RunFlowSkills

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: 创建 README.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/README.md`：

```markdown
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
```

- [ ] **Step 5: 创建 QUICKSTART.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/QUICKSTART.md`：

```markdown
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
```

- [ ] **Step 6: 创建 DEPLOY.md**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/DEPLOY.md`：

```markdown
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
```

- [ ] **Step 7: 运行测试验证通过**

Run: `uv run pytest tests/test_docs.py -v`
Expected: 所有文档测试 PASS

- [ ] **Step 8: Commit**

```bash
git add README.md QUICKSTART.md DEPLOY.md LICENSE run-flow-skills-mcp/tests/test_docs.py
git commit -m "feat(docs): add README, QUICKSTART, DEPLOY, and LICENSE"
```

---

### Task 7: 全量一致性测试

**Files:**
- Test: `run-flow-skills-mcp/tests/test_skills_rules_consistency.py`

**说明：** 验证 Skills 引用的 Tool 名称与 Plan 2 的 14 个 tool 一致，Rules 的 scope 与 Skills 一致。

- [ ] **Step 1: 写一致性测试 — test_skills_rules_consistency.py**

写入 `run-flow-skills-mcp/tests/test_skills_rules_consistency.py`：

```python
"""Skills 与 Rules 一致性测试."""
import re
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SKILLS_DIR = _PROJECT_ROOT / ".trae" / "skills"
_RULES_DIR = _PROJECT_ROOT / ".trae" / "rules"

# 14 个合法 Tool（Plan 2）
VALID_TOOLS = {
    "import_file", "import_manual", "query_sessions", "calc_metrics",
    "get_trends", "analyze_fatigue", "generate_plan", "query_plan",
    "get_period_summary", "read_body_signals", "get_decision_trace",
    "save_decision_log", "get_statistics", "export_data",
}

EXPECTED_SKILLS = [
    "runflow-import", "runflow-analyze", "runflow-plan",
    "runflow-review", "runflow-coach", "runflow-stats",
]


def test_all_skills_exist():
    """6 个 Skill 全部存在."""
    for skill in EXPECTED_SKILLS:
        assert (_SKILLS_DIR / skill / "SKILL.md").exists()


def test_all_rules_exist():
    """5 个 Rule 全部存在."""
    expected = [
        "calculation-rules.md", "analysis-rules.md", "coaching-rules.md",
        "data-safety-rules.md", "interaction-rules.md",
    ]
    for rule in expected:
        assert (_RULES_DIR / rule).exists()


def test_skills_reference_only_valid_tools():
    """所有 Skill 引用的 Tool 在 14 个合法 tool 内."""
    tool_pattern = re.compile(
        r"`(import_file|import_manual|query_sessions|calc_metrics|"
        r"get_trends|analyze_fatigue|generate_plan|query_plan|"
        r"get_period_summary|read_body_signals|get_decision_trace|"
        r"save_decision_log|get_statistics|export_data)`"
    )
    for skill in EXPECTED_SKILLS:
        content = (_SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        referenced = set(tool_pattern.findall(content))
        assert referenced.issubset(VALID_TOOLS), f"{skill} 引用了非法 tool: {referenced - VALID_TOOLS}"


def test_rules_scope_references_valid_skills():
    """所有 Rule 的 scope 引用合法 Skill 名称."""
    skill_names = set(EXPECTED_SKILLS)
    for rule_file in _RULES_DIR.glob("*.md"):
        content = rule_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            fm = content.split("---")[1]
            scope_match = re.search(r"scope:\s*(.+)", fm)
            if scope_match:
                scopes = [s.strip() for s in scope_match.group(1).split(",")]
                for s in scopes:
                    if s:
                        assert s in skill_names, f"{rule_file.name} scope '{s}' 不在合法 Skill 中"


def test_every_skill_has_workflow_section():
    """每个 Skill 有 Workflow 章节."""
    for skill in EXPECTED_SKILLS:
        content = (_SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "## Workflow" in content or "## 工作流" in content, f"{skill} 缺少 Workflow 章节"


def test_every_skill_has_common_mistakes():
    """每个 Skill 有 Common Mistakes 章节."""
    for skill in EXPECTED_SKILLS:
        content = (_SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "Common Mistakes" in content or "常见错误" in content, f"{skill} 缺少 Common Mistakes"
```

- [ ] **Step 2: 运行全量测试**

Run: `uv run pytest tests/ -v --tb=short`
Expected: 所有测试 PASS（Plan 1 + 2 + 3 + 4 全部）

- [ ] **Step 3: Commit**

```bash
git add run-flow-skills-mcp/tests/test_skills_rules_consistency.py
git commit -m "test: add skills-rules consistency tests for tool references and scope"
```

---

## Self-Review

### 1. Spec 覆盖检查

| 设计文档章节 | 覆盖 Task | 说明 |
|---|---|---|
| 7.1-7.6 六个 Skills | Task 3/4/5 | import/analyze/plan/review/coach/stats |
| 7.7 命令清单 | Task 3/4/5 | 每个 SKILL.md 含 Quick Reference |
| 8.1-8.5 五个 Rules | Task 2 | calculation/analysis/coaching/data-safety/interaction |
| 3.x .trae/mcp.json | Task 1 | MCP server 注册 |
| 14.x 文档 | Task 6 | README/QUICKSTART/DEPLOY/LICENSE |

### 2. 占位符扫描

- ✅ 无 TBD/TODO
- ✅ 所有 SKILL.md 完整含 Workflow + Quick Reference + Common Mistakes + 约束规则
- ✅ 所有 Rules 完整含 frontmatter + 规则条目
- ✅ 文档完整可读

### 3. 类型一致性

- Skills 引用的 14 个 tool 名称与 Plan 2 一致
- Rules 的 scope 引用的 skill 名称与 Task 3/4/5 创建的一致
- mcp.json 的 server 名称与 pyproject.toml 的 script 名称一致（`run-flow-skills-mcp`）
- 端口号 8002 与 constants.WEB_PORT 一致
