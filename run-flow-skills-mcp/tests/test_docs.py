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
