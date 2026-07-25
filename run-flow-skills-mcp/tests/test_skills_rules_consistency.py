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
