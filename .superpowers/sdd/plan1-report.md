# Plan 1 实现报告 - 基础设施层

> **日期**: 2026-07-25
> **Plan**: 2026-07-25-runflow-skills-mvp-plan1-infrastructure.md
> **状态**: DONE_WITH_CONCERNS

---

## 1. 实现了什么

完成 RunFlowSkills MCP Server 基础设施层全部 13 个 Task：

| Task | 模块 | 说明 |
|------|------|------|
| 1 | 项目骨架 | pyproject.toml / .gitignore / __init__.py / conftest.py |
| 2 | constants.py | 默认配置、区间常量、format_pace / format_duration |
| 3 | models.py | 10 个 Pydantic 模型 + generate_session_id |
| 4 | calculators/vdot.py | VDOT 计算（Powers 方法），<1500m 标 estimated |
| 5 | calculators/training_load.py | TSS / CTL / ATL / TSB / EWMA / IF |
| 6 | calculators/hrv.py | RMSSD / SDNN / pNN50 / 基线偏离 |
| 7 | calculators/pace_zones.py | E/M/T/I/R 配速区间 + 分类 |
| 8 | calculators/hr_zones.py | Z1-Z5 心率区间边界 + 样本分类 |
| 9 | calculators/fatigue.py | 疲劳度综合评估（HRV+TSB+RPE） |
| 10 | storage/parquet_store.py | Session/Metrics 按年分片 Parquet 读写 |
| 11 | storage/json_store.py | Load/BodySignal/DecisionLog/Plan/UserConfig JSON 读写 |
| 12 | storage/dedup.py | SHA256 去重 + 跨平台去重 |
| 13 | storage/importer.py | FIT/GPX/CSV/TCX/XML 解析 + SHA256 哈希 |

---

## 2. 测试结果

### 预期测试总数：104 个

| 测试文件 | 测试数 |
|----------|--------|
| test_constants.py | 9 |
| test_models.py | 13 |
| test_vdot.py | 8 |
| test_training_load.py | 11 |
| test_hrv.py | 11 |
| test_pace_zones.py | 7 |
| test_hr_zones.py | 6 |
| test_fatigue.py | 6 |
| test_parquet_store.py | 7 |
| test_json_store.py | 11 |
| test_dedup.py | 8 |
| test_importer.py | 7 |
| **合计** | **104** |

### 实际测试执行结果

**未执行** — 当前环境无 Shell 工具，无法运行 `uv sync` 和 `uv run pytest`。

请执行以下命令验证：

```powershell
cd d:\yecll\Documents\LocalCode\RunFlowSkills\run-flow-skills-mcp
uv sync --extra dev
uv run pytest tests/ -v --cov=src/run_flow_skills_mcp --cov-report=term-missing
```

---

## 3. TDD 证据

### RED 阶段
每个 Task 按计划先创建测试文件，测试因 `ImportError`（模块/函数不存在）而失败。
由于无 Shell 工具，RED 阶段的失败输出未能实际捕获，但测试文件先于实现文件创建，
且所有导入的目标函数/类在创建测试时确实不存在。

### GREEN 阶段
每个 Task 在测试文件创建后写入实现代码。实现严格按 Plan 提供的代码落地，
以下 Task 对 Plan 原始实现做了修正（详见第 5 节）：
- Task 9 (fatigue.py)：评分权重修正
- Task 10 (parquet_store.py)：弃用 API / 裸 Exception 修正
- Task 11 (json_store.py)：弃用 API 修正
- Task 12 (dedup.py)：session_id 跳过逻辑修正
- Task 13 (importer.py)：裸 Exception / 类型标注修正

---

## 4. 修改的文件列表

### 源码文件（15 个）
- `run-flow-skills-mcp/src/run_flow_skills_mcp/__init__.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/constants.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/models.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/__init__.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/vdot.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/training_load.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hrv.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/pace_zones.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hr_zones.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/fatigue.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/__init__.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/parquet_store.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/json_store.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/dedup.py`
- `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/importer.py`

### 测试文件（17 个）
- `run-flow-skills-mcp/tests/__init__.py`
- `run-flow-skills-mcp/tests/conftest.py`
- `run-flow-skills-mcp/tests/test_constants.py`
- `run-flow-skills-mcp/tests/test_models.py`
- `run-flow-skills-mcp/tests/calculators/__init__.py`
- `run-flow-skills-mcp/tests/calculators/test_vdot.py`
- `run-flow-skills-mcp/tests/calculators/test_training_load.py`
- `run-flow-skills-mcp/tests/calculators/test_hrv.py`
- `run-flow-skills-mcp/tests/calculators/test_pace_zones.py`
- `run-flow-skills-mcp/tests/calculators/test_hr_zones.py`
- `run-flow-skills-mcp/tests/calculators/test_fatigue.py`
- `run-flow-skills-mcp/tests/storage/__init__.py`
- `run-flow-skills-mcp/tests/storage/test_parquet_store.py`
- `run-flow-skills-mcp/tests/storage/test_json_store.py`
- `run-flow-skills-mcp/tests/storage/test_dedup.py`
- `run-flow-skills-mcp/tests/storage/test_importer.py`
- `run-flow-skills-mcp/tests/data/fixtures/.gitkeep`

### 配置文件（2 个）
- `run-flow-skills-mcp/pyproject.toml`
- `run-flow-skills-mcp/.gitignore`

---

## 5. 问题或疑虑

### 5.1 无 Shell 工具 — 无法执行测试和 git commit

当前环境仅有文件操作工具（Read/Write/Edit/Delete），无 Shell/Bash 工具。
因此以下环节需要你手动执行：

**依赖安装**：
```powershell
cd d:\yecll\Documents\LocalCode\RunFlowSkills\run-flow-skills-mcp
uv sync --extra dev
```

**全量测试**：
```powershell
uv run pytest tests/ -v --cov=src/run_flow_skills_mcp --cov-report=term-missing
```

**静态检查**：
```powershell
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/ --ignore-missing-imports
```

**冒烟测试**：
```powershell
uv run python -c "from run_flow_skills_mcp import constants, models; from run_flow_skills_mcp.calculators import vdot, training_load, hrv, pace_zones, hr_zones, fatigue; from run_flow_skills_mcp.storage import parquet_store, json_store, dedup, importer; print('All modules imported successfully')"
```

**Git 提交**（在项目根目录执行）：
```powershell
cd d:\yecll\Documents\LocalCode\RunFlowSkills

# Task 1
git add run-flow-skills-mcp/pyproject.toml run-flow-skills-mcp/.gitignore run-flow-skills-mcp/src/run_flow_skills_mcp/__init__.py run-flow-skills-mcp/tests/__init__.py run-flow-skills-mcp/tests/conftest.py
git commit -m "feat(scaffold): init run-flow-skills-mcp project skeleton"

# Task 2
git add run-flow-skills-mcp/src/run_flow_skills_mcp/constants.py run-flow-skills-mcp/tests/test_constants.py
git commit -m "feat(constants): add default config and zone factors with formatters"

# Task 3
git add run-flow-skills-mcp/src/run_flow_skills_mcp/models.py run-flow-skills-mcp/tests/test_models.py
git commit -m "feat(models): add pydantic data models for all core entities"

# Task 4
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/vdot.py run-flow-skills-mcp/tests/calculators/__init__.py run-flow-skills-mcp/tests/calculators/test_vdot.py
git commit -m "feat(calculators/vdot): implement VDOT calculation with Powers method"

# Task 5
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/training_load.py run-flow-skills-mcp/tests/calculators/test_training_load.py
git commit -m "feat(calculators/training_load): implement TSS/CTL/ATL/TSB and EWMA"

# Task 6
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hrv.py run-flow-skills-mcp/tests/calculators/test_hrv.py
git commit -m "feat(calculators/hrv): implement RMSSD/SDNN/pNN50 and baseline deviation"

# Task 7
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/pace_zones.py run-flow-skills-mcp/tests/calculators/test_pace_zones.py
git commit -m "feat(calculators/pace_zones): implement E/M/T/I/R zone calculation from VDOT"

# Task 8
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hr_zones.py run-flow-skills-mcp/tests/calculators/test_hr_zones.py
git commit -m "feat(calculators/hr_zones): implement HR zone boundaries and sample classification"

# Task 9
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/fatigue.py run-flow-skills-mcp/tests/calculators/test_fatigue.py
git commit -m "feat(calculators/fatigue): implement composite fatigue score from HRV/TSB/RPE"

# Task 10
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/storage/parquet_store.py run-flow-skills-mcp/tests/storage/__init__.py run-flow-skills-mcp/tests/storage/test_parquet_store.py
git commit -m "feat(storage/parquet_store): implement yearly-sharded Session/Metrics storage"

# Task 11
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/json_store.py run-flow-skills-mcp/tests/storage/test_json_store.py
git commit -m "feat(storage/json_store): implement JSON storage for Load/BodySignal/DecisionLog/Plan/UserConfig"

# Task 12
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/dedup.py run-flow-skills-mcp/tests/storage/test_dedup.py
git commit -m "feat(storage/dedup): implement SHA256 and cross-platform deduplication"

# Task 13
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/importer.py run-flow-skills-mcp/tests/storage/test_importer.py run-flow-skills-mcp/tests/data/fixtures/.gitkeep
git commit -m "feat(storage/importer): implement FIT/GPX/CSV/TCX/XML parsers with SHA256 dedup key"
```

### 5.2 Plan 实现代码的修正（5 处）

以下修正均因 Plan 原始实现与测试用例不一致或违反编码规范：

#### 5.2.1 Task 9 fatigue.py — 评分权重不匹配测试期望

**问题**：Plan 的权重（HRV 系数 2/上限 40、TSB 系数 1.5/上限 30、RPE 系数 5/上限 30）
无法让 `test_fatigue_hrv_low_returns_high`（hrv=-15, tsb=-10, rpe=[7,8,9]）达到 >=70 分
（实际仅得 30 分）。同时 HRV 阈值 -10% 与 `test_fatigue_partial_data_returns_moderate`（hrv=-8%）期望 `"hrv_deviation" in factors` 不一致。
且 `test_fatigue_all_normal_returns_low` 期望 `len(factors)==0`，但 Plan 在所有指标正常时
返回 `["insufficient_data"]`。

**修正**：
- HRV 阈值改为 -5% 起算，系数 3，上限 50
- TSB 系数 2，上限 40
- RPE 阈值改为 >=5 起算，系数 8，上限 30
- `insufficient_data` 仅在全部输入为 None 时返回（而非所有指标正常时）

#### 5.2.2 Task 10 parquet_store.py — 编码规范修正

- `datetime.utcnow()` → `datetime.now().year`（Python 3.12 弃用）
- `except Exception: continue` → 移除裸 Exception（改为让错误自然传播）
- `pl.lit(date_from).str.to_datetime()` → `datetime.strptime()` + end-of-day 处理
- `Session(**row)` / `TrainingMetrics(**row)` → `model_validate(row)` 避免 `# type: ignore`

#### 5.2.3 Task 11 json_store.py — 弃用 API 修正

- `datetime.utcnow().isoformat()` → `datetime.now(timezone.utc).isoformat()`
- `typing.Type` → `type`（Python 3.12 现代语法）
- 变量名 `l` → `item`（避免与 `1` 混淆）

#### 5.2.4 Task 12 dedup.py — session_id 跳过逻辑修正

**问题**：测试中 `_make_session` 对同一天的活动生成相同 `session_id`（`sess_20260725_001`），
导致 `find_cross_platform_duplicate` 的 `if existing.session_id == candidate.session_id: continue`
错误跳过了应匹配的已存会话。

**修正**：移除 session_id 跳过逻辑（候选会话尚未入库，不会匹配自身），仅保留 source 跳过。

#### 5.2.5 Task 13 importer.py — 编码规范修正

- `except Exception` → `except (OSError, ValueError, KeyError, RuntimeError)`（parse_fit）
- `import math` 移至模块顶部
- `dict[str, callable]` → `dict[str, Callable[..., Session]]`（callable 是函数不是类型）
- `parse_tcx` / `parse_xml` 的 except 增加 `ValueError`
- GPX 距离为 0 时 `distance_m` 和 `avg_pace` 设安全正值避免 ValidationError

### 5.3 models.py 未使用导入修正

Plan 的 models.py 导入了 `field_validator` 但未使用（ruff F401），已移除。

### 5.4 测试文件未使用导入修正

- `test_json_store.py`：移除未使用的 `import json`
- `test_vdot.py`：移除未使用的 `import pytest`
- `test_fatigue.py`：移除未使用的 `import pytest`
- `test_dedup.py`：移除未使用的 `timedelta` 导入

### 5.5 Plan 文档中测试数量与实际不一致

Plan 声称 Task 2 有 8 个测试（实际 9 个）、Task 3 有 12 个（实际 13 个）。
这不影响代码正确性，仅是文档计数偏差。

### 5.6 跨模块时区一致性潜在风险

importer.py 的 `parse_gpx` 生成 timezone-aware 的 `activity_date`（UTC），
而 `parquet_store.py` 的 `query_sessions` 用 naive `datetime.strptime` 做日期过滤。
若 parsed session 直接存入 parquet 再查询，可能因 timezone 不匹配导致过滤异常。
此为跨模块集成问题，Plan 1 单元测试不覆盖，需在 Plan 2 集成测试中验证。

---

## 6. 后续衔接

Plan 1 提供的接口供 Plan 2 使用：

| 接口 | 使用方（Plan 2） |
|------|-----------------|
| calc_vdot | analysis service / tools |
| calc_tss / calc_ctl / calc_atl / calc_tsb | training load service |
| calc_rmssd / calc_hrv_baseline | body signal service |
| calc_pace_zones / classify_pace_zone | plan service |
| calc_hr_zones_boundaries / classify_hr_samples | import service |
| calc_fatigue_score | coach service |
| ParquetStore | all services |
| JsonStore | all services |
| check_hash_duplicate / find_cross_platform_duplicate | import service |
| parse_file / compute_file_hash | import service |
