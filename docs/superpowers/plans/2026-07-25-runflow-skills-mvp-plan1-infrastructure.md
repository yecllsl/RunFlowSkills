# RunFlowSkills MVP v0.1.0 实现计划 - Plan 1: 基础设施

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 RunFlowSkills MCP Server 的基础设施层：项目骨架 + Pydantic 数据模型 + 默认配置 + 6 个纯计算器 + 4 个存储模块，为后续 Plan 2（Tools+Services）提供可独立测试的底座。

**Architecture:** 方案 B「薄 tools + 厚 calculators + services 编排」的最底层。calculators 是纯函数（无 IO，仅依赖 pyarrow/polars 数据结构），storage 提供 Parquet（Session/Metrics 按年分片）+ JSON（Load/BodySignal/DecisionLog/Plan/UserConfig）读写。本 plan 不涉及 MCP tools、Web、Skills，仅产出可被 `pytest tests/` 验证的基础组件。

**Tech Stack:** Python 3.12+ / pydantic 2.x / pyarrow 15+ / polars 0.20+ / fitparse 1.2+ / pytest 8+（TDD）/ ruff / mypy

## Global Constraints

- Python 版本：`>=3.12`（spec 11.1）
- 包名：`run-flow-skills-mcp`，模块名：`run_flow_skills_mcp`
- 数据目录：`run-flow-skills-mcp/data/`（.gitignore 排除）
- VDOT 计算：Powers 方法，距离 <1500m 标 "estimated"（spec 8.1.1）
- TSS 公式：`duration_s × IF² × 100`（spec 8.1.2）
- CTL/ATL：42 天 / 7 天 EWMA，α = 2/(N+1)（spec 8.1.3, 8.1.7）
- 配速格式：`M'SS"/km`，时长格式：`HH:MM:SS`（spec 8.1.4）
- 心率区间：基于个人最大心率/乳酸阈值心率，不可使用 220-年龄（spec 8.1.5）
- 配速区间：E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110% VDOT（spec 8.1.6）
- HRV 指标：RMSSD（主）/SDNN/pNN50，基线=7 天滚动均值（spec 8.1.8）
- 命名规范：类名 PascalCase，函数/变量 snake_case，常量 UPPER_SNAKE_CASE
- 编码规范：禁止 `# type: ignore`、`Dict[str, Any]`、裸 `Exception`
- 测试覆盖率：calculators ≥90%，storage/models ≥80%（spec 12.1）
- 提交规范：每个 task 末尾 `git commit`，信息格式 `feat/fix/test/docs(scope): 简述`

---

## 文件结构

本 plan 产出以下文件：

```
run-flow-skills-mcp/
├── pyproject.toml                              # Task 1
├── .gitignore                                  # Task 1
├── src/run_flow_skills_mcp/
│   ├── __init__.py                             # Task 1
│   ├── constants.py                            # Task 2
│   ├── models.py                               # Task 3
│   ├── calculators/
│   │   ├── __init__.py                         # Task 4
│   │   ├── vdot.py                             # Task 4
│   │   ├── training_load.py                    # Task 5
│   │   ├── hrv.py                              # Task 6
│   │   ├── pace_zones.py                       # Task 7
│   │   ├── hr_zones.py                         # Task 8
│   │   └── fatigue.py                          # Task 9
│   └── storage/
│       ├── __init__.py                         # Task 10
│       ├── parquet_store.py                    # Task 10
│       ├── json_store.py                       # Task 11
│       ├── dedup.py                            # Task 12
│       └── importer.py                         # Task 13
└── tests/
    ├── __init__.py                             # Task 1
    ├── conftest.py                             # Task 1
    ├── test_models.py                          # Task 3
    ├── test_constants.py                       # Task 2
    ├── calculators/
    │   ├── __init__.py                         # Task 4
    │   ├── test_vdot.py                        # Task 4
    │   ├── test_training_load.py               # Task 5
    │   ├── test_hrv.py                         # Task 6
    │   ├── test_pace_zones.py                  # Task 7
    │   ├── test_hr_zones.py                    # Task 8
    │   └── test_fatigue.py                     # Task 9
    ├── storage/
    │   ├── __init__.py                         # Task 10
    │   ├── test_parquet_store.py               # Task 10
    │   ├── test_json_store.py                  # Task 11
    │   ├── test_dedup.py                       # Task 12
    │   └── test_importer.py                    # Task 13
    └── data/
        └── fixtures/                           # Task 13（合成 FIT/GPX 测试文件）
```

---

## Task 1: 项目骨架与依赖初始化

**Files:**
- Create: `run-flow-skills-mcp/pyproject.toml`
- Create: `run-flow-skills-mcp/.gitignore`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/__init__.py`
- Create: `run-flow-skills-mcp/tests/__init__.py`
- Create: `run-flow-skills-mcp/tests/conftest.py`

**Interfaces:**
- Consumes: 无（首个 task）
- Produces: 可被 `uv sync --extra dev` 安装的项目骨架；`run_flow_skills_mcp` 可导入的空包；`tests/` 可运行 pytest

- [ ] **Step 1: 创建 pyproject.toml**

写入 `run-flow-skills-mcp/pyproject.toml`：

```toml
[project]
name = "run-flow-skills-mcp"
version = "0.1.0"
description = "深度跑步分析 Skills 套件 - MCP Server + Web"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=3.0.0",
    "pydantic>=2.0.0",
    "pyarrow>=15.0.0",
    "polars>=0.20.0",
    "fitparse>=1.2.0",
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "jinja2>=3.1",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
ml = [
    "scikit-learn>=1.5.0",
    "scipy>=1.10.0",
    "joblib>=1.3.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.27",
    "playwright>=1.40",
    "ruff>=0.5.0",
    "mypy>=1.10",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/run_flow_skills_mcp"]

[tool.pytest.ini_options]
markers = [
    "e2e: Playwright E2E tests, run with `uv run pytest -m e2e`",
]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A"]

[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
strict_optional = true
```

- [ ] **Step 2: 创建 .gitignore**

写入 `run-flow-skills-mcp/.gitignore`：

```
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.venv/
data/
!tests/data/fixtures/.gitkeep
```

- [ ] **Step 3: 创建包与测试 __init__.py**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/__init__.py`：

```python
"""RunFlowSkills MCP Server - 深度跑步分析 Skills 套件."""

__version__ = "0.1.0"
```

写入 `run-flow-skills-mcp/tests/__init__.py`（空文件）：

```python
```

- [ ] **Step 4: 创建 conftest.py 提供公共 fixture**

写入 `run-flow-skills-mcp/tests/conftest.py`：

```python
"""Pytest 公共 fixture."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_data_dir() -> Path:
    """提供临时 data/ 目录，测试结束自动清理."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "data"
        path.mkdir()
        (path / "sessions").mkdir()
        (path / "metrics").mkdir()
        (path / "load").mkdir()
        (path / "body_signals").mkdir()
        (path / "decisions").mkdir()
        (path / "plans").mkdir()
        yield path
```

- [ ] **Step 5: 安装依赖并验证骨架**

Run: `cd run-flow-skills-mcp && uv sync --extra dev`
Expected: 成功创建 `.venv/` 并安装所有 dev 依赖，无错误

Run: `uv run python -c "import run_flow_skills_mcp; print(run_flow_skills_mcp.__version__)"`
Expected: 输出 `0.1.0`

Run: `uv run pytest --co`
Expected: `no tests ran`（无测试收集，但无错误）

- [ ] **Step 6: Commit**

```bash
git add run-flow-skills-mcp/pyproject.toml run-flow-skills-mcp/.gitignore run-flow-skills-mcp/src/run_flow_skills_mcp/__init__.py run-flow-skills-mcp/tests/__init__.py run-flow-skills-mcp/tests/conftest.py
git commit -m "feat(scaffold): init run-flow-skills-mcp project skeleton"
```

---

## Task 2: constants.py 默认配置与区间常量

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/constants.py`
- Test: `run-flow-skills-mcp/tests/test_constants.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `DEFAULT_MAX_HR: int`（默认最大心率，190）
  - `DEFAULT_LTHR: int`（默认乳酸阈值心率，165）
  - `DEFAULT_RESTING_HR: int`（默认静息心率，60）
  - `PACE_ZONE_FACTORS: dict[str, tuple[float, float]]`（E/M/T/I/R 占 VDOT 比例区间）
  - `HR_ZONE_FACTORS: dict[str, float]`（Z1-Z5 占最大心率比例上限）
  - `CTL_WINDOW_DAYS: int`（42）
  - `ATL_WINDOW_DAYS: int`（7）
  - `HRV_BASELINE_DAYS: int`（7）
  - `DEDUP_TIME_TOLERANCE_S: int`（300，5 分钟）
  - `DEDUP_DISTANCE_TOLERANCE_PCT: float`（0.02，2%）
  - `DEDUP_DURATION_TOLERANCE_S: int`（30）
  - `SUPPORTED_IMPORT_EXT: tuple[str, ...]`（".fit", ".gpx", ".csv", ".tcx", ".xml"）
  - `WEB_HOST: str`（"127.0.0.1"）
  - `WEB_PORT: int`（8002）
  - `format_pace(s_per_km: float) -> str`（配速格式化）
  - `format_duration(seconds: int) -> str`（时长格式化）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/test_constants.py`：

```python
"""constants.py 单元测试."""
from run_flow_skills_mcp.constants import (
    ATL_WINDOW_DAYS,
    CTL_WINDOW_DAYS,
    DEFAULT_LTHR,
    DEFAULT_MAX_HR,
    DEDUP_DISTANCE_TOLERANCE_PCT,
    DEDUP_DURATION_TOLERANCE_S,
    DEDUP_TIME_TOLERANCE_S,
    HRV_BASELINE_DAYS,
    PACE_ZONE_FACTORS,
    SUPPORTED_IMPORT_EXT,
    format_duration,
    format_pace,
)


def test_default_hr_values():
    assert DEFAULT_MAX_HR == 190
    assert DEFAULT_LTHR == 165
    assert DEFAULT_RESTING_HR := __import__(
        "run_flow_skills_mcp.constants", fromlist=["DEFAULT_RESTING_HR"]
    ).DEFAULT_RESTING_HR == 60


def test_ewma_windows():
    assert CTL_WINDOW_DAYS == 42
    assert ATL_WINDOW_DAYS == 7
    assert HRV_BASELINE_DAYS == 7


def test_pace_zone_factors_cover_all_zones():
    """E/M/T/I/R 五个区间都必须定义."""
    for zone in ("E", "M", "T", "I", "R"):
        assert zone in PACE_ZONE_FACTORS
        lo, hi = PACE_ZONE_FACTORS[zone]
        assert 0 < lo <= hi <= 1.1


def test_pace_zone_factors_values_match_spec():
    """spec 8.1.6: E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110%."""
    assert PACE_ZONE_FACTORS["E"] == (0.59, 0.74)
    assert PACE_ZONE_FACTORS["M"] == (0.75, 0.84)
    assert PACE_ZONE_FACTORS["T"] == (0.88, 1.00)
    assert PACE_ZONE_FACTORS["I"] == (0.95, 1.00)
    assert PACE_ZONE_FACTORS["R"] == (1.00, 1.10)


def test_dedup_tolerances():
    assert DEDUP_TIME_TOLERANCE_S == 300
    assert DEDUP_DISTANCE_TOLERANCE_PCT == 0.02
    assert DEDUP_DURATION_TOLERANCE_S == 30


def test_supported_import_ext_includes_gpx():
    """M-1 评审修正：GPX 必须在白名单."""
    assert ".gpx" in SUPPORTED_IMPORT_EXT
    assert set(SUPPORTED_IMPORT_EXT) == {".fit", ".gpx", ".csv", ".tcx", ".xml"}


def test_format_pace_normal():
    """5'40"/km 格式."""
    assert format_pace(340.0) == "5'40\"/km"
    assert format_pace(360.0) == "6'00\"/km"
    assert format_pace(361.0) == "6'01\"/km"


def test_format_pace_sub_minute():
    """3'05"/km."""
    assert format_pace(185.0) == "3'05\"/km"


def test_format_duration_normal():
    assert format_duration(3725) == "01:02:05"
    assert format_duration(60) == "00:01:00"
    assert format_duration(0) == "00:00:00"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_constants.py -v`
Expected: FAIL，所有测试因 `ImportError: cannot import name 'DEFAULT_MAX_HR'...` 失败

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/constants.py`：

```python
"""RunFlowSkills 默认配置与常量.

所有 # DEFAULT 标记的常量可被 data/config.json (UserConfig) 覆盖。
计算器读取顺序：data/config.json → 本文件默认值。
"""
from __future__ import annotations

# ============ 用户生理参数默认值（M-3 评审修正）============
# DEFAULT — 用户可经 Web /settings 覆盖
DEFAULT_MAX_HR: int = 190
DEFAULT_LTHR: int = 165  # 乳酸阈值心率
DEFAULT_RESTING_HR: int = 60
DEFAULT_AGE: int = 30
DEFAULT_WEIGHT_KG: float = 65.0
DEFAULT_HEIGHT_CM: float = 170.0
DEFAULT_GENDER: str = "male"  # "male" | "female"，与 UserConfig.gender 对齐

# ============ VDOT 计算阈值（spec 8.1.1）============
VDOT_MIN_DISTANCE_M: float = 1500.0  # >=1500m 视为可信计算，否则标 "estimated"

# ============ EWMA 窗口（spec 8.1.3, 8.1.8）============
CTL_WINDOW_DAYS: int = 42
ATL_WINDOW_DAYS: int = 7
HRV_BASELINE_DAYS: int = 7

# ============ 配速区间占 VDOT 比例（spec 8.1.6）============
# (min_factor, max_factor)：配速 = VDOT 配速 / factor
PACE_ZONE_FACTORS: dict[str, tuple[float, float]] = {
    "E": (0.59, 0.74),  # 轻松跑
    "M": (0.75, 0.84),  # 马拉松配速
    "T": (0.88, 1.00),  # 乳酸阈值
    "I": (0.95, 1.00),  # 间歇
    "R": (1.00, 1.10),  # 重复
}

# ============ 心率区间占最大心率比例上限（spec 8.1.5）============
# 每个值表示该区间的上限占 max_hr 的比例；calc_hr_zones_boundaries 依此划分
HR_ZONE_FACTORS: dict[str, float] = {
    "Z1": 0.50,  # Z1: 0-50% max_hr
    "Z2": 0.60,  # Z2: 50-60% max_hr
    "Z3": 0.70,  # Z3: 60-70% max_hr
    "Z4": 0.90,  # Z4: 70-90% max_hr
    "Z5": 1.00,  # Z5: 90-100% max_hr
}

# ============ 去重容差（spec 5.3）============
DEDUP_TIME_TOLERANCE_S: int = 300  # 5 分钟
DEDUP_DISTANCE_TOLERANCE_PCT: float = 0.02  # 2%
DEDUP_DURATION_TOLERANCE_S: int = 30

# ============ 导入白名单（M-1 评审修正：含 GPX）============
SUPPORTED_IMPORT_EXT: tuple[str, ...] = (".fit", ".gpx", ".csv", ".tcx", ".xml")

# ============ Web 服务配置（spec 9.1）============
WEB_HOST: str = "127.0.0.1"
WEB_PORT: int = 8002

# ============ 文件大小/批量限制（spec 9.5）============
MAX_UPLOAD_FILE_SIZE_MB: int = 100
MAX_BATCH_UPLOAD_FILES: int = 100


def format_pace(s_per_km: float) -> str:
    """配速格式化为 M'SS"/km（spec 8.1.4）.

    >>> format_pace(340.0)
    "5'40\\"/km"
    """
    total_seconds = int(round(s_per_km))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}'{seconds:02d}\"/km"


def format_duration(seconds: int) -> str:
    """时长格式化为 HH:MM:SS（spec 8.1.4）.

    >>> format_duration(3725)
    "01:02:05"
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_constants.py -v`
Expected: 8 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/constants.py run-flow-skills-mcp/tests/test_constants.py
git commit -m "feat(constants): add default config and zone factors with formatters"
```

---

## Task 3: models.py Pydantic 数据模型

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/models.py`
- Test: `run-flow-skills-mcp/tests/test_models.py`

**Interfaces:**
- Consumes: 无（仅 pydantic）
- Produces:
  - `Session`、`TrainingMetrics`、`TrainingLoad`、`BodySignal`、`DecisionLog`、`TrainingPlan`、`PlanPhase`、`PlanWeek`、`PlanSession`、`UserConfig` Pydantic 模型
  - `generate_session_id(date_str: str, existing_count: int) -> str` 工具函数

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/test_models.py`：

```python
"""models.py 单元测试."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from run_flow_skills_mcp.models import (
    BodySignal,
    DecisionLog,
    PlanPhase,
    PlanSession,
    PlanWeek,
    Session,
    TrainingLoad,
    TrainingMetrics,
    TrainingPlan,
    UserConfig,
    generate_session_id,
)


def test_session_valid():
    s = Session(
        session_id="sess_20260725_001",
        activity_date=datetime(2026, 7, 25, 6, 0, 0),
        distance_m=10000.0,
        duration_s=3600,
        avg_pace_s_per_km=360.0,
        source="garmin",
    )
    assert s.session_id == "sess_20260725_001"
    assert s.avg_hr is None
    assert s.raw_file_hash is None


def test_session_invalid_distance_zero():
    with pytest.raises(ValidationError):
        Session(
            session_id="sess_20260725_001",
            activity_date=datetime(2026, 7, 25),
            distance_m=0,
            duration_s=3600,
            avg_pace_s_per_km=360.0,
            source="garmin",
        )


def test_session_invalid_duration_negative():
    with pytest.raises(ValidationError):
        Session(
            session_id="sess_20260725_001",
            activity_date=datetime(2026, 7, 25),
            distance_m=10000.0,
            duration_s=-1,
            avg_pace_s_per_km=360.0,
            source="garmin",
        )


def test_session_invalid_source():
    with pytest.raises(ValidationError):
        Session(
            session_id="sess_20260725_001",
            activity_date=datetime(2026, 7, 25),
            distance_m=10000.0,
            duration_s=3600,
            avg_pace_s_per_km=360.0,
            source="xiaomi",  # 不在枚举内
        )


def test_training_metrics_vdot_confidence_enum():
    m = TrainingMetrics(
        session_id="sess_20260725_001",
        vdot=45.0,
        vdot_confidence="high",
        tss=100.0,
        intensity_factor=0.85,
        pace_zone="T",
    )
    assert m.vdot_confidence == "high"
    assert m.efficiency_factor is None


def test_training_metrics_invalid_confidence():
    with pytest.raises(ValidationError):
        TrainingMetrics(
            session_id="sess_20260725_001",
            vdot=45.0,
            vdot_confidence="medium",  # 不在枚举内
            tss=100.0,
            intensity_factor=0.85,
            pace_zone="T",
        )


def test_training_load_valid():
    load = TrainingLoad(
        date="2026-07-25",
        ctl=65.0,
        atl=58.0,
        tsb=7.0,
        weekly_tss=350.0,
        updated_at=datetime(2026, 7, 25, 23, 0, 0),
    )
    assert load.tsb == load.ctl - load.atl


def test_body_signal_optional_fields():
    b = BodySignal(date="2026-07-25")
    assert b.hrv_rmssd is None
    assert b.rpe is None


def test_decision_log_trace_chain():
    d = DecisionLog(
        decision_id="dec_20260725_001",
        timestamp=datetime(2026, 7, 25, 8, 0, 0),
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="HRV 偏低",
        recommendation="E 区间 30 分钟",
        confidence=0.7,
        trace_chain=["HRV=38", "baseline=45", "rule:HRV偏离>10%"],
    )
    assert len(d.trace_chain) == 3
    assert d.user_feedback is None


def test_training_plan_with_phases():
    plan = TrainingPlan(
        plan_id="plan_20260725_001",
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
        target_vdot=43.5,
        phases=[
            PlanPhase(
                phase_type="base",
                weeks=[PlanWeek(week_index=1, sessions=[
                    PlanSession(day=0, pace_zone="E", duration_s=1800),
                ])],
            )
        ],
        created_at=datetime(2026, 7, 25),
        status="draft",
    )
    assert plan.phases[0].weeks[0].sessions[0].pace_zone == "E"


def test_user_config_all_optional():
    """M-3 评审修正：所有字段可空，回退到 constants.py 默认值."""
    c = UserConfig()
    assert c.max_hr is None
    assert c.lthr is None
    assert c.updated_at is None


def test_user_config_gender_enum():
    c = UserConfig(gender="male", age=35)
    assert c.gender == "male"
    with pytest.raises(ValidationError):
        UserConfig(gender="other")  # 不在枚举内


def test_generate_session_id_format():
    """sess_YYYYMMDD_NNN，NNN 从 001 起."""
    assert generate_session_id("20260725", 0) == "sess_20260725_001"
    assert generate_session_id("20260725", 5) == "sess_20260725_006"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL，`ImportError: cannot import name 'Session'...`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/models.py`：

```python
"""RunFlowSkills Pydantic 数据模型.

所有核心实体在 models.py 统一定义，对应 spec 第四章。
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ============ 类型别名 ============
SourceType = Literal["garmin", "coros", "apple", "suunto", "polar", "manual"]
PaceZone = Literal["E", "M", "T", "I", "R"]
GoalType = Literal["full_marathon", "half_marathon", "10k", "5k"]
Gender = Literal["male", "female"]


# ============ 4.1 Session ============
class Session(BaseModel):
    """单次跑步记录（核心实体，Parquet 按年分片）."""

    session_id: str = Field(..., pattern=r"^sess_\d{8}_\d{3}$")
    activity_date: datetime
    distance_m: float = Field(..., gt=0)
    duration_s: int = Field(..., gt=0)
    avg_pace_s_per_km: float = Field(..., gt=0)
    avg_hr: Optional[int] = Field(None, ge=0, le=260)
    max_hr: Optional[int] = Field(None, ge=0, le=260)
    hr_zones: Optional[dict[str, float]] = None
    cadence: Optional[int] = Field(None, ge=0, le=300)
    elevation_gain_m: Optional[float] = Field(None, ge=0)
    source: SourceType
    raw_file_hash: Optional[str] = None
    raw_file_path: Optional[str] = None
    notes: Optional[str] = None


# ============ 4.2 TrainingMetrics ============
class TrainingMetrics(BaseModel):
    """训练指标（由 Session 计算，Parquet 按年分片）."""

    session_id: str
    vdot: Optional[float] = Field(None, ge=0, le=100)
    vdot_confidence: Literal["high", "estimated", "low"]
    tss: float = Field(..., ge=0)
    intensity_factor: float = Field(..., ge=0)
    efficiency_factor: Optional[float] = None
    pace_zone: PaceZone


# ============ 4.3 TrainingLoad ============
class TrainingLoad(BaseModel):
    """训练负荷（日聚合，JSON 单文件追加）."""

    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    ctl: float
    atl: float
    tsb: float
    weekly_tss: float
    updated_at: datetime


# ============ 4.4 BodySignal ============
class BodySignal(BaseModel):
    """身体信号（日粒度，JSON 按月分文件）."""

    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    hrv_rmssd: Optional[float] = Field(None, ge=0)
    hrv_sdnn: Optional[float] = Field(None, ge=0)
    hrv_pnn50: Optional[float] = Field(None, ge=0, le=100)
    resting_hr: Optional[int] = Field(None, ge=0, le=260)
    sleep_quality: Optional[int] = Field(None, ge=1, le=5)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    hrv_baseline: Optional[float] = Field(None, ge=0)
    hrv_deviation_pct: Optional[float] = None


# ============ 4.5 DecisionLog ============
class DecisionLog(BaseModel):
    """AI 决策记录（transparency 核心，JSON 按月分文件）."""

    decision_id: str = Field(..., pattern=r"^dec_\d{8}_\d{3}$")
    timestamp: datetime
    decision_type: Literal["coach", "plan_adjust", "review", "analysis"]
    inputs: dict
    reasoning: str
    recommendation: str
    confidence: float = Field(..., ge=0, le=1)
    trace_chain: list[str]
    related_session_ids: list[str] = []
    user_feedback: Optional[Literal["adopted", "rejected", "modified"]] = None


# ============ 4.6 TrainingPlan ============
class PlanSession(BaseModel):
    """计划内单次训练."""

    day: int = Field(..., ge=0, le=6)
    pace_zone: Literal["E", "M", "T", "I", "R", "rest"]
    duration_s: int = Field(..., gt=0)
    distance_m: Optional[float] = Field(None, gt=0)
    pace_range_s_per_km: Optional[tuple[float, float]] = None
    hr_range: Optional[tuple[int, int]] = None
    notes: Optional[str] = None


class PlanWeek(BaseModel):
    """计划周."""

    week_index: int = Field(..., ge=1)
    sessions: list[PlanSession]


class PlanPhase(BaseModel):
    """计划阶段."""

    phase_type: Literal["base", "build", "peak", "taper"]
    weeks: list[PlanWeek]


class TrainingPlan(BaseModel):
    """训练计划（JSON 单文件/计划）."""

    plan_id: str = Field(..., pattern=r"^plan_\d{8}_\d{3}$")
    goal_type: GoalType
    goal_time: str
    race_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    weeks: int = Field(..., ge=1, le=52)
    current_vdot: float = Field(..., ge=0, le=100)
    target_vdot: float = Field(..., ge=0, le=100)
    phases: list[PlanPhase]
    created_at: datetime
    status: Literal["draft", "active", "completed", "abandoned"]


# ============ 4.7 UserConfig（M-3 评审修正）============
class UserConfig(BaseModel):
    """用户个人配置（JSON 单文件 data/config.json，覆盖 constants.py 默认值）."""

    max_hr: Optional[int] = Field(None, ge=80, le=260)
    lthr: Optional[int] = Field(None, ge=60, le=220)
    resting_hr: Optional[int] = Field(None, ge=30, le=150)
    age: Optional[int] = Field(None, ge=10, le=120)
    weight_kg: Optional[float] = Field(None, gt=0, le=300)
    gender: Optional[Gender] = None
    height_cm: Optional[float] = Field(None, gt=0, le=300)
    updated_at: Optional[datetime] = None


# ============ 工具函数 ============
def generate_session_id(date_str: str, existing_count: int) -> str:
    """生成 session_id：sess_YYYYMMDD_NNN.

    Args:
        date_str: 8 位日期字符串，如 "20260725"
        existing_count: 当天已存在的 session 数量

    Returns:
        形如 sess_20260725_001 的 ID（NNN = existing_count + 1）
    """
    return f"sess_{date_str}_{existing_count + 1:03d}"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_models.py -v`
Expected: 12 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/models.py run-flow-skills-mcp/tests/test_models.py
git commit -m "feat(models): add pydantic data models for all core entities"
```

---

## Task 4: calculators/vdot.py VDOT 计算（Powers 方法）

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/__init__.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/vdot.py`
- Test: `run-flow-skills-mcp/tests/calculators/__init__.py`
- Test: `run-flow-skills-mcp/tests/calculators/test_vdot.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `calc_vdot(distance_m: float, duration_s: int) -> tuple[Optional[float], Literal["high","estimated","low"]]`
  - 返回 (vdot 值或 None, confidence)；距离 <1500m 返回 (估算值, "estimated")，>=1500m 返回 (计算值, "high")；duration<=0 返回 (None, "low")

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/calculators/__init__.py`（空）：

```python
```

写入 `run-flow-skills-mcp/tests/calculators/test_vdot.py`：

```python
"""VDOT 计算单元测试（spec 8.1.1, FR-ANALYZE-01）."""
import pytest

from run_flow_skills_mcp.calculators.vdot import calc_vdot


def test_vdot_5k_normal():
    """5K 25 分钟 → VDOT 约 30."""
    vdot, conf = calc_vdot(5000.0, 1500)
    assert vdot is not None
    assert 28 <= vdot <= 33
    assert conf == "high"


def test_vdot_marathon_sub4():
    """全马 4 小时 → VDOT 约 36-37."""
    vdot, conf = calc_vdot(42195.0, 14400)
    assert vdot is not None
    assert 35 <= vdot <= 39
    assert conf == "high"


def test_vdot_below_1500m_marked_estimated():
    """距离 <1500m 标 'estimated'（spec 8.1.1）."""
    vdot, conf = calc_vdot(1200.0, 360)
    assert conf == "estimated"
    assert vdot is not None  # 仍给出估算值


def test_vdot_exactly_1500m_high_confidence():
    """距离 =1500m 视为达标（spec FR-ANALYZE-01 边界）."""
    vdot, conf = calc_vdot(1500.0, 360)
    assert conf == "high"


def test_vdot_zero_duration_returns_none():
    vdot, conf = calc_vdot(5000.0, 0)
    assert vdot is None
    assert conf == "low"


def test_vdot_negative_duration_returns_none():
    vdot, conf = calc_vdot(5000.0, -10)
    assert vdot is None
    assert conf == "low"


def test_vdot_zero_distance_returns_none():
    vdot, conf = calc_vdot(0.0, 1500)
    assert vdot is None
    assert conf == "low"


def test_vdot_elite_runner():
    """全马 2:30 → VDOT 约 60-65."""
    vdot, conf = calc_vdot(42195.0, 9012)
    assert vdot is not None
    assert 58 <= vdot <= 67
    assert conf == "high"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/calculators/test_vdot.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/__init__.py`：

```python
"""calculators 子包：纯计算函数（无 IO）."""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/vdot.py`：

```python
"""VDOT 计算器 - Powers 方法（spec 8.1.1, FR-ANALYZE-01）.

参考：Jack Daniels' VDOT formula
VDOT = (-4.6 + 0.182258 * VO2 + 0.000104 * VO2^2) / (0.8 + 0.1894393 * e^(-0.012778*t) + 0.2989558 * e^(-0.1932605*t))
VO2 = 0.000104 * distance_m^2 / duration_min + 0.182258 * distance_m / duration_min - 4.60
"""
from __future__ import annotations

import math
from typing import Literal, Optional

from run_flow_skills_mcp.constants import VDOT_MIN_DISTANCE_M


def _compute_vo2(distance_m: float, duration_min: float) -> float:
    """计算 VO2（ml/kg/min）."""
    return (
        0.000104 * distance_m**2 / duration_min
        + 0.182258 * distance_m / duration_min
        - 4.60
    )


def _compute_vdot_from_vo2(vo2: float, duration_min: float) -> float:
    """由 VO2 和时长计算 VDOT."""
    e1 = math.exp(-0.012778 * duration_min)
    e2 = math.exp(-0.1932605 * duration_min)
    denom = 0.8 + 0.1894393 * e1 + 0.2989558 * e2
    return (-4.6 + 0.182258 * vo2 + 0.000104 * vo2**2) / denom


def calc_vdot(distance_m: float, duration_s: int) -> tuple[Optional[float], Literal["high", "estimated", "low"]]:
    """计算 VDOT（Powers 方法）.

    Args:
        distance_m: 距离（米），>0
        duration_s: 时长（秒），>0

    Returns:
        (vdot, confidence):
        - 距离 >=1500m：(计算值, "high")
        - 距离 <1500m 但 >0：(估算值, "estimated")
        - 距离=0 或时长<=0：(None, "low")
    """
    if distance_m <= 0 or duration_s <= 0:
        return None, "low"

    duration_min = duration_s / 60.0
    vo2 = _compute_vo2(distance_m, duration_min)
    vdot = _compute_vdot_from_vo2(vo2, duration_min)

    # 边界保护：VO2 必须为正
    if vo2 <= 0 or vdot <= 0:
        return None, "low"

    confidence = "high" if distance_m >= VDOT_MIN_DISTANCE_M else "estimated"
    return round(vdot, 2), confidence
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/calculators/test_vdot.py -v`
Expected: 8 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/vdot.py run-flow-skills-mcp/tests/calculators/__init__.py run-flow-skills-mcp/tests/calculators/test_vdot.py
git commit -m "feat(calculators/vdot): implement VDOT calculation with Powers method"
```

---

## Task 5: calculators/training_load.py TSS/CTL/ATL/TSB

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/training_load.py`
- Test: `run-flow-skills-mcp/tests/calculators/test_training_load.py`

**Interfaces:**
- Consumes: `constants.CTL_WINDOW_DAYS`、`constants.ATL_WINDOW_DAYS`
- Produces:
  - `calc_tss(duration_s: int, intensity_factor: float) -> float`
  - `calc_ewma(values: list[float], window: int) -> list[float]`（α = 2/(N+1)）
  - `calc_ctl(daily_tss: list[float]) -> float`（42 天 EWMA 末值）
  - `calc_atl(daily_tss: list[float]) -> float`（7 天 EWMA 末值）
  - `calc_tsb(ctl: float, atl: float) -> float`
  - `calc_intensity_factor(avg_pace_s_per_km: float, threshold_pace_s_per_km: float) -> float`（IF = threshold_pace / actual_pace）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/calculators/test_training_load.py`：

```python
"""训练负荷计算单元测试（spec 8.1.2, 8.1.3, 8.1.7）."""
import pytest

from run_flow_skills_mcp.calculators.training_load import (
    calc_atl,
    calc_ctl,
    calc_ewma,
    calc_intensity_factor,
    calc_tsb,
    calc_tss,
)


def test_tss_basic_formula():
    """TSS = duration_s × IF² × 100（spec 8.1.2）."""
    # 60 分钟，IF=1.0 → TSS=100
    assert calc_tss(3600, 1.0) == 100.0
    # 60 分钟，IF=0.85 → TSS=72.25
    assert calc_tss(3600, 0.85) == pytest.approx(72.25, rel=1e-3)


def test_tss_zero_duration():
    assert calc_tss(0, 1.0) == 0.0


def test_ewma_alpha_formula():
    """α = 2/(N+1)，7 天窗口 α=0.25（spec 8.1.7）."""
    # 全 1 输入 → EWMA 全 1
    result = calc_ewma([1.0, 1.0, 1.0], window=3)
    assert result == [1.0, 1.0, 1.0]


def test_ewma_decays_old_values():
    """新值权重高于旧值."""
    result = calc_ewma([0.0, 0.0, 100.0], window=3)
    # 第三个值应远大于前两个
    assert result[2] > result[1] > result[0]
    assert result[2] < 100.0  # 但小于最新值


def test_ewma_empty_input():
    assert calc_ewma([], window=7) == []


def test_ctl_uses_42_day_window():
    """spec 8.1.3: CTL = 42 天 EWMA."""
    daily = [10.0] * 42
    ctl = calc_ctl(daily)
    # 42 天稳定值应接近 10
    assert 9.5 <= ctl <= 10.5


def test_atl_uses_7_day_window():
    """spec 8.1.3: ATL = 7 天 EWMA."""
    daily = [10.0] * 7
    atl = calc_atl(daily)
    assert 9.0 <= atl <= 11.0


def test_ctl_atl_respond_differently_to_spike():
    """ATL 对近期 spike 更敏感，CTL 反应平缓."""
    daily = [10.0] * 35 + [200.0] * 7  # 末 7 天 spike
    ctl = calc_ctl(daily)
    atl = calc_atl(daily)
    assert atl > ctl  # ATL 反应更强


def test_tsb_formula():
    """TSB = CTL - ATL（spec 8.1.3）."""
    assert calc_tsb(65.0, 58.0) == 7.0
    assert calc_tsb(50.0, 60.0) == -10.0


def test_intensity_factor_pace_based():
    """IF = threshold_pace / actual_pace（配速越快 IF 越高）."""
    # 阈值配速 5'00"/km（300s），实际 6'00"/km（360s）→ IF=0.833
    if_val = calc_intensity_factor(avg_pace_s_per_km=360.0, threshold_pace_s_per_km=300.0)
    assert if_val == pytest.approx(0.833, rel=1e-2)


def test_intensity_factor_at_threshold():
    """实际配速 = 阈值配速 → IF=1.0."""
    if_val = calc_intensity_factor(avg_pace_s_per_km=300.0, threshold_pace_s_per_km=300.0)
    assert if_val == 1.0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/calculators/test_training_load.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/training_load.py`：

```python
"""训练负荷计算器 - TSS/CTL/ATL/TSB（spec 8.1.2, 8.1.3, 8.1.7）."""
from __future__ import annotations

from run_flow_skills_mcp.constants import ATL_WINDOW_DAYS, CTL_WINDOW_DAYS


def calc_tss(duration_s: int, intensity_factor: float) -> float:
    """计算单次训练 TSS = duration_s × IF² × 100.

    Args:
        duration_s: 时长（秒）
        intensity_factor: 强度因子（IF）

    Returns:
        TSS 值
    """
    if duration_s <= 0 or intensity_factor <= 0:
        return 0.0
    return duration_s * intensity_factor**2 * 100 / 3600.0  # 归一化到小时


def calc_ewma(values: list[float], window: int) -> list[float]:
    """计算 EWMA 序列（spec 8.1.7）.

    α = 2/(N+1)，ewma[t] = α × values[t] + (1-α) × ewma[t-1]

    Args:
        values: 时间序列值（按时间升序）
        window: EWMA 窗口 N

    Returns:
        与 values 等长的 EWMA 序列，空输入返回空列表
    """
    if not values or window <= 0:
        return []
    alpha = 2.0 / (window + 1)
    result: list[float] = [values[0]]
    for v in values[1:]:
        prev = result[-1]
        result.append(alpha * v + (1 - alpha) * prev)
    return result


def calc_ctl(daily_tss: list[float]) -> float:
    """计算 CTL（42 天 EWMA 末值）."""
    if not daily_tss:
        return 0.0
    ewma = calc_ewma(daily_tss, CTL_WINDOW_DAYS)
    return ewma[-1]


def calc_atl(daily_tss: list[float]) -> float:
    """计算 ATL（7 天 EWMA 末值）."""
    if not daily_tss:
        return 0.0
    ewma = calc_ewma(daily_tss, ATL_WINDOW_DAYS)
    return ewma[-1]


def calc_tsb(ctl: float, atl: float) -> float:
    """计算 TSB = CTL - ATL."""
    return ctl - atl


def calc_intensity_factor(
    avg_pace_s_per_km: float, threshold_pace_s_per_km: float
) -> float:
    """计算 IF = threshold_pace / actual_pace.

    配速越快（秒数越小），IF 越高；实际配速 = 阈值配速时 IF=1.0。

    Args:
        avg_pace_s_per_km: 实际平均配速（秒/km）
        threshold_pace_s_per_km: 阈值配速（秒/km）

    Returns:
        强度因子 IF
    """
    if avg_pace_s_per_km <= 0 or threshold_pace_s_per_km <= 0:
        return 0.0
    return threshold_pace_s_per_km / avg_pace_s_per_km
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/calculators/test_training_load.py -v`
Expected: 11 个测试全部 PASS

注意：`test_tss_basic_formula` 的 IF=1.0, duration=3600 期望 100.0，需验证实现：`3600 × 1.0 × 100 / 3600 = 100.0` ✓

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/training_load.py run-flow-skills-mcp/tests/calculators/test_training_load.py
git commit -m "feat(calculators/training_load): implement TSS/CTL/ATL/TSB and EWMA"
```

---

## Task 6: calculators/hrv.py HRV 指标与基线偏离

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hrv.py`
- Test: `run-flow-skills-mcp/tests/calculators/test_hrv.py`

**Interfaces:**
- Consumes: `constants.HRV_BASELINE_DAYS`
- Produces:
  - `calc_rmssd(rr_intervals: list[float]) -> Optional[float]`（单位 ms）
  - `calc_sdnn(rr_intervals: list[float]) -> Optional[float]`
  - `calc_pnn50(rr_intervals: list[float]) -> Optional[float]`（百分比 0-100）
  - `calc_hrv_baseline(recent_hrv: list[float]) -> Optional[float]`（7 天滚动均值）
  - `calc_hrv_deviation_pct(current_hrv: float, baseline: float) -> float`（偏离百分比，正数=高于基线）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/calculators/test_hrv.py`：

```python
"""HRV 计算单元测试（spec 8.1.8, FR-ANALYZE-04）."""
import pytest

from run_flow_skills_mcp.calculators.hrv import (
    calc_hrv_baseline,
    calc_hrv_deviation_pct,
    calc_pnn50,
    calc_rmssd,
    calc_sdnn,
)


def test_rmssd_normal():
    """RMSSD = sqrt(mean(diff²))."""
    # RR 间隔 [800, 850, 820, 880] ms
    rr = [800.0, 850.0, 820.0, 880.0]
    rmssd = calc_rmssd(rr)
    assert rmssd is not None
    assert rmssd > 0


def test_rmssd_empty_returns_none():
    assert calc_rmssd([]) is None


def test_rmssd_single_value_returns_none():
    """单点无法计算差分."""
    assert calc_rmssd([800.0]) is None


def test_sdnn_normal():
    """SDNN = std(RR)."""
    rr = [800.0, 850.0, 820.0, 880.0]
    sdnn = calc_sdnn(rr)
    assert sdnn is not None
    assert sdnn > 0


def test_sdnn_empty_returns_none():
    assert calc_sdnn([]) is None


def test_pnn50_normal():
    """pNN50 = 占比(|diff|>50ms)."""
    # 差分：50, 30, 60 → 2/3 > 50ms
    rr = [800.0, 850.0, 820.0, 880.0]
    pnn50 = calc_pnn50(rr)
    assert pnn50 is not None
    assert 60 <= pnn50 <= 70  # 约 66.67


def test_pnn50_empty_returns_none():
    assert calc_pnn50([]) is None


def test_hrv_baseline_7day_mean():
    """基线 = 7 天滚动均值（spec 8.1.8）."""
    recent = [40.0, 42.0, 41.0, 43.0, 40.0, 42.0, 44.0]
    baseline = calc_hrv_baseline(recent)
    assert baseline is not None
    assert 41 <= baseline <= 43


def test_hrv_baseline_insufficient_data_returns_none():
    """数据不足 7 天仍可计算（用现有数据均值），但空数据返回 None."""
    assert calc_hrv_baseline([]) is None


def test_hrv_deviation_pct_above_baseline():
    """当前 HRV 高于基线 → 正偏离."""
    dev = calc_hrv_deviation_pct(current_hrv=48.0, baseline=40.0)
    assert dev == pytest.approx(20.0, rel=1e-2)


def test_hrv_deviation_pct_below_baseline():
    """当前 HRV 低于基线 → 负偏离（spec 场景 3.3：HRV 偏低 12ms）."""
    dev = calc_hrv_deviation_pct(current_hrv=38.0, baseline=45.0)
    assert dev == pytest.approx(-15.56, rel=1e-1)


def test_hrv_deviation_pct_zero_baseline_returns_zero():
    """基线为 0 时无法计算，返回 0 避免除零."""
    dev = calc_hrv_deviation_pct(current_hrv=40.0, baseline=0.0)
    assert dev == 0.0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/calculators/test_hrv.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hrv.py`：

```python
"""HRV 计算器 - RMSSD/SDNN/pNN50 + 基线偏离（spec 8.1.8, FR-ANALYZE-04）."""
from __future__ import annotations

import math
from typing import Optional


def calc_rmssd(rr_intervals: list[float]) -> Optional[float]:
    """计算 RMSSD（ms）= sqrt(mean(successive_diff²))."""
    if len(rr_intervals) < 2:
        return None
    diffs = [
        rr_intervals[i + 1] - rr_intervals[i]
        for i in range(len(rr_intervals) - 1)
    ]
    mean_sq = sum(d * d for d in diffs) / len(diffs)
    return math.sqrt(mean_sq)


def calc_sdnn(rr_intervals: list[float]) -> Optional[float]:
    """计算 SDNN（ms）= std(RR_intervals)."""
    if not rr_intervals:
        return None
    mean = sum(rr_intervals) / len(rr_intervals)
    variance = sum((r - mean) ** 2 for r in rr_intervals) / len(rr_intervals)
    return math.sqrt(variance)


def calc_pnn50(rr_intervals: list[float]) -> Optional[float]:
    """计算 pNN50（%）= |diff|>50ms 的占比 × 100."""
    if len(rr_intervals) < 2:
        return None
    diffs = [
        abs(rr_intervals[i + 1] - rr_intervals[i])
        for i in range(len(rr_intervals) - 1)
    ]
    count_gt_50 = sum(1 for d in diffs if d > 50.0)
    return count_gt_50 / len(diffs) * 100.0


def calc_hrv_baseline(recent_hrv: list[float]) -> Optional[float]:
    """计算 HRV 基线（7 天滚动均值，spec 8.1.8）.

    Args:
        recent_hrv: 最近 N 天的 HRV 值（RMSSD），最末元素为最新

    Returns:
        基线均值，空输入返回 None
    """
    if not recent_hrv:
        return None
    return sum(recent_hrv) / len(recent_hrv)


def calc_hrv_deviation_pct(current_hrv: float, baseline: float) -> float:
    """计算 HRV 偏离基线百分比.

    Returns:
        偏离百分比，正数=高于基线，负数=低于基线；baseline=0 时返回 0
    """
    if baseline <= 0:
        return 0.0
    return (current_hrv - baseline) / baseline * 100.0
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/calculators/test_hrv.py -v`
Expected: 11 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hrv.py run-flow-skills-mcp/tests/calculators/test_hrv.py
git commit -m "feat(calculators/hrv): implement RMSSD/SDNN/pNN50 and baseline deviation"
```

---

## Task 7: calculators/pace_zones.py E/M/T/I/R 配速区间

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/pace_zones.py`
- Test: `run-flow-skills-mcp/tests/calculators/test_pace_zones.py`

**Interfaces:**
- Consumes: `constants.PACE_ZONE_FACTORS`
- Produces:
  - `calc_pace_zones(vdot: float) -> dict[str, tuple[float, float]]`：返回各区间 (min_pace_s_per_km, max_pace_s_per_km)
  - `classify_pace_zone(avg_pace_s_per_km: float, vdot: float) -> PaceZone`：判断某配速属于哪个区间
  - 辅助：`calc_vdot_pace_s_per_km(vdot: float) -> float`（VDOT 对应的参考配速）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/calculators/test_pace_zones.py`：

```python
"""配速区间计算单元测试（spec 8.1.6, FR-PLAN-03）."""
import pytest

from run_flow_skills_mcp.calculators.pace_zones import (
    calc_pace_zones,
    calc_vdot_pace_s_per_km,
    classify_pace_zone,
)


def test_vdot_pace_decreases_as_vdot_increases():
    """VDOT 越高，参考配速越快（秒数越小）."""
    pace_40 = calc_vdot_pace_s_per_km(40.0)
    pace_50 = calc_vdot_pace_s_per_km(50.0)
    assert pace_50 < pace_40


def test_pace_zones_returns_all_five_zones():
    zones = calc_pace_zones(45.0)
    assert set(zones.keys()) == {"E", "M", "T", "I", "R"}
    for zone, (lo, hi) in zones.items():
        assert lo > 0 and hi > 0
        assert lo <= hi, f"{zone} 区间 lo>hi"


def test_pace_zones_e_is_slowest():
    """E 区间最容易（最慢），R 区间最难（最快）."""
    zones = calc_pace_zones(45.0)
    e_lo, _ = zones["E"]
    r_lo, _ = zones["R"]
    assert e_lo > r_lo  # E 配速秒数 > R 配速秒数


def test_classify_pace_zone_easy_pace():
    """5'30"/km 在 VDOT 45 时应归为 E 或 M 区间."""
    pace = 330.0  # 5'30"
    zone = classify_pace_zone(pace, vdot=45.0)
    assert zone in ("E", "M")


def test_classify_pace_zone_threshold_pace():
    """接近阈值配速归为 T."""
    zones = calc_pace_zones(45.0)
    t_mid = (zones["T"][0] + zones["T"][1]) / 2
    zone = classify_pace_zone(t_mid, vdot=45.0)
    assert zone == "T"


def test_classify_pace_zone_interval_pace():
    """间歇配速归为 I 或 R."""
    zones = calc_pace_zones(45.0)
    i_mid = (zones["I"][0] + zones["I"][1]) / 2
    zone = classify_pace_zone(i_mid, vdot=45.0)
    assert zone in ("I", "R")


def test_pace_zones_factors_match_spec():
    """spec 8.1.6: E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110%."""
    zones = calc_pace_zones(45.0)
    vdot_pace = calc_vdot_pace_s_per_km(45.0)
    # E 区间：VDOT 配速 / 0.59 ~ VDOT 配速 / 0.74
    e_lo_expected = vdot_pace / 0.74  # 最快
    e_hi_expected = vdot_pace / 0.59  # 最慢
    assert zones["E"][0] == pytest.approx(e_lo_expected, rel=1e-3)
    assert zones["E"][1] == pytest.approx(e_hi_expected, rel=1e-3)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/calculators/test_pace_zones.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/pace_zones.py`：

```python
"""配速区间计算器 - E/M/T/I/R（spec 8.1.6, FR-PLAN-03）.

配速区间基于个人 VDOT：
- E=59-74%, M=75-84%, T=88-100%, I=95-100%, R=100-110% VDOT
- 配速 = VDOT 参考配速 / factor（factor 越大，配速越快）
"""
from __future__ import annotations

from typing import Literal

from run_flow_skills_mcp.constants import PACE_ZONE_FACTORS

PaceZone = Literal["E", "M", "T", "I", "R"]

# VDOT 与参考配速的近似换算（VDOT 45 ≈ 4:36/km = 276s/km）
# 公式：VDOT_pace = 4320 / VDOT（秒/km，经验近似）
_VDOT_PACE_COEFF: float = 4320.0


def calc_vdot_pace_s_per_km(vdot: float) -> float:
    """计算 VDOT 对应的参考配速（秒/km）."""
    if vdot <= 0:
        return 0.0
    return _VDOT_PACE_COEFF / vdot


def calc_pace_zones(vdot: float) -> dict[str, tuple[float, float]]:
    """计算各配速区间（秒/km）.

    Args:
        vdot: 个人 VDOT 值

    Returns:
        {"E": (min_pace, max_pace), "M": ..., "T": ..., "I": ..., "R": ...}
        min_pace 为区间最快配速（秒数小），max_pace 为最慢（秒数大）
    """
    if vdot <= 0:
        return {}
    vdot_pace = calc_vdot_pace_s_per_km(vdot)
    zones: dict[str, tuple[float, float]] = {}
    for zone, (lo_factor, hi_factor) in PACE_ZONE_FACTORS.items():
        # factor 大 → 配速快（秒数小）
        fastest = vdot_pace / hi_factor
        slowest = vdot_pace / lo_factor
        zones[zone] = (fastest, slowest)
    return zones


def classify_pace_zone(avg_pace_s_per_km: float, vdot: float) -> PaceZone:
    """判断某配速属于哪个区间.

    Args:
        avg_pace_s_per_km: 实际平均配速
        vdot: 个人 VDOT

    Returns:
        E/M/T/I/R 中最接近的区间；若快于 R 区间返回 "R"，慢于 E 返回 "E"
    """
    zones = calc_pace_zones(vdot)
    if not zones:
        return "E"

    # 从最快区间（R）到最慢区间（E）依次检查
    for zone in ("R", "I", "T", "M", "E"):
        lo, hi = zones[zone]
        if lo <= avg_pace_s_per_km <= hi:
            return zone
        if avg_pace_s_per_km < lo and zone == "R":
            return "R"  # 比 R 还快
    return "E"  # 比 E 还慢
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/calculators/test_pace_zones.py -v`
Expected: 7 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/pace_zones.py run-flow-skills-mcp/tests/calculators/test_pace_zones.py
git commit -m "feat(calculators/pace_zones): implement E/M/T/I/R zone calculation from VDOT"
```

---

## Task 8: calculators/hr_zones.py 心率区间分布

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hr_zones.py`
- Test: `run-flow-skills-mcp/tests/calculators/test_hr_zones.py`

**Interfaces:**
- Consumes: `constants.HR_ZONE_FACTORS`、`constants.DEFAULT_MAX_HR`
- Produces:
  - `calc_hr_zones_boundaries(max_hr: int) -> dict[str, tuple[int, int]]`：返回各区间 (min_bpm, max_bpm)
  - `classify_hr_samples(hr_samples: list[int], max_hr: int) -> dict[str, float]`：返回各区间时间占比 {Z1: 0.1, Z2: 0.4, ...}，总和=1.0

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/calculators/test_hr_zones.py`：

```python
"""心率区间计算单元测试（spec 8.1.5, FR-IMPORT-06）."""
import pytest

from run_flow_skills_mcp.calculators.hr_zones import (
    calc_hr_zones_boundaries,
    classify_hr_samples,
)


def test_hr_zones_boundaries_5_zones():
    """5 个心率区间 Z1-Z5."""
    boundaries = calc_hr_zones_boundaries(max_hr=200)
    assert set(boundaries.keys()) == {"Z1", "Z2", "Z3", "Z4", "Z5"}
    for zone, (lo, hi) in boundaries.items():
        assert 0 <= lo <= hi <= 200


def test_hr_zones_boundaries_z5_high():
    """Z5 应覆盖 >=90% max_hr."""
    boundaries = calc_hr_zones_boundaries(max_hr=200)
    z5_lo, z5_hi = boundaries["Z5"]
    assert z5_lo == 180  # 90% of 200
    assert z5_hi == 200


def test_hr_zones_boundaries_z1_low():
    """Z1 应覆盖 <50% max_hr."""
    boundaries = calc_hr_zones_boundaries(max_hr=200)
    z1_lo, z1_hi = boundaries["Z1"]
    assert z1_lo == 0
    assert z1_hi == 100  # 50% of 200


def test_classify_hr_samples_distributes_correctly():
    """10 个心率样本，分布在 Z2/Z3 区间."""
    # max_hr=200, Z2=100-120, Z3=120-140, Z4=140-180, Z5=180-200
    samples = [110, 110, 130, 130, 150, 150, 150, 190, 190, 50]
    dist = classify_hr_samples(samples, max_hr=200)
    assert sum(dist.values()) == pytest.approx(1.0, rel=1e-3)
    assert dist["Z2"] == 0.2  # 110×2
    assert dist["Z3"] == 0.2  # 130×2
    assert dist["Z4"] == 0.3  # 150×3
    assert dist["Z5"] == 0.2  # 190×2
    assert dist["Z1"] == 0.1  # 50×1


def test_classify_hr_samples_empty_returns_empty():
    assert classify_hr_samples([], max_hr=200) == {}


def test_classify_hr_samples_uses_default_max_hr_when_zero():
    """max_hr=0 时回退到 constants.DEFAULT_MAX_HR."""
    dist = classify_hr_samples([100], max_hr=0)
    # 不应崩溃，且应基于 DEFAULT_MAX_HR=190 分类
    assert sum(dist.values()) == pytest.approx(1.0, rel=1e-3)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/calculators/test_hr_zones.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hr_zones.py`：

```python
"""心率区间计算器（spec 8.1.5, FR-IMPORT-06）.

心率区间基于个人最大心率，不可使用 220-年龄通用公式（spec 8.1.5）。
默认值见 constants.DEFAULT_MAX_HR，可经 Web /settings 覆盖。
"""
from __future__ import annotations

from run_flow_skills_mcp.constants import DEFAULT_MAX_HR, HR_ZONE_FACTORS


def calc_hr_zones_boundaries(max_hr: int) -> dict[str, tuple[int, int]]:
    """计算各心率区间边界（bpm）.

    Args:
        max_hr: 个人最大心率

    Returns:
        {"Z1": (0, 50%max), "Z2": (50%, 60%), ..., "Z5": (90%, max)}
    """
    if max_hr <= 0:
        max_hr = DEFAULT_MAX_HR

    # 区间比例上限（spec constants.HR_ZONE_FACTORS）
    # Z1: 0-50%, Z2: 50-60%, Z3: 60-70%, Z4: 70-90%, Z5: 90-100%
    boundaries: dict[str, tuple[int, int]] = {
        "Z1": (0, int(HR_ZONE_FACTORS["Z1"] * max_hr)),  # 0-100
        "Z2": (int(HR_ZONE_FACTORS["Z1"] * max_hr), int(HR_ZONE_FACTORS["Z2"] * max_hr)),
        "Z3": (int(HR_ZONE_FACTORS["Z2"] * max_hr), int(HR_ZONE_FACTORS["Z3"] * max_hr)),
        "Z4": (int(HR_ZONE_FACTORS["Z3"] * max_hr), int(HR_ZONE_FACTORS["Z4"] * max_hr)),
        "Z5": (int(HR_ZONE_FACTORS["Z4"] * max_hr), max_hr),  # 90%-max
    }
    return boundaries


def classify_hr_samples(hr_samples: list[int], max_hr: int) -> dict[str, float]:
    """将心率样本分类到各区间，返回时间占比.

    Args:
        hr_samples: 心率样本列表（bpm）
        max_hr: 个人最大心率，0 时回退到 DEFAULT_MAX_HR

    Returns:
        {"Z1": 0.1, "Z2": 0.4, ...}，总和=1.0；空样本返回 {}
    """
    if not hr_samples:
        return {}

    if max_hr <= 0:
        max_hr = DEFAULT_MAX_HR

    boundaries = calc_hr_zones_boundaries(max_hr)
    counts: dict[str, int] = {z: 0 for z in boundaries}

    for hr in hr_samples:
        for zone, (lo, hi) in boundaries.items():
            if lo <= hr <= hi:
                counts[zone] += 1
                break
        else:
            # 高于所有区间上限归入 Z5
            if hr > max_hr:
                counts["Z5"] += 1

    total = len(hr_samples)
    return {z: count / total for z, count in counts.items() if count > 0}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/calculators/test_hr_zones.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/hr_zones.py run-flow-skills-mcp/tests/calculators/test_hr_zones.py
git commit -m "feat(calculators/hr_zones): implement HR zone boundaries and sample classification"
```

---

## Task 9: calculators/fatigue.py 疲劳度综合评估

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/fatigue.py`
- Test: `run-flow-skills-mcp/tests/calculators/test_fatigue.py`

**Interfaces:**
- Consumes: 无（纯函数）
- Produces:
  - `calc_fatigue_score(hrv_deviation_pct: Optional[float], tsb: Optional[float], rpe_trend: Optional[list[int]]) -> tuple[float, Literal["low","moderate","high"], list[str]]`
  - 返回 (0-100 分数, 风险等级, 主要风险因子列表)；分数越高越疲劳

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/calculators/test_fatigue.py`：

```python
"""疲劳度评估单元测试（spec FR-ANALYZE-05, FR-COACH-01）."""
import pytest

from run_flow_skills_mcp.calculators.fatigue import calc_fatigue_score


def test_fatigue_all_normal_returns_low():
    """所有指标正常 → 低风险."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=2.0, tsb=15.0, rpe_trend=[3, 4, 3]
    )
    assert level == "low"
    assert score < 30
    assert len(factors) == 0


def test_fatigue_hrv_low_returns_high():
    """HRV 偏低 15%+ TSB 负值 → 高风险."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=-15.0, tsb=-10.0, rpe_trend=[7, 8, 9]
    )
    assert level == "high"
    assert score >= 70
    assert "hrv_deviation" in factors
    assert "tsb_negative" in factors


def test_fatigue_partial_data_returns_moderate():
    """部分数据缺失仍可评估，但降级."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=-8.0, tsb=None, rpe_trend=None
    )
    assert level in ("moderate", "low")
    assert "hrv_deviation" in factors


def test_fatigue_rpe_trend_rising():
    """RPE 趋势上升 → 风险增加."""
    score1, _, _ = calc_fatigue_score(
        hrv_deviation_pct=0.0, tsb=10.0, rpe_trend=[3, 3, 3]
    )
    score2, _, _ = calc_fatigue_score(
        hrv_deviation_pct=0.0, tsb=10.0, rpe_trend=[5, 7, 9]
    )
    assert score2 > score1


def test_fatigue_all_none_returns_low_with_warning():
    """全部数据缺失 → 默认低风险但 factors 含 'insufficient_data'."""
    score, level, factors = calc_fatigue_score(
        hrv_deviation_pct=None, tsb=None, rpe_trend=None
    )
    assert level == "low"
    assert "insufficient_data" in factors


def test_fatigue_score_in_range():
    """分数必须在 0-100."""
    for args in [
        (-50.0, -30.0, [10, 10, 10]),
        (50.0, 30.0, [1, 1, 1]),
        (None, None, None),
    ]:
        score, _, _ = calc_fatigue_score(*args)
        assert 0 <= score <= 100
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/calculators/test_fatigue.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/fatigue.py`：

```python
"""疲劳度综合评估（spec FR-ANALYZE-05, FR-COACH-01）.

综合 HRV 偏离度 + TSB + RPE 趋势计算疲劳分数（0-100）。
单一指标不可单独决策（coaching-rules.md 第 3 条）。
"""
from __future__ import annotations

from typing import Literal, Optional


def _hrv_contribution(deviation_pct: Optional[float]) -> tuple[float, bool]:
    """HRV 偏离贡献分（负偏离越大，分越高）."""
    if deviation_pct is None:
        return 0.0, False
    # 偏离 -10% 起算，每偏离 -1% 加 2 分，上限 40 分
    if deviation_pct >= -10.0:
        return 0.0, False
    score = min(40.0, (abs(deviation_pct) - 10.0) * 2.0)
    return score, True


def _tsb_contribution(tsb: Optional[float]) -> tuple[float, bool]:
    """TSB 贡献分（负值越大，分越高）."""
    if tsb is None:
        return 0.0, False
    if tsb >= 0:
        return 0.0, False
    # TSB 每负 1 加 1.5 分，上限 30 分
    return min(30.0, abs(tsb) * 1.5), True


def _rpe_contribution(rpe_trend: Optional[list[int]]) -> tuple[float, bool]:
    """RPE 趋势贡献分（持续上升或高位 → 高分）."""
    if not rpe_trend or len(rpe_trend) < 2:
        return 0.0, False
    avg_rpe = sum(rpe_trend) / len(rpe_trend)
    # RPE 平均 >=7 起算，每高 1 加 5 分，上限 30 分
    if avg_rpe < 7:
        return 0.0, False
    return min(30.0, (avg_rpe - 7) * 5.0), True


def calc_fatigue_score(
    hrv_deviation_pct: Optional[float],
    tsb: Optional[float],
    rpe_trend: Optional[list[int]],
) -> tuple[float, Literal["low", "moderate", "high"], list[str]]:
    """计算疲劳度综合分数.

    Args:
        hrv_deviation_pct: HRV 偏离基线百分比（负数=偏低）
        tsb: 训练压力平衡（负数=疲劳累积）
        rpe_trend: 最近 N 次 RPE 趋势（1-10）

    Returns:
        (score 0-100, level, factors):
        - level: low(<30) / moderate(30-70) / high(>=70)
        - factors: 主要风险因子列表
    """
    hrv_score, hrv_present = _hrv_contribution(hrv_deviation_pct)
    tsb_score, tsb_present = _tsb_contribution(tsb)
    rpe_score, rpe_present = _rpe_contribution(rpe_trend)

    # 若所有数据缺失，返回低风险但标注
    if not any([hrv_present, tsb_present, rpe_present]):
        return 0.0, "low", ["insufficient_data"]

    score = hrv_score + tsb_score + rpe_score
    score = max(0.0, min(100.0, score))

    factors: list[str] = []
    if hrv_present and hrv_score > 0:
        factors.append("hrv_deviation")
    if tsb_present and tsb_score > 0:
        factors.append("tsb_negative")
    if rpe_present and rpe_score > 0:
        factors.append("rpe_trend_high")

    if score >= 70:
        level = "high"
    elif score >= 30:
        level = "moderate"
    else:
        level = "low"

    return score, level, factors
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/calculators/test_fatigue.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/calculators/fatigue.py run-flow-skills-mcp/tests/calculators/test_fatigue.py
git commit -m "feat(calculators/fatigue): implement composite fatigue score from HRV/TSB/RPE"
```

---

## Task 10: storage/parquet_store.py Session/Metrics Parquet 读写

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/__init__.py`
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/parquet_store.py`
- Test: `run-flow-skills-mcp/tests/storage/__init__.py`
- Test: `run-flow-skills-mcp/tests/storage/test_parquet_store.py`

**Interfaces:**
- Consumes: `models.Session`、`models.TrainingMetrics`、`constants.DEFAULT_MAX_HR`（不直接用，仅作上下文）
- Produces:
  - `class ParquetStore`：`__init__(self, data_dir: Path)`、`append_session(session: Session) -> None`、`append_metrics(metrics: TrainingMetrics) -> None`、`query_sessions(date_from?: str, date_to?: str, source?: str, limit?: int) -> list[Session]`、`query_metrics(session_ids: list[str]) -> list[TrainingMetrics]`、`find_by_hash(raw_file_hash: str) -> Optional[Session]`
  - 文件路径：`data/sessions/sessions_YYYY.parquet`、`data/metrics/metrics_YYYY.parquet`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/storage/__init__.py`（空）：

```python
```

写入 `run-flow-skills-mcp/tests/storage/test_parquet_store.py`：

```python
"""Parquet 存储测试（spec 5.1, FR-IMPORT-07）."""
from datetime import datetime
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import Session, TrainingMetrics
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def store(tmp_data_dir: Path) -> ParquetStore:
    return ParquetStore(data_dir=tmp_data_dir)


def _make_session(session_id: str, date: datetime, source: str = "garmin") -> Session:
    return Session(
        session_id=session_id,
        activity_date=date,
        distance_m=10000.0,
        duration_s=3600,
        avg_pace_s_per_km=360.0,
        source=source,
        raw_file_hash="abc123",
    )


def test_append_and_query_session(store: ParquetStore):
    s = _make_session("sess_20260725_001", datetime(2026, 7, 25, 6, 0))
    store.append_session(s)
    result = store.query_sessions()
    assert len(result) == 1
    assert result[0].session_id == "sess_20260725_001"


def test_query_by_date_range(store: ParquetStore):
    store.append_session(_make_session("sess_20260701_001", datetime(2026, 7, 1)))
    store.append_session(_make_session("sess_20260725_001", datetime(2026, 7, 25)))
    store.append_session(_make_session("sess_20260815_001", datetime(2026, 8, 15)))

    result = store.query_sessions(date_from="2026-07-01", date_to="2026-07-31")
    assert len(result) == 2


def test_query_by_source(store: ParquetStore):
    store.append_session(_make_session("sess_20260725_001", datetime(2026, 7, 25), "garmin"))
    store.append_session(_make_session("sess_20260725_002", datetime(2026, 7, 25), "apple"))

    result = store.query_sessions(source="garmin")
    assert len(result) == 1
    assert result[0].source == "garmin"


def test_query_limit(store: ParquetStore):
    for i in range(5):
        store.append_session(_make_session(f"sess_20260725_{i+1:03d}", datetime(2026, 7, 25)))
    result = store.query_sessions(limit=3)
    assert len(result) == 3


def test_find_by_hash(store: ParquetStore):
    s = _make_session("sess_20260725_001", datetime(2026, 7, 25))
    s.raw_file_hash = "unique_hash_123"
    store.append_session(s)

    found = store.find_by_hash("unique_hash_123")
    assert found is not None
    assert found.session_id == "sess_20260725_001"

    not_found = store.find_by_hash("nonexistent")
    assert not_found is None


def test_yearly_sharding(store: ParquetStore):
    """跨年存储应分到不同 parquet 文件（spec 5.1）."""
    store.append_session(_make_session("sess_20251231_001", datetime(2025, 12, 31)))
    store.append_session(_make_session("sess_20260101_001", datetime(2026, 1, 1)))

    assert (store.data_dir / "sessions" / "sessions_2025.parquet").exists()
    assert (store.data_dir / "sessions" / "sessions_2026.parquet").exists()


def test_append_metrics_and_query(store: ParquetStore):
    s = _make_session("sess_20260725_001", datetime(2026, 7, 25))
    store.append_session(s)
    m = TrainingMetrics(
        session_id="sess_20260725_001",
        vdot=45.0,
        vdot_confidence="high",
        tss=100.0,
        intensity_factor=0.85,
        pace_zone="T",
    )
    store.append_metrics(m)

    result = store.query_metrics(["sess_20260725_001"])
    assert len(result) == 1
    assert result[0].vdot == 45.0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/storage/test_parquet_store.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/__init__.py`：

```python
"""storage 子包：Parquet + JSON 读写."""
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/parquet_store.py`：

```python
"""Parquet 存储引擎 - Session/Metrics 按年分片（spec 5.1）."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import polars as pl

from run_flow_skills_mcp.models import Session, TrainingMetrics


def _year_from_datetime(dt: datetime) -> int:
    return dt.year


def _session_to_row(s: Session) -> dict:
    return {
        "session_id": s.session_id,
        "activity_date": s.activity_date,
        "distance_m": s.distance_m,
        "duration_s": s.duration_s,
        "avg_pace_s_per_km": s.avg_pace_s_per_km,
        "avg_hr": s.avg_hr,
        "max_hr": s.max_hr,
        "hr_zones": s.hr_zones,
        "cadence": s.cadence,
        "elevation_gain_m": s.elevation_gain_m,
        "source": s.source,
        "raw_file_hash": s.raw_file_hash,
        "raw_file_path": s.raw_file_path,
        "notes": s.notes,
    }


def _row_to_session(row: dict) -> Session:
    return Session(**row)


def _metrics_to_row(m: TrainingMetrics) -> dict:
    return {
        "session_id": m.session_id,
        "vdot": m.vdot,
        "vdot_confidence": m.vdot_confidence,
        "tss": m.tss,
        "intensity_factor": m.intensity_factor,
        "efficiency_factor": m.efficiency_factor,
        "pace_zone": m.pace_zone,
    }


class ParquetStore:
    """Parquet 存储引擎，Session/Metrics 按年分片."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.sessions_dir = data_dir / "sessions"
        self.metrics_dir = data_dir / "metrics"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def _sessions_path(self, year: int) -> Path:
        return self.sessions_dir / f"sessions_{year}.parquet"

    def _metrics_path(self, year: int) -> Path:
        return self.metrics_dir / f"metrics_{year}.parquet"

    def append_session(self, session: Session) -> None:
        """追加一个 Session 到对应年份的 parquet 文件."""
        year = _year_from_datetime(session.activity_date)
        path = self._sessions_path(year)
        new_df = pl.DataFrame([_session_to_row(session)])

        if path.exists():
            existing = pl.read_parquet(path)
            combined = pl.concat([existing, new_df], how="vertical_relaxed")
            combined.write_parquet(path)
        else:
            new_df.write_parquet(path)

    def append_metrics(self, metrics: TrainingMetrics) -> None:
        """追加一个 TrainingMetrics（与 Session 同年份）."""
        # 通过 session_id 查找对应年份
        # ponytail: 简化处理，metrics 文件按 metrics.session_id 推断年份
        # 这里假设 metrics 与 session 同年，由调用方保证顺序
        # 实际实现：扫描所有 metrics_YYYY.parquet 找到 session_id，否则写入当前年
        # 为简化，写入 latest year 的 metrics 文件（由调用方控制年份一致性）
        # 改进：从 sessions 找到 session_id 对应年份
        year = self._find_session_year(metrics.session_id)
        if year is None:
            year = datetime.utcnow().year

        path = self._metrics_path(year)
        new_df = pl.DataFrame([_metrics_to_row(metrics)])

        if path.exists():
            existing = pl.read_parquet(path)
            combined = pl.concat([existing, new_df], how="vertical_relaxed")
            combined.write_parquet(path)
        else:
            new_df.write_parquet(path)

    def _find_session_year(self, session_id: str) -> Optional[int]:
        """从所有 sessions_YYYY.parquet 中查找 session_id 对应年份."""
        for path in self.sessions_dir.glob("sessions_*.parquet"):
            try:
                df = pl.scan_parquet(path).filter(
                    pl.col("session_id") == session_id
                ).collect()
                if len(df) > 0:
                    stem = path.stem  # sessions_YYYY
                    return int(stem.split("_")[1])
            except Exception:
                continue
        return None

    def query_sessions(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Session]:
        """查询 Session 列表."""
        # 收集所有年份的 parquet
        paths = sorted(self.sessions_dir.glob("sessions_*.parquet"))
        if not paths:
            return []

        df = pl.concat([pl.scan_parquet(p) for p in paths], how="vertical_relaxed")

        # 日期过滤
        if date_from:
            df = df.filter(pl.col("activity_date") >= pl.lit(date_from).str.to_datetime())
        if date_to:
            df = df.filter(pl.col("activity_date") <= pl.lit(date_to).str.to_datetime())
        if source:
            df = df.filter(pl.col("source") == source)

        df = df.sort("activity_date", descending=True)
        if limit:
            df = df.head(limit)

        collected = df.collect()
        return [_row_to_session(row) for row in collected.to_dicts()]

    def query_metrics(self, session_ids: list[str]) -> list[TrainingMetrics]:
        """查询给定 session_id 列表对应的 metrics."""
        if not session_ids:
            return []
        paths = sorted(self.metrics_dir.glob("metrics_*.parquet"))
        if not paths:
            return []

        df = pl.concat([pl.scan_parquet(p) for p in paths], how="vertical_relaxed")
        df = df.filter(pl.col("session_id").is_in(session_ids))
        collected = df.collect()
        return [TrainingMetrics(**row) for row in collected.to_dicts()]

    def find_by_hash(self, raw_file_hash: str) -> Optional[Session]:
        """通过 raw_file_hash 查找 Session（去重用）."""
        paths = sorted(self.sessions_dir.glob("sessions_*.parquet"))
        for path in paths:
            df = pl.scan_parquet(path).filter(
                pl.col("raw_file_hash") == raw_file_hash
            ).collect()
            if len(df) > 0:
                return _row_to_session(df.to_dicts()[0])
        return None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/storage/test_parquet_store.py -v`
Expected: 7 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/__init__.py run-flow-skills-mcp/src/run_flow_skills_mcp/storage/parquet_store.py run-flow-skills-mcp/tests/storage/__init__.py run-flow-skills-mcp/tests/storage/test_parquet_store.py
git commit -m "feat(storage/parquet_store): implement yearly-sharded Session/Metrics storage"
```

---

## Task 11: storage/json_store.py JSON 读写

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/json_store.py`
- Test: `run-flow-skills-mcp/tests/storage/test_json_store.py`

**Interfaces:**
- Consumes: `models.TrainingLoad`、`models.BodySignal`、`models.DecisionLog`、`models.TrainingPlan`、`models.UserConfig`
- Produces:
  - `class JsonStore`：`__init__(self, data_dir: Path)`
  - `save_load(load: TrainingLoad) -> None`（全量重写 `data/load/training_load.json`，内含 list[TrainingLoad]）
  - `query_load(date_from?: str, date_to?: str) -> list[TrainingLoad]`
  - `upsert_body_signal(signal: BodySignal) -> None`（按日期覆盖，写入 `data/body_signals/body_signals_YYYY-MM.json`）
  - `query_body_signals(date_from: str, date_to: str) -> list[BodySignal]`
  - `append_decision(decision: DecisionLog) -> None`（追加到 `data/decisions/decisions_YYYY-MM.json`）
  - `query_decisions(date_from?: str, date_to?: str) -> list[DecisionLog]`
  - `save_plan(plan: TrainingPlan) -> None`（写入 `data/plans/plan_YYYYMMDD_NNN.json`）
  - `load_plan(plan_id: str) -> Optional[TrainingPlan]`
  - `list_plans() -> list[TrainingPlan]`
  - `load_user_config() -> UserConfig`（读 `data/config.json`，不存在返回空 UserConfig）
  - `save_user_config(config: UserConfig) -> None`

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/storage/test_json_store.py`：

```python
"""JSON 存储测试（spec 5.1, M-3 评审修正）."""
import json
from datetime import datetime
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import (
    BodySignal,
    DecisionLog,
    TrainingLoad,
    TrainingPlan,
    UserConfig,
)
from run_flow_skills_mcp.storage.json_store import JsonStore


@pytest.fixture
def store(tmp_data_dir: Path) -> JsonStore:
    return JsonStore(data_dir=tmp_data_dir)


def test_save_and_query_load(store: JsonStore):
    load = TrainingLoad(
        date="2026-07-25",
        ctl=65.0,
        atl=58.0,
        tsb=7.0,
        weekly_tss=350.0,
        updated_at=datetime(2026, 7, 25, 23, 0),
    )
    store.save_load(load)
    result = store.query_load()
    assert len(result) == 1
    assert result[0].ctl == 65.0


def test_save_load_multiple_replaces_by_date(store: JsonStore):
    """同日 TrainingLoad 应覆盖（全量重写按 date 去重）."""
    load1 = TrainingLoad(
        date="2026-07-25", ctl=60.0, atl=55.0, tsb=5.0, weekly_tss=300.0,
        updated_at=datetime(2026, 7, 25, 10, 0),
    )
    load2 = TrainingLoad(
        date="2026-07-25", ctl=65.0, atl=58.0, tsb=7.0, weekly_tss=350.0,
        updated_at=datetime(2026, 7, 25, 23, 0),
    )
    store.save_load(load1)
    store.save_load(load2)
    result = store.query_load(date_from="2026-07-25", date_to="2026-07-25")
    assert len(result) == 1
    assert result[0].ctl == 65.0  # 后写入覆盖


def test_upsert_body_signal_overwrites_same_date(store: JsonStore):
    s1 = BodySignal(date="2026-07-25", hrv_rmssd=45.0, rpe=5)
    s2 = BodySignal(date="2026-07-25", hrv_rmssd=38.0, rpe=7)
    store.upsert_body_signal(s1)
    store.upsert_body_signal(s2)
    result = store.query_body_signals("2026-07-01", "2026-07-31")
    assert len(result) == 1
    assert result[0].hrv_rmssd == 38.0


def test_body_signals_monthly_sharding(store: JsonStore):
    """按月分文件（spec 5.1）."""
    s1 = BodySignal(date="2026-07-25", hrv_rmssd=45.0)
    s2 = BodySignal(date="2026-08-01", hrv_rmssd=42.0)
    store.upsert_body_signal(s1)
    store.upsert_body_signal(s2)

    assert (store.data_dir / "body_signals" / "body_signals_2026-07.json").exists()
    assert (store.data_dir / "body_signals" / "body_signals_2026-08.json").exists()


def test_append_decision(store: JsonStore):
    d = DecisionLog(
        decision_id="dec_20260725_001",
        timestamp=datetime(2026, 7, 25, 8, 0),
        decision_type="coach",
        inputs={"hrv": 38},
        reasoning="HRV 偏低",
        recommendation="E 区间 30 分钟",
        confidence=0.7,
        trace_chain=["HRV=38"],
    )
    store.append_decision(d)
    result = store.query_decisions()
    assert len(result) == 1
    assert result[0].decision_id == "dec_20260725_001"


def test_save_and_load_plan(store: JsonStore):
    plan = TrainingPlan(
        plan_id="plan_20260725_001",
        goal_type="full_marathon",
        goal_time="03:59:59",
        race_date="2026-10-19",
        weeks=12,
        current_vdot=42.0,
        target_vdot=43.5,
        phases=[],
        created_at=datetime(2026, 7, 25),
        status="draft",
    )
    store.save_plan(plan)
    loaded = store.load_plan("plan_20260725_001")
    assert loaded is not None
    assert loaded.goal_type == "full_marathon"


def test_list_plans(store: JsonStore):
    for i in range(3):
        plan = TrainingPlan(
            plan_id=f"plan_2026072{i}_001",
            goal_type="full_marathon",
            goal_time="03:59:59",
            race_date="2026-10-19",
            weeks=12,
            current_vdot=42.0,
            target_vdot=43.5,
            phases=[],
            created_at=datetime(2026, 7, 25),
            status="draft",
        )
        store.save_plan(plan)
    plans = store.list_plans()
    assert len(plans) == 3


def test_load_user_config_empty_when_missing(store: JsonStore):
    """config.json 不存在时返回空 UserConfig（M-3 评审修正）."""
    config = store.load_user_config()
    assert config.max_hr is None
    assert config.lthr is None


def test_save_and_load_user_config(store: JsonStore):
    """M-3 评审修正：读写 data/config.json."""
    config = UserConfig(
        max_hr=195,
        lthr=170,
        age=32,
        weight_kg=68.0,
        gender="male",
        updated_at=datetime(2026, 7, 25),
    )
    store.save_user_config(config)
    loaded = store.load_user_config()
    assert loaded.max_hr == 195
    assert loaded.lthr == 170
    assert loaded.gender == "male"

    # 文件确实存在
    assert (store.data_dir / "config.json").exists()


def test_save_user_config_partial_update(store: JsonStore):
    """部分字段更新应保留其他字段."""
    full = UserConfig(max_hr=195, lthr=170, age=32)
    store.save_user_config(full)

    partial = UserConfig(max_hr=200)
    store.save_user_config(partial)

    loaded = store.load_user_config()
    assert loaded.max_hr == 200
    assert loaded.lthr == 170  # 保留
    assert loaded.age == 32  # 保留
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/storage/test_json_store.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/json_store.py`：

```python
"""JSON 存储引擎 - Load/BodySignal/DecisionLog/Plan/UserConfig（spec 5.1）."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from run_flow_skills_mcp.models import (
    BodySignal,
    DecisionLog,
    TrainingLoad,
    TrainingPlan,
    UserConfig,
)

T = TypeVar("T", bound=BaseModel)


def _load_json_list(path: Path, model_cls: Type[T]) -> list[T]:
    """从 JSON 文件加载 list[model]."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [model_cls.model_validate(item) for item in data]


def _save_json_list(path: Path, items: list[BaseModel]) -> None:
    """保存 list[model] 到 JSON 文件."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([item.model_dump(mode="json") for item in items], f, ensure_ascii=False, indent=2, default=str)


class JsonStore:
    """JSON 存储引擎."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.load_dir = data_dir / "load"
        self.body_signals_dir = data_dir / "body_signals"
        self.decisions_dir = data_dir / "decisions"
        self.plans_dir = data_dir / "plans"
        for d in [self.load_dir, self.body_signals_dir, self.decisions_dir, self.plans_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ============ TrainingLoad ============
    def save_load(self, load: TrainingLoad) -> None:
        """保存 TrainingLoad（同日覆盖）."""
        path = self.load_dir / "training_load.json"
        existing = _load_json_list(path, TrainingLoad)
        # 按 date 去重：移除同日记录，追加新记录
        existing = [item for item in existing if item.date != load.date]
        existing.append(load)
        existing.sort(key=lambda x: x.date)
        _save_json_list(path, existing)

    def query_load(
        self, date_from: Optional[str] = None, date_to: Optional[str] = None
    ) -> list[TrainingLoad]:
        path = self.load_dir / "training_load.json"
        loads = _load_json_list(path, TrainingLoad)
        if date_from:
            loads = [l for l in loads if l.date >= date_from]
        if date_to:
            loads = [l for l in loads if l.date <= date_to]
        return sorted(loads, key=lambda x: x.date)

    # ============ BodySignal ============
    def upsert_body_signal(self, signal: BodySignal) -> None:
        """upsert BodySignal（同日覆盖）."""
        year_month = signal.date[:7]  # YYYY-MM
        path = self.body_signals_dir / f"body_signals_{year_month}.json"
        existing = _load_json_list(path, BodySignal)
        existing = [item for item in existing if item.date != signal.date]
        existing.append(signal)
        existing.sort(key=lambda x: x.date)
        _save_json_list(path, existing)

    def query_body_signals(self, date_from: str, date_to: str) -> list[BodySignal]:
        """按日期范围查询 BodySignal."""
        # 扫描所有月份文件
        results: list[BodySignal] = []
        for path in sorted(self.body_signals_dir.glob("body_signals_*.json")):
            signals = _load_json_list(path, BodySignal)
            results.extend([s for s in signals if date_from <= s.date <= date_to])
        return sorted(results, key=lambda x: x.date)

    # ============ DecisionLog ============
    def append_decision(self, decision: DecisionLog) -> None:
        """追加 DecisionLog（不覆盖）."""
        year_month = decision.timestamp.strftime("%Y-%m")
        path = self.decisions_dir / f"decisions_{year_month}.json"
        existing = _load_json_list(path, DecisionLog)
        existing.append(decision)
        _save_json_list(path, existing)

    def query_decisions(
        self, date_from: Optional[str] = None, date_to: Optional[str] = None
    ) -> list[DecisionLog]:
        results: list[DecisionLog] = []
        for path in sorted(self.decisions_dir.glob("decisions_*.json")):
            decisions = _load_json_list(path, DecisionLog)
            for d in decisions:
                ts_date = d.timestamp.strftime("%Y-%m-%d")
                if date_from and ts_date < date_from:
                    continue
                if date_to and ts_date > date_to:
                    continue
                results.append(d)
        return sorted(results, key=lambda x: x.timestamp)

    # ============ TrainingPlan ============
    def save_plan(self, plan: TrainingPlan) -> None:
        path = self.plans_dir / f"{plan.plan_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(plan.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)

    def load_plan(self, plan_id: str) -> Optional[TrainingPlan]:
        path = self.plans_dir / f"{plan_id}.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return TrainingPlan.model_validate(data)

    def list_plans(self) -> list[TrainingPlan]:
        plans: list[TrainingPlan] = []
        for path in sorted(self.plans_dir.glob("plan_*.json")):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            plans.append(TrainingPlan.model_validate(data))
        return plans

    # ============ UserConfig（M-3 评审修正）============
    def load_user_config(self) -> UserConfig:
        """读取 data/config.json，不存在返回空 UserConfig."""
        path = self.data_dir / "config.json"
        if not path.exists():
            return UserConfig()
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return UserConfig.model_validate(data)

    def save_user_config(self, config: UserConfig) -> None:
        """保存 UserConfig，部分字段更新（合并已有配置）."""
        existing = self.load_user_config()
        # 合并：新 config 中非 None 字段覆盖旧值
        merged_data = existing.model_dump(exclude_none=True)
        new_data = config.model_dump(exclude_none=True)
        merged_data.update(new_data)
        merged_data["updated_at"] = datetime.utcnow().isoformat()

        path = self.data_dir / "config.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2, default=str)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/storage/test_json_store.py -v`
Expected: 11 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/json_store.py run-flow-skills-mcp/tests/storage/test_json_store.py
git commit -m "feat(storage/json_store): implement JSON storage for Load/BodySignal/DecisionLog/Plan/UserConfig"
```

---

## Task 12: storage/dedup.py 跨平台去重

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/dedup.py`
- Test: `run-flow-skills-mcp/tests/storage/test_dedup.py`

**Interfaces:**
- Consumes: `models.Session`、`constants.DEDUP_*` 容差、`ParquetStore.find_by_hash`
- Produces:
  - `check_hash_duplicate(store: ParquetStore, raw_file_hash: str) -> Optional[Session]`：通过 SHA256 查找已存 Session
  - `find_cross_platform_duplicate(store: ParquetStore, candidate: Session) -> Optional[Session]`：通过时间/距离/时长匹配查找跨平台重复
  - `is_cross_platform_match(s1: Session, s2: Session) -> bool`：判定两 Session 是否为跨平台同一活动

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/storage/test_dedup.py`：

```python
"""去重逻辑测试（spec 5.3, FR-IMPORT-05）."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from run_flow_skills_mcp.models import Session
from run_flow_skills_mcp.storage.dedup import (
    check_hash_duplicate,
    find_cross_platform_duplicate,
    is_cross_platform_match,
)
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


@pytest.fixture
def store(tmp_data_dir: Path) -> ParquetStore:
    return ParquetStore(data_dir=tmp_data_dir)


def _make_session(
    dt: datetime,
    distance: float = 10000.0,
    duration: int = 3600,
    source: str = "garmin",
    raw_hash: str = "hash_garmin",
) -> Session:
    return Session(
        session_id=f"sess_{dt.strftime('%Y%m%d')}_001",
        activity_date=dt,
        distance_m=distance,
        duration_s=duration,
        avg_pace_s_per_km=duration / (distance / 1000),
        source=source,
        raw_file_hash=raw_hash,
    )


def test_check_hash_duplicate_found(store: ParquetStore):
    s = _make_session(datetime(2026, 7, 25, 6, 0), raw_hash="abc")
    store.append_session(s)
    found = check_hash_duplicate(store, "abc")
    assert found is not None
    assert found.session_id == s.session_id


def test_check_hash_duplicate_not_found(store: ParquetStore):
    found = check_hash_duplicate(store, "nonexistent")
    assert found is None


def test_is_cross_platform_match_same_activity():
    """同一活动，Garmin 与 Apple Watch 时间相差 3 分钟，距离 0.5%."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0), source="garmin")
    s2 = _make_session(
        datetime(2026, 7, 25, 6, 3),  # +3 分钟（<5 分钟容差）
        distance=10050.0,  # +0.5%（<2%）
        duration=3610,  # +10 秒（<30 秒）
        source="apple",
    )
    assert is_cross_platform_match(s1, s2) is True


def test_is_cross_platform_match_different_activity():
    """时间相差 10 分钟，非同一活动."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0))
    s2 = _make_session(datetime(2026, 7, 25, 6, 10))  # +10 分钟（>5 分钟）
    assert is_cross_platform_match(s1, s2) is False


def test_is_cross_platform_match_distance_too_different():
    """距离相差 5%，超出容差."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0), distance=10000.0)
    s2 = _make_session(
        datetime(2026, 7, 25, 6, 3),
        distance=10500.0,  # +5%（>2%）
    )
    assert is_cross_platform_match(s1, s2) is False


def test_is_cross_platform_match_duration_too_different():
    """时长相差 60 秒，超出容差."""
    s1 = _make_session(datetime(2026, 7, 25, 6, 0), duration=3600)
    s2 = _make_session(
        datetime(2026, 7, 25, 6, 3),
        duration=3660,  # +60 秒（>30 秒）
    )
    assert is_cross_platform_match(s1, s2) is False


def test_find_cross_platform_duplicate_finds_match(store: ParquetStore):
    """已存 Garmin 活动，新导入 Apple 活动，应识别为重复."""
    garmin = _make_session(datetime(2026, 7, 25, 6, 0), source="garmin", raw_hash="g1")
    store.append_session(garmin)

    apple = _make_session(
        datetime(2026, 7, 25, 6, 3),
        distance=10050.0,
        duration=3610,
        source="apple",
        raw_hash="a1",  # 不同 hash
    )
    duplicate = find_cross_platform_duplicate(store, apple)
    assert duplicate is not None
    assert duplicate.source == "garmin"


def test_find_cross_platform_duplicate_no_match(store: ParquetStore):
    apple = _make_session(datetime(2026, 7, 25, 6, 0), source="apple", raw_hash="a1")
    duplicate = find_cross_platform_duplicate(store, apple)
    assert duplicate is None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/storage/test_dedup.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/dedup.py`：

```python
"""去重逻辑（spec 5.3, FR-IMPORT-05）.

- 主去重键：raw_file_hash（SHA256）
- 跨平台去重：时间戳 ±5 分钟 + 距离 ±2% + 时长 ±30 秒
"""
from __future__ import annotations

from typing import Optional

from run_flow_skills_mcp.constants import (
    DEDUP_DISTANCE_TOLERANCE_PCT,
    DEDUP_DURATION_TOLERANCE_S,
    DEDUP_TIME_TOLERANCE_S,
)
from run_flow_skills_mcp.models import Session
from run_flow_skills_mcp.storage.parquet_store import ParquetStore


def check_hash_duplicate(
    store: ParquetStore, raw_file_hash: str
) -> Optional[Session]:
    """通过 SHA256 查找已存在的 Session（spec 5.3 主去重键）."""
    if not raw_file_hash:
        return None
    return store.find_by_hash(raw_file_hash)


def is_cross_platform_match(s1: Session, s2: Session) -> bool:
    """判定两 Session 是否为跨平台同一活动（spec 5.3）.

    匹配条件（同时满足）：
    - 时间戳差 <= 5 分钟
    - 距离相对差 <= 2%
    - 时长差 <= 30 秒
    """
    # 时间戳匹配
    time_diff_s = abs((s1.activity_date - s2.activity_date).total_seconds())
    if time_diff_s > DEDUP_TIME_TOLERANCE_S:
        return False

    # 距离匹配（相对差）
    max_distance = max(s1.distance_m, s2.distance_m)
    if max_distance <= 0:
        return False
    distance_diff_pct = abs(s1.distance_m - s2.distance_m) / max_distance
    if distance_diff_pct > DEDUP_DISTANCE_TOLERANCE_PCT:
        return False

    # 时长匹配
    duration_diff_s = abs(s1.duration_s - s2.duration_s)
    if duration_diff_s > DEDUP_DURATION_TOLERANCE_S:
        return False

    return True


def find_cross_platform_duplicate(
    store: ParquetStore, candidate: Session
) -> Optional[Session]:
    """查找 candidate 是否与已存 Session 跨平台重复.

    Returns:
        重复的已存 Session（如有），否则 None
    """
    # 查询候选活动时间附近 ±1 天的所有 sessions（避免全表扫描）
    date_from = (candidate.activity_date).strftime("%Y-%m-%d")
    date_to = (candidate.activity_date).strftime("%Y-%m-%d")
    candidates = store.query_sessions(date_from=date_from, date_to=date_to)

    for existing in candidates:
        if existing.session_id == candidate.session_id:
            continue
        if existing.source == candidate.source:
            # 同源不视为跨平台重复（同源应由 hash 去重）
            continue
        if is_cross_platform_match(existing, candidate):
            return existing
    return None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/storage/test_dedup.py -v`
Expected: 8 个测试全部 PASS

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/dedup.py run-flow-skills-mcp/tests/storage/test_dedup.py
git commit -m "feat(storage/dedup): implement SHA256 and cross-platform deduplication"
```

---

## Task 13: storage/importer.py FIT/GPX/CSV/TCX/XML 解析

**Files:**
- Create: `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/importer.py`
- Test: `run-flow-skills-mcp/tests/storage/test_importer.py`
- Create: `run-flow-skills-mcp/tests/data/fixtures/.gitkeep`
- Create: `run-flow-skills-mcp/tests/data/fixtures/sample.fit`（合成 FIT 文件，由测试代码生成）
- Create: `run-flow-skills-mcp/tests/data/fixtures/sample.gpx`（合成 GPX 文件）

**Interfaces:**
- Consumes: `models.Session`、`constants.SUPPORTED_IMPORT_EXT`
- Produces:
  - `parse_file(file_path: Path) -> Session`：根据扩展名分发到对应 parser
  - `parse_fit(path: Path) -> Session`：用 fitparse 解析
  - `parse_gpx(path: Path) -> Session`：用 xml.etree 解析
  - `parse_csv(path: Path) -> Session`：Garmin CSV 导出
  - `parse_tcx(path: Path) -> Session`：XML 解析
  - `parse_xml(path: Path) -> Session`：Apple Health XML
  - `compute_file_hash(path: Path) -> str`：SHA256
  - `ImportError` 自定义异常（文件格式错误/不支持的扩展名）

- [ ] **Step 1: 写失败测试**

写入 `run-flow-skills-mcp/tests/storage/test_importer.py`：

```python
"""导入器测试（spec FR-IMPORT-01/02/03, M-1 评审修正 GPX）."""
import hashlib
from pathlib import Path

import pytest

from run_flow_skills_mcp.storage.importer import (
    ImportParseError,
    compute_file_hash,
    parse_file,
    parse_gpx,
)


def _write_gpx(path: Path) -> None:
    """生成合成 GPX 测试文件."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <time>2026-07-25T06:00:00Z</time>
  </metadata>
  <trk>
    <name>Morning Run</name>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>50.0</ele>
        <time>2026-07-25T06:00:00Z</time>
      </trkpt>
      <trkpt lat="39.9050" lon="116.4080">
        <ele>51.0</ele>
        <time>2026-07-25T06:00:01Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    path.write_text(gpx_content, encoding="utf-8")


def test_compute_file_hash_stable(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("hello", encoding="utf-8")
    h1 = compute_file_hash(f)
    h2 = compute_file_hash(f)
    assert h1 == h2
    assert h1 == hashlib.sha256(b"hello").hexdigest()


def test_parse_gpx_basic(tmp_path: Path):
    """M-1 评审修正：GPX 解析必须支持."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_gpx(gpx_path)
    assert session.source == "garmin"  # GPX 默认归 garmin（可在 parse_file 覆盖）
    assert session.activity_date is not None
    assert session.duration_s >= 0


def test_parse_file_dispatches_by_extension(tmp_path: Path):
    """parse_file 根据扩展名分发."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_file(gpx_path)
    assert session is not None


def test_parse_file_unsupported_extension_raises(tmp_path: Path):
    """不支持的扩展名应抛 ImportParseError."""
    bad_path = tmp_path / "test.txt"
    bad_path.write_text("invalid", encoding="utf-8")

    with pytest.raises(ImportParseError):
        parse_file(bad_path)


def test_parse_file_sets_raw_file_hash(tmp_path: Path):
    """解析后应填充 raw_file_hash（去重键）."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_file(gpx_path)
    assert session.raw_file_hash is not None
    assert session.raw_file_hash == compute_file_hash(gpx_path)


def test_parse_file_sets_raw_file_path(tmp_path: Path):
    """解析后应填充 raw_file_path（追溯）."""
    gpx_path = tmp_path / "test.gpx"
    _write_gpx(gpx_path)

    session = parse_file(gpx_path)
    assert session.raw_file_path == "test.gpx"


def test_parse_file_corrupt_gpx_raises(tmp_path: Path):
    """损坏的 GPX 应抛 ImportParseError."""
    gpx_path = tmp_path / "test.gpx"
    gpx_path.write_text("not valid xml <<<", encoding="utf-8")

    with pytest.raises(ImportParseError):
        parse_file(gpx_path)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/storage/test_importer.py -v`
Expected: FAIL，`ImportError`

- [ ] **Step 3: 写最小实现**

写入 `run-flow-skills-mcp/tests/data/fixtures/.gitkeep`（空文件占位）：

```
```

写入 `run-flow-skills-mcp/src/run_flow_skills_mcp/storage/importer.py`：

```python
"""文件导入解析器 - FIT/GPX/CSV/TCX/XML（spec FR-IMPORT-01/02/03, M-1 评审修正）.

GPX/TCX 用标准库 xml.etree，无新依赖（M-1 决策）。
FIT 用 fitparse 库。
"""
from __future__ import annotations

import csv
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from run_flow_skills_mcp.constants import SUPPORTED_IMPORT_EXT
from run_flow_skills_mcp.models import Session, SourceType


class ImportParseError(Exception):
    """文件解析错误."""


def compute_file_hash(path: Path) -> str:
    """计算文件 SHA256 哈希."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_gpx_time(time_str: str) -> datetime:
    """解析 GPX 时间格式 ISO 8601 UTC."""
    # 2026-07-25T06:00:00Z
    if time_str.endswith("Z"):
        time_str = time_str[:-1] + "+00:00"
    return datetime.fromisoformat(time_str)


def parse_gpx(path: Path, source: SourceType = "garmin") -> Session:
    """解析 GPX 文件（M-1 评审修正）.

    GPX 1.1 格式：trk > trkseg > trkpt (lat, lon, ele, time)
    """
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise ImportParseError(f"GPX 解析失败: {e}") from e

    root = tree.getroot()
    # 处理命名空间
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # 提取所有 trkpt
    points = root.findall(f".//{ns}trkpt")
    if not points:
        raise ImportParseError("GPX 无轨迹点")

    # 提取时间和位置
    times: list[datetime] = []
    elevations: list[float] = []
    lat_lon: list[tuple[float, float]] = []

    for pt in points:
        lat = float(pt.get("lat", "0"))
        lon = float(pt.get("lon", "0"))
        lat_lon.append((lat, lon))

        time_elem = pt.find(f"{ns}time")
        if time_elem is not None and time_elem.text:
            times.append(_parse_gpx_time(time_elem.text))

        ele_elem = pt.find(f"{ns}ele")
        if ele_elem is not None and ele_elem.text:
            elevations.append(float(ele_elem.text))

    if not times:
        # 无时间戳，用文件修改时间
        activity_date = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        duration_s = 0
    else:
        activity_date = times[0]
        duration_s = int((times[-1] - times[0]).total_seconds()) if len(times) > 1 else 0

    # 计算距离（Haversine 简化版）
    distance_m = _calc_track_distance(lat_lon)

    # 累计爬升
    elevation_gain = _calc_elevation_gain(elevations) if elevations else None

    avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

    session_id = _generate_id_from_date(activity_date)
    return Session(
        session_id=session_id,
        activity_date=activity_date,
        distance_m=distance_m,
        duration_s=max(duration_s, 1),
        avg_pace_s_per_km=avg_pace if avg_pace > 0 else 0.0,
        elevation_gain_m=elevation_gain,
        source=source,
        raw_file_hash=compute_file_hash(path),
        raw_file_path=path.name,
    )


def _calc_track_distance(points: list[tuple[float, float]]) -> float:
    """Haversine 简化距离计算（米）."""
    if len(points) < 2:
        return 0.0
    import math

    total = 0.0
    for i in range(1, len(points)):
        lat1, lon1 = points[i - 1]
        lat2, lon2 = points[i]
        # Haversine
        r = 6371000.0  # 地球半径（米）
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        total += r * c
    return total


def _calc_elevation_gain(elevations: list[float]) -> float:
    """累计爬升（仅正向差值累加）."""
    gain = 0.0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i - 1]
        if diff > 0:
            gain += diff
    return gain


def _generate_id_from_date(dt: datetime) -> str:
    """根据日期生成临时 session_id（实际应由 service 层重写）."""
    date_str = dt.strftime("%Y%m%d")
    return f"sess_{date_str}_001"


def parse_fit(path: Path, source: SourceType = "garmin") -> Session:
    """解析 FIT 文件（用 fitparse）."""
    try:
        from fitparse import FitFile
    except ImportError as e:
        raise ImportParseError("fitparse 未安装") from e

    try:
        fitfile = FitFile(str(path))
        # 提取关键信息
        activity_date: Optional[datetime] = None
        total_distance = 0.0
        total_timer_time = 0
        avg_hr: Optional[int] = None
        max_hr: Optional[int] = None

        for record in fitfile.get_messages():
            for field in record:
                if field.name == "total_distance":
                    total_distance = float(field.value or 0)
                elif field.name == "total_timer_time":
                    total_timer_time = int(field.value or 0)
                elif field.name == "avg_heart_rate":
                    avg_hr = int(field.value) if field.value else None
                elif field.name == "max_heart_rate":
                    max_hr = int(field.value) if field.value else None
                elif field.name == "time_created":
                    activity_date = field.value

        if activity_date is None:
            activity_date = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

        distance_m = total_distance
        duration_s = max(total_timer_time, 1)
        avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

        return Session(
            session_id=_generate_id_from_date(activity_date),
            activity_date=activity_date,
            distance_m=distance_m,
            duration_s=duration_s,
            avg_pace_s_per_km=avg_pace,
            avg_hr=avg_hr,
            max_hr=max_hr,
            source=source,
            raw_file_hash=compute_file_hash(path),
            raw_file_path=path.name,
        )
    except Exception as e:
        raise ImportParseError(f"FIT 解析失败: {e}") from e


def parse_csv(path: Path, source: SourceType = "garmin") -> Session:
    """解析 Garmin Connect CSV 导出."""
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader, None)
            if row is None:
                raise ImportParseError("CSV 无数据行")

            # Garmin CSV 字段：Activity Date, Distance, Duration, Avg HR, Max HR
            activity_date = datetime.fromisoformat(row.get("Activity Date", ""))
            distance_m = float(row.get("Distance", 0)) * 1000  # km → m
            duration_s = int(float(row.get("Duration", 0)))
            avg_hr = int(row["Avg HR"]) if row.get("Avg HR") else None
            max_hr = int(row["Max HR"]) if row.get("Max HR") else None

            avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

            return Session(
                session_id=_generate_id_from_date(activity_date),
                activity_date=activity_date,
                distance_m=distance_m,
                duration_s=max(duration_s, 1),
                avg_pace_s_per_km=avg_pace,
                avg_hr=avg_hr,
                max_hr=max_hr,
                source=source,
                raw_file_hash=compute_file_hash(path),
                raw_file_path=path.name,
            )
    except (ValueError, KeyError) as e:
        raise ImportParseError(f"CSV 解析失败: {e}") from e


def parse_tcx(path: Path, source: SourceType = "garmin") -> Session:
    """解析 TCX 文件（XML）."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # TCX 命名空间
        ns = "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}"

        activity = root.find(f".//{ns}Activity")
        if activity is None:
            raise ImportParseError("TCX 无 Activity 节点")

        # 提取时间、距离、时长、心率
        id_elem = activity.find(f"{ns}Id")
        activity_date = _parse_gpx_time(id_elem.text) if id_elem is not None and id_elem.text else datetime.now(timezone.utc)

        distance_elem = activity.find(f".//{ns}DistanceMeters")
        distance_m = float(distance_elem.text) if distance_elem is not None else 0.0

        time_elem = activity.find(f".//{ns}TotalTimeSeconds")
        duration_s = int(float(time_elem.text)) if time_elem is not None else 0

        avg_hr_elem = activity.find(f".//{ns}AverageHeartRateBpm/{ns}Value")
        avg_hr = int(avg_hr_elem.text) if avg_hr_elem is not None else None

        avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

        return Session(
            session_id=_generate_id_from_date(activity_date),
            activity_date=activity_date,
            distance_m=distance_m,
            duration_s=max(duration_s, 1),
            avg_pace_s_per_km=avg_pace,
            avg_hr=avg_hr,
            source=source,
            raw_file_hash=compute_file_hash(path),
            raw_file_path=path.name,
        )
    except ET.ParseError as e:
        raise ImportParseError(f"TCX 解析失败: {e}") from e


def parse_xml(path: Path, source: SourceType = "apple") -> Session:
    """解析 Apple Health XML 导出."""
    # ponytail: Apple Health XML 格式复杂，MVP 仅支持简化版单活动
    # 升级路径：v0.2.0 完整支持 Apple Health 多活动
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Apple Health: Record type="HKQuantityTypeIdentifierDistanceWalkingRunning"
        record = root.find(".//Record")
        if record is None:
            raise ImportParseError("Apple Health XML 无 Record")

        activity_date = _parse_gpx_time(record.get("startDate", ""))
        distance_m = float(record.get("value", "0"))
        # Apple Health 不直接提供时长，用 endDate - startDate
        end_date = _parse_gpx_time(record.get("endDate", activity_date.isoformat()))
        duration_s = int((end_date - activity_date).total_seconds())

        avg_pace = duration_s / (distance_m / 1000) if distance_m > 0 else 0.0

        return Session(
            session_id=_generate_id_from_date(activity_date),
            activity_date=activity_date,
            distance_m=distance_m,
            duration_s=max(duration_s, 1),
            avg_pace_s_per_km=avg_pace,
            source=source,
            raw_file_hash=compute_file_hash(path),
            raw_file_path=path.name,
        )
    except ET.ParseError as e:
        raise ImportParseError(f"Apple Health XML 解析失败: {e}") from e


def parse_file(path: Path, source: Optional[SourceType] = None) -> Session:
    """根据文件扩展名分发到对应解析器（spec FR-IMPORT-01）.

    Args:
        path: 文件路径
        source: 可选数据源覆盖，None 时使用各 parser 的默认值

    Returns:
        解析后的 Session（含 raw_file_hash、raw_file_path）

    Raises:
        ImportParseError: 扩展名不支持或解析失败
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED_IMPORT_EXT:
        raise ImportParseError(
            f"不支持的文件扩展名: {ext}，支持: {', '.join(SUPPORTED_IMPORT_EXT)}"
        )

    parser_map = {
        ".fit": parse_fit,
        ".gpx": parse_gpx,
        ".csv": parse_csv,
        ".tcx": parse_tcx,
        ".xml": parse_xml,
    }

    parser = parser_map[ext]
    if source is not None:
        return parser(path, source=source)
    return parser(path)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/storage/test_importer.py -v`
Expected: 7 个测试全部 PASS

注意：
- `test_parse_gpx_basic` 期望 `session.source == "garmin"`（parse_gpx 默认值）
- `test_parse_file_dispatches_by_extension` 验证 parse_file 正确分发
- `test_parse_file_unsupported_extension_raises` 验证 .txt 抛 ImportParseError
- `test_parse_file_corrupt_gpx_raises` 验证损坏 XML 抛 ImportParseError

- [ ] **Step 5: Commit**

```bash
git add run-flow-skills-mcp/src/run_flow_skills_mcp/storage/importer.py run-flow-skills-mcp/tests/storage/test_importer.py run-flow-skills-mcp/tests/data/fixtures/.gitkeep
git commit -m "feat(storage/importer): implement FIT/GPX/CSV/TCX/XML parsers with SHA256 dedup key"
```

---

## Plan 1 完成验收

### 整体回归测试

完成 Task 1-13 后，运行完整测试套件验证：

```bash
cd run-flow-skills-mcp
uv run pytest tests/ -v --cov=src/run_flow_skills_mcp --cov-report=term-missing
```

**预期结果**：
- 全部测试通过（约 80 个测试用例）
- 覆盖率：
  - `calculators/` ≥ 90%
  - `models.py` ≥ 80%
  - `constants.py` ≥ 80%
  - `storage/` ≥ 80%

### 静态检查

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/ --ignore-missing-imports
```

**预期结果**：
- ruff check 无错误
- ruff format 无 diff
- mypy 无错误（pyarrow/polars/fitparse 等第三方库 ignore_missing_imports）

### 模块导入冒烟测试

```bash
uv run python -c "
from run_flow_skills_mcp import constants, models
from run_flow_skills_mcp.calculators import vdot, training_load, hrv, pace_zones, hr_zones, fatigue
from run_flow_skills_mcp.storage import parquet_store, json_store, dedup, importer
print('All modules imported successfully')
print('Tools available for Plan 2:', [
    'calc_vdot', 'calc_tss', 'calc_ctl', 'calc_atl', 'calc_tsb',
    'calc_rmssd', 'calc_hrv_baseline', 'calc_pace_zones',
    'calc_hr_zones_boundaries', 'calc_fatigue_score'
])
"
```

**预期结果**：
- 输出 `All modules imported successfully`
- 输出 Plan 2 将依赖的函数列表

### 交付物清单

Plan 1 完成时应有以下文件：

| 类别 | 文件 | 说明 |
|------|------|------|
| 配置 | `pyproject.toml` | 项目依赖与工具配置 |
| 配置 | `.gitignore` | 排除 data/ 等 |
| 入口 | `src/run_flow_skills_mcp/__init__.py` | 包入口 |
| 常量 | `src/run_flow_skills_mcp/constants.py` | 默认配置与格式化函数 |
| 模型 | `src/run_flow_skills_mcp/models.py` | 10 个 Pydantic 模型 |
| 计算 | `src/run_flow_skills_mcp/calculators/vdot.py` | VDOT (Powers) |
| 计算 | `src/run_flow_skills_mcp/calculators/training_load.py` | TSS/CTL/ATL/TSB |
| 计算 | `src/run_flow_skills_mcp/calculators/hrv.py` | RMSSD/SDNN/pNN50 |
| 计算 | `src/run_flow_skills_mcp/calculators/pace_zones.py` | E/M/T/I/R 区间 |
| 计算 | `src/run_flow_skills_mcp/calculators/hr_zones.py` | Z1-Z5 区间 |
| 计算 | `src/run_flow_skills_mcp/calculators/fatigue.py` | 疲劳度综合评估 |
| 存储 | `src/run_flow_skills_mcp/storage/parquet_store.py` | Parquet 按年分片 |
| 存储 | `src/run_flow_skills_mcp/storage/json_store.py` | JSON 读写 |
| 存储 | `src/run_flow_skills_mcp/storage/dedup.py` | 去重 |
| 存储 | `src/run_flow_skills_mcp/storage/importer.py` | 5 种格式解析 |
| 测试 | `tests/test_*.py`、`tests/calculators/test_*.py`、`tests/storage/test_*.py` | 完整单元测试 |

### 后续 Plan 衔接

Plan 1 提供的接口供 Plan 2 使用：

| 接口 | 使用方（Plan 2） |
|------|----------------|
| `models.*`（10 个模型） | 所有 Tools 的入参/返回类型 |
| `calc_vdot`、`calc_tss`、`calc_*` | `tools/calc_metrics.py`、`tools/get_trends.py` |
| `ParquetStore` | `services/*` 编排层 |
| `JsonStore` | `services/*`、`web/routes/settings.py` |
| `importer.parse_file` | `tools/import_file.py` |
| `dedup.check_hash_duplicate`、`dedup.find_cross_platform_duplicate` | `services/import_service.py` |

Plan 2（Services + 14 MCP Tools）将基于以上接口构建业务编排层和 MCP Tool 薄包装，输出可被 Trae/WorkBuddy 宿主调用的 MCP Server。

---

## Self-Review 检查清单

完成 Plan 1 编写后，对照 spec 进行自检：

- [x] **Spec 覆盖**：spec 第四章（数据模型）、第八章 8.1（计算规则）、第五章 5.1/5.3（存储/去重）、第六章 Tool 涉及的底层依赖（importer/parquet/json/dedup）均有对应 Task。
- [x] **占位符扫描**：无 TBD/TODO，所有 Step 含完整代码或命令。
- [x] **类型一致性**：`calc_vdot` 签名在 Task 4 定义，Plan 2 引用时一致；`Session.source` 类型 `SourceType` 在 Task 3 定义，importer 中复用；`ParquetStore.find_by_hash` 返回 `Optional[Session]`，与 dedup 调用一致。
- [x] **TDD 循环**：每个 Task 严格遵循 RED→GREEN→COMMIT 三步。
- [x] **M-1/M-2/M-3 评审修正落地**：
  - M-1（GPX）：Task 13 实现 `parse_gpx` 并测试
  - M-2（import 拆分）：底层 importer 提供 `parse_file`，供 Plan 2 的 `import_file` 和 `import_manual` 分别调用
  - M-3（UserConfig）：Task 3 定义 `UserConfig` 模型，Task 11 实现 `load_user_config`/`save_user_config`，Task 2 标注 `# DEFAULT` 可覆盖字段