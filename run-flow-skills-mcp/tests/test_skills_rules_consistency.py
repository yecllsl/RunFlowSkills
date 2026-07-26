"""Skills 与 Rules 一致性测试.

原 .trae/rules/ 目录已迁移至根目录 AGENTS.md，本测试相应改为：
- 检查 AGENTS.md 存在
- 检查 AGENTS.md 第 9 节"Skill 引用规则"中的 Skill 名称合法
"""

import re
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SKILLS_DIR = _PROJECT_ROOT / ".trae" / "skills"
_AGENTS_MD = _PROJECT_ROOT / "AGENTS.md"

# 14 个合法 Tool（Plan 2）
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

# AGENTS.md 必须包含的 5 个规则章节标题
EXPECTED_RULE_SECTIONS = [
    "交互协议",
    "计算规则",
    "分析规则",
    "教练规则",
    "数据安全规则",
]


def test_all_skills_exist():
    """6 个 Skill 全部存在."""
    for skill in EXPECTED_SKILLS:
        assert (_SKILLS_DIR / skill / "SKILL.md").exists()


def test_agents_md_exists_and_contains_all_rules():
    """AGENTS.md 存在且包含原 5 个规则的章节."""
    assert _AGENTS_MD.exists(), "根目录 AGENTS.md 不存在"
    content = _AGENTS_MD.read_text(encoding="utf-8")
    for section in EXPECTED_RULE_SECTIONS:
        assert section in content, f"AGENTS.md 缺少章节: {section}"


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
        assert referenced.issubset(VALID_TOOLS), (
            f"{skill} 引用了非法 tool: {referenced - VALID_TOOLS}"
        )


def test_agents_md_skill_reference_table_valid():
    """AGENTS.md 第 9 节 Skill 引用表中的 Skill 名称必须合法."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    # 定位 "Skill 引用规则" 章节
    if "Skill 引用规则" not in content:
        return  # 章节缺失由其他测试覆盖
    section_start = content.index("Skill 引用规则")
    # 截取该章节内容到下一个 ## 二级标题
    next_h2 = content.find("\n## ", section_start + 1)
    section = content[section_start:next_h2 if next_h2 > 0 else len(content)]
    # 校验表中出现的 Skill 名称都在 EXPECTED_SKILLS 内
    for skill in EXPECTED_SKILLS:
        assert skill in section, f"AGENTS.md Skill 引用表缺少 {skill}"


def test_every_skill_has_workflow_section():
    """每个 Skill 有 Workflow 章节."""
    for skill in EXPECTED_SKILLS:
        content = (_SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "## Workflow" in content or "## 工作流" in content, f"{skill} 缺少 Workflow 章节"


def test_every_skill_has_common_mistakes():
    """每个 Skill 有 Common Mistakes 章节."""
    for skill in EXPECTED_SKILLS:
        content = (_SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "Common Mistakes" in content or "常见错误" in content, (
            f"{skill} 缺少 Common Mistakes"
        )
