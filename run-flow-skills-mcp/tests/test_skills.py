"""Skills SKILL.md 文件测试."""

import re
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SKILLS_DIR = _PROJECT_ROOT / ".trae" / "skills"

# 14 个合法 Tool 名称（Plan 2）
VALID_TOOLS = {
    "import_file",
    "import_manual",
    "query_sessions",
    "calc_metrics",
    "get_trends",
    "analyze_fatigue",
    "generate_plan",
    "query_plan",
    "get_period_summary",
    "read_body_signals",
    "get_decision_trace",
    "save_decision_log",
    "get_statistics",
    "export_data",
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
    referenced = set(
        re.findall(
            r"`(import_file|import_manual|query_sessions|calc_metrics|"
            r"get_trends|analyze_fatigue|generate_plan|query_plan|"
            r"get_period_summary|read_body_signals|get_decision_trace|"
            r"save_decision_log|get_statistics|export_data)`",
            content,
        )
    )
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
