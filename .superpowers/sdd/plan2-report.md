# Plan 2 实施报告 — Services + 14 MCP Tools

**计划**: `docs/superpowers/plans/2026-07-25-runflow-skills-mvp-plan2-services-tools.md`
**基线版本**: v0.1.0 (MVP)
**完成日期**: 2026-07-25
**状态**: DONE

## 一、交付物总览

### 1.1 Services 层（6 个）

| 文件 | 职责 | 测试数 |
|------|------|--------|
| `src/run_flow_skills_mcp/services/import_service.py` | 文件解析 + 去重 + 指标计算 | 8 |
| `src/run_flow_skills_mcp/services/analysis_service.py` | 指标聚合 + 趋势 + 疲劳 | 7 |
| `src/run_flow_skills_mcp/services/plan_service.py` | 周期化计划生成 + 忠实度 | 6 |
| `src/run_flow_skills_mcp/services/review_service.py` | 周期复盘聚合 | 5 |
| `src/run_flow_skills_mcp/services/coach_service.py` | 身体信号 + 就绪状态 + 决策溯源 | 10 |
| `src/run_flow_skills_mcp/services/stats_service.py` | 多维统计 + CSV/JSON/Parquet/MD 导出 | 9 |

### 1.2 MCP Tools 层（14 个，spec 6.1）

| 类别 | Tool | 文件 | 测试数 |
|------|------|------|--------|
| 导入 | `import_file` | `tools/import_file.py` | 5 |
| 导入 | `import_manual` | `tools/import_manual.py` | （同上） |
| 查询 | `query_sessions` | `tools/query_sessions.py` | 5 |
| 查询 | `calc_metrics` | `tools/calc_metrics.py` | （同上） |
| 分析 | `get_trends` | `tools/get_trends.py` | 5 |
| 分析 | `analyze_fatigue` | `tools/analyze_fatigue.py` | （同上） |
| 计划 | `generate_plan` | `tools/generate_plan.py` | 5 |
| 计划 | `query_plan` | `tools/query_plan.py` | （同上） |
| 复盘 | `get_period_summary` | `tools/get_period_summary.py` | 4 |
| 教练 | `read_body_signals` | `tools/read_body_signals.py` | （同上） |
| 决策 | `save_decision_log` | `tools/save_decision_log.py` | 4 |
| 决策 | `get_decision_trace` | `tools/get_decision_trace.py` | （同上） |
| 统计 | `get_statistics` | `tools/get_statistics.py` | 6 |
| 导出 | `export_data` | `tools/export_data.py` | （同上） |

### 1.3 公共组件

- `src/run_flow_skills_mcp/tools/_deps.py`：`Services` dataclass + `get_services()` 单例工厂 + `reset_services_cache()`
- `src/run_flow_skills_mcp/server.py`：FastMCP 入口，14 个 `@mcp.tool()` 注册 + `main()` 启动 stdio 传输

### 1.4 端到端集成测试

- `tests/test_integration_workflows.py`：4 个跨 tool 链路测试

## 二、测试结果

### 2.1 全量回归

```
uv run pytest tests/ -v
============================ 198 passed in 20.81s =============================
```

### 2.2 分类统计

| 模块 | 测试数 |
|------|--------|
| constants | 11 |
| models | 13 |
| calculators（fatigue/hr_zones/hrv/pace_zones/training_load/vdot） | 50 |
| storage（dedup/importer/json_store/parquet_store） | 32 |
| prompts | 6 |
| services（import/analysis/plan/review/coach/stats） | 45 |
| tools（import/query/trends/plan/period/decision/stats） | 34 |
| server | 3 |
| integration | 4 |
| **总计** | **198** |

## 三、关键设计决策

### 3.1 Tool 不调 LLM（spec 10.2）

所有 14 个 tool 都是薄包装：
1. 参数校验（输入层防御）
2. 调用对应 service 方法（业务层）
3. 附 prompt 字符串（output schema 含 `prompt` 字段）

宿主 AI 用 `prompt` 调 LLM 生成自然语言反馈，tool 自身不依赖 LLM。

### 3.2 Services 单例工厂（spec 10.2）

`tools/_deps.py::get_services(data_dir)` 按 `data_dir` 缓存：
- 生产环境：默认 `constants.DATA_DIR`
- 测试环境：通过 `_data_dir` 参数注入 tmp_path，并 `reset_services_cache()` 隔离

`Services` dataclass 一次性定义 8 个字段（6 service + parquet_store + json_store），供 Plan 3 Web 层复用，避免跨 Plan 修改。

### 3.3 输入层降级（interaction-rules.md 第 4 条）

- `generate_plan` 工具层捕获 `pydantic.ValidationError`，返回降级结构（含 `error` + 降级 `prompt`）
- `import_file` 不支持格式返回 `error + prompt`，建议手动录入
- `export_data` 不支持格式返回 `error + prompt`
- `read_body_signals` 无数据时 None 值替换为 "无数据" 填入 prompt

### 3.4 CoachService 就绪状态（coaching-rules.md 第 3 条）

`compute_readiness_level(hrv_deviation, tsb, rpe)` 加权评分：
- 每指标 0/1/2 分（normal/warning/danger）
- 总分 0-1: green, 2-3: yellow, 4+: red
- 单一指标缺失计 0 分，避免单点决策

## 四、关键修复

### 4.1 VDOT 配速系数（Task 6 衍生修复）

`calculators/pace_zones.py`：`_VDOT_PACE_COEFF` 从 `4320.0` 修正为 `12420.0`，对齐注释 "VDOT 45 ≈ 276s/km"。

**根因**：原系数导致 VDOT 配速偏快，所有 pace_zone 分类错位，间接导致 `CoachService._detect_recent_high_intensity` 误判（高强度训练被归为 E 区间）。

**影响测试**：`test_read_body_signals_detects_recent_high_intensity` 由失败转通过。

### 4.2 COACH_PROMPT 字面花括号转义（Task 12 修复）

`prompts/coach_prompt.py`：`{置信度提示，若 < 0.6}` 转义为 `{{置信度提示，若 < 0.6}}`。

**根因**：`str.format` 将字面 `{...}` 误识别为占位符。修复后该位置输出为字面 `{置信度提示，若 < 0.6}`，符合 prompt 作者意图（对 LLM 的注释提示）。

### 4.3 DecisionLog decision_type 字面量（Task 16 修复）

集成测试原使用 `decision_type="analyze"`，实际 `DecisionLog` 模型约束为 `analysis`。修正测试用例对齐模型约束。

## 五、已知简化（ponytail: 标注）

- `_GOAL_VDOT_TABLE`：经验值查表，非 Powers 反算（升级路径：v0.2.0）
- `_PHASE_RATIOS`：固定周期化比例（base/build/peak/taper），非 ML 生成
- `_build_week`：每 phase 固定课表模板
- `compute_fidelity`：按日期匹配，不精确到课表内容
- `test_server_registers_14_tools`：通过 `asyncio.run(mcp.list_tools())` 兼容 FastMCP 3.x API
- `pace_zones._VDOT_PACE_COEFF`：VDOT→参考配速线性近似，非 Daniels 原始查表

## 六、Spec 覆盖检查

| Spec 章节 | 需求 | 对应 Task | 状态 |
|----------|------|----------|------|
| 6.1 MCP Tools 14 个 | 全部实现 | Task 8-14 + Task 15 | ✅ |
| 6.2 Tool 返回 {prompt, data} | 所有 tool 附 prompt | Task 8-14 | ✅ |
| 7.2-7.5 Prompt 模板 | analyze/plan/review/coach | Task 1 | ✅（前置） |
| 10.1 决策溯源链 | save/get_decision_log | Task 13 | ✅ |
| 10.2 Tool 不调 LLM | tools 薄包装 | Task 8-14 | ✅ |
| FR-IMPORT-01/05 | 文件/手动导入 | Task 8 | ✅ |
| FR-ANALYZE-01/04/05 | 指标/趋势/疲劳 | Task 9-10 | ✅ |
| FR-PLAN-01/02/03/04 | 计划生成/查询/忠实度 | Task 11 | ✅ |
| FR-REVIEW-01/02 | 周期复盘 | Task 12 | ✅ |
| FR-COACH-01/02/03 | 身体信号/决策 | Task 12-13 | ✅ |
| FR-STATS-01/02 | 统计/导出 | Task 14 | ✅ |
| 8.2 analysis-rules | 数据依据/风险因子 | Task 1（ANALYZE_PROMPT 内嵌） | ✅ |
| 8.3 coaching-rules | 就绪状态综合计算 | Task 6（compute_readiness_level） | ✅ |

## 七、提交记录

| Task | Commit | 说明 |
|------|--------|------|
| Task 6 | `87de713` | CoachService + VDOT pace 系数修正 |
| Task 7 | `a410379` | StatsService 多维聚合与导出 |
| Task 8 | `2d7f7e7` | _deps 工厂 + import_file/import_manual |
| Task 9 | `bdec9e5` | query_sessions + calc_metrics |
| Task 10 | `de07e8e` | get_trends + analyze_fatigue |
| Task 11 | `0c96163` | generate_plan + query_plan（含 ValidationError 降级） |
| Task 12 | `45ead5c` | get_period_summary + read_body_signals（含 COACH_PROMPT 转义修复） |
| Task 13 | `7e3e9ce` | get_decision_trace + save_decision_log |
| Task 14 | `ae52dcb` | get_statistics + export_data |
| Task 15 | `62e1792` | FastMCP server 入口注册 14 tools |
| Task 16 | `94c80aa` | 端到端集成测试 |

## 八、状态

**DONE** — 198/198 测试通过；6 services + 14 tools + FastMCP server 全部交付；spec 覆盖完整；集成测试验证端到端工作流。
