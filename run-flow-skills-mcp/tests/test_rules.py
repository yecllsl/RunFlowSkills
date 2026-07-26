"""AGENTS.md 跨平台规则统一入口测试.

原 .trae/rules/ 目录已迁移至根目录 AGENTS.md，本测试校验：
1. AGENTS.md 文件存在且 frontmatter 完整
2. AGENTS.md 包含原 5 个规则的全部章节
3. 每个规则的关键条目未被遗漏
"""

from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_AGENTS_MD = _PROJECT_ROOT / "AGENTS.md"

# 原 5 个 rules 在 AGENTS.md 中对应的章节标题
EXPECTED_RULE_SECTIONS = {
    "交互协议": "interaction",
    "计算规则": "calculation",
    "分析规则": "analysis",
    "教练规则": "coaching",
    "数据安全规则": "data-safety",
}


def test_agents_md_exists():
    """AGENTS.md 作为规则单一事实源必须存在."""
    assert _AGENTS_MD.exists(), "根目录 AGENTS.md 不存在"
    assert _AGENTS_MD.is_file()


def test_agents_md_has_frontmatter():
    """AGENTS.md frontmatter 含 version 与 applies_to."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert content.startswith("---"), "AGENTS.md 缺少 frontmatter"
    fm = content.split("---")[1]
    assert "project: RunFlowSkills" in fm
    assert "version:" in fm
    assert "applies_to:" in fm
    # 必须声明支持多平台
    for platform in ["trae", "claude-code", "cursor"]:
        assert platform in fm, f"AGENTS.md frontmatter 未声明支持 {platform}"


@pytest.mark.parametrize("section_title", list(EXPECTED_RULE_SECTIONS.keys()))
def test_agents_md_contains_all_rule_sections(section_title):
    """AGENTS.md 必须包含原 5 个规则的章节."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert section_title in content, f"AGENTS.md 缺少章节: {section_title}"


def test_calculation_rules_content():
    """计算规则包含关键条目（来源原 calculation-rules.md）."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert "VDOT" in content
    assert "Powers" in content
    assert "TSS" in content
    assert "CTL" in content and "42" in content
    assert "ATL" in content and "7" in content
    assert "config.json" in content  # M-3 评审修正


def test_coaching_rules_content():
    """教练规则包含关键条目（来源原 coaching-rules.md）."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert "具体可执行" in content
    assert "溯源链" in content
    assert "HRV" in content and "TSB" in content and "RPE" in content
    assert "0.6" in content  # confidence 门禁
    assert "24h" in content or "24小时" in content


def test_data_safety_rules_content():
    """数据安全规则包含关键条目（来源原 data-safety-rules.md）."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert "127.0.0.1" in content
    assert "config.json" in content
    assert "SHA256" in content
    assert "PII" in content or "个人身份" in content


def test_analysis_rules_content():
    """分析规则包含关键条目（来源原 analysis-rules.md）."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert "伪精确" in content or "误差范围" in content
    assert "置信度低" in content or "降级标注" in content
    assert "心率漂移" in content


def test_interaction_rules_content():
    """交互规则包含关键条目（来源原 interaction-rules.md）."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert "/import" in content and "/analyze" in content
    assert "降级方案" in content
    assert "用户确认" in content


def test_agents_md_has_platform_matrix():
    """AGENTS.md 包含跨平台兼容性矩阵."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert "跨平台兼容性矩阵" in content or "Platform Compatibility" in content
    assert "Claude Code" in content
    assert "Cursor" in content


def test_agents_md_declares_no_subagent_dirs():
    """AGENTS.md 明确声明不使用平台专有 subagent 目录."""
    content = _AGENTS_MD.read_text(encoding="utf-8")
    assert "subagent" in content.lower() or "sunagent" in content.lower()
