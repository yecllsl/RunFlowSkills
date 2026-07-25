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
