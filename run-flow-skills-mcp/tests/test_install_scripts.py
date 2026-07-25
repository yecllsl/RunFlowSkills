"""安装脚本测试."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_install_ps1_exists():
    """install.ps1 存在."""
    path = _PROJECT_ROOT / "install.ps1"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "uv" in content
    assert "run-flow-skills-mcp" in content


def test_install_sh_exists():
    """install.sh 存在."""
    path = _PROJECT_ROOT / "install.sh"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "uv" in content
    assert "run-flow-skills-mcp" in content


def test_install_ps1_mentions_trae():
    """install.ps1 提示在 Trae 中打开."""
    content = (_PROJECT_ROOT / "install.ps1").read_text(encoding="utf-8")
    assert "Trae" in content or "trae" in content.lower()
    assert "MCP" in content or "mcp" in content.lower()


def test_install_sh_mentions_trae():
    """install.sh 提示在 Trae 中打开."""
    content = (_PROJECT_ROOT / "install.sh").read_text(encoding="utf-8")
    assert "Trae" in content or "trae" in content.lower()
    assert "MCP" in content or "mcp" in content.lower()


def test_install_ps1_has_fixpath_option():
    """install.ps1 含 -FixPath 选项（mcp.json 路径修复）."""
    content = (_PROJECT_ROOT / "install.ps1").read_text(encoding="utf-8")
    assert "FixPath" in content or "workspaceFolder" in content


def test_install_scripts_mention_commands():
    """安装脚本提示可用命令."""
    for filename in ["install.ps1", "install.sh"]:
        content = (_PROJECT_ROOT / filename).read_text(encoding="utf-8")
        assert "/import" in content
        assert "/coach" in content
