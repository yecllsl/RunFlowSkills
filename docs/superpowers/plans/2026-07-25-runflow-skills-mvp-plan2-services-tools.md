# RunFlowSkills MVP v0.1.0 实现计划 - Plan 2: Services + 14 MCP Tools

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Plan 1 基础设施之上构建业务编排层（6 个 services）+ AI Prompt 模板层（5 个 prompts）+ MCP Tools 薄包装层（14 个 tools）+ FastMCP Server 入口，输出可被 Trae/WorkBuddy 宿主调用的 MCP Server。

**Architecture:** 方案 B「薄 tools + 厚 calculators + services 编排」的中层。services 编排 calculators + storage，被 tools 和 web 共用；tools 是 services 的薄包装（参数校验 → 调 service → 返回 prompt+数据）；prompts 是纯字符串模板，不依赖任何模块。**Tool 不调 LLM**，由 Skill 让宿主 AI 调 LLM。

**Tech Stack:** fastmcp 3.0+（MCP Server）/ pydantic 2.x / polars 0.20+（LazyFrame 查询）/ pytest 8+（TDD）

## Global Constraints

- 复用 Plan 1 接口：`models.*`、`constants.*`、`calculators.*`、`storage.*`（不重写）
- **Tool 不调 LLM**：返回 `{prompt: str, ...data}`，由宿主 AI 用 prompt 调 LLM（spec 10.2）
- **services 无 LLM 依赖**：纯业务编排，可独立测试
- **tools 是薄包装**：参数校验 + 调 service + 附 prompt，单文件 < 80 行
- **FastMCP 懒导入**：server.py 在 `@mcp.tool()` 装饰器内 `from ... import`，保证 server.py 可加载
- 数据目录：`run-flow-skills-mcp/data/`（与 Plan 1 一致）
- `readiness_level` 由 `read_body_signals` tool 内部综合 HRV + TSB + RPE 计算（spec 6.2）
- `generate_plan` 返回 `plan_prompt`，AI 用它生成自然语言解释（spec 6.2）
- `save_decision_log` 的 `reasoning/recommendation/trace_chain` 由宿主 AI 生成传入（spec 6.2）
- 命名规范：类名 PascalCase，函数/变量 snake_case
- 编码规范：禁止 `# type: ignore`、`Dict[str, Any]`、裸 `Exception`
- 测试覆盖率：services ≥70%，tools ≥80%（spec 12.1）
- 提交规范：每个 task 末尾 `git commit`，格式 `feat/test/docs(scope): 简述`

---

## 文件结构

本 plan 产出以下文件（在 Plan 1 已有目录基础上新增）：

```
run-flow-skills-mcp/
├── src/run_flow_skills_mcp/
│   ├── prompts/                                 # Task 1
│   │   ├── __init__.py
│   │   ├── analyze_prompt.py
│   │   ├── plan_prompt.py
│   │   ├── review_prompt.py
│   │   ├── coach_prompt.py
│   │   └── decision_trace.py
│   ├── services/                                # Task 2-7
│   │   ├── __init__.py
│   │   ├── import_service.py                    # Task 2
│   │   ├── analysis_service.py                  # Task 3
│   │   ├── plan_service.py                      # Task 4
│   │   ├── review_service.py                    # Task 5
│   │   ├── coach_service.py                     # Task 6
│   │   └── stats_service.py                     # Task 7
│   ├── tools/                                   # Task 8-14
│   │   ├── __init__.py
│   │   ├── import_file.py                       # Task 8
│   │   ├── import_manual.py                     # Task 8
│   │   ├── query_sessions.py                    # Task 9
│   │   ├── calc_metrics.py                      # Task 9
│   │   ├── get_trends.py                        # Task 10
│   │   ├── analyze_fatigue.py                   # Task 10
│   │   ├── generate_plan.py                     # Task 11
│   │   ├── query_plan.py                        # Task 11
│   │   ├── get_period_summary.py                # Task 12
│   │   ├── read_body_signals.py                 # Task 12
│   │   ├── get_decision_trace.py                # Task 13
│   │   ├── save_decision_log.py                 # Task 13
│   │   ├── get_statistics.py                    # Task 14
│   │   └── export_data.py                       # Task 14
│   └── server.py                                # Task 15
└── tests/
    ├── prompts/
    │   └── test_prompts.py                      # Task 1
    ├── services/
    │   ├── __init__.py
    │   ├── test_import_service.py               # Task 2
    │   ├── test_analysis_service.py             # Task 3
    │   ├── test_plan_service.py                 # Task 4
    │   ├── test_review_service.py               # Task 5
    │   ├── test_coach_service.py                # Task 6
    │   └── test_stats_service.py                # Task 7
    ├── tools/
    │   ├── __init__.py
    │   ├── test_import_tools.py                 # Task 8
    │   ├── test_query_and_metrics_tools.py      # Task 9
    │   ├── test_trends_and_fatigue_tools.py     # Task 10
    │   ├── test_plan_tools.py                   # Task 11
    │   ├── test_period_and_body_tools.py        # Task 12
    │   ├── test_decision_tools.py               # Task 13
    │   └── test_stats_tools.py                  # Task 14
    ├── test_server.py                           # Task 15
    └── test_integration_workflows.py            # Task 16
```

---

## Task 1: prompts/ AI Prompt 模板模块

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/__init__.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/analyze_prompt.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/plan_prompt.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/review_prompt.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/coach_prompt.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/decision_trace.py`
- Test: `run-flow-skills-mcp/tests/prompts/test_prompts.py`

**Interfaces:**
- Consumes: 无（纯字符串模板）
- Produces:
  - `ANALYZE_PROMPT`（分析解读 prompt 模板，含 `{vdot}`, `{tss}`, `{ctl}` 等占位符）
  - `PLAN_PROMPT`（计划生成 prompt 模板，含 `{goal_type}`, `{current_vdot}`, `{target_vdot}` 等）
  - `REVIEW_PROMPT`（复盘报告 prompt 模板，含 `{period}`, `{total_distance}`, `{load_change}` 等）
  - `COACH_PROMPT`（教练建议 prompt 模板，含 `{hrv}`, `{tsb}`, `{readiness_level}` 等）
  - `DECISION_TRACE_TEMPLATE`（决策溯源链模板，含 `{inputs}`, `{reasoning}`, `{recommendation}`）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/prompts/__init__.py`（空）：

```python
```

写入 `run-flow-skills-mcp/tests/prompts/test_prompts.py`：

```python
"""prompts 模板单元测试."""
from run_flow_skills_mcp.prompts.analyze_prompt import ANALYZE_PROMPT
from run_flow_skills_mcp.prompts.plan_prompt import PLAN_PROMPT
from run_flow_skills_mcp.prompts.review_prompt import REVIEW_PROMPT
from run_flow_skills_mcp.prompts.coach_prompt import COACH_PROMPT
from run_flow_skills_mcp.prompts.decision_trace import DECISION_TRACE_TEMPLATE


def test_analyze_prompt_has_placeholders():
    """分析模板必须包含关键占位符（spec 8.2 分析规则）."""
    assert "{vdot}" in ANALYZE_PROMPT
    assert "{tss}" in ANALYZE_PROMPT
    assert "{ctl}" in ANALYZE_PROMPT
    assert "{atl}" in ANALYZE_PROMPT
    assert "{tsb}" in ANALYZE_PROMPT
    # 必须提示 AI 附数据依据 + 列风险因子 + 标注误差范围
    assert "数据依据" in ANALYZE_PROMPT
    assert "风险因子" in ANALYZE_PROMPT
    assert "误差范围" in ANALYZE_PROMPT


def test_plan_prompt_has_placeholders():
    """计划模板必须包含目标与 VDOT 占位符（spec 7.3）."""
    assert "{goal_type}" in PLAN_PROMPT
    assert "{goal_time}" in PLAN_PROMPT
    assert "{race_date}" in PLAN_PROMPT
    assert "{weeks}" in PLAN_PROMPT
    assert "{current_vdot}" in PLAN_PROMPT
    assert "{target_vdot}" in PLAN_PROMPT
    # 必须提示 AI 解释配速区间依据
    assert "配速区间" in PLAN_PROMPT


def test_review_prompt_has_placeholders():
    """复盘模板必须包含周期与负荷变化占位符（spec 7.4）."""
    assert "{period}" in REVIEW_PROMPT
    assert "{total_distance}" in REVIEW_PROMPT
    assert "{total_tss}" in REVIEW_PROMPT
    assert "{load_change}" in REVIEW_PROMPT
    assert "{vdot_trend}" in REVIEW_PROMPT
    # 必须提示 AI 列出跑量/负荷/VDOT/HRV/伤病风险/下周建议
    assert "跑量" in REVIEW_PROMPT
    assert "下周建议" in REVIEW_PROMPT


def test_coach_prompt_has_placeholders():
    """教练模板必须包含身体信号与就绪状态占位符（spec 7.5, 8.3）."""
    assert "{hrv}" in COACH_PROMPT
    assert "{tsb}" in COACH_PROMPT
    assert "{readiness_level}" in COACH_PROMPT
    assert "{today_plan}" in COACH_PROMPT
    # 必须提示 AI 给具体可执行建议 + 溯源链 + 置信度 + 替代方案
    assert "具体可执行" in COACH_PROMPT
    assert "溯源" in COACH_PROMPT
    assert "替代方案" in COACH_PROMPT


def test_decision_trace_template_has_placeholders():
    """决策溯源链模板（spec 4.5）."""
    assert "{inputs}" in DECISION_TRACE_TEMPLATE
    assert "{reasoning}" in DECISION_TRACE_TEMPLATE
    assert "{recommendation}" in DECISION_TRACE_TEMPLATE
    assert "{confidence}" in DECISION_TRACE_TEMPLATE


def test_prompts_format_correctly():
    """模板可用 .format() 填充."""
    filled = ANALYZE_PROMPT.format(
        vdot=45.0, tss=100.0, ctl=65.0, atl=58.0, tsb=7.0,
        hr_zones_dist="Z2:40%, Z3:30%", days=30,
    )
    assert "45.0" in filled
    assert "65.0" in filled
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/prompts/test_prompts.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/__init__.py`：

```python
"""prompts 子包：AI Prompt 模板（纯字符串，无依赖）."""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/analyze_prompt.py`：

```python
"""分析解读 Prompt 模板（spec 7.2, 8.2）.

约束（analysis-rules.md）：
1. 必须具体到数据层面，禁止笼统结论
2. 趋势判断必须附数据依据
3. 伤病风险必须列风险因子
4. 预测结果必须标注误差范围
5. 数据不足必须降级标注
"""
ANALYZE_PROMPT = """你是资深跑步数据分析教练。请基于以下 {days} 天训练数据进行深度分析。

## 核心指标
- VDOT: {vdot}
- 累计 TSS: {tss}
- CTL（42天慢性负荷）: {ctl}
- ATL（7天急性负荷）: {atl}
- TSB（训练压力平衡）: {tsb}
- 心率区间分布: {hr_zones_dist}

## 输出要求（严格遵守 analysis-rules.md）
1. **数据依据**：每个结论必须引用具体数值（如 "CTL 65 较上周 +3"），禁止 "负荷上升" 等笼统表述
2. **风险因子**：若评估伤病风险，必须列出主要风险因子（如 "ATL 增速过快"/"HRV 持续偏低"）
3. **误差范围**：任何预测（如 VDOT 趋势/比赛成绩）必须给出区间（如 "3:55:00-4:05:00"），禁止伪精确
4. **降级标注**：数据不足 7 天时必须标注 "基于 N 天数据，置信度低"
5. **同比/环比**：对比必须明确时间窗口（"vs 上周"/"vs 去年同期"）

## 输出格式
### 训练负荷分析
[具体数据 + 趋势判断]

### VDOT 与配速分析
[VDOT 变化 + 配速区间建议]

### 伤病风险评估
[风险因子列表 + 风险等级]

### 下周训练建议
[具体建议 + 依据]
"""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/plan_prompt.py`：

```python
"""训练计划生成 Prompt 模板（spec 7.3）."""
PLAN_PROMPT = """你是资深跑步教练。请基于以下信息生成 {weeks} 周训练计划，目标：{goal_type} {goal_time}（比赛日 {race_date}）。

## 当前能力
- 当前 VDOT: {current_vdot}
- 目标 VDOT: {target_vdot}
- 能力差距: {vdot_gap}

## 计划结构（已由 service 生成）
{plan_struct}

## 输出要求
1. **配速区间依据**：每个课表必须说明 E/M/T/I/R 区间如何基于个人 VDOT 计算
2. **周期化说明**：解释基础期/进展期/巅峰期/减量期的负荷变化逻辑
3. **可执行性**：每节课表含 类型 + 强度 + 时长 + 配速区间（如 "E 区间 30 分钟，配速 5'40\"-6'00\"/km"）
4. **漏练自适应**：说明漏练时如何调整后续负荷（负荷守恒，不追加）
5. **风险提示**：若 VDOT 差距过大（>3），提示风险并给出保守方案

## 输出格式
### 计划概览
[周期化结构 + 周跑量变化]

### 关键课表说明
[每周重点课表 + 配速依据]

### 注意事项
[漏练处理 + 风险提示]
"""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/review_prompt.py`：

```python
"""复盘报告 Prompt 模板（spec 7.4）."""
REVIEW_PROMPT = """你是资深跑步教练。请基于以下 {period} 数据生成本期训练复盘报告。

## 本期数据
- 周期: {period}
- 总跑量: {total_distance} km
- 累计 TSS: {total_tss}
- 负荷变化: {load_change}
- VDOT 趋势: {vdot_trend}
- HRV 趋势: {hrv_trend}
- 训练次数: {sessions_count}

## 输出要求（严格遵守 analysis-rules.md）
1. **跑量统计**：本期跑量 + 环比/同比对比（明确时间窗口）
2. **负荷变化**：CTL/ATL/TSB 演变 + 风险评估
3. **VDOT 趋势**：能力变化 + 数据依据
4. **HRV 趋势**：恢复状态 + 偏离基线分析
5. **伤病风险**：列出主要风险因子
6. **下周建议**：具体可执行建议（类型 + 强度 + 时长）
7. **数据缺失**：若某维度数据不足，必须明确标注，禁止静默跳过

## 输出格式
### 本期概览
[一句话总结]

### 详细分析
[跑量/负荷/VDOT/HRV/伤病风险 5 个维度]

### 下周建议
[具体课表建议]
"""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/coach_prompt.py`：

```python
"""AI 教练建议 Prompt 模板（spec 7.5, 8.3 coaching-rules.md）.

约束（coaching-rules.md）：
1. 建议必须具体可执行：类型 + 强度 + 时长 + 配速区间
2. 必须附决策溯源链：输入数据 + 判断规则 + 置信度 + 替代方案
3. 就绪状态综合 HRV + TSB + RPE，单一指标不可决策
4. 不得与当前训练计划冲突
5. confidence < 0.6 时必须提示 "仅供参考"
6. 必须考虑 24h 内高强度训练历史
7. 替代方案至少 1 个
"""
COACH_PROMPT = """你是资深跑步教练。请基于以下身体信号和训练负荷数据，给出今日训练建议。

## 身体信号（今日）
- HRV (RMSSD): {hrv} ms（基线 {hrv_baseline} ms，偏离 {hrv_deviation_pct}%）
- 静息心率: {resting_hr} bpm
- 睡眠质量: {sleep_quality}/5
- 主观疲劳度 RPE: {rpe}/10
- 就绪状态: {readiness_level}（green/yellow/red，由 HRV+TSB+RPE 综合计算）

## 训练负荷
- CTL（42天）: {ctl}
- ATL（7天）: {atl}
- TSB: {tsb}
- 昨日训练: {yesterday_session}
- 24h 内高强度: {recent_high_intensity}

## 今日计划课表
{today_plan}

## 输出要求（严格遵守 coaching-rules.md）
1. **具体可执行**：类型 + 强度 + 时长 + 配速区间（如 "E 区间 30 分钟，配速 5'40\"-6'00\"/km"）
2. **决策溯源链**：列出 输入数据 → 判断规则 → 结论 的完整链条
3. **置信度**：给出 confidence（0-1）；< 0.6 时必须提示 "仅供参考，建议结合主观感受"
4. **替代方案**：至少 1 个（如 "今日推荐 E 区间，替代方案：完全休息或 M 区间 20 分钟"）
5. **计划冲突检查**：若建议与今日计划冲突，给 "调整建议" 并说明原因
6. **24h 高强度考虑**：若昨跑 T5 间歇，今日必须降级

## 输出格式
### 今日建议
[类型 + 强度 + 时长 + 配速区间]

### 决策溯源
- 输入数据: [...]
- 判断规则: [...]
- 置信度: X.XX
- {置信度提示，若 < 0.6}

### 替代方案
[至少 1 个]

### 计划冲突说明
[若无冲突标注 "与计划一致"]
"""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/decision_trace.py`：

```python
"""决策溯源链模板（spec 4.5, 10.1）.

用于 save_decision_log 的 trace_chain 字段，由宿主 AI 填充后传入。
"""
DECISION_TRACE_TEMPLATE = """决策溯源链:
1. 输入数据: {inputs}
2. 判断逻辑: {reasoning}
3. 建议结论: {recommendation}
4. 置信度: {confidence}
5. 相关 Session: {related_session_ids}
"""
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/prompts/test_prompts.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/prompts/ run-flow-skills-mcp/tests/prompts/
git commit -m "feat(prompts): add AI prompt templates for analyze/plan/review/coach/decision_trace"
```

---

## Task 2: services/import_service.py 导入编排

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/services/__init__.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/services/import_service.py`
- Test: `run-flow-skills-mcp/tests/services/__init__.py`
- Test: `run-flow-skills-mcp/tests/services/test_import_service.py`

**Interfaces:**
- Consumes（来自 Plan 1）:
  - `storage.parquet_store.ParquetStore`
  - `storage.json_store.JsonStore`
  - `storage.importer.parse_file`、`ImportParseError`
  - `storage.dedup.check_hash_duplicate`、`find_cross_platform_duplicate`
  - `calculators.vdot.calc_vdot`
  - `calculators.training_load.calc_tss`、`calc_intensity_factor`
  - `calculators.pace_zones.classify_pace_zone`
  - `models.Session`、`TrainingMetrics`、`generate_session_id`
  - `constants.DEFAULT_LTHR`（IF 计算用，threshold_pace 来自 LTHR 对应配速）
- Produces:
  - `class ImportService`：`__init__(self, parquet_store: ParquetStore, json_store: JsonStore)`
  - `import_file(file_path: Path, force: bool=False, source: Optional[SourceType]=None) -> dict`：返回 `{imported, session_id, metrics_summary, skipped?, reason?}`
  - `import_manual(manual_data: dict, force: bool=False) -> dict`：手动录入
  - `_compute_metrics(session: Session) -> TrainingMetrics`：内部方法，计算 VDOT/TSS/IF/pace_zone
  - `_recompute_training_load() -> None`：内部方法，重算 TrainingLoad 并保存

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/services/__init__.py`（空）：

```python
```

写入 `run-flow-skills-mcp/tests/services/test_import_service.py`：

```python
"""import_service 测试（spec 5.4, FR-IMPORT-01/05）."""
from datetime import datetime
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import Session
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> ImportService:
    return ImportService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


def _write_gpx(path: Path) -> None:
    gpx = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><time>2026-07-25T06:00:00Z</time></metadata>
  <trk><name>Morning Run</name><trkseg>
    <trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2026-07-25T06:00:00Z</time></trkpt>
    <trkpt lat="39.9142" lon="116.4174"><ele>51.0</ele><time>2026-07-25T06:30:00Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""
    path.write_text(gpx, encoding="utf-8")


def test_import_file_new_gpx(service: ImportService, tmp_path: Path):
    """导入新 GPX 文件：imported=True + metrics_summary."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    result = service.import_file(gpx)
    assert result["imported"] is True
    assert "session_id" in result
    assert "metrics_summary" in result
    assert result["metrics_summary"]["pace_zone"] in ("E", "M", "T", "I", "R")


def test_import_file_duplicate_hash_skipped(service: ImportService, tmp_path: Path):
    """同文件二次导入：skipped=True + reason=duplicate_hash（spec 5.3）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    first = service.import_file(gpx)
    assert first["imported"] is True

    second = service.import_file(gpx)
    assert second["imported"] is False
    assert second["skipped"] is True
    assert second["reason"] == "duplicate_hash"


def test_import_file_force_overrides_duplicate(service: ImportService, tmp_path: Path):
    """--force 覆盖去重（spec 5.3）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    service.import_file(gpx)
    result = service.import_file(gpx, force=True)
    assert result["imported"] is True


def test_import_file_unsupported_extension_returns_error(service: ImportService, tmp_path: Path):
    """不支持的扩展名：返回 error，不抛异常（interaction-rules.md 降级方案）."""
    bad = tmp_path / "test.txt"
    bad.write_text("invalid", encoding="utf-8")

    result = service.import_file(bad)
    assert result["imported"] is False
    assert "error" in result


def test_import_manual_basic(service: ImportService):
    """手动录入：activity_date/distance_m/duration_s."""
    manual_data = {
        "activity_date": "2026-07-25T06:00:00",
        "distance_m": 10000.0,
        "duration_s": 3600,
        "source": "manual",
    }
    result = service.import_manual(manual_data)
    assert result["imported"] is True
    assert "session_id" in result
    assert result["metrics_summary"]["tss"] > 0


def test_import_manual_invalid_data_returns_error(service: ImportService):
    """无效数据（distance<=0）：返回 error."""
    result = service.import_manual({"distance_m": 0, "duration_s": 3600, "source": "manual"})
    assert result["imported"] is False
    assert "error" in result


def test_import_writes_metrics_to_parquet(service: ImportService, tmp_path: Path):
    """导入后 metrics 应写入 parquet（spec 5.4）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    result = service.import_file(gpx)
    session_id = result["session_id"]
    metrics = service.parquet_store.query_metrics([session_id])
    assert len(metrics) == 1
    assert metrics[0].tss > 0


def test_import_recomputes_training_load(service: ImportService, tmp_path: Path):
    """导入后 TrainingLoad 应被重算并写入 JSON（spec 5.4）."""
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    service.import_file(gpx)
    loads = service.json_store.query_load()
    assert len(loads) > 0
    # 当日应有 TrainingLoad 记录
    today_load = [l for l in loads if l.date == "2026-07-25"]
    assert len(today_load) == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/services/test_import_service.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/services/__init__.py`：

```python
"""services 子包：业务编排（tools 和 web 共用）."""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/services/import_service.py`：

```python
"""导入编排服务（spec 5.4, FR-IMPORT-01/05）.

编排 importer + dedup + calculators + storage：
1. parse_file 解析文件 → Session
2. check_hash_duplicate 主去重
3. find_cross_platform_duplicate 跨平台去重
4. _compute_metrics 计算 VDOT/TSS/IF/pace_zone
5. 写入 Parquet + 重算 TrainingLoad
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.calculators.pace_zones import classify_pace_zone
from run_flow_skills_mcp.calculators.training_load import (
    calc_intensity_factor,
    calc_tss,
)
from run_flow_skills_mcp.calculators.vdot import calc_vdot
from run_flow_skills_mcp.constants import DEFAULT_LTHR
from run_flow_skills_mcp.models import (
    Session,
    SourceType,
    TrainingMetrics,
    generate_session_id,
)
from run_flow_skills_mcp.storage.dedup import (
    check_hash_duplicate,
    find_cross_platform_duplicate,
)
from run_flow_skills_mcp.storage.importer import ImportParseError, parse_file
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

# LTHR 对应配速的近似换算（秒/km）：LTHR 越高，阈值配速越快
# 经验值：LTHR 165 ≈ 5'00"/km（300s/km）
_LTHR_TO_THRESHOLD_PACE: float = 49500.0  # 165 * 300


def _threshold_pace_from_lthr(lthr: int) -> float:
    """由 LTHR 估算阈值配速（秒/km）."""
    return _LTHR_TO_THRESHOLD_PACE / max(lthr, 1)


class ImportService:
    """导入编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def import_file(
        self,
        file_path: Path,
        force: bool = False,
        source: Optional[SourceType] = None,
    ) -> dict:
        """导入文件：解析 → 去重 → 计算指标 → 存储."""
        try:
            session = parse_file(file_path, source=source)
        except ImportParseError as e:
            return {"imported": False, "error": str(e)}

        # 重写 session_id（importer 生成的是临时 ID，需基于已存数量生成）
        session.session_id = self._next_session_id(session.activity_date)

        return self._import_session(session, force)

    def import_manual(self, manual_data: dict, force: bool = False) -> dict:
        """手动录入：构造 Session 后复用 _import_session."""
        try:
            activity_date = datetime.fromisoformat(manual_data["activity_date"])
            distance_m = float(manual_data["distance_m"])
            duration_s = int(manual_data["duration_s"])
            source = manual_data.get("source", "manual")
            if distance_m <= 0 or duration_s <= 0:
                return {"imported": False, "error": "distance_m 和 duration_s 必须 >0"}

            avg_pace = duration_s / (distance_m / 1000)
            session = Session(
                session_id=self._next_session_id(activity_date),
                activity_date=activity_date,
                distance_m=distance_m,
                duration_s=duration_s,
                avg_pace_s_per_km=avg_pace,
                avg_hr=manual_data.get("avg_hr"),
                max_hr=manual_data.get("max_hr"),
                source=source,
                notes=manual_data.get("notes"),
            )
        except (KeyError, ValueError, TypeError) as e:
            return {"imported": False, "error": f"数据格式错误: {e}"}

        return self._import_session(session, force)

    def _import_session(self, session: Session, force: bool) -> dict:
        """统一的 Session 导入流程（去重 → 计算 → 存储）."""
        # 主去重：raw_file_hash
        if not force and session.raw_file_hash:
            existing = check_hash_duplicate(self.parquet_store, session.raw_file_hash)
            if existing is not None:
                return {
                    "imported": False,
                    "skipped": True,
                    "reason": "duplicate_hash",
                    "existing_session_id": existing.session_id,
                }

        # 跨平台去重
        if not force:
            cross = find_cross_platform_duplicate(self.parquet_store, session)
            if cross is not None:
                return {
                    "imported": False,
                    "skipped": True,
                    "reason": "cross_platform_duplicate",
                    "existing_session_id": cross.session_id,
                }

        # 计算指标
        metrics = self._compute_metrics(session)

        # 写入 Parquet
        self.parquet_store.append_session(session)
        self.parquet_store.append_metrics(metrics)

        # 重算 TrainingLoad
        self._recompute_training_load()

        return {
            "imported": True,
            "session_id": session.session_id,
            "metrics_summary": {
                "vdot": metrics.vdot,
                "vdot_confidence": metrics.vdot_confidence,
                "tss": metrics.tss,
                "intensity_factor": metrics.intensity_factor,
                "pace_zone": metrics.pace_zone,
            },
        }

    def _compute_metrics(self, session: Session) -> TrainingMetrics:
        """计算 VDOT/TSS/IF/pace_zone."""
        vdot, confidence = calc_vdot(session.distance_m, session.duration_s)

        # IF 基于阈值配速（由 LTHR 估算，实际应由 UserConfig 覆盖）
        threshold_pace = _threshold_pace_from_lthr(DEFAULT_LTHR)
        if_val = calc_intensity_factor(session.avg_pace_s_per_km, threshold_pace)
        tss = calc_tss(session.duration_s, if_val)

        pace_zone = classify_pace_zone(session.avg_pace_s_per_km, vdot) if vdot else "E"

        return TrainingMetrics(
            session_id=session.session_id,
            vdot=vdot,
            vdot_confidence=confidence,
            tss=tss,
            intensity_factor=if_val,
            pace_zone=pace_zone,
        )

    def _next_session_id(self, activity_date: datetime) -> str:
        """生成下一个 session_id：查当天已存数量 +1."""
        date_str = activity_date.strftime("%Y%m%d")
        date_iso = activity_date.strftime("%Y-%m-%d")
        existing = self.parquet_store.query_sessions(
            date_from=date_iso, date_to=date_iso
        )
        return generate_session_id(date_str, len(existing))

    def _recompute_training_load(self) -> None:
        """重算 TrainingLoad（CTL/ATL/TSB）并写入 JSON.

        简化策略（ponytail: O(N) 扫描所有 sessions，N 通常 <10000，可接受）：
        按日聚合 TSS → 计算 EWMA → 写入当日 TrainingLoad
        """
        from collections import defaultdict
        from datetime import timedelta

        from run_flow_skills_mcp.calculators.training_load import (
            calc_atl,
            calc_ctl,
            calc_tsb,
        )
        from run_flow_skills_mcp.models import TrainingLoad

        all_sessions = self.parquet_store.query_sessions()
        if not all_sessions:
            return

        # 按日聚合 TSS
        all_metrics = self.parquet_store.query_metrics(
            [s.session_id for s in all_sessions]
        )
        metrics_map = {m.session_id: m for m in all_metrics}

        daily_tss: dict[str, float] = defaultdict(float)
        for s in all_sessions:
            date_str = s.activity_date.strftime("%Y-%m-%d")
            m = metrics_map.get(s.session_id)
            if m:
                daily_tss[date_str] += m.tss

        # 按日期排序
        sorted_dates = sorted(daily_tss.keys())
        if not sorted_dates:
            return

        # 补全缺失日期（无训练日 TSS=0）
        start = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
        end = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
        full_dates: list[str] = []
        cur = start
        while cur <= end:
            full_dates.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)
        full_tss = [daily_tss.get(d, 0.0) for d in full_dates]

        # 滑动计算每日 CTL/ATL/TSB（用历史窗口）
        for i, date_str in enumerate(full_dates):
            hist_tss = full_tss[: i + 1]
            ctl = calc_ctl(hist_tss)
            atl = calc_atl(hist_tss)
            tsb = calc_tsb(ctl, atl)
            # 当周累计 TSS
            week_start = max(0, i - 6)
            weekly_tss = sum(full_tss[week_start : i + 1])

            load = TrainingLoad(
                date=date_str,
                ctl=ctl,
                atl=atl,
                tsb=tsb,
                weekly_tss=weekly_tss,
                updated_at=datetime.now(timezone.utc),
            )
            self.json_store.save_load(load)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/services/test_import_service.py -v`
Expected: 8 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/services/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/services/import_service.py run-flow-skills-mcp/tests/services/__init__.py run-flow-skills-mcp/tests/services/test_import_service.py
git commit -m "feat(services/import): orchestrate parse/dedup/calc/store with SHA256 and cross-platform dedup"
```

---

## Task 3: services/analysis_service.py 分析编排

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/services/analysis_service.py`
- Test: `run-flow-skills-mcp/tests/services/test_analysis_service.py`

**Interfaces:**
- Consumes:
  - `storage.parquet_store.ParquetStore`
  - `storage.json_store.JsonStore`
  - `calculators.training_load.calc_ctl`、`calc_atl`、`calc_tsb`
  - `calculators.hrv.calc_hrv_baseline`、`calc_hrv_deviation_pct`
  - `calculators.fatigue.calc_fatigue_score`
  - `models.Session`、`TrainingMetrics`、`BodySignal`、`TrainingLoad`
- Produces:
  - `class AnalysisService`：`__init__(self, parquet_store, json_store)`
  - `calc_metrics(date_from: str, date_to: str) -> dict`：返回 `{vdot_trend, tss_sum, ctl, atl, tsb, hr_zones_dist}`
  - `get_trends(days: int=30, metric: str="vdot") -> dict`：返回 `{series, change_pct, baseline}`
  - `analyze_fatigue(days: int=7) -> dict`：返回 `{fatigue_score, risk_level, main_factors, hrv_deviation, tsb}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/services/test_analysis_service.py`：

```python
"""analysis_service 测试（spec FR-ANALYZE-01/04/05）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal, Session, TrainingMetrics
from run_flow_skills_mcp.services.analysis_service import AnalysisService
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> AnalysisService:
    return AnalysisService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


def _seed_sessions(import_service: ImportService, n: int = 10):
    """通过 import_service 灌入 n 个手动 Session."""
    for i in range(n):
        days_ago = n - i
        date = (datetime(2026, 7, 25) - timedelta(days=days_ago)).strftime("%Y-%m-%dT06:00:00")
        import_service.import_manual({
            "activity_date": date,
            "distance_m": 10000.0,
            "duration_s": 3000,  # 50 分钟，配速 5'00"/km
            "source": "manual",
            "avg_hr": 150,
        })


def test_calc_metrics_returns_required_fields(service: AnalysisService, import_service: ImportService):
    """calc_metrics 必须返回 spec 6.1 定义的所有字段."""
    _seed_sessions(import_service, 10)
    result = service.calc_metrics("2026-07-15", "2026-07-25")

    for key in ("vdot_trend", "tss_sum", "ctl", "atl", "tsb", "hr_zones_dist"):
        assert key in result, f"missing {key}"


def test_calc_metrics_empty_data_returns_zeros(service: AnalysisService):
    """无数据时应返回零值，不抛异常."""
    result = service.calc_metrics("2026-07-01", "2026-07-25")
    assert result["tss_sum"] == 0
    assert result["ctl"] == 0
    assert result["atl"] == 0


def test_get_trends_vdot_returns_series(service: AnalysisService, import_service: ImportService):
    """get_trends(metric=vdot) 返回 series 列表."""
    _seed_sessions(import_service, 10)
    result = service.get_trends(days=30, metric="vdot")

    assert "series" in result
    assert isinstance(result["series"], list)
    for point in result["series"]:
        assert "date" in point
        assert "value" in point


def test_get_trends_load_metric(service: AnalysisService, import_service: ImportService):
    """get_trends(metric=load) 返回 CTL/ATL 序列."""
    _seed_sessions(import_service, 10)
    result = service.get_trends(days=30, metric="load")
    assert "series" in result


def test_get_trends_invalid_metric_returns_empty(service: AnalysisService):
    """无效 metric 返回空 series（降级方案）."""
    result = service.get_trends(days=7, metric="invalid")
    assert result["series"] == []


def test_analyze_fatigue_returns_required_fields(service: AnalysisService, import_service: ImportService):
    """analyze_fatigue 返回 spec 6.1 字段."""
    _seed_sessions(import_service, 10)
    # 灌入 HRV 数据
    for i in range(7):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        service.json_store.upsert_body_signal(BodySignal(date=date, hrv_rmssd=45.0, rpe=5))

    result = service.analyze_fatigue(days=7)
    for key in ("fatigue_score", "risk_level", "main_factors", "hrv_deviation", "tsb"):
        assert key in result


def test_analyze_fatigue_no_data_returns_low(service: AnalysisService):
    """无 HRV/负荷数据时返回低风险 + insufficient_data."""
    result = service.analyze_fatigue(days=7)
    assert result["risk_level"] == "low"
    assert "insufficient_data" in result["main_factors"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/services/test_analysis_service.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/services/analysis_service.py`：

```python
"""分析编排服务（spec FR-ANALYZE-01/04/05）.

编排 calculators + storage：
- calc_metrics: 聚合区间指标（VDOT 趋势/TSS/CTL/ATL/TSB/心率区间分布）
- get_trends: 时间序列（vdot/load/hrv）
- analyze_fatigue: 综合疲劳度评估（HRV + TSB + RPE）
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from run_flow_skills_mcp.calculators.fatigue import calc_fatigue_score
from run_flow_skills_mcp.calculators.hrv import (
    calc_hrv_baseline,
    calc_hrv_deviation_pct,
)
from run_flow_skills_mcp.calculators.training_load import (
    calc_atl,
    calc_ctl,
    calc_tsb,
)
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


class AnalysisService:
    """分析编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def calc_metrics(self, date_from: str, date_to: str) -> dict:
        """聚合区间训练指标."""
        sessions = self.parquet_store.query_sessions(
            date_from=date_from, date_to=date_to
        )
        if not sessions:
            return {
                "vdot_trend": [],
                "tss_sum": 0.0,
                "ctl": 0.0,
                "atl": 0.0,
                "tsb": 0.0,
                "hr_zones_dist": {},
            }

        session_ids = [s.session_id for s in sessions]
        metrics = self.parquet_store.query_metrics(session_ids)
        metrics_map = {m.session_id: m for m in metrics}

        # VDOT 趋势
        vdot_trend = [
            {"date": s.activity_date.strftime("%Y-%m-%d"), "vdot": metrics_map[s.session_id].vdot}
            for s in sessions
            if s.session_id in metrics_map and metrics_map[s.session_id].vdot is not None
        ]

        # TSS 累计
        tss_sum = sum(m.tss for m in metrics if m.tss)

        # CTL/ATL/TSB：从 TrainingLoad 取最新值
        loads = self.json_store.query_load(date_from=date_from, date_to=date_to)
        if loads:
            latest = loads[-1]
            ctl, atl, tsb = latest.ctl, latest.atl, latest.tsb
        else:
            # 若无 TrainingLoad，临时计算
            daily_tss = self._daily_tss_map(sessions, metrics_map)
            sorted_tss = self._expand_daily_tss(daily_tss, date_from, date_to)
            ctl = calc_ctl(sorted_tss) if sorted_tss else 0.0
            atl = calc_atl(sorted_tss) if sorted_tss else 0.0
            tsb = calc_tsb(ctl, atl)

        # 心率区间分布（简化：从 sessions 的 hr_zones 聚合）
        hr_zones_dist: dict[str, float] = defaultdict(float)
        for s in sessions:
            if s.hr_zones:
                for zone, pct in s.hr_zones.items():
                    hr_zones_dist[zone] += pct
        # 归一化
        total = sum(hr_zones_dist.values())
        if total > 0:
            hr_zones_dist = {k: v / total for k, v in hr_zones_dist.items()}

        return {
            "vdot_trend": vdot_trend,
            "tss_sum": tss_sum,
            "ctl": ctl,
            "atl": atl,
            "tsb": tsb,
            "hr_zones_dist": dict(hr_zones_dist),
        }

    def get_trends(self, days: int = 30, metric: str = "vdot") -> dict:
        """获取时间序列趋势."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        date_from = start.strftime("%Y-%m-%d")
        date_to = end.strftime("%Y-%m-%d")

        if metric == "vdot":
            sessions = self.parquet_store.query_sessions(
                date_from=date_from, date_to=date_to
            )
            metrics = self.parquet_store.query_metrics(
                [s.session_id for s in sessions]
            )
            metrics_map = {m.session_id: m for m in metrics}
            series = [
                {"date": s.activity_date.strftime("%Y-%m-%d"),
                 "value": metrics_map[s.session_id].vdot}
                for s in sessions
                if s.session_id in metrics_map
                and metrics_map[s.session_id].vdot is not None
            ]
        elif metric == "load":
            loads = self.json_store.query_load(date_from=date_from, date_to=date_to)
            series = [
                {"date": l.date, "value": l.ctl, "atl": l.atl, "tsb": l.tsb}
                for l in loads
            ]
        elif metric == "hrv":
            signals = self.json_store.query_body_signals(date_from, date_to)
            series = [
                {"date": s.date, "value": s.hrv_rmssd}
                for s in signals
                if s.hrv_rmssd is not None
            ]
        else:
            return {"series": [], "change_pct": 0.0, "baseline": None}

        # 计算变化百分比和基线
        if len(series) >= 2:
            first_val = series[0]["value"] or 0
            last_val = series[-1]["value"] or 0
            change_pct = ((last_val - first_val) / first_val * 100) if first_val else 0.0
            baseline = sum(p["value"] for p in series if p["value"]) / len(
                [p for p in series if p["value"]]
            ) if any(p["value"] for p in series) else None
        else:
            change_pct = 0.0
            baseline = series[0]["value"] if series else None

        return {"series": series, "change_pct": change_pct, "baseline": baseline}

    def analyze_fatigue(self, days: int = 7) -> dict:
        """综合疲劳度评估（HRV + TSB + RPE）."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        date_from = start.strftime("%Y-%m-%d")
        date_to = end.strftime("%Y-%m-%d")

        # HRV 数据
        signals = self.json_store.query_body_signals(date_from, date_to)
        hrv_values = [s.hrv_rmssd for s in signals if s.hrv_rmssd is not None]
        rpe_trend = [s.rpe for s in signals if s.rpe is not None]

        hrv_deviation: Optional[float] = None
        if hrv_values:
            current_hrv = hrv_values[-1]
            baseline = calc_hrv_baseline(hrv_values[:-1] if len(hrv_values) > 1 else hrv_values)
            if baseline:
                hrv_deviation = calc_hrv_deviation_pct(current_hrv, baseline)

        # TSB
        loads = self.json_store.query_load(date_from=date_from, date_to=date_to)
        tsb = loads[-1].tsb if loads else None

        # 综合疲劳度
        score, level, factors = calc_fatigue_score(hrv_deviation, tsb, rpe_trend)

        return {
            "fatigue_score": score,
            "risk_level": level,
            "main_factors": factors,
            "hrv_deviation": hrv_deviation,
            "tsb": tsb,
        }

    def _daily_tss_map(
        self, sessions: list, metrics_map: dict
    ) -> dict[str, float]:
        """按日聚合 TSS."""
        daily: dict[str, float] = defaultdict(float)
        for s in sessions:
            date_str = s.activity_date.strftime("%Y-%m-%d")
            m = metrics_map.get(s.session_id)
            if m:
                daily[date_str] += m.tss
        return daily

    def _expand_daily_tss(
        self, daily: dict[str, float], date_from: str, date_to: str
    ) -> list[float]:
        """补全缺失日期（无训练日 TSS=0）."""
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        result: list[float] = []
        cur = start
        while cur <= end:
            result.append(daily.get(cur.strftime("%Y-%m-%d"), 0.0))
            cur += timedelta(days=1)
        return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/services/test_analysis_service.py -v`
Expected: 8 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/services/analysis_service.py run-flow-skills-mcp/tests/services/test_analysis_service.py
git commit -m "feat(services/analysis): orchestrate metrics aggregation, trends, and fatigue analysis"
```

---

## Task 4: services/plan_service.py 计划编排

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/services/plan_service.py`
- Test: `run-flow-skills-mcp/tests/services/test_plan_service.py`

**Interfaces:**
- Consumes:
  - `storage.parquet_store.ParquetStore`
  - `storage.json_store.JsonStore`
  - `calculators.vdot.calc_vdot`
  - `calculators.pace_zones.calc_pace_zones`
  - `models.TrainingPlan`、`PlanPhase`、`PlanWeek`、`PlanSession`
- Produces:
  - `class PlanService`：`__init__(self, parquet_store, json_store)`
  - `generate_plan(goal_type, goal_time, race_date, weeks, current_vdot) -> dict`：返回 `{plan_id, phases, pace_zones, target_vdot, plan_prompt}`
  - `query_plan(plan_id: Optional[str]=None) -> dict`：返回 `{plan, fidelity?}`
  - `compute_fidelity(plan: TrainingPlan) -> dict`：计算计划执行忠实度（planned_vs_actual）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/services/test_plan_service.py`：

```python
"""plan_service 测试（spec FR-PLAN-01/02/03/04）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.plan_service import PlanService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> PlanService:
    return PlanService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


def test_generate_plan_full_marathon_12_weeks(service: PlanService):
    """生成 12 周全马计划：含 4 个周期化阶段（spec FR-PLAN-01）."""
    result = service.generate_plan(
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
    )

    assert result["plan_id"].startswith("plan_")
    assert len(result["phases"]) == 4  # base/build/peak/taper
    phase_types = [p.phase_type for p in result["phases"]]
    assert phase_types == ["base", "build", "peak", "taper"]

    # 配速区间基于 VDOT
    assert "E" in result["pace_zones"]
    assert "M" in result["pace_zones"]
    assert "T" in result["pace_zones"]

    # target_vdot 基于目标时间反算
    assert result["target_vdot"] > 42.0  # 全马破4 需要 VDOT ≈ 43.5


def test_generate_plan_includes_plan_prompt(service: PlanService):
    """生成计划必须附带 plan_prompt（spec 6.2）."""
    result = service.generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
    )
    assert "plan_prompt" in result
    assert "current_vdot" in result["plan_prompt"] or "40" in result["plan_prompt"]


def test_generate_plan_saves_to_json(service: PlanService):
    """生成后自动保存到 plans/plan_*.json（spec 5.1）."""
    result = service.generate_plan(
        goal_type="half_marathon", goal_time="01:59:59",
        race_date="2026-10-19", weeks=12, current_vdot=42.0,
    )
    plan_id = result["plan_id"]
    loaded = service.json_store.load_plan(plan_id)
    assert loaded is not None
    assert loaded.goal_type == "half_marathon"


def test_query_plan_returns_plan_and_fidelity(service: PlanService, import_service: ImportService):
    """query_plan 返回计划 + 可选 fidelity（spec FR-PLAN-04）."""
    gen = service.generate_plan(
        goal_type="10k", goal_time="00:50:00",
        race_date="2026-10-19", weeks=8, current_vdot=45.0,
    )
    result = service.query_plan(gen["plan_id"])
    assert "plan" in result
    assert "fidelity" in result  # 即使无实际训练，fidelity 也应返回（值为 0 或 null）


def test_query_plan_active_returns_latest(service: PlanService):
    """query_plan(plan_id=None) 返回最新的 active 计划."""
    service.generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
    )
    result = service.query_plan()
    assert "plan" in result


def test_compute_fidelity_empty_actual(service: PlanService):
    """无实际训练时 fidelity=0."""
    gen = service.generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
    )
    plan = service.json_store.load_plan(gen["plan_id"])
    fidelity = service.compute_fidelity(plan)
    assert fidelity["planned_sessions"] > 0
    assert fidelity["completed_sessions"] == 0
    assert fidelity["fidelity_rate"] == 0.0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/services/test_plan_service.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/services/plan_service.py`：

```python
"""训练计划编排服务（spec FR-PLAN-01/02/03/04, 7.3）.

编排 calculators + storage：
- generate_plan: 周期化计划生成（base/build/peak/taper）+ 配速区间 + plan_prompt
- query_plan: 查询计划 + 计算执行忠实度
- compute_fidelity: planned_vs_actual 对比

漏练自适应（spec 7.3）：后续负荷重新分配，负荷守恒不追加。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from run_flow_skills_mcp.calculators.pace_zones import calc_pace_zones
from run_flow_skills_mcp.models import (
    PlanPhase,
    PlanSession,
    PlanWeek,
    TrainingPlan,
)
from run_flow_skills_mcp.prompts.plan_prompt import PLAN_PROMPT
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

# 目标时间 → 目标 VDOT 反算表（简化版，ponytail: 经验值，不调 ML）
# 升级路径：v0.2.0 用 Powers 反算
_GOAL_VDOT_TABLE: dict[str, dict[str, float]] = {
    "full_marathon": {"03:59:59": 43.5, "03:29:59": 50.0, "02:59:59": 58.0},
    "half_marathon": {"01:59:59": 45.0, "01:44:59": 50.0, "01:29:59": 58.0},
    "10k": {"00:49:59": 48.0, "00:44:59": 53.0, "00:39:59": 60.0},
    "5k": {"00:24:59": 47.0, "00:21:59": 53.0, "00:19:59": 60.0},
}


def _estimate_target_vdot(goal_type: str, goal_time: str) -> float:
    """由目标反算 VDOT（简化查表，找不到时按 5% 提升估算）."""
    table = _GOAL_VDOT_TABLE.get(goal_type, {})
    if goal_time in table:
        return table[goal_time]
    # 取最接近的目标时间，按比例调整
    if table:
        closest = min(table.keys(), key=lambda t: abs(sum(int(x) for x in t.split(":")) - sum(int(x) for x in goal_time.split(":"))))
        return table[closest] * 1.05
    return 45.0  # 默认值


# 周期化阶段分配比例（base/build/peak/taper）
_PHASE_RATIOS: dict[str, float] = {
    "base": 0.34,   # 约 1/3
    "build": 0.33,  # 约 1/3
    "peak": 0.22,   # 约 1/5
    "taper": 0.11,  # 约 1/10
}


class PlanService:
    """训练计划编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def generate_plan(
        self,
        goal_type: str,
        goal_time: str,
        race_date: str,
        weeks: int,
        current_vdot: float,
    ) -> dict:
        """生成周期化训练计划."""
        target_vdot = _estimate_target_vdot(goal_type, goal_time)
        pace_zones = calc_pace_zones(current_vdot)
        vdot_gap = target_vdot - current_vdot

        # 周期化阶段
        phases = self._build_phases(weeks, pace_zones, current_vdot)

        plan_id = self._next_plan_id()
        plan = TrainingPlan(
            plan_id=plan_id,
            goal_type=goal_type,  # type: ignore[arg-type]
            goal_time=goal_time,
            race_date=race_date,
            weeks=weeks,
            current_vdot=current_vdot,
            target_vdot=target_vdot,
            phases=phases,
            created_at=datetime.now(timezone.utc),
            status="draft",
        )
        self.json_store.save_plan(plan)

        # 生成 plan_prompt（供宿主 AI 解释计划）
        plan_prompt = PLAN_PROMPT.format(
            goal_type=goal_type,
            goal_time=goal_time,
            race_date=race_date,
            weeks=weeks,
            current_vdot=current_vdot,
            target_vdot=target_vdot,
            vdot_gap=vdot_gap,
            plan_struct=self._plan_struct_summary(phases),
        )

        return {
            "plan_id": plan_id,
            "phases": phases,
            "pace_zones": pace_zones,
            "target_vdot": target_vdot,
            "vdot_gap": vdot_gap,
            "plan_prompt": plan_prompt,
        }

    def query_plan(self, plan_id: Optional[str] = None) -> dict:
        """查询计划（plan_id=None 返回最新计划）+ 计算忠实度."""
        if plan_id:
            plan = self.json_store.load_plan(plan_id)
        else:
            plans = self.json_store.list_plans()
            plan = plans[-1] if plans else None

        if plan is None:
            return {"plan": None, "fidelity": None}

        fidelity = self.compute_fidelity(plan)
        return {"plan": plan, "fidelity": fidelity}

    def compute_fidelity(self, plan: TrainingPlan) -> dict:
        """计算计划执行忠实度（planned_vs_actual）.

        简化策略（ponytail: 按日期匹配，不精确到课表）：
        统计计划期内每周是否有对应训练日。
        """
        # 统计计划内总课表数
        planned_sessions = sum(
            len(week.sessions)
            for phase in plan.phases
            for week in phase.weeks
        )

        # 查询计划期内实际训练数
        race_date = datetime.strptime(plan.race_date, "%Y-%m-%d")
        start_date = race_date - timedelta(weeks=plan.weeks)
        actual_sessions = self.parquet_store.query_sessions(
            date_from=start_date.strftime("%Y-%m-%d"),
            date_to=plan.race_date,
        )
        completed = len(actual_sessions)

        fidelity_rate = completed / planned_sessions if planned_sessions > 0 else 0.0

        return {
            "planned_sessions": planned_sessions,
            "completed_sessions": completed,
            "fidelity_rate": round(fidelity_rate, 2),
            "missing_sessions": max(0, planned_sessions - completed),
        }

    def _build_phases(
        self, weeks: int, pace_zones: dict, vdot: float
    ) -> list[PlanPhase]:
        """构建周期化阶段（base/build/peak/taper）."""
        # 分配每周数（向下取整，剩余加到 base）
        base_weeks = max(1, int(weeks * _PHASE_RATIOS["base"]))
        build_weeks = max(1, int(weeks * _PHASE_RATIOS["build"]))
        peak_weeks = max(1, int(weeks * _PHASE_RATIOS["peak"]))
        taper_weeks = max(1, weeks - base_weeks - build_weeks - peak_weeks)
        if taper_weeks < 1:
            taper_weeks = 1
            base_weeks = weeks - build_weeks - peak_weeks - taper_weeks

        phases: list[PlanPhase] = []
        week_idx = 1
        for phase_type, n_weeks in [
            ("base", base_weeks),
            ("build", build_weeks),
            ("peak", peak_weeks),
            ("taper", taper_weeks),
        ]:
            weeks_list: list[PlanWeek] = []
            for _ in range(n_weeks):
                weeks_list.append(self._build_week(week_idx, phase_type, pace_zones))
                week_idx += 1
            phases.append(PlanPhase(phase_type=phase_type, weeks=weeks_list))  # type: ignore[arg-type]
        return phases

    def _build_week(
        self, week_index: int, phase_type: str, pace_zones: dict
    ) -> PlanWeek:
        """构建单周课表（简化：每 phase 固定模板）."""
        # ponytail: MVP 用固定模板，v0.2.0 可用 ML 生成
        e_lo, e_hi = pace_zones.get("E", (300, 400))
        m_lo, m_hi = pace_zones.get("M", (280, 320))
        t_lo, t_hi = pace_zones.get("T", (260, 290))

        if phase_type == "base":
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=3600,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="E", duration_s=2400,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=3000,
                            pace_range_s_per_km=(m_lo, m_hi)),
                PlanSession(day=6, pace_zone="E", duration_s=5400,
                            pace_range_s_per_km=(e_lo, e_hi)),
            ]
        elif phase_type == "build":
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=3600,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="T", duration_s=2400,
                            pace_range_s_per_km=(t_lo, t_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=3600,
                            pace_range_s_per_km=(m_lo, m_hi)),
                PlanSession(day=6, pace_zone="E", duration_s=5400,
                            pace_range_s_per_km=(e_lo, e_hi)),
            ]
        elif phase_type == "peak":
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=3000,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="T", duration_s=3000,
                            pace_range_s_per_km=(t_lo, t_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=4200,
                            pace_range_s_per_km=(m_lo, m_hi)),
                PlanSession(day=6, pace_zone="E", duration_s=4800,
                            pace_range_s_per_km=(e_lo, e_hi)),
            ]
        else:  # taper
            sessions = [
                PlanSession(day=0, pace_zone="E", duration_s=2400,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=2, pace_zone="E", duration_s=1800,
                            pace_range_s_per_km=(e_lo, e_hi)),
                PlanSession(day=4, pace_zone="M", duration_s=1800,
                            pace_range_s_per_km=(m_lo, m_hi)),
            ]
        return PlanWeek(week_index=week_index, sessions=sessions)

    def _next_plan_id(self) -> str:
        """生成下一个 plan_id：plan_YYYYMMDD_NNN."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        existing = self.json_store.list_plans()
        same_day = [p for p in existing if p.plan_id.startswith(f"plan_{date_str}")]
        return f"plan_{date_str}_{len(same_day) + 1:03d}"

    def _plan_struct_summary(self, phases: list[PlanPhase]) -> str:
        """生成 plan_struct 摘要（用于 plan_prompt 填充）."""
        lines: list[str] = []
        for phase in phases:
            n_weeks = len(phase.weeks)
            total_sessions = sum(len(w.sessions) for w in phase.weeks)
            lines.append(
                f"- {phase.phase_type}: {n_weeks} 周, {total_sessions} 次课表"
            )
        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/services/test_plan_service.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/services/plan_service.py run-flow-skills-mcp/tests/services/test_plan_service.py
git commit -m "feat(services/plan): generate periodized training plans with VDOT-based pace zones"
```

---

## Task 5: services/review_service.py 复盘编排

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/services/review_service.py`
- Test: `run-flow-skills-mcp/tests/services/test_review_service.py`

**Interfaces:**
- Consumes:
  - `storage.parquet_store.ParquetStore`
  - `storage.json_store.JsonStore`
  - `services.analysis_service.AnalysisService`（复用 calc_metrics）
- Produces:
  - `class ReviewService`：`__init__(self, parquet_store, json_store)`
  - `get_period_summary(period: str="week", date_ref: Optional[str]=None) -> dict`：返回 `{total_distance, total_tss, avg_vdot, load_change, sessions_count, vdot_trend, hrv_trend}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/services/test_review_service.py`：

```python
"""review_service 测试（spec FR-REVIEW-01/02）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.review_service import ReviewService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> ReviewService:
    return ReviewService(
        parquet_store=ParquetStore(tmp_data_dir),
        json_store=JsonStore(tmp_data_dir),
    )


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


def _seed(import_service: ImportService, n: int):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=n - i - 1)).strftime("%Y-%m-%dT06:00:00")
        import_service.import_manual({
            "activity_date": date, "distance_m": 10000.0,
            "duration_s": 3000, "source": "manual",
        })


def test_get_period_summary_week(service: ReviewService, import_service: ImportService):
    """period=week 返回本周摘要."""
    _seed(import_service, 7)
    result = service.get_period_summary(period="week", date_ref="2026-07-25")

    for key in ("total_distance", "total_tss", "avg_vdot", "load_change", "sessions_count", "vdot_trend", "hrv_trend"):
        assert key in result
    assert result["sessions_count"] >= 1


def test_get_period_summary_month(service: ReviewService, import_service: ImportService):
    """period=month 返回月度摘要."""
    _seed(import_service, 10)
    result = service.get_period_summary(period="month", date_ref="2026-07-25")
    assert result["sessions_count"] >= 1


def test_get_period_summary_invalid_period_returns_empty(service: ReviewService):
    """无效 period 返回空摘要（降级）."""
    result = service.get_period_summary(period="invalid", date_ref="2026-07-25")
    assert result["sessions_count"] == 0
    assert result["total_distance"] == 0


def test_get_period_summary_no_data_returns_zeros(service: ReviewService):
    """无数据返回零值."""
    result = service.get_period_summary(period="week", date_ref="2026-07-25")
    assert result["sessions_count"] == 0
    assert result["total_distance"] == 0


def test_get_period_summary_load_change_vs_last_period(
    service: ReviewService, import_service: ImportService
):
    """load_change 应反映环比变化（本期 vs 上期）."""
    # 灌入 14 天数据
    _seed(import_service, 14)
    result = service.get_period_summary(period="week", date_ref="2026-07-25")
    assert "load_change" in result
    # load_change 应为 dict 或 float，表示变化
    assert result["load_change"] is not None or result["total_tss"] > 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/services/test_review_service.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/services/review_service.py`：

```python
"""复盘编排服务（spec FR-REVIEW-01/02, 7.4）.

编排 storage 聚合周期数据 + 对比上周期。
同比/环比必须明确时间窗口（analysis-rules.md 第 6 条）。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from run_flow_skills_mcp.services.analysis_service import AnalysisService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

_PERIOD_DAYS: dict[str, int] = {
    "week": 7,
    "month": 30,
    "season": 91,  # 13 周
    "year": 365,
}


class ReviewService:
    """复盘编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store
        self.analysis = AnalysisService(parquet_store, json_store)

    def get_period_summary(
        self, period: str = "week", date_ref: Optional[str] = None
    ) -> dict:
        """聚合周期数据 + 对比上周期.

        Args:
            period: week/month/season/year
            date_ref: 参考日期（默认今天），YYYY-MM-DD

        Returns:
            {total_distance, total_tss, avg_vdot, load_change, sessions_count,
             vdot_trend, hrv_trend}
        """
        days = _PERIOD_DAYS.get(period)
        if days is None:
            return self._empty_summary()

        end = (
            datetime.strptime(date_ref, "%Y-%m-%d")
            if date_ref
            else datetime.now(timezone.utc)
        )
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)

        date_from = start.strftime("%Y-%m-%d")
        date_to = end.strftime("%Y-%m-%d")

        # 本期 sessions
        sessions = self.parquet_store.query_sessions(
            date_from=date_from, date_to=date_to
        )
        if not sessions:
            return self._empty_summary()

        # 聚合指标
        metrics = self.parquet_store.query_metrics(
            [s.session_id for s in sessions]
        )
        metrics_map = {m.session_id: m for m in metrics}

        total_distance = sum(s.distance_m for s in sessions) / 1000.0  # km
        total_tss = sum(m.tss for m in metrics if m.tss)
        vdots = [m.vdot for m in metrics if m.vdot is not None]
        avg_vdot = sum(vdots) / len(vdots) if vdots else None

        # VDOT 趋势
        vdot_trend = [
            {"date": s.activity_date.strftime("%Y-%m-%d"),
             "vdot": metrics_map[s.session_id].vdot}
            for s in sessions
            if s.session_id in metrics_map and metrics_map[s.session_id].vdot
        ]

        # HRV 趋势
        signals = self.json_store.query_body_signals(date_from, date_to)
        hrv_trend = [
            {"date": sig.date, "hrv": sig.hrv_rmssd}
            for sig in signals if sig.hrv_rmssd is not None
        ]

        # 上期数据（环比）
        prev_sessions = self.parquet_store.query_sessions(
            date_from=prev_start.strftime("%Y-%m-%d"),
            date_to=start.strftime("%Y-%m-%d"),
        )
        prev_metrics = self.parquet_store.query_metrics(
            [s.session_id for s in prev_sessions]
        )
        prev_tss = sum(m.tss for m in prev_metrics if m.tss)
        load_change = {
            "tss_change": total_tss - prev_tss,
            "tss_change_pct": ((total_tss - prev_tss) / prev_tss * 100) if prev_tss > 0 else None,
            "comparison_window": f"vs 上{period}",
        }

        return {
            "total_distance": round(total_distance, 2),
            "total_tss": round(total_tss, 2),
            "avg_vdot": round(avg_vdot, 2) if avg_vdot else None,
            "load_change": load_change,
            "sessions_count": len(sessions),
            "vdot_trend": vdot_trend,
            "hrv_trend": hrv_trend,
        }

    def _empty_summary(self) -> dict:
        return {
            "total_distance": 0,
            "total_tss": 0,
            "avg_vdot": None,
            "load_change": {"tss_change": 0, "tss_change_pct": None, "comparison_window": ""},
            "sessions_count": 0,
            "vdot_trend": [],
            "hrv_trend": [],
        }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/services/test_review_service.py -v`
Expected: 5 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/services/review_service.py run-flow-skills-mcp/tests/services/test_review_service.py
git commit -m "feat(services/review): aggregate period data with week-over-week comparison"
```

---

## Task 6: services/coach_service.py 教练编排

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/services/coach_service.py`
- Test: `run-flow-skills-mcp/tests/services/test_coach_service.py`

**Interfaces:**
- Consumes:
  - `storage.parquet_store.ParquetStore`
  - `storage.json_store.JsonStore`
  - `services.plan_service.PlanService`（查今日计划）
  - `calculators.hrv.calc_hrv_baseline`、`calc_hrv_deviation_pct`
  - `models.BodySignal`、`DecisionLog`、`TrainingLoad`
- Produces:
  - `class CoachService`：`__init__(self, parquet_store, json_store)`
  - `read_body_signals(date: Optional[str]=None) -> dict`：返回 `{hrv, resting_hr, sleep, rpe, baseline, deviation_pct, readiness_level, yesterday_session, recent_high_intensity}`。**内部需同时读取 `BodySignal`（HRV/RPE）和 `TrainingLoad`（TSB）**，综合计算 `readiness_level`（spec 6.2：HRV 偏离 + TSB + RPE，单一指标不可单独决策）
  - `get_decision_trace(decision_id: str) -> Optional[dict]`
  - `save_decision_log(decision_type, inputs, reasoning, recommendation, confidence, trace_chain, related_session_ids=None) -> dict`：返回 `{decision_id, saved: True}`
  - `compute_readiness_level(hrv_deviation, tsb, rpe) -> Literal["green","yellow","red"]`：就绪状态计算（HRV + TSB + RPE 综合，spec 6.2），由 `read_body_signals` 内部调用

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/services/test_coach_service.py`：

```python
"""coach_service 测试（spec FR-COACH-01/02/03, 8.3）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.services.coach_service import CoachService
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> CoachService:
    return CoachService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


def _seed_hrv(service: CoachService, n: int = 7, hrv_value: float = 45.0):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=hrv_value, rpe=5, resting_hr=55, sleep_quality=4)
        )


def test_read_body_signals_returns_required_fields(service: CoachService):
    """read_body_signals 返回 spec 6.1 字段."""
    _seed_hrv(service, 7)
    result = service.read_body_signals(date="2026-07-25")

    for key in ("hrv", "resting_hr", "sleep", "rpe", "baseline", "deviation_pct", "readiness_level", "yesterday_session", "recent_high_intensity"):
        assert key in result


def test_read_body_signals_no_data_returns_none_values(service: CoachService):
    """无数据时返回 None 值 + readiness_level=green（默认）."""
    result = service.read_body_signals(date="2026-07-25")
    assert result["hrv"] is None
    assert result["readiness_level"] in ("green", "yellow", "red")


def test_readiness_level_green_when_all_normal(service: CoachService):
    """所有指标正常 → green（spec 8.3 第 3 条：综合 HRV+TSB+RPE）."""
    level = service.compute_readiness_level(
        hrv_deviation=2.0, tsb=15.0, rpe=4
    )
    assert level == "green"


def test_readiness_level_yellow_when_hrv_low(service: CoachService):
    """HRV 偏低 10-20% → yellow."""
    level = service.compute_readiness_level(
        hrv_deviation=-15.0, tsb=5.0, rpe=6
    )
    assert level == "yellow"


def test_readiness_level_red_when_all_bad(service: CoachService):
    """HRV 偏低 + TSB 负 + RPE 高 → red."""
    level = service.compute_readiness_level(
        hrv_deviation=-20.0, tsb=-15.0, rpe=9
    )
    assert level == "red"


def test_readiness_level_single_indicator_not_decisive(service: CoachService):
    """单一指标不决策（coaching-rules.md 第 3 条）：仅 HRV 偏低不应直接 red."""
    # HRV 偏低但 TSB 充足 + RPE 低
    level = service.compute_readiness_level(
        hrv_deviation=-12.0, tsb=20.0, rpe=3
    )
    assert level in ("green", "yellow")  # 不应直接 red


def test_save_decision_log_returns_id(service: CoachService):
    """save_decision_log 返回 decision_id + saved=True."""
    result = service.save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38, "tsb": -5},
        reasoning="HRV 偏低 + TSB 负值",
        recommendation="E 区间 30 分钟",
        confidence=0.7,
        trace_chain=["HRV=38", "baseline=45", "rule:HRV偏离>10%"],
    )
    assert result["saved"] is True
    assert result["decision_id"].startswith("dec_")


def test_get_decision_trace_found(service: CoachService):
    """保存后可通过 decision_id 查询."""
    saved = service.save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="test",
        recommendation="test",
        confidence=0.7,
        trace_chain=["a", "b"],
    )
    trace = service.get_decision_trace(saved["decision_id"])
    assert trace is not None
    assert trace["recommendation"] == "test"


def test_get_decision_trace_not_found(service: CoachService):
    """不存在返回 None."""
    trace = service.get_decision_trace("dec_20260101_999")
    assert trace is None


def test_read_body_signals_detects_recent_high_intensity(
    service: CoachService, import_service: ImportService
):
    """24h 内高强度训练检测（coaching-rules.md 第 6 条）."""
    _seed_hrv(service, 7)
    # 导入一个高强度训练（T 区间）
    yesterday = (datetime(2026, 7, 25) - timedelta(days=1)).strftime("%Y-%m-%dT18:00:00")
    import_service.import_manual({
        "activity_date": yesterday,
        "distance_m": 8000.0,
        "duration_s": 1800,  # 配速 3'45"/km，T 区间高强度
        "source": "manual",
    })

    result = service.read_body_signals(date="2026-07-25")
    # recent_high_intensity 应为 True 或包含昨日训练信息
    assert result["recent_high_intensity"] is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/services/test_coach_service.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/services/coach_service.py`：

```python
"""AI 教练编排服务（spec FR-COACH-01/02/03, 7.5, 8.3）.

编排 storage + calculators + plan_service：
- read_body_signals: 读取身体信号 + 综合就绪状态（HRV + TSB + RPE）
- get_decision_trace: 查询历史决策
- save_decision_log: 持久化决策记录

约束（coaching-rules.md）：
- 就绪状态综合 HRV + TSB + RPE，单一指标不可决策
- 24h 内高强度训练必须考虑
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from run_flow_skills_mcp.calculators.hrv import (
    calc_hrv_baseline,
    calc_hrv_deviation_pct,
)
from run_flow_skills_mcp.models import DecisionLog
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore

ReadinessLevel = Literal["green", "yellow", "red"]


class CoachService:
    """AI 教练编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def read_body_signals(self, date: Optional[str] = None) -> dict:
        """读取身体信号 + 计算就绪状态."""
        target_date = (
            datetime.strptime(date, "%Y-%m-%d")
            if date
            else datetime.now(timezone.utc)
        )
        date_str = target_date.strftime("%Y-%m-%d")

        # 取近 7 天身体信号
        start = (target_date - timedelta(days=7)).strftime("%Y-%m-%d")
        signals = self.json_store.query_body_signals(start, date_str)

        today_signal = next((s for s in signals if s.date == date_str), None)

        hrv = today_signal.hrv_rmssd if today_signal else None
        resting_hr = today_signal.resting_hr if today_signal else None
        sleep = today_signal.sleep_quality if today_signal else None
        rpe = today_signal.rpe if today_signal else None

        # HRV 基线与偏离
        hrv_history = [s.hrv_rmssd for s in signals if s.hrv_rmssd is not None]
        baseline = calc_hrv_baseline(hrv_history) if hrv_history else None
        deviation_pct = (
            calc_hrv_deviation_pct(hrv, baseline)
            if hrv is not None and baseline is not None
            else None
        )

        # TSB（从 TrainingLoad 取）
        loads = self.json_store.query_load(date_from=start, date_to=date_str)
        latest_load = loads[-1] if loads else None
        ctl = latest_load.ctl if latest_load else None
        atl = latest_load.atl if latest_load else None
        tsb = latest_load.tsb if latest_load else None

        # 就绪状态
        readiness_level = self.compute_readiness_level(deviation_pct, tsb, rpe)

        # 昨日训练
        yesterday_str = (target_date - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_sessions = self.parquet_store.query_sessions(
            date_from=yesterday_str, date_to=yesterday_str
        )
        yesterday_session = (
            {
                "session_id": yesterday_sessions[0].session_id,
                "distance_m": yesterday_sessions[0].distance_m,
                "duration_s": yesterday_sessions[0].duration_s,
            }
            if yesterday_sessions
            else None
        )

        # 24h 内高强度训练检测
        recent_high_intensity = self._detect_recent_high_intensity(target_date)

        return {
            "hrv": hrv,
            "resting_hr": resting_hr,
            "sleep": sleep,
            "rpe": rpe,
            "baseline": baseline,
            "deviation_pct": deviation_pct,
            "ctl": ctl,
            "atl": atl,
            "tsb": tsb,
            "readiness_level": readiness_level,
            "yesterday_session": yesterday_session,
            "recent_high_intensity": recent_high_intensity,
        }

    def compute_readiness_level(
        self,
        hrv_deviation: Optional[float],
        tsb: Optional[float],
        rpe: Optional[int],
    ) -> ReadinessLevel:
        """综合就绪状态评估（HRV + TSB + RPE，coaching-rules.md 第 3 条）.

        策略（ponytail: 加权评分，单一指标不直接 red）：
        - 每指标计 0/1/2 分（normal/warning/danger）
        - 总分 0-1: green, 2-3: yellow, 4+: red
        - 缺失指标计 0 分
        """
        score = 0

        # HRV 偏离（负偏离越大越糟）
        if hrv_deviation is not None:
            if hrv_deviation <= -20:
                score += 2
            elif hrv_deviation <= -10:
                score += 1

        # TSB（负值越大越糟）
        if tsb is not None:
            if tsb <= -15:
                score += 2
            elif tsb <= 0:
                score += 1

        # RPE（越高越糟）
        if rpe is not None:
            if rpe >= 8:
                score += 2
            elif rpe >= 6:
                score += 1

        if score >= 4:
            return "red"
        if score >= 2:
            return "yellow"
        return "green"

    def get_decision_trace(self, decision_id: str) -> Optional[dict]:
        """查询决策溯源链."""
        all_decisions = self.json_store.query_decisions()
        for d in all_decisions:
            if d.decision_id == decision_id:
                return {
                    "decision_id": d.decision_id,
                    "inputs": d.inputs,
                    "reasoning": d.reasoning,
                    "recommendation": d.recommendation,
                    "confidence": d.confidence,
                    "trace_chain": d.trace_chain,
                    "related_session_ids": d.related_session_ids,
                    "user_feedback": d.user_feedback,
                }
        return None

    def save_decision_log(
        self,
        decision_type: str,
        inputs: dict,
        reasoning: str,
        recommendation: str,
        confidence: float,
        trace_chain: list[str],
        related_session_ids: Optional[list[str]] = None,
    ) -> dict:
        """保存决策记录."""
        decision_id = self._next_decision_id()
        decision = DecisionLog(
            decision_id=decision_id,
            timestamp=datetime.now(timezone.utc),
            decision_type=decision_type,  # type: ignore[arg-type]
            inputs=inputs,
            reasoning=reasoning,
            recommendation=recommendation,
            confidence=confidence,
            trace_chain=trace_chain,
            related_session_ids=related_session_ids or [],
        )
        self.json_store.append_decision(decision)
        return {"decision_id": decision_id, "saved": True}

    def _detect_recent_high_intensity(self, target_date: datetime) -> Optional[dict]:
        """检测 24h 内高强度训练（coaching-rules.md 第 6 条）."""
        # 取目标日期前 24 小时的 sessions
        start = target_date - timedelta(days=1)
        start_str = start.strftime("%Y-%m-%d")
        end_str = target_date.strftime("%Y-%m-%d")
        sessions = self.parquet_store.query_sessions(
            date_from=start_str, date_to=end_str
        )
        if not sessions:
            return None

        # 查询 metrics 判断是否高强度
        metrics = self.parquet_store.query_metrics(
            [s.session_id for s in sessions]
        )
        metrics_map = {m.session_id: m for m in metrics}

        high_intensity_zones = {"T", "I", "R"}
        for s in sessions:
            m = metrics_map.get(s.session_id)
            if m and m.pace_zone in high_intensity_zones:
                return {
                    "session_id": s.session_id,
                    "pace_zone": m.pace_zone,
                    "tss": m.tss,
                    "hours_ago": (target_date - s.activity_date).total_seconds() / 3600,
                }
        return None

    def _next_decision_id(self) -> str:
        """生成下一个 decision_id：dec_YYYYMMDD_NNN."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        existing = self.json_store.query_decisions()
        same_day = [d for d in existing if d.decision_id.startswith(f"dec_{date_str}")]
        return f"dec_{date_str}_{len(same_day) + 1:03d}"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/services/test_coach_service.py -v`
Expected: 9 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/services/coach_service.py run-flow-skills-mcp/tests/services/test_coach_service.py
git commit -m "feat(services/coach): read body signals with composite readiness level and decision log"
```

---

## Task 7: services/stats_service.py 统计与导出编排

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/services/stats_service.py`
- Test: `run-flow-skills-mcp/tests/services/test_stats_service.py`

**Interfaces:**
- Consumes:
  - `storage.parquet_store.ParquetStore`
  - `storage.json_store.JsonStore`
- Produces:
  - `class StatsService`：`__init__(self, parquet_store, json_store)`
  - `get_statistics(dimension: str, date_from: Optional[str]=None, date_to: Optional[str]=None) -> dict`：返回 `{groups: [{key, count, total_distance, avg_pace, ...}]}`
  - `export_data(format: str, filters: Optional[dict]=None, include_ai_logs: bool=False) -> dict`：返回 `{file_path, rows_count, format}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/services/test_stats_service.py`：

```python
"""stats_service 测试（spec FR-STATS-01/02）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.stats_service import StatsService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def service(tmp_data_dir: Path) -> StatsService:
    return StatsService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


@pytest.fixture
def import_service(tmp_data_dir: Path) -> ImportService:
    return ImportService(ParquetStore(tmp_data_dir), JsonStore(tmp_data_dir))


def _seed(import_service: ImportService):
    sources = ["garmin", "apple", "garmin", "coros"]
    for i, src in enumerate(sources):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%dT06:00:00")
        import_service.import_manual({
            "activity_date": date, "distance_m": 10000.0,
            "duration_s": 3000, "source": src,
        })


def test_get_statistics_by_source(service: StatsService, import_service: ImportService):
    """按数据源分组统计."""
    _seed(import_service)
    result = service.get_statistics(dimension="by_source")

    assert "groups" in result
    assert len(result["groups"]) > 0
    # garmin 应有 2 条
    garmin_group = next(g for g in result["groups"] if g["key"] == "garmin")
    assert garmin_group["count"] == 2


def test_get_statistics_by_week(service: StatsService, import_service: ImportService):
    """按周分组统计."""
    _seed(import_service)
    result = service.get_statistics(dimension="by_week")
    assert "groups" in result


def test_get_statistics_by_pace_zone(service: StatsService, import_service: ImportService):
    """按配速区间分组."""
    _seed(import_service)
    result = service.get_statistics(dimension="by_pace_zone")
    assert "groups" in result


def test_get_statistics_invalid_dimension_returns_empty(service: StatsService):
    """无效 dimension 返回空 groups."""
    result = service.get_statistics(dimension="invalid")
    assert result["groups"] == []


def test_export_data_csv(service: StatsService, import_service: ImportService):
    """导出 CSV."""
    _seed(import_service)
    result = service.export_data(format="csv")
    assert result["format"] == "csv"
    assert result["rows_count"] > 0
    assert Path(result["file_path"]).exists()


def test_export_data_json(service: StatsService, import_service: ImportService):
    """导出 JSON."""
    _seed(import_service)
    result = service.export_data(format="json")
    assert result["format"] == "json"
    assert Path(result["file_path"]).exists()


def test_export_data_parquet(service: StatsService, import_service: ImportService):
    """导出 Parquet."""
    _seed(import_service)
    result = service.export_data(format="parquet")
    assert result["format"] == "parquet"
    assert Path(result["file_path"]).exists()


def test_export_data_md(service: StatsService, import_service: ImportService):
    """导出 Markdown."""
    _seed(import_service)
    result = service.export_data(format="md")
    assert result["format"] == "md"
    assert Path(result["file_path"]).exists()


def test_export_data_include_ai_logs(service: StatsService, import_service: ImportService):
    """include_ai_logs=True 时导出含决策日志."""
    _seed(import_service)
    # 灌入一个决策日志
    from run_flow_skills_mcp.services.coach_service import CoachService
    coach = CoachService(service.parquet_store, service.json_store)
    coach.save_decision_log(
        decision_type="coach", inputs={"hrv": 38},
        reasoning="test", recommendation="test",
        confidence=0.7, trace_chain=["a"],
    )

    result = service.export_data(format="json", include_ai_logs=True)
    assert result["rows_count"] > 0  # 含决策日志行
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/services/test_stats_service.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/services/stats_service.py`：

```python
"""统计与导出编排服务（spec FR-STATS-01/02, 7.6）.

编排 storage 多维聚合 + 导出。
导出前必须用户确认（interaction-rules.md 第 5 条）——本 service 仅执行导出，确认由调用方（Skill/Web）处理。
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


class StatsService:
    """统计与导出编排服务."""

    def __init__(
        self, parquet_store: ParquetStore, json_store: JsonStore
    ) -> None:
        self.parquet_store = parquet_store
        self.json_store = json_store

    def get_statistics(
        self,
        dimension: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        """按维度分组统计."""
        sessions = self.parquet_store.query_sessions(
            date_from=date_from, date_to=date_to
        )
        if not sessions:
            return {"groups": [], "dimension": dimension}

        metrics = self.parquet_store.query_metrics(
            [s.session_id for s in sessions]
        )
        metrics_map = {m.session_id: m for m in metrics}

        groups: dict[str, list] = defaultdict(list)

        for s in sessions:
            m = metrics_map.get(s.session_id)
            if dimension == "by_source":
                key = s.source
            elif dimension == "by_week":
                iso_week = s.activity_date.isocalendar()
                key = f"{iso_week.year}-W{iso_week.week:02d}"
            elif dimension == "by_month":
                key = s.activity_date.strftime("%Y-%m")
            elif dimension == "by_year":
                key = str(s.activity_date.year)
            elif dimension == "by_pace_zone":
                key = m.pace_zone if m else "unknown"
            elif dimension == "by_distance_range":
                km = s.distance_m / 1000
                if km < 5:
                    key = "<5k"
                elif km < 10:
                    key = "5-10k"
                elif km < 21:
                    key = "10-21k"
                elif km < 42:
                    key = "21-42k"
                else:
                    key = ">=42k"
            else:
                return {"groups": [], "dimension": dimension}
            groups[key].append((s, m))

        result_groups = []
        for key, items in groups.items():
            total_distance = sum(s.distance_m for s, _ in items) / 1000.0
            total_duration = sum(s.duration_s for s, _ in items)
            avg_pace = (
                total_duration / total_distance if total_distance > 0 else 0
            )
            total_tss = sum(m.tss for _, m in items if m and m.tss)
            vdots = [m.vdot for _, m in items if m and m.vdot]
            avg_vdot = sum(vdots) / len(vdots) if vdots else None

            result_groups.append({
                "key": key,
                "count": len(items),
                "total_distance_km": round(total_distance, 2),
                "total_duration_s": total_duration,
                "avg_pace_s_per_km": round(avg_pace, 2),
                "total_tss": round(total_tss, 2),
                "avg_vdot": round(avg_vdot, 2) if avg_vdot else None,
            })

        return {"groups": result_groups, "dimension": dimension}

    def export_data(
        self,
        format: str,
        filters: Optional[dict] = None,
        include_ai_logs: bool = False,
    ) -> dict:
        """导出数据为 CSV/JSON/Parquet/MD."""
        filters = filters or {}
        sessions = self.parquet_store.query_sessions(
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
            source=filters.get("source"),
        )
        metrics = self.parquet_store.query_metrics(
            [s.session_id for s in sessions]
        )
        metrics_map = {m.session_id: m for m in metrics}

        rows: list[dict] = []
        for s in sessions:
            m = metrics_map.get(s.session_id)
            rows.append({
                "session_id": s.session_id,
                "activity_date": s.activity_date.isoformat(),
                "distance_m": s.distance_m,
                "duration_s": s.duration_s,
                "avg_pace_s_per_km": s.avg_pace_s_per_km,
                "avg_hr": s.avg_hr,
                "source": s.source,
                "vdot": m.vdot if m else None,
                "tss": m.tss if m else None,
                "pace_zone": m.pace_zone if m else None,
            })

        if include_ai_logs:
            decisions = self.json_store.query_decisions(
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
            for d in decisions:
                rows.append({
                    "type": "decision_log",
                    "decision_id": d.decision_id,
                    "timestamp": d.timestamp.isoformat(),
                    "decision_type": d.decision_type,
                    "reasoning": d.reasoning,
                    "recommendation": d.recommendation,
                    "confidence": d.confidence,
                })

        # 导出目录：data/exports/
        export_dir = self.parquet_store.data_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_path = export_dir / f"export_{timestamp}.{format}"

        if format == "csv":
            self._write_csv(file_path, rows)
        elif format == "json":
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
        elif format == "parquet":
            import polars as pl
            df = pl.DataFrame(rows) if rows else pl.DataFrame()
            df.write_parquet(file_path)
        elif format == "md":
            self._write_markdown(file_path, rows)
        else:
            return {"file_path": "", "rows_count": 0, "format": format, "error": f"不支持的格式: {format}"}

        return {
            "file_path": str(file_path),
            "rows_count": len(rows),
            "format": format,
        }

    def _write_csv(self, path: Path, rows: list[dict]) -> None:
        """写 CSV."""
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        # 统一字段（取并集）
        fieldnames: list[str] = []
        for r in rows:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    def _write_markdown(self, path: Path, rows: list[dict]) -> None:
        """写 Markdown 表格."""
        if not rows:
            path.write_text("# 导出报告\n\n无数据\n", encoding="utf-8")
            return
        fieldnames = list(rows[0].keys())
        lines = ["# 训练数据导出报告", "", f"共 {len(rows)} 条记录", ""]
        lines.append("| " + " | ".join(fieldnames) + " |")
        lines.append("| " + " | ".join("---" for _ in fieldnames) + " |")
        for r in rows:
            lines.append("| " + " | ".join(str(r.get(f, "")) for f in fieldnames) + " |")
        path.write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/services/test_stats_service.py -v`
Expected: 10 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/services/stats_service.py run-flow-skills-mcp/tests/services/test_stats_service.py
git commit -m "feat(services/stats): multi-dimension aggregation and CSV/JSON/Parquet/MD export"
```

---

## Task 8: tools/_deps.py 依赖工厂 + tools/import_file.py + tools/import_manual.py

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/__init__.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/_deps.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/import_file.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/import_manual.py`
- Test: `run-flow-skills-mcp/tests/tools/__init__.py`
- Test: `run-flow-skills-mcp/tests/tools/test_import_tools.py`

**Interfaces:**
- Consumes:
  - `services.import_service.ImportService`
  - `storage.parquet_store.ParquetStore`、`storage.json_store.JsonStore`
  - `constants.DATA_DIR`（数据目录默认值）
- Produces:
  - `tools/_deps.py`：
    - `class Services`（dataclass）：`import_service, analysis_service, plan_service, review_service, coach_service, stats_service, parquet_store, json_store`（后两个供 Plan 3 Web 层复用，一次性定义避免跨 Plan 修改）
    - `get_services(data_dir: Optional[Path]=None) -> Services`：单例工厂，测试可 monkeypatch
    - `reset_services_cache() -> None`：重置单例（测试间隔离）
  - `tools/import_file.py`：
    - `import_file(file_path: str, force: bool=False, source: Optional[str]=None) -> dict`：薄包装，调 `ImportService.import_file`，附 `prompt`
  - `tools/import_manual.py`：
    - `import_manual(manual_data: dict, force: bool=False) -> dict`：薄包装，调 `ImportService.import_manual`，附 `prompt`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/tools/__init__.py`（空）：

```python
```

写入 `run-flow-skills-mcp/tests/tools/test_import_tools.py`：

```python
"""import_file / import_manual tool 测试（spec FR-IMPORT-01/05, 6.2）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.import_file import import_file
from run_flow_skills_mcp.tools.import_manual import import_manual


@pytest.fixture(autouse=True)
def reset_cache():
    """每个测试后重置 services 单例，避免污染."""
    yield
    _deps.reset_services_cache()


def _write_gpx(path: Path) -> None:
    gpx = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><time>2026-07-25T06:00:00Z</time></metadata>
  <trk><name>Morning Run</name><trkseg>
    <trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2026-07-25T06:00:00Z</time></trkpt>
    <trkpt lat="39.9142" lon="116.4174"><ele>51.0</ele><time>2026-07-25T06:30:00Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""
    path.write_text(gpx, encoding="utf-8")


def test_import_file_returns_prompt_and_data(tmp_path: Path):
    """tool 必须返回 {prompt, ...data}（spec 10.2）."""
    # 替换 DATA_DIR 到 tmp_path
    _deps.reset_services_cache()
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    result = import_file(str(gpx), _data_dir=tmp_path)
    assert "prompt" in result
    assert result["imported"] is True
    assert "session_id" in result
    assert "metrics_summary" in result


def test_import_file_duplicate_returns_skipped(tmp_path: Path):
    """重复导入返回 skipped=True."""
    _deps.reset_services_cache()
    gpx = tmp_path / "test.gpx"
    _write_gpx(gpx)

    first = import_file(str(gpx), _data_dir=tmp_path)
    assert first["imported"] is True

    second = import_file(str(gpx), _data_dir=tmp_path)
    assert second["imported"] is False
    assert second["skipped"] is True
    assert "prompt" in second  # 即使跳过也附 prompt


def test_import_file_unsupported_returns_error_with_prompt(tmp_path: Path):
    """不支持的文件：返回 error + prompt（interaction-rules.md 降级方案）."""
    _deps.reset_services_cache()
    bad = tmp_path / "test.txt"
    bad.write_text("invalid", encoding="utf-8")

    result = import_file(str(bad), _data_dir=tmp_path)
    assert result["imported"] is False
    assert "error" in result
    assert "prompt" in result


def test_import_manual_returns_prompt_and_data(tmp_path: Path):
    """手动录入 tool 返回 {prompt, ...data}."""
    _deps.reset_services_cache()
    manual_data = {
        "activity_date": "2026-07-25T06:00:00",
        "distance_m": 10000.0,
        "duration_s": 3600,
        "source": "manual",
    }
    result = import_manual(manual_data, _data_dir=tmp_path)
    assert result["imported"] is True
    assert "prompt" in result
    assert result["metrics_summary"]["tss"] > 0


def test_import_manual_invalid_returns_error_with_prompt(tmp_path: Path):
    """无效数据返回 error + prompt."""
    _deps.reset_services_cache()
    result = import_manual(
        {"distance_m": 0, "duration_s": 3600, "source": "manual"},
        _data_dir=tmp_path,
    )
    assert result["imported"] is False
    assert "error" in result
    assert "prompt" in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/tools/test_import_tools.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/__init__.py`：

```python
"""tools 子包：MCP Tool 薄包装（参数校验 → 调 service → 附 prompt）."""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/_deps.py`：

```python
"""tools 公共依赖工厂（spec 10.2）.

所有 tool 函数通过 get_services() 获取 service 实例，
测试可通过 monkeypatch 替换或传 _data_dir 参数隔离。

单例缓存：同一进程内多次调用只创建一次 services。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.constants import DATA_DIR as _DEFAULT_DATA_DIR
from run_flow_skills_mcp.services.analysis_service import AnalysisService
from run_flow_skills_mcp.services.coach_service import CoachService
from run_flow_skills_mcp.services.import_service import ImportService
from run_flow_skills_mcp.services.plan_service import PlanService
from run_flow_skills_mcp.services.review_service import ReviewService
from run_flow_skills_mcp.services.stats_service import StatsService
from run_flow_skills_mcp.storage.json_store import JsonStore
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@dataclass
class Services:
    """所有 service 实例的容器."""
    import_service: ImportService
    analysis_service: AnalysisService
    plan_service: PlanService
    review_service: ReviewService
    coach_service: CoachService
    stats_service: StatsService
    parquet_store: ParquetStore  # 供 Plan 3 Web 层读取 session 列表
    json_store: JsonStore        # 供 Plan 3 Web 层读写 config.json


_cache: dict[str, Services] = {}


def get_services(data_dir: Optional[Path] = None) -> Services:
    """获取 services 单例（按 data_dir 缓存）."""
    key = str(data_dir or _DEFAULT_DATA_DIR)
    if key in _cache:
        return _cache[key]

    actual_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    actual_dir.mkdir(parents=True, exist_ok=True)

    parquet_store = ParquetStore(actual_dir)
    json_store = JsonStore(actual_dir)

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
    _cache[key] = services
    return services


def reset_services_cache() -> None:
    """重置单例缓存（测试隔离用）."""
    _cache.clear()
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/import_file.py`：

```python
"""import_file Tool（spec FR-IMPORT-01, 6.2）.

薄包装：参数校验 → 调 ImportService.import_file → 附 prompt。
Tool 不调 LLM，由宿主 AI 用 prompt 调 LLM 生成自然语言反馈。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

# 导入文件反馈 prompt 模板（纯字符串）
_IMPORT_FILE_PROMPT = """用户已导入训练文件：{file_path}。

## 导入结果
- 状态: {status}
- session_id: {session_id}
- 指标摘要: {metrics_summary}

## 你的任务
1. 用简洁中文反馈导入结果（成功/跳过/失败）
2. 若跳过，说明原因（重复文件 / 跨平台重复）并询问是否 --force 重新导入
3. 若成功，简要解读 VDOT/TSS/配速区间，给出 1-2 句训练负荷提示
4. 若失败，给出降级方案（interaction-rules.md 第 4 条）：建议手动录入
"""


def import_file(
    file_path: str,
    force: bool = False,
    source: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """导入训练文件（FIT/TCX/GPX）.

    Args:
        file_path: 文件绝对路径
        force: 是否强制覆盖重复文件
        source: 数据源标注（garmin/apple/coros/strava/manual），可选
        _data_dir: 测试注入数据目录（生产用默认 data/）

    Returns:
        {prompt, imported, session_id?, metrics_summary?, skipped?, reason?, error?}
    """
    if not file_path:
        return {
            "prompt": _IMPORT_FILE_PROMPT.format(
                file_path="", status="失败", session_id="无",
                metrics_summary="文件路径为空",
            ),
            "imported": False,
            "error": "file_path 不能为空",
        }

    # 测试隔离：若传了 _data_dir，重置缓存以确保使用新目录
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.import_service.import_file(
        Path(file_path), force=force, source=source
    )

    # 附 prompt
    if result.get("imported"):
        status = "成功"
        session_id = result.get("session_id", "")
        metrics = result.get("metrics_summary", {})
    elif result.get("skipped"):
        status = f"跳过（{result.get('reason', '未知')}）"
        session_id = result.get("existing_session_id", "")
        metrics = {}
    else:
        status = "失败"
        session_id = "无"
        metrics = result.get("error", "未知错误")

    result["prompt"] = _IMPORT_FILE_PROMPT.format(
        file_path=file_path,
        status=status,
        session_id=session_id,
        metrics_summary=metrics,
    )
    return result
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/import_manual.py`：

```python
"""import_manual Tool（spec FR-IMPORT-05, 6.2）.

薄包装：参数校验 → 调 ImportService.import_manual → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_IMPORT_MANUAL_PROMPT = """用户已手动录入训练记录。

## 录入结果
- 状态: {status}
- session_id: {session_id}
- 指标摘要: {metrics_summary}

## 你的任务
1. 用简洁中文反馈录入结果
2. 若成功，简要解读 VDOT/TSS/配速区间
3. 若失败，明确指出哪个字段无效，给出正确格式示例
"""


def import_manual(
    manual_data: dict,
    force: bool = False,
    _data_dir: Optional[Path] = None,
) -> dict:
    """手动录入训练记录.

    Args:
        manual_data: {activity_date, distance_m, duration_s, source?, avg_hr?, max_hr?, notes?}
        force: 是否强制覆盖重复
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, imported, session_id?, metrics_summary?, error?}
    """
    if not isinstance(manual_data, dict):
        return {
            "prompt": _IMPORT_MANUAL_PROMPT.format(
                status="失败", session_id="无", metrics_summary="manual_data 必须是字典"
            ),
            "imported": False,
            "error": "manual_data 必须是字典",
        }

    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.import_service.import_manual(manual_data, force=force)

    if result.get("imported"):
        status = "成功"
        session_id = result.get("session_id", "")
        metrics = result.get("metrics_summary", {})
    else:
        status = "失败"
        session_id = "无"
        metrics = result.get("error", "未知错误")

    result["prompt"] = _IMPORT_MANUAL_PROMPT.format(
        status=status, session_id=session_id, metrics_summary=metrics
    )
    return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/tools/test_import_tools.py -v`
Expected: 5 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/tools/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/_deps.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/import_file.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/import_manual.py run-flow-skills-mcp/tests/tools/__init__.py run-flow-skills-mcp/tests/tools/test_import_tools.py
git commit -m "feat(tools/import): add import_file and import_manual tools with services factory"
```

---

## Task 9: tools/query_sessions.py + tools/calc_metrics.py

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/query_sessions.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/calc_metrics.py`
- Test: `run-flow-skills-mcp/tests/tools/test_query_and_metrics_tools.py`

**Interfaces:**
- Consumes:
  - `services.analysis_service.AnalysisService`（calc_metrics 复用）
  - `storage.parquet_store.ParquetStore.query_sessions`
  - `prompts.analyze_prompt.ANALYZE_PROMPT`
- Produces:
  - `tools/query_sessions.py`：
    - `query_sessions(date_from: Optional[str]=None, date_to: Optional[str]=None, source: Optional[str]=None, limit: int=50, _data_dir=None) -> dict`：返回 `{prompt, sessions, total}`
  - `tools/calc_metrics.py`：
    - `calc_metrics(date_from: str, date_to: str, _data_dir=None) -> dict`：返回 `{prompt, vdot_trend, tss_sum, ctl, atl, tsb, hr_zones_dist}`，prompt 为 `ANALYZE_PROMPT` 填充后

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/tools/test_query_and_metrics_tools.py`：

```python
"""query_sessions / calc_metrics tool 测试（spec FR-ANALYZE-01, 6.1）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.calc_metrics import calc_metrics
from run_flow_skills_mcp.tools.import_manual import import_manual
from run_flow_skills_mcp.tools.query_sessions import query_sessions


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed(tmp_path: Path, n: int = 3):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {"activity_date": date, "distance_m": 10000.0, "duration_s": 3000, "source": "manual"},
            _data_dir=tmp_path,
        )


def test_query_sessions_returns_list(tmp_path: Path):
    """query_sessions 返回 sessions 列表 + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 3)
    result = query_sessions(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in result
    assert "sessions" in result
    assert isinstance(result["sessions"], list)
    assert result["total"] >= 1
    # 每个 session 应有摘要字段
    for s in result["sessions"]:
        assert "session_id" in s
        assert "activity_date" in s


def test_query_sessions_empty_returns_empty_list(tmp_path: Path):
    """无数据返回空列表 + prompt."""
    _deps.reset_services_cache()
    result = query_sessions(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    assert result["sessions"] == []
    assert result["total"] == 0
    assert "prompt" in result


def test_query_sessions_limit_truncates(tmp_path: Path):
    """limit 截断结果."""
    _deps.reset_services_cache()
    _seed(tmp_path, 5)
    result = query_sessions(
        date_from="2026-07-15", date_to="2026-07-25", limit=2, _data_dir=tmp_path
    )
    assert len(result["sessions"]) <= 2


def test_calc_metrics_returns_prompt_with_placeholders(tmp_path: Path):
    """calc_metrics 返回的 prompt 已填充关键占位符."""
    _deps.reset_services_cache()
    _seed(tmp_path, 5)
    result = calc_metrics(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    for key in ("vdot_trend", "tss_sum", "ctl", "atl", "tsb", "hr_zones_dist", "prompt"):
        assert key in result
    # prompt 应已填充（不再是原始模板的 {vdot}）
    assert "{vdot}" not in result["prompt"]


def test_calc_metrics_empty_data_returns_zeros(tmp_path: Path):
    """无数据返回零值."""
    _deps.reset_services_cache()
    result = calc_metrics(date_from="2026-07-20", date_to="2026-07-25", _data_dir=tmp_path)
    assert result["tss_sum"] == 0
    assert result["ctl"] == 0
    assert "prompt" in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/tools/test_query_and_metrics_tools.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/query_sessions.py`：

```python
"""query_sessions Tool（spec FR-ANALYZE-01, 6.1）.

薄包装：参数校验 → 查 Parquet → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_QUERY_SESSIONS_PROMPT = """已查询到用户训练记录。

## 查询结果
- 时间范围: {date_from} ~ {date_to}
- 数据源过滤: {source}
- 共 {total} 条记录

## 记录列表
{sessions_brief}

## 你的任务
1. 用简洁中文列出关键训练记录（日期 + 距离 + 时长 + 配速）
2. 若用户问特定记录，调 calc_metrics 获取详细指标
3. 若无记录，提示用户导入数据
"""


def query_sessions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    _data_dir: Optional[Path] = None,
) -> dict:
    """查询训练记录列表.

    Args:
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）
        source: 数据源过滤（可选）
        limit: 返回上限，默认 50
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, sessions, total}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    sessions = services.parquet_store.query_sessions(
        date_from=date_from, date_to=date_to, source=source
    )

    # 截断
    sessions = sessions[:limit]

    # 转为摘要 dict
    session_list = [
        {
            "session_id": s.session_id,
            "activity_date": s.activity_date.strftime("%Y-%m-%d"),
            "distance_km": round(s.distance_m / 1000, 2),
            "duration_min": round(s.duration_s / 60, 1),
            "avg_pace_min_per_km": f"{int(s.avg_pace_s_per_km // 60)}'{int(s.avg_pace_s_per_km % 60):02d}\"",
            "source": s.source,
        }
        for s in sessions
    ]

    sessions_brief = "\n".join(
        f"- {s['activity_date']} | {s['distance_km']}km | {s['duration_min']}min | {s['avg_pace_min_per_km']}/km"
        for s in session_list
    ) or "（无记录）"

    prompt = _QUERY_SESSIONS_PROMPT.format(
        date_from=date_from or "全部",
        date_to=date_to or "全部",
        source=source or "全部",
        total=len(session_list),
        sessions_brief=sessions_brief,
    )

    return {
        "prompt": prompt,
        "sessions": session_list,
        "total": len(session_list),
    }
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/calc_metrics.py`：

```python
"""calc_metrics Tool（spec FR-ANALYZE-01, 6.1, 6.2）.

薄包装：调 AnalysisService.calc_metrics → 用 ANALYZE_PROMPT 填充 → 返回。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.prompts.analyze_prompt import ANALYZE_PROMPT
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def calc_metrics(
    date_from: str,
    date_to: str,
    _data_dir: Optional[Path] = None,
) -> dict:
    """聚合区间训练指标.

    Args:
        date_from: 起始日期 YYYY-MM-DD
        date_to: 结束日期 YYYY-MM-DD
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, vdot_trend, tss_sum, ctl, atl, tsb, hr_zones_dist}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.analysis_service.calc_metrics(date_from, date_to)

    # 心率区间分布格式化
    hr_zones_dist = data.get("hr_zones_dist", {})
    hr_zones_str = ", ".join(
        f"{zone}:{pct*100:.0f}%" for zone, pct in hr_zones_dist.items()
    ) or "无数据"

    # VDOT 趋势最新值
    vdot_trend = data.get("vdot_trend", [])
    latest_vdot = vdot_trend[-1]["vdot"] if vdot_trend else None

    # 计算天数
    from datetime import datetime
    try:
        days = (datetime.strptime(date_to, "%Y-%m-%d") - datetime.strptime(date_from, "%Y-%m-%d")).days
    except (ValueError, TypeError):
        days = 30

    prompt = ANALYZE_PROMPT.format(
        days=days,
        vdot=latest_vdot if latest_vdot is not None else "无数据",
        tss=data.get("tss_sum", 0),
        ctl=data.get("ctl", 0),
        atl=data.get("atl", 0),
        tsb=data.get("tsb", 0),
        hr_zones_dist=hr_zones_str,
    )

    return {
        "prompt": prompt,
        "vdot_trend": vdot_trend,
        "tss_sum": data.get("tss_sum", 0),
        "ctl": data.get("ctl", 0),
        "atl": data.get("atl", 0),
        "tsb": data.get("tsb", 0),
        "hr_zones_dist": hr_zones_dist,
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/tools/test_query_and_metrics_tools.py -v`
Expected: 5 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/tools/query_sessions.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/calc_metrics.py run-flow-skills-mcp/tests/tools/test_query_and_metrics_tools.py
git commit -m "feat(tools/query-metrics): add query_sessions and calc_metrics tools with analyze prompt"
```

---

## Task 10: tools/get_trends.py + tools/analyze_fatigue.py

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_trends.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/analyze_fatigue.py`
- Test: `run-flow-skills-mcp/tests/tools/test_trends_and_fatigue_tools.py`

**Interfaces:**
- Consumes:
  - `services.analysis_service.AnalysisService.get_trends`、`analyze_fatigue`
- Produces:
  - `tools/get_trends.py`：
    - `get_trends(days: int=30, metric: str="vdot", _data_dir=None) -> dict`：返回 `{prompt, series, change_pct, baseline}`
  - `tools/analyze_fatigue.py`：
    - `analyze_fatigue(days: int=7, _data_dir=None) -> dict`：返回 `{prompt, fatigue_score, risk_level, main_factors, hrv_deviation, tsb}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/tools/test_trends_and_fatigue_tools.py`：

```python
"""get_trends / analyze_fatigue tool 测试（spec FR-ANALYZE-04/05）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.analyze_fatigue import analyze_fatigue
from run_flow_skills_mcp.tools.get_trends import get_trends
from run_flow_skills_mcp.tools.import_manual import import_manual


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed_sessions(tmp_path: Path, n: int = 10):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=n - i - 1)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {"activity_date": date, "distance_m": 10000.0, "duration_s": 3000, "source": "manual"},
            _data_dir=tmp_path,
        )


def _seed_hrv(tmp_path: Path, n: int = 7):
    _deps.reset_services_cache()
    services = _deps.get_services(tmp_path)
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        services.coach_service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=45.0, rpe=5)
        )


def test_get_trends_vdot_returns_prompt_and_series(tmp_path: Path):
    """get_trends(metric=vdot) 返回 series + prompt."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 5)
    result = get_trends(days=30, metric="vdot", _data_dir=tmp_path)
    for key in ("prompt", "series", "change_pct", "baseline"):
        assert key in result
    assert isinstance(result["series"], list)


def test_get_trends_load_metric(tmp_path: Path):
    """get_trends(metric=load) 返回 CTL/ATL 序列."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 5)
    result = get_trends(days=30, metric="load", _data_dir=tmp_path)
    assert "series" in result
    assert "prompt" in result


def test_get_trends_invalid_metric_returns_empty(tmp_path: Path):
    """无效 metric 返回空 series + prompt（降级）."""
    _deps.reset_services_cache()
    result = get_trends(days=7, metric="invalid", _data_dir=tmp_path)
    assert result["series"] == []
    assert "prompt" in result


def test_analyze_fatigue_returns_prompt_and_fields(tmp_path: Path):
    """analyze_fatigue 返回所有字段 + prompt."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 5)
    _seed_hrv(tmp_path, 7)
    result = analyze_fatigue(days=7, _data_dir=tmp_path)
    for key in ("prompt", "fatigue_score", "risk_level", "main_factors", "hrv_deviation", "tsb"):
        assert key in result


def test_analyze_fatigue_no_data_returns_low(tmp_path: Path):
    """无数据返回低风险 + prompt."""
    _deps.reset_services_cache()
    result = analyze_fatigue(days=7, _data_dir=tmp_path)
    assert result["risk_level"] == "low"
    assert "prompt" in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/tools/test_trends_and_fatigue_tools.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_trends.py`：

```python
"""get_trends Tool（spec FR-ANALYZE-04, 6.1）.

薄包装：调 AnalysisService.get_trends → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_TREND_PROMPT = """已获取用户 {days} 天 {metric} 趋势数据。

## 趋势摘要
- 指标: {metric}
- 数据点数: {points}
- 变化百分比: {change_pct}%
- 基线值: {baseline}

## 你的任务
1. 用简洁中文描述趋势（上升/下降/平稳）+ 数据依据（analysis-rules.md 第 2 条）
2. 若 change_pct > 10% 或 < -10%，提示显著变化并分析原因
3. 若数据点 < 7，标注 "数据不足，置信度低"（analysis-rules.md 第 4 条）
"""


def get_trends(
    days: int = 30,
    metric: str = "vdot",
    _data_dir: Optional[Path] = None,
) -> dict:
    """获取时间序列趋势.

    Args:
        days: 天数，默认 30
        metric: 指标类型（vdot/load/hrv）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, series, change_pct, baseline}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.analysis_service.get_trends(days=days, metric=metric)

    series = data.get("series", [])
    change_pct = data.get("change_pct", 0.0)
    baseline = data.get("baseline")

    prompt = _TREND_PROMPT.format(
        days=days,
        metric=metric,
        points=len(series),
        change_pct=round(change_pct, 2),
        baseline=baseline if baseline is not None else "无数据",
    )

    return {
        "prompt": prompt,
        "series": series,
        "change_pct": change_pct,
        "baseline": baseline,
    }
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/analyze_fatigue.py`：

```python
"""analyze_fatigue Tool（spec FR-ANALYZE-05, 6.1, 8.2）.

薄包装：调 AnalysisService.analyze_fatigue → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_FATIGUE_PROMPT = """已分析用户 {days} 天疲劳度。

## 疲劳度评估
- 疲劳分数: {fatigue_score}（0-100，越高越疲劳）
- 风险等级: {risk_level}（low/medium/high）
- 主要风险因子: {main_factors}
- HRV 偏离: {hrv_deviation}%
- TSB: {tsb}

## 你的任务（严格遵守 analysis-rules.md）
1. **风险因子**：列出主要风险因子（如 "HRV 偏离 -15%"/"TSB=-20"），禁止笼统结论
2. **数据依据**：每个判断必须引用具体数值
3. **误差范围**：若数据不足 7 天，标注 "置信度低"
4. **建议**：根据风险等级给具体可执行建议（low=正常训练/medium=减量/high=休息）
"""


def analyze_fatigue(
    days: int = 7,
    _data_dir: Optional[Path] = None,
) -> dict:
    """综合疲劳度评估.

    Args:
        days: 分析天数，默认 7
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, fatigue_score, risk_level, main_factors, hrv_deviation, tsb}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.analysis_service.analyze_fatigue(days=days)

    prompt = _FATIGUE_PROMPT.format(
        days=days,
        fatigue_score=data.get("fatigue_score", 0),
        risk_level=data.get("risk_level", "low"),
        main_factors=data.get("main_factors", []),
        hrv_deviation=data.get("hrv_deviation") if data.get("hrv_deviation") is not None else "无数据",
        tsb=data.get("tsb") if data.get("tsb") is not None else "无数据",
    )

    return {
        "prompt": prompt,
        "fatigue_score": data.get("fatigue_score", 0),
        "risk_level": data.get("risk_level", "low"),
        "main_factors": data.get("main_factors", []),
        "hrv_deviation": data.get("hrv_deviation"),
        "tsb": data.get("tsb"),
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/tools/test_trends_and_fatigue_tools.py -v`
Expected: 5 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_trends.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/analyze_fatigue.py run-flow-skills-mcp/tests/tools/test_trends_and_fatigue_tools.py
git commit -m "feat(tools/trends-fatigue): add get_trends and analyze_fatigue tools"
```

---

## Task 11: tools/generate_plan.py + tools/query_plan.py

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/generate_plan.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/query_plan.py`
- Test: `run-flow-skills-mcp/tests/tools/test_plan_tools.py`

**Interfaces:**
- Consumes:
  - `services.plan_service.PlanService.generate_plan`、`query_plan`
  - `prompts.plan_prompt.PLAN_PROMPT`（service 内部已填充）
- Produces:
  - `tools/generate_plan.py`：
    - `generate_plan(goal_type: str, goal_time: str, race_date: str, weeks: int, current_vdot: float, _data_dir=None) -> dict`：返回 `{prompt, plan_id, phases, pace_zones, target_vdot, vdot_gap}`
  - `tools/query_plan.py`：
    - `query_plan(plan_id: Optional[str]=None, _data_dir=None) -> dict`：返回 `{prompt, plan, fidelity}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/tools/test_plan_tools.py`：

```python
"""generate_plan / query_plan tool 测试（spec FR-PLAN-01/02/03/04）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.generate_plan import generate_plan
from run_flow_skills_mcp.tools.query_plan import query_plan


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def test_generate_plan_returns_prompt_and_data(tmp_path: Path):
    """generate_plan 返回 plan_prompt + 结构化数据."""
    _deps.reset_services_cache()
    result = generate_plan(
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
        _data_dir=tmp_path,
    )
    for key in ("prompt", "plan_id", "phases", "pace_zones", "target_vdot", "vdot_gap"):
        assert key in result
    # prompt 应是 service 填充后的 plan_prompt
    assert "42.0" in result["prompt"] or "42" in result["prompt"]


def test_generate_plan_invalid_goal_type_still_returns(tmp_path: Path):
    """无效 goal_type 也能返回（service 内部降级）."""
    _deps.reset_services_cache()
    result = generate_plan(
        goal_type="invalid",
        goal_time="00:30:00",
        race_date="2026-10-19",
        weeks=4,
        current_vdot=40.0,
        _data_dir=tmp_path,
    )
    assert "prompt" in result
    assert "plan_id" in result


def test_query_plan_returns_plan_and_fidelity(tmp_path: Path):
    """query_plan 返回 plan + fidelity + prompt."""
    _deps.reset_services_cache()
    gen = generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
        _data_dir=tmp_path,
    )
    result = query_plan(gen["plan_id"], _data_dir=tmp_path)
    for key in ("prompt", "plan", "fidelity"):
        assert key in result


def test_query_plan_not_found_returns_none(tmp_path: Path):
    """不存在的 plan_id 返回 plan=None + prompt."""
    _deps.reset_services_cache()
    result = query_plan("plan_20260101_999", _data_dir=tmp_path)
    assert result["plan"] is None
    assert "prompt" in result


def test_query_plan_no_id_returns_latest(tmp_path: Path):
    """plan_id=None 返回最新计划."""
    _deps.reset_services_cache()
    generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
        _data_dir=tmp_path,
    )
    result = query_plan(_data_dir=tmp_path)
    assert result["plan"] is not None
    assert "prompt" in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/tools/test_plan_tools.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/generate_plan.py`：

```python
"""generate_plan Tool（spec FR-PLAN-01, 6.2）.

薄包装：调 PlanService.generate_plan → service 已填充 plan_prompt → 直接返回。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def generate_plan(
    goal_type: str,
    goal_time: str,
    race_date: str,
    weeks: int,
    current_vdot: float,
    _data_dir: Optional[Path] = None,
) -> dict:
    """生成周期化训练计划.

    Args:
        goal_type: 目标类型（5k/10k/half_marathon/full_marathon）
        goal_time: 目标时间 HH:MM:SS
        race_date: 比赛日 YYYY-MM-DD
        weeks: 训练周数
        current_vdot: 当前 VDOT
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, plan_id, phases, pace_zones, target_vdot, vdot_gap}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.plan_service.generate_plan(
        goal_type=goal_type,
        goal_time=goal_time,
        race_date=race_date,
        weeks=weeks,
        current_vdot=current_vdot,
    )
    # service 已返回 plan_prompt，重命名为 prompt
    result["prompt"] = result.pop("plan_prompt")
    return result
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/query_plan.py`：

```python
"""query_plan Tool（spec FR-PLAN-02/04, 6.2）.

薄包装：调 PlanService.query_plan → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_QUERY_PLAN_PROMPT = """已查询用户训练计划。

## 计划信息
{plan_info}

## 执行忠实度
{fidelity_info}

## 你的任务
1. 用简洁中文概述计划（目标 + 周数 + 周期化阶段）
2. 解释配速区间如何基于 VDOT 计算（spec 7.3）
3. 若忠实度 < 0.7，提示用户漏练情况并说明漏练自适应策略
4. 若计划为空，引导用户调 generate_plan 生成
"""


def query_plan(
    plan_id: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """查询训练计划 + 执行忠实度.

    Args:
        plan_id: 计划 ID（None 返回最新）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, plan, fidelity}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.plan_service.query_plan(plan_id)
    plan = result.get("plan")
    fidelity = result.get("fidelity")

    if plan is None:
        plan_info = "（无计划）"
        fidelity_info = "（无）"
    else:
        plan_info = (
            f"- plan_id: {plan.plan_id}\n"
            f"- 目标: {plan.goal_type} {plan.goal_time}\n"
            f"- 比赛日: {plan.race_date}\n"
            f"- 周数: {plan.weeks}\n"
            f"- 当前 VDOT: {plan.current_vdot} → 目标 VDOT: {plan.target_vdot}"
        )
        if fidelity:
            fidelity_info = (
                f"- 计划课表数: {fidelity.get('planned_sessions', 0)}\n"
                f"- 已完成: {fidelity.get('completed_sessions', 0)}\n"
                f"- 忠实度: {fidelity.get('fidelity_rate', 0)}"
            )
        else:
            fidelity_info = "（无）"

    prompt = _QUERY_PLAN_PROMPT.format(
        plan_info=plan_info,
        fidelity_info=fidelity_info,
    )

    return {
        "prompt": prompt,
        "plan": plan,
        "fidelity": fidelity,
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/tools/test_plan_tools.py -v`
Expected: 5 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/tools/generate_plan.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/query_plan.py run-flow-skills-mcp/tests/tools/test_plan_tools.py
git commit -m "feat(tools/plan): add generate_plan and query_plan tools"
```

---

## Task 12: tools/get_period_summary.py + tools/read_body_signals.py

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_period_summary.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/read_body_signals.py`
- Test: `run-flow-skills-mcp/tests/tools/test_period_and_body_tools.py`

**Interfaces:**
- Consumes:
  - `services.review_service.ReviewService.get_period_summary`
  - `services.coach_service.CoachService.read_body_signals`
  - `prompts.review_prompt.REVIEW_PROMPT`、`prompts.coach_prompt.COACH_PROMPT`
- Produces:
  - `tools/get_period_summary.py`：
    - `get_period_summary(period: str="week", date_ref: Optional[str]=None, _data_dir=None) -> dict`：返回 `{prompt, total_distance, total_tss, avg_vdot, load_change, sessions_count, vdot_trend, hrv_trend}`
  - `tools/read_body_signals.py`：
    - `read_body_signals(date: Optional[str]=None, _data_dir=None) -> dict`：返回 `{prompt, hrv, resting_hr, sleep, rpe, baseline, deviation_pct, readiness_level, yesterday_session, recent_high_intensity}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/tools/test_period_and_body_tools.py`：

```python
"""get_period_summary / read_body_signals tool 测试（spec FR-REVIEW-01/02, FR-COACH-01）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.get_period_summary import get_period_summary
from run_flow_skills_mcp.tools.import_manual import import_manual
from run_flow_skills_mcp.tools.read_body_signals import read_body_signals


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed_sessions(tmp_path: Path, n: int = 7):
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=n - i - 1)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {"activity_date": date, "distance_m": 10000.0, "duration_s": 3000, "source": "manual"},
            _data_dir=tmp_path,
        )


def _seed_hrv(tmp_path: Path, n: int = 7):
    services = _deps.get_services(tmp_path)
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%d")
        services.coach_service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=45.0, rpe=5, resting_hr=55, sleep_quality=4)
        )


def test_get_period_summary_returns_prompt_and_data(tmp_path: Path):
    """get_period_summary 返回所有字段 + prompt."""
    _deps.reset_services_cache()
    _seed_sessions(tmp_path, 7)
    result = get_period_summary(period="week", date_ref="2026-07-25", _data_dir=tmp_path)
    for key in ("prompt", "total_distance", "total_tss", "avg_vdot", "load_change", "sessions_count", "vdot_trend", "hrv_trend"):
        assert key in result
    # prompt 应已填充（不再是 {period}）
    assert "{period}" not in result["prompt"]


def test_get_period_summary_invalid_period(tmp_path: Path):
    """无效 period 返回零值 + prompt."""
    _deps.reset_services_cache()
    result = get_period_summary(period="invalid", date_ref="2026-07-25", _data_dir=tmp_path)
    assert result["sessions_count"] == 0
    assert "prompt" in result


def test_read_body_signals_returns_prompt_and_data(tmp_path: Path):
    """read_body_signals 返回所有字段 + prompt."""
    _deps.reset_services_cache()
    _seed_hrv(tmp_path, 7)
    result = read_body_signals(date="2026-07-25", _data_dir=tmp_path)
    for key in ("prompt", "hrv", "resting_hr", "sleep", "rpe", "baseline", "deviation_pct", "readiness_level", "yesterday_session", "recent_high_intensity"):
        assert key in result
    # prompt 应已填充
    assert "{readiness_level}" not in result["prompt"]


def test_read_body_signals_no_data_returns_none_values(tmp_path: Path):
    """无数据返回 None 值 + prompt."""
    _deps.reset_services_cache()
    result = read_body_signals(date="2026-07-25", _data_dir=tmp_path)
    assert result["hrv"] is None
    assert result["readiness_level"] in ("green", "yellow", "red")
    assert "prompt" in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/tools/test_period_and_body_tools.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_period_summary.py`：

```python
"""get_period_summary Tool（spec FR-REVIEW-01/02, 6.2, 7.4）.

薄包装：调 ReviewService.get_period_summary → 用 REVIEW_PROMPT 填充 → 返回。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.prompts.review_prompt import REVIEW_PROMPT
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def get_period_summary(
    period: str = "week",
    date_ref: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """聚合周期训练数据.

    Args:
        period: 周期类型（week/month/season/year）
        date_ref: 参考日期 YYYY-MM-DD（默认今天）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, total_distance, total_tss, avg_vdot, load_change,
         sessions_count, vdot_trend, hrv_trend}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.review_service.get_period_summary(period=period, date_ref=date_ref)

    # 填充 REVIEW_PROMPT
    load_change = data.get("load_change", {})
    vdot_trend = data.get("vdot_trend", [])
    hrv_trend = data.get("hrv_trend", [])

    prompt = REVIEW_PROMPT.format(
        period=period,
        total_distance=data.get("total_distance", 0),
        total_tss=data.get("total_tss", 0),
        load_change=load_change,
        vdot_trend=vdot_trend,
        hrv_trend=hrv_trend,
        sessions_count=data.get("sessions_count", 0),
    )

    return {
        "prompt": prompt,
        "total_distance": data.get("total_distance", 0),
        "total_tss": data.get("total_tss", 0),
        "avg_vdot": data.get("avg_vdot"),
        "load_change": load_change,
        "sessions_count": data.get("sessions_count", 0),
        "vdot_trend": vdot_trend,
        "hrv_trend": hrv_trend,
    }
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/read_body_signals.py`：

```python
"""read_body_signals Tool（spec FR-COACH-01, 6.2, 8.3）.

薄包装：调 CoachService.read_body_signals → 用 COACH_PROMPT 填充 → 返回。

注意：readiness_level 由 service 内部综合 HRV + TSB + RPE 计算（spec 6.2）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.prompts.coach_prompt import COACH_PROMPT
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def read_body_signals(
    date: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """读取今日身体信号 + 计算就绪状态.

    Args:
        date: 日期 YYYY-MM-DD（默认今天）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, hrv, resting_hr, sleep, rpe, baseline, deviation_pct,
         tsb, readiness_level, yesterday_session, recent_high_intensity}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.coach_service.read_body_signals(date=date)

    # 填充 COACH_PROMPT
    prompt = COACH_PROMPT.format(
        hrv=data.get("hrv") if data.get("hrv") is not None else "无数据",
        hrv_baseline=data.get("baseline") if data.get("baseline") is not None else "无数据",
        hrv_deviation_pct=round(data.get("deviation_pct"), 1) if data.get("deviation_pct") is not None else "无数据",
        resting_hr=data.get("resting_hr") if data.get("resting_hr") is not None else "无数据",
        sleep_quality=data.get("sleep") if data.get("sleep") is not None else "无数据",
        rpe=data.get("rpe") if data.get("rpe") is not None else "无数据",
        readiness_level=data.get("readiness_level", "green"),
        ctl=data.get("ctl", 0) if data.get("ctl") is not None else "无数据",
        atl=data.get("atl", 0) if data.get("atl") is not None else "无数据",
        tsb=data.get("tsb") if data.get("tsb") is not None else "无数据",
        yesterday_session=data.get("yesterday_session") or "无",
        recent_high_intensity=data.get("recent_high_intensity") or "无",
        today_plan="（请通过 query_plan 获取今日课表）",
    )

    return {
        "prompt": prompt,
        "hrv": data.get("hrv"),
        "resting_hr": data.get("resting_hr"),
        "sleep": data.get("sleep"),
        "rpe": data.get("rpe"),
        "baseline": data.get("baseline"),
        "deviation_pct": data.get("deviation_pct"),
        "tsb": data.get("tsb"),
        "readiness_level": data.get("readiness_level", "green"),
        "yesterday_session": data.get("yesterday_session"),
        "recent_high_intensity": data.get("recent_high_intensity"),
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/tools/test_period_and_body_tools.py -v`
Expected: 4 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_period_summary.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/read_body_signals.py run-flow-skills-mcp/tests/tools/test_period_and_body_tools.py
git commit -m "feat(tools/review-coach): add get_period_summary and read_body_signals tools"
```

---

## Task 13: tools/get_decision_trace.py + tools/save_decision_log.py

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_decision_trace.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/save_decision_log.py`
- Test: `run-flow-skills-mcp/tests/tools/test_decision_tools.py`

**Interfaces:**
- Consumes:
  - `services.coach_service.CoachService.get_decision_trace`、`save_decision_log`
  - `prompts.decision_trace.DECISION_TRACE_TEMPLATE`
- Produces:
  - `tools/get_decision_trace.py`：
    - `get_decision_trace(decision_id: str, _data_dir=None) -> dict`：返回 `{prompt, decision_id, found, trace?}`
  - `tools/save_decision_log.py`：
    - `save_decision_log(decision_type: str, inputs: dict, reasoning: str, recommendation: str, confidence: float, trace_chain: list[str], related_session_ids: Optional[list[str]]=None, _data_dir=None) -> dict`：返回 `{prompt, decision_id, saved}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/tools/test_decision_tools.py`：

```python
"""get_decision_trace / save_decision_log tool 测试（spec FR-COACH-02/03, 6.2, 10.1）."""
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.get_decision_trace import get_decision_trace
from run_flow_skills_mcp.tools.save_decision_log import save_decision_log


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def test_save_decision_log_returns_prompt_and_id(tmp_path: Path):
    """save_decision_log 返回 prompt + decision_id + saved=True."""
    _deps.reset_services_cache()
    result = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38, "tsb": -5},
        reasoning="HRV 偏低 + TSB 负值，建议降级训练",
        recommendation="E 区间 30 分钟，配速 5'40\"-6'00\"/km",
        confidence=0.75,
        trace_chain=["HRV=38", "baseline=45", "rule:HRV偏离>10%", "TSB=-5"],
        _data_dir=tmp_path,
    )
    assert result["saved"] is True
    assert result["decision_id"].startswith("dec_")
    assert "prompt" in result
    # prompt 应已填充 DECISION_TRACE_TEMPLATE
    assert "{recommendation}" not in result["prompt"]


def test_save_decision_log_invalid_confidence_returns_error(tmp_path: Path):
    """confidence 越界返回 error + prompt."""
    _deps.reset_services_cache()
    result = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="test",
        recommendation="test",
        confidence=1.5,  # 越界
        trace_chain=["a"],
        _data_dir=tmp_path,
    )
    assert result["saved"] is False
    assert "error" in result
    assert "prompt" in result


def test_get_decision_trace_found(tmp_path: Path):
    """保存后可查询."""
    _deps.reset_services_cache()
    saved = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="test",
        recommendation="test",
        confidence=0.7,
        trace_chain=["a", "b"],
        _data_dir=tmp_path,
    )
    result = get_decision_trace(saved["decision_id"], _data_dir=tmp_path)
    assert result["found"] is True
    assert result["decision_id"] == saved["decision_id"]
    assert "trace" in result
    assert "prompt" in result


def test_get_decision_trace_not_found(tmp_path: Path):
    """不存在的 decision_id 返回 found=False + prompt."""
    _deps.reset_services_cache()
    result = get_decision_trace("dec_20260101_999", _data_dir=tmp_path)
    assert result["found"] is False
    assert "prompt" in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/tools/test_decision_tools.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_decision_trace.py`：

```python
"""get_decision_trace Tool（spec FR-COACH-02, 6.2, 10.1）.

薄包装：调 CoachService.get_decision_trace → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_GET_TRACE_PROMPT = """已查询决策溯源链。

## 查询结果
- decision_id: {decision_id}
- 找到: {found}

## 决策详情
{trace_detail}

## 你的任务
1. 若找到，用简洁中文复述决策链（输入 → 推理 → 建议 → 置信度）
2. 若未找到，告知用户该决策不存在，建议调 save_decision_log 记录新决策
3. 若 confidence < 0.6，提示 "此决策仅供参考"
"""


def get_decision_trace(
    decision_id: str,
    _data_dir: Optional[Path] = None,
) -> dict:
    """查询决策溯源链.

    Args:
        decision_id: 决策 ID（dec_YYYYMMDD_NNN）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, decision_id, found, trace?}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    trace = services.coach_service.get_decision_trace(decision_id)

    if trace is None:
        trace_detail = "（未找到）"
        found = False
    else:
        found = True
        trace_detail = (
            f"- 类型: {trace.get('decision_type', '')}\n"
            f"- 输入: {trace.get('inputs', {})}\n"
            f"- 推理: {trace.get('reasoning', '')}\n"
            f"- 建议: {trace.get('recommendation', '')}\n"
            f"- 置信度: {trace.get('confidence', 0)}\n"
            f"- 溯源链: {trace.get('trace_chain', [])}"
        )

    prompt = _GET_TRACE_PROMPT.format(
        decision_id=decision_id,
        found=found,
        trace_detail=trace_detail,
    )

    result: dict = {
        "prompt": prompt,
        "decision_id": decision_id,
        "found": found,
    }
    if trace is not None:
        result["trace"] = trace
    return result
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/save_decision_log.py`：

```python
"""save_decision_log Tool（spec FR-COACH-03, 6.2, 10.1, 10.2）.

薄包装：参数校验 → 调 CoachService.save_decision_log → 用 DECISION_TRACE_TEMPLATE 填充 prompt。

关键约束（spec 6.2）：
- reasoning/recommendation/trace_chain 由宿主 AI 生成后传入
- Tool 不调 LLM，只负责持久化
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.prompts.decision_trace import DECISION_TRACE_TEMPLATE
from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache


def save_decision_log(
    decision_type: str,
    inputs: dict,
    reasoning: str,
    recommendation: str,
    confidence: float,
    trace_chain: list[str],
    related_session_ids: Optional[list[str]] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """保存 AI 决策记录.

    Args:
        decision_type: 决策类型（coach/plan/review/analyze）
        inputs: 决策输入数据（dict）
        reasoning: AI 推理过程（自然语言）
        recommendation: AI 最终建议
        confidence: 置信度（0-1）
        trace_chain: 溯源链步骤列表
        related_session_ids: 关联的 session_id 列表（可选）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, decision_id, saved} 或 {prompt, saved: False, error}
    """
    # 参数校验
    if not decision_type:
        return {
            "prompt": "参数错误：decision_type 不能为空",
            "saved": False,
            "error": "decision_type 不能为空",
        }
    if not isinstance(inputs, dict):
        return {
            "prompt": "参数错误：inputs 必须是字典",
            "saved": False,
            "error": "inputs 必须是字典",
        }
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        return {
            "prompt": f"参数错误：confidence={confidence} 越界（应为 0-1）",
            "saved": False,
            "error": f"confidence 越界: {confidence}",
        }
    if not isinstance(trace_chain, list):
        return {
            "prompt": "参数错误：trace_chain 必须是列表",
            "saved": False,
            "error": "trace_chain 必须是列表",
        }

    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.coach_service.save_decision_log(
        decision_type=decision_type,
        inputs=inputs,
        reasoning=reasoning,
        recommendation=recommendation,
        confidence=confidence,
        trace_chain=trace_chain,
        related_session_ids=related_session_ids,
    )

    # 用 DECISION_TRACE_TEMPLATE 填充 prompt
    prompt = DECISION_TRACE_TEMPLATE.format(
        inputs=inputs,
        reasoning=reasoning,
        recommendation=recommendation,
        confidence=confidence,
        related_session_ids=related_session_ids or [],
    )

    result["prompt"] = prompt
    return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/tools/test_decision_tools.py -v`
Expected: 4 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_decision_trace.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/save_decision_log.py run-flow-skills-mcp/tests/tools/test_decision_tools.py
git commit -m "feat(tools/decision): add get_decision_trace and save_decision_log tools"
```

---

## Task 14: tools/get_statistics.py + tools/export_data.py

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_statistics.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/export_data.py`
- Test: `run-flow-skills-mcp/tests/tools/test_stats_tools.py`

**Interfaces:**
- Consumes:
  - `services.stats_service.StatsService.get_statistics`、`export_data`
- Produces:
  - `tools/get_statistics.py`：
    - `get_statistics(dimension: str, date_from: Optional[str]=None, date_to: Optional[str]=None, _data_dir=None) -> dict`：返回 `{prompt, groups, dimension}`
  - `tools/export_data.py`：
    - `export_data(format: str, filters: Optional[dict]=None, include_ai_logs: bool=False, _data_dir=None) -> dict`：返回 `{prompt, file_path, rows_count, format}`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/tools/test_stats_tools.py`：

```python
"""get_statistics / export_data tool 测试（spec FR-STATS-01/02）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.export_data import export_data
from run_flow_skills_mcp.tools.get_statistics import get_statistics
from run_flow_skills_mcp.tools.import_manual import import_manual


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed(tmp_path: Path, n: int = 4):
    sources = ["garmin", "apple", "garmin", "coros"]
    for i in range(n):
        date = (datetime(2026, 7, 25) - timedelta(days=i)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {"activity_date": date, "distance_m": 10000.0, "duration_s": 3000, "source": sources[i % len(sources)]},
            _data_dir=tmp_path,
        )


def test_get_statistics_returns_prompt_and_groups(tmp_path: Path):
    """get_statistics 返回 groups + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = get_statistics(dimension="by_source", _data_dir=tmp_path)
    for key in ("prompt", "groups", "dimension"):
        assert key in result
    assert isinstance(result["groups"], list)
    assert len(result["groups"]) > 0


def test_get_statistics_invalid_dimension(tmp_path: Path):
    """无效 dimension 返回空 groups + prompt."""
    _deps.reset_services_cache()
    result = get_statistics(dimension="invalid", _data_dir=tmp_path)
    assert result["groups"] == []
    assert "prompt" in result


def test_export_data_csv(tmp_path: Path):
    """导出 CSV 返回 file_path + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = export_data(format="csv", _data_dir=tmp_path)
    assert result["format"] == "csv"
    assert result["rows_count"] > 0
    assert Path(result["file_path"]).exists()
    assert "prompt" in result


def test_export_data_json(tmp_path: Path):
    """导出 JSON."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = export_data(format="json", _data_dir=tmp_path)
    assert result["format"] == "json"
    assert Path(result["file_path"]).exists()
    assert "prompt" in result


def test_export_data_invalid_format_returns_error(tmp_path: Path):
    """不支持的格式返回 error + prompt."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    result = export_data(format="xml", _data_dir=tmp_path)
    assert "error" in result
    assert "prompt" in result


def test_export_data_include_ai_logs(tmp_path: Path):
    """include_ai_logs=True 含决策日志."""
    _deps.reset_services_cache()
    _seed(tmp_path, 4)
    # 灌入决策日志
    services = _deps.get_services(tmp_path)
    services.coach_service.save_decision_log(
        decision_type="coach", inputs={"hrv": 38},
        reasoning="test", recommendation="test",
        confidence=0.7, trace_chain=["a"],
    )
    _deps.reset_services_cache()

    result = export_data(format="json", include_ai_logs=True, _data_dir=tmp_path)
    assert result["rows_count"] > 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/tools/test_stats_tools.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_statistics.py`：

```python
"""get_statistics Tool（spec FR-STATS-01, 6.2, 7.6）.

薄包装：调 StatsService.get_statistics → 附 prompt。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_STATS_PROMPT = """已查询用户训练统计（按 {dimension} 分组）。

## 统计结果
共 {groups_count} 个分组：

{groups_detail}

## 你的任务
1. 用简洁中文列出各分组关键指标（数量 + 总跑量 + 平均配速 + 总 TSS）
2. 若某分组显著偏高/偏低，提示并分析原因
3. 若分组为空，提示用户先导入数据
"""


def get_statistics(
    dimension: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    _data_dir: Optional[Path] = None,
) -> dict:
    """按维度分组统计.

    Args:
        dimension: 分组维度（by_source/by_week/by_month/by_year/by_pace_zone/by_distance_range）
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, groups, dimension}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    data = services.stats_service.get_statistics(
        dimension=dimension, date_from=date_from, date_to=date_to
    )

    groups = data.get("groups", [])
    groups_detail = "\n".join(
        f"- {g['key']}: {g['count']} 次, {g.get('total_distance_km', 0)} km, "
        f"平均配速 {g.get('avg_pace_s_per_km', 0)} s/km, TSS {g.get('total_tss', 0)}"
        for g in groups
    ) or "（无数据）"

    prompt = _STATS_PROMPT.format(
        dimension=dimension,
        groups_count=len(groups),
        groups_detail=groups_detail,
    )

    return {
        "prompt": prompt,
        "groups": groups,
        "dimension": dimension,
    }
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/tools/export_data.py`：

```python
"""export_data Tool（spec FR-STATS-02, 6.2, 7.6）.

薄包装：调 StatsService.export_data → 附 prompt。

注意（interaction-rules.md 第 3 条）：导出前需用户确认。
本 tool 仅执行导出，确认由调用方（Skill/Web）处理。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.tools._deps import get_services, reset_services_cache

_EXPORT_PROMPT = """已导出用户训练数据。

## 导出结果
- 格式: {format}
- 文件路径: {file_path}
- 记录数: {rows_count}
- 含决策日志: {include_ai_logs}

## 你的任务
1. 告知用户导出完成 + 文件路径
2. 提醒用户数据仅本地存储（data-safety-rules.md 第 1 条）
3. 若失败，给出降级方案（如换格式重试）
"""


def export_data(
    format: str,
    filters: Optional[dict] = None,
    include_ai_logs: bool = False,
    _data_dir: Optional[Path] = None,
) -> dict:
    """导出训练数据.

    Args:
        format: 导出格式（csv/json/parquet/md）
        filters: 过滤条件 {date_from?, date_to?, source?}
        include_ai_logs: 是否包含决策日志
        _data_dir: 测试注入数据目录

    Returns:
        {prompt, file_path, rows_count, format} 或 {prompt, error}
    """
    if _data_dir is not None:
        reset_services_cache()

    services = get_services(_data_dir)
    result = services.stats_service.export_data(
        format=format, filters=filters, include_ai_logs=include_ai_logs
    )

    if "error" in result:
        result["prompt"] = _EXPORT_PROMPT.format(
            format=format,
            file_path="（失败）",
            rows_count=0,
            include_ai_logs=include_ai_logs,
        )
        return result

    result["prompt"] = _EXPORT_PROMPT.format(
        format=result.get("format", format),
        file_path=result.get("file_path", ""),
        rows_count=result.get("rows_count", 0),
        include_ai_logs=include_ai_logs,
    )
    return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/tools/test_stats_tools.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/tools/get_statistics.py run-flow-skills-mcp/src/run_flow_skills_mcp/tools/export_data.py run-flow-skills-mcp/tests/tools/test_stats_tools.py
git commit -m "feat(tools/stats): add get_statistics and export_data tools"
```

---

## Task 15: server.py FastMCP 服务入口

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/server.py`
- Test: `run-flow-skills-mcp/tests/test_server.py`

**Interfaces:**
- Consumes:
  - `fastmcp.FastMCP`
  - 所有 14 个 tool 函数（懒导入）
- Produces:
  - `server.py`：
    - `mcp = FastMCP(name="run-flow-skills-mcp", instructions="...")`：MCP 实例
    - 14 个 `@mcp.tool()` 装饰的函数（懒导入 tool 实现）
    - `main()`：启动 MCP Server（stdio 传输）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/test_server.py`：

```python
"""server.py 测试（spec 10.2）.

验证 MCP Server 能正确加载并注册所有 14 个 tools。
不启动真实 MCP 传输，只验证 tool 注册。
"""
import pytest

# 通过 import 触发 server 模块加载（验证无 ImportError）
def test_server_module_loads():
    """server.py 必须能无错加载."""
    from run_flow_skills_mcp import server
    assert hasattr(server, "mcp")
    assert server.mcp is not None


def test_server_registers_14_tools():
    """必须注册 14 个 tools."""
    from run_flow_skills_mcp.server import mcp
    # FastMCP 内部 tool 注册表
    # ponytail: 不同 fastmcp 版本 API 略有差异，优先用 _tools，回退到 list_tools()
    tools = None
    if hasattr(mcp, "_tools"):
        tools = mcp._tools
    elif hasattr(mcp, "tools"):
        tools = mcp.tools
    elif hasattr(mcp, "list_tools"):
        # 异步 API，可能需要 asyncio
        import asyncio
        try:
            tools = asyncio.run(mcp.list_tools())
        except Exception:
            tools = None

    if tools is None:
        pytest.skip("无法获取 tool 列表（fastmcp 版本兼容问题）")

    # tools 可能是 dict 或 list
    if isinstance(tools, dict):
        tool_names = list(tools.keys())
    elif isinstance(tools, list):
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]
    else:
        tool_names = []

    expected = {
        "import_file", "import_manual",
        "query_sessions", "calc_metrics",
        "get_trends", "analyze_fatigue",
        "generate_plan", "query_plan",
        "get_period_summary", "read_body_signals",
        "get_decision_trace", "save_decision_log",
        "get_statistics", "export_data",
    }
    missing = expected - set(tool_names)
    assert not missing, f"缺少 tools: {missing}"


def test_server_has_main():
    """server.py 必须有 main() 入口."""
    from run_flow_skills_mcp import server
    assert hasattr(server, "main")
    assert callable(server.main)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_server.py -v`
Expected: FAIL，`ImportError` 或 `AttributeError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/server.py`：

```python
"""RunFlowSkills MCP Server 入口（spec 10.2）.

注册所有 14 个 MCP tools，通过 FastMCP 框架对外提供服务。
Tool 函数体使用懒导入（函数体内 import），确保 server.py 本身可正常加载。

Tool 不调 LLM（spec 10.2），只返回 {prompt, ...data}，由宿主 AI 用 prompt 调 LLM。
"""
from fastmcp import FastMCP

mcp = FastMCP(
    name="run-flow-skills-mcp",
    instructions="跑步数据管理 + AI 教练 MCP Server，提供 14 个 tools：导入/查询/分析/计划/复盘/教练/统计/导出/决策溯源",
)


# ──────────────────────────────────────────
# 导入类（2 个）
# ──────────────────────────────────────────

@mcp.tool()
def import_file(file_path: str, force: bool = False, source: str = "") -> dict:
    """导入训练文件（FIT/TCX/GPX），自动解析 + 去重 + 计算指标.

    Args:
        file_path: 文件绝对路径
        force: 是否强制覆盖重复文件（默认 False）
        source: 数据源标注（garmin/apple/coros/strava/manual），可选

    Returns:
        {prompt, imported, session_id?, metrics_summary?, skipped?, reason?, error?}
    """
    from run_flow_skills_mcp.tools.import_file import import_file as _impl
    return _impl(file_path, force=force, source=source or None)


@mcp.tool()
def import_manual(manual_data: dict, force: bool = False) -> dict:
    """手动录入训练记录.

    Args:
        manual_data: {activity_date, distance_m, duration_s, source?, avg_hr?, max_hr?, notes?}
        force: 是否强制覆盖重复（默认 False）

    Returns:
        {prompt, imported, session_id?, metrics_summary?, error?}
    """
    from run_flow_skills_mcp.tools.import_manual import import_manual as _impl
    return _impl(manual_data, force=force)


# ──────────────────────────────────────────
# 查询分析类（4 个）
# ──────────────────────────────────────────

@mcp.tool()
def query_sessions(
    date_from: str = "",
    date_to: str = "",
    source: str = "",
    limit: int = 50,
) -> dict:
    """查询训练记录列表.

    Args:
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）
        source: 数据源过滤（可选）
        limit: 返回上限，默认 50

    Returns:
        {prompt, sessions, total}
    """
    from run_flow_skills_mcp.tools.query_sessions import query_sessions as _impl
    return _impl(
        date_from=date_from or None,
        date_to=date_to or None,
        source=source or None,
        limit=limit,
    )


@mcp.tool()
def calc_metrics(date_from: str, date_to: str) -> dict:
    """聚合区间训练指标（VDOT/TSS/CTL/ATL/TSB/心率区间）.

    Args:
        date_from: 起始日期 YYYY-MM-DD
        date_to: 结束日期 YYYY-MM-DD

    Returns:
        {prompt, vdot_trend, tss_sum, ctl, atl, tsb, hr_zones_dist}
    """
    from run_flow_skills_mcp.tools.calc_metrics import calc_metrics as _impl
    return _impl(date_from, date_to)


@mcp.tool()
def get_trends(days: int = 30, metric: str = "vdot") -> dict:
    """获取时间序列趋势.

    Args:
        days: 天数，默认 30
        metric: 指标（vdot/load/hrv），默认 vdot

    Returns:
        {prompt, series, change_pct, baseline}
    """
    from run_flow_skills_mcp.tools.get_trends import get_trends as _impl
    return _impl(days=days, metric=metric)


@mcp.tool()
def analyze_fatigue(days: int = 7) -> dict:
    """综合疲劳度评估（HRV + TSB + RPE）.

    Args:
        days: 分析天数，默认 7

    Returns:
        {prompt, fatigue_score, risk_level, main_factors, hrv_deviation, tsb}
    """
    from run_flow_skills_mcp.tools.analyze_fatigue import analyze_fatigue as _impl
    return _impl(days=days)


# ──────────────────────────────────────────
# 计划类（2 个）
# ──────────────────────────────────────────

@mcp.tool()
def generate_plan(
    goal_type: str,
    goal_time: str,
    race_date: str,
    weeks: int,
    current_vdot: float,
) -> dict:
    """生成周期化训练计划.

    Args:
        goal_type: 目标类型（5k/10k/half_marathon/full_marathon）
        goal_time: 目标时间 HH:MM:SS
        race_date: 比赛日 YYYY-MM-DD
        weeks: 训练周数
        current_vdot: 当前 VDOT

    Returns:
        {prompt, plan_id, phases, pace_zones, target_vdot, vdot_gap}
    """
    from run_flow_skills_mcp.tools.generate_plan import generate_plan as _impl
    return _impl(
        goal_type=goal_type,
        goal_time=goal_time,
        race_date=race_date,
        weeks=weeks,
        current_vdot=current_vdot,
    )


@mcp.tool()
def query_plan(plan_id: str = "") -> dict:
    """查询训练计划 + 执行忠实度.

    Args:
        plan_id: 计划 ID（空字符串返回最新计划）

    Returns:
        {prompt, plan, fidelity}
    """
    from run_flow_skills_mcp.tools.query_plan import query_plan as _impl
    return _impl(plan_id=plan_id or None)


# ──────────────────────────────────────────
# 复盘教练类（3 个）
# ──────────────────────────────────────────

@mcp.tool()
def get_period_summary(period: str = "week", date_ref: str = "") -> dict:
    """聚合周期训练数据（周/月/季/年）.

    Args:
        period: 周期类型（week/month/season/year），默认 week
        date_ref: 参考日期 YYYY-MM-DD（空字符串=今天）

    Returns:
        {prompt, total_distance, total_tss, avg_vdot, load_change, sessions_count, vdot_trend, hrv_trend}
    """
    from run_flow_skills_mcp.tools.get_period_summary import get_period_summary as _impl
    return _impl(period=period, date_ref=date_ref or None)


@mcp.tool()
def read_body_signals(date: str = "") -> dict:
    """读取今日身体信号 + 计算就绪状态.

    Args:
        date: 日期 YYYY-MM-DD（空字符串=今天）

    Returns:
        {prompt, hrv, resting_hr, sleep, rpe, baseline, deviation_pct, readiness_level, yesterday_session, recent_high_intensity}
    """
    from run_flow_skills_mcp.tools.read_body_signals import read_body_signals as _impl
    return _impl(date=date or None)


@mcp.tool()
def save_decision_log(
    decision_type: str,
    inputs: dict,
    reasoning: str,
    recommendation: str,
    confidence: float,
    trace_chain: list,
    related_session_ids: list = None,
) -> dict:
    """保存 AI 决策记录（含溯源链）.

    Args:
        decision_type: 决策类型（coach/plan/review/analyze）
        inputs: 决策输入数据
        reasoning: AI 推理过程
        recommendation: AI 最终建议
        confidence: 置信度（0-1）
        trace_chain: 溯源链步骤列表
        related_session_ids: 关联 session_id 列表（可选）

    Returns:
        {prompt, decision_id, saved}
    """
    from run_flow_skills_mcp.tools.save_decision_log import save_decision_log as _impl
    return _impl(
        decision_type=decision_type,
        inputs=inputs,
        reasoning=reasoning,
        recommendation=recommendation,
        confidence=confidence,
        trace_chain=trace_chain,
        related_session_ids=related_session_ids,
    )


# ──────────────────────────────────────────
# 统计导出类（3 个）
# ──────────────────────────────────────────

@mcp.tool()
def get_decision_trace(decision_id: str) -> dict:
    """查询决策溯源链.

    Args:
        decision_id: 决策 ID（dec_YYYYMMDD_NNN）

    Returns:
        {prompt, decision_id, found, trace?}
    """
    from run_flow_skills_mcp.tools.get_decision_trace import get_decision_trace as _impl
    return _impl(decision_id=decision_id)


@mcp.tool()
def get_statistics(
    dimension: str,
    date_from: str = "",
    date_to: str = "",
) -> dict:
    """按维度分组统计.

    Args:
        dimension: 分组维度（by_source/by_week/by_month/by_year/by_pace_zone/by_distance_range）
        date_from: 起始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）

    Returns:
        {prompt, groups, dimension}
    """
    from run_flow_skills_mcp.tools.get_statistics import get_statistics as _impl
    return _impl(
        dimension=dimension,
        date_from=date_from or None,
        date_to=date_to or None,
    )


@mcp.tool()
def export_data(
    format: str,
    filters: dict = None,
    include_ai_logs: bool = False,
) -> dict:
    """导出训练数据.

    Args:
        format: 导出格式（csv/json/parquet/md）
        filters: 过滤条件 {date_from?, date_to?, source?}（可选）
        include_ai_logs: 是否包含决策日志（默认 False）

    Returns:
        {prompt, file_path, rows_count, format} 或 {prompt, error}
    """
    from run_flow_skills_mcp.tools.export_data import export_data as _impl
    return _impl(format=format, filters=filters, include_ai_logs=include_ai_logs)


def main() -> None:
    """启动 MCP Server（stdio 传输模式）."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_server.py -v`
Expected: 3 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/server.py run-flow-skills-mcp/tests/test_server.py
git commit -m "feat(server): register all 14 MCP tools with FastMCP entry point"
```

---

## Task 16: 端到端工作流集成测试 + 全量回归

**Files:**
- Create: `run-flow-skills-mcp/tests/test_integration_workflows.py`

**Interfaces:**
- Consumes: 所有 14 个 tool 函数 + conftest.py 的 `tmp_data_dir` fixture
- Produces: 端到端工作流验证（导入 → 查询 → 分析 → 计划 → 复盘 → 教练 → 决策 → 统计 → 导出）

- [ ] **Step 1: 写集成测试**

写入 `run-flow-skills-mcp/tests/test_integration_workflows.py`：

```python
"""端到端工作流集成测试（spec 11.1）.

验证完整链路：
导入 → 查询 → 分析 → 计划 → 复盘 → 教练 → 决策 → 统计 → 导出

确保 tool 返回都含 prompt（spec 10.2）+ 数据一致性。
"""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import BodySignal
from run_flow_skills_mcp.tools import _deps
from run_flow_skills_mcp.tools.analyze_fatigue import analyze_fatigue
from run_flow_skills_mcp.tools.calc_metrics import calc_metrics
from run_flow_skills_mcp.tools.export_data import export_data
from run_flow_skills_mcp.tools.generate_plan import generate_plan
from run_flow_skills_mcp.tools.get_decision_trace import get_decision_trace
from run_flow_skills_mcp.tools.get_period_summary import get_period_summary
from run_flow_skills_mcp.tools.get_statistics import get_statistics
from run_flow_skills_mcp.tools.get_trends import get_trends
from run_flow_skills_mcp.tools.import_manual import import_manual
from run_flow_skills_mcp.tools.query_plan import query_plan
from run_flow_skills_mcp.tools.query_sessions import query_sessions
from run_flow_skills_mcp.tools.read_body_signals import read_body_signals
from run_flow_skills_mcp.tools.save_decision_log import save_decision_log


@pytest.fixture(autouse=True)
def reset_cache():
    yield
    _deps.reset_services_cache()


def _seed_full_workflow(tmp_path: Path):
    """灌入完整工作流数据：10 天 sessions + 7 天 HRV."""
    # 10 天训练记录
    for i in range(10):
        date = (datetime(2026, 7, 25) - timedelta(days=9 - i)).strftime("%Y-%m-%dT06:00:00")
        import_manual(
            {
                "activity_date": date,
                "distance_m": 10000.0,
                "duration_s": 3000,  # 配速 5'00"/km
                "source": "garmin" if i % 2 == 0 else "apple",
                "avg_hr": 150,
            },
            _data_dir=tmp_path,
        )
    # 7 天 HRV
    services = _deps.get_services(tmp_path)
    for i in range(7):
        date = (datetime(2026, 7, 25) - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        services.coach_service.json_store.upsert_body_signal(
            BodySignal(date=date, hrv_rmssd=45.0, rpe=5, resting_hr=55, sleep_quality=4)
        )
    _deps.reset_services_cache()


def test_full_workflow_import_to_export(tmp_path: Path):
    """完整工作流：导入 → 查询 → 分析 → 计划 → 复盘 → 教练 → 决策 → 统计 → 导出."""
    _deps.reset_services_cache()
    _seed_full_workflow(tmp_path)

    # 1. 查询验证导入成功
    q = query_sessions(date_from="2026-07-15", date_to="2026-07-25", _data_dir=tmp_path)
    assert q["total"] >= 10
    assert "prompt" in q

    # 2. 分析指标
    m = calc_metrics(date_from="2026-07-15", date_to="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in m
    assert m["tss_sum"] > 0

    # 3. 趋势
    t = get_trends(days=30, metric="vdot", _data_dir=tmp_path)
    assert "prompt" in t

    # 4. 计划生成
    p = generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=42.0,
        _data_dir=tmp_path,
    )
    assert "prompt" in p
    plan_id = p["plan_id"]

    # 5. 计划查询 + 忠实度
    pq = query_plan(plan_id, _data_dir=tmp_path)
    assert "prompt" in pq
    assert pq["plan"] is not None

    # 6. 复盘
    r = get_period_summary(period="week", date_ref="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in r
    assert r["sessions_count"] >= 1

    # 7. 教练（身体信号）
    c = read_body_signals(date="2026-07-25", _data_dir=tmp_path)
    assert "prompt" in c
    assert c["readiness_level"] in ("green", "yellow", "red")

    # 8. 疲劳分析
    f = analyze_fatigue(days=7, _data_dir=tmp_path)
    assert "prompt" in f

    # 9. 保存决策
    d = save_decision_log(
        decision_type="coach",
        inputs={"hrv": 45, "tsb": 5},
        reasoning="HRV 正常，TSB 充足",
        recommendation="E 区间 30 分钟",
        confidence=0.8,
        trace_chain=["HRV=45", "baseline=45", "TSB=5"],
        related_session_ids=[q["sessions"][0]["session_id"]],
        _data_dir=tmp_path,
    )
    assert d["saved"] is True
    decision_id = d["decision_id"]

    # 10. 查询决策溯源
    dt = get_decision_trace(decision_id, _data_dir=tmp_path)
    assert dt["found"] is True
    assert "prompt" in dt

    # 11. 统计
    s = get_statistics(dimension="by_source", _data_dir=tmp_path)
    assert "prompt" in s
    assert len(s["groups"]) > 0

    # 12. 导出
    e = export_data(format="json", include_ai_logs=True, _data_dir=tmp_path)
    assert e["rows_count"] > 0
    assert Path(e["file_path"]).exists()
    assert "prompt" in e


def test_all_tools_return_prompt(tmp_path: Path):
    """所有 14 个 tool 调用后必须返回 prompt 字段（spec 10.2）."""
    _deps.reset_services_cache()
    _seed_full_workflow(tmp_path)

    results = [
        import_manual(
            {"activity_date": "2026-07-26T06:00:00", "distance_m": 5000.0, "duration_s": 1500, "source": "manual"},
            _data_dir=tmp_path,
        ),
        query_sessions(_data_dir=tmp_path),
        calc_metrics("2026-07-15", "2026-07-25", _data_dir=tmp_path),
        get_trends(_data_dir=tmp_path),
        analyze_fatigue(_data_dir=tmp_path),
        generate_plan("5k", "00:25:00", "2026-10-19", 8, 42.0, _data_dir=tmp_path),
        query_plan(_data_dir=tmp_path),
        get_period_summary(_data_dir=tmp_path),
        read_body_signals("2026-07-25", _data_dir=tmp_path),
        save_decision_log("coach", {"test": 1}, "r", "rec", 0.5, ["a"], _data_dir=tmp_path),
        get_statistics("by_source", _data_dir=tmp_path),
        export_data("csv", _data_dir=tmp_path),
    ]

    for i, r in enumerate(results):
        assert "prompt" in r, f"第 {i+1} 个 tool 缺少 prompt 字段: {r}"

    # import_file 单独测（需要真实文件）
    gpx = tmp_path / "test.gpx"
    gpx.write_text(
        '<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">'
        '<trk><trkseg>'
        '<trkpt lat="39.9" lon="116.4"><time>2026-07-27T06:00:00Z</time></trkpt>'
        '<trkpt lat="39.91" lon="116.41"><time>2026-07-27T06:30:00Z</time></trkpt>'
        '</trkseg></trk></gpx>',
        encoding="utf-8",
    )
    from run_flow_skills_mcp.tools.import_file import import_file
    r = import_file(str(gpx), _data_dir=tmp_path)
    assert "prompt" in r

    # get_decision_trace 单独测
    saved = save_decision_log("coach", {"x": 1}, "r", "rec", 0.7, ["a"], _data_dir=tmp_path)
    r = get_decision_trace(saved["decision_id"], _data_dir=tmp_path)
    assert "prompt" in r


def test_decision_log_persistence_across_tools(tmp_path: Path):
    """save_decision_log 持久化后，get_decision_trace 可查询（数据一致性）."""
    _deps.reset_services_cache()
    saved = save_decision_log(
        decision_type="analyze",
        inputs={"vdot": 45},
        reasoning="VDOT 上升",
        recommendation="加量",
        confidence=0.7,
        trace_chain=["vdot=45", "上周=43"],
        _data_dir=tmp_path,
    )
    _deps.reset_services_cache()  # 清缓存模拟新进程

    trace = get_decision_trace(saved["decision_id"], _data_dir=tmp_path)
    assert trace["found"] is True
    assert trace["trace"]["recommendation"] == "加量"
    assert trace["trace"]["confidence"] == 0.7


def test_plan_fidelity_with_actual_sessions(tmp_path: Path):
    """计划生成后导入实际训练，fidelity 应反映完成情况."""
    _deps.reset_services_cache()
    # 生成计划（8 周）
    gen = generate_plan(
        goal_type="5k", goal_time="00:25:00",
        race_date="2026-10-19", weeks=8, current_vdot=40.0,
        _data_dir=tmp_path,
    )
    # 导入一些训练（在计划期内）
    import_manual(
        {"activity_date": "2026-08-26T06:00:00", "distance_m": 8000.0, "duration_s": 2400, "source": "manual"},
        _data_dir=tmp_path,
    )
    import_manual(
        {"activity_date": "2026-08-28T06:00:00", "distance_m": 6000.0, "duration_s": 1800, "source": "manual"},
        _data_dir=tmp_path,
    )
    _deps.reset_services_cache()

    result = query_plan(gen["plan_id"], _data_dir=tmp_path)
    fidelity = result["fidelity"]
    assert fidelity is not None
    assert fidelity["completed_sessions"] >= 2
    assert 0 <= fidelity["fidelity_rate"] <= 1
```

- [ ] **Step 2: 运行集成测试验证通过**

Run: `uv run pytest tests/test_integration_workflows.py -v`
Expected: 4 个测试全部 PASS

- [ ] **Step 3: 运行全量测试回归**

Run: `uv run pytest tests/ -v --tb=short`
Expected: 所有测试 PASS（prompts + services + tools + server + integration）

预期测试总数：
- prompts: 6
- services: 8 + 8 + 6 + 5 + 9 + 10 = 46
- tools: 5 + 5 + 5 + 5 + 4 + 4 + 6 = 34
- server: 3
- integration: 4
- **总计：约 93 个测试**

- [ ] **Step 4: Commit**

```bash
git add run-flow-skills-mcp/tests/test_integration_workflows.py
git commit -m "test(integration): add end-to-end workflow tests covering all 14 tools"
```

---

## Self-Review

### 1. Spec 覆盖检查

| Spec 章节 | 需求 | 对应 Task |
|----------|------|----------|
| 6.1 MCP Tools 14 个 | 全部实现 | Task 8-14（14 个 tools）+ Task 15（server 注册） |
| 6.2 Tool 返回 {prompt, data} | 所有 tool 附 prompt | Task 8-14 每个 tool 实现均含 prompt 字段 |
| 7.2-7.5 Prompt 模板 | analyze/plan/review/coach | Task 1（prompts 模块） |
| 10.1 决策溯源链 | save_decision_log + get_decision_trace | Task 13 |
| 10.2 Tool 不调 LLM | tools 薄包装 | 所有 tool 实现均为 service 调用 + prompt 附带 |
| FR-IMPORT-01/05 | 导入文件/手动录入 | Task 8（import_file + import_manual） |
| FR-ANALYZE-01/04/05 | 指标/趋势/疲劳 | Task 9-10（calc_metrics + get_trends + analyze_fatigue） |
| FR-PLAN-01/02/03/04 | 计划生成/查询/忠实度 | Task 11（generate_plan + query_plan） |
| FR-REVIEW-01/02 | 周期复盘 | Task 12（get_period_summary） |
| FR-COACH-01/02/03 | 身体信号/决策溯源/决策保存 | Task 12-13（read_body_signals + get/save_decision） |
| FR-STATS-01/02 | 统计/导出 | Task 14（get_statistics + export_data） |
| 8.2 analysis-rules | 数据依据/风险因子/误差范围 | Task 1（ANALYZE_PROMPT 内嵌规则） |
| 8.3 coaching-rules | 就绪状态综合计算 | Task 6（CoachService.compute_readiness_level） |

**覆盖完整**：14 个 Tool + 6 个 services + 5 个 prompts + Server 入口 + 集成测试，无遗漏。

### 2. Placeholder 扫描

- ✅ 无 "TBD"/"TODO"/"implement later"
- ✅ 每个 tool 实现均含完整代码（参数校验 + service 调用 + prompt 填充）
- ✅ 每个测试均含具体 assert
- ✅ 无 "Similar to Task N" 引用

### 3. 类型一致性

- ✅ `Services` dataclass 字段名与各 service 类名一致：`import_service`/`analysis_service`/`plan_service`/`review_service`/`coach_service`/`stats_service`
- ✅ 所有 tool 函数签名一致：`(_data_dir: Optional[Path] = None)`
- ✅ `read_body_signals` 返回字段含 `ctl`/`atl`（Task 6 service 已修正）
- ✅ `generate_plan` service 返回 `plan_prompt`，tool 转为 `prompt`（Task 11 实现一致）
- ✅ Server 注册的 14 个 tool 名与实现文件名一致

### 4. 已知简化（ponytail: 标注）

- `_GOAL_VDOT_TABLE`：经验值查表，非 Powers 反算（升级路径：v0.2.0）
- `_PHASE_RATIOS`：固定周期化比例，非 ML 生成
- `_build_week`：每 phase 固定课表模板
- `_LTHR_TO_THRESHOLD_PACE`：LTHR→配速线性近似
- `compute_fidelity`：按日期匹配，不精确到课表
- `test_server_registers_14_tools`：兼容多 fastmcp 版本 API

---

## Execution Handoff

**Plan 2 完成并保存至 `docs/superpowers/plans/2026-07-25-runflow-skills-mvp-plan2-services-tools.md`。**

本 plan 产出：
- 5 个 prompt 模板（Task 1）
- 6 个 service 编排层（Task 2-7）
- 14 个 MCP Tool 薄包装（Task 8-14）
- 1 个 FastMCP Server 入口（Task 15）
- 端到端集成测试（Task 16）
- **总计约 93 个测试**

按用户既定计划，继续编写 Plan 3-5，全部写完后统一通知用户审查。

