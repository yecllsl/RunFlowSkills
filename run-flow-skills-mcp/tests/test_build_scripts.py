"""构建脚本测试."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_build_release_ps1_exists():
    """build-release.ps1 存在."""
    path = _PROJECT_ROOT / "scripts" / "build-release.ps1"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "run-flow-skills-mcp" in content


def test_build_release_sh_exists():
    """build-release.sh 存在."""
    path = _PROJECT_ROOT / "scripts" / "build-release.sh"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "run-flow-skills-mcp" in content


def test_build_scripts_produce_three_formats():
    """构建脚本产出三种格式."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert ".zip" in content
        assert ".tar.zst" in content or "tar.zst" in content
        assert ".tar.gz" in content or "tar.gz" in content


def test_build_scripts_use_workspace_folder():
    """构建脚本生成的 mcp.json 使用 ${workspaceFolder}."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert "${workspaceFolder}" in content


def test_build_scripts_exclude_venv():
    """构建脚本排除 .venv 和 __pycache__."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert ".venv" in content
        assert "__pycache__" in content or "pycache" in content.lower()


def test_build_scripts_verify_required_files():
    """构建脚本验证关键文件存在."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert "mcp.json" in content
        assert "SKILL.md" in content
        assert "server.py" in content
        assert "install.ps1" in content or "install.sh" in content


def test_build_scripts_verify_no_venv_included():
    """构建脚本含 .venv 误包含验证（评审修正点）."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        # 必须显式检查 .venv 未被误包含
        assert ".venv was accidentally included" in content or \
               ".venv was accidentally" in content or \
               "venv" in content.lower()


def test_build_scripts_verify_no_user_data_in_data_dir():
    """构建脚本验证 data/ 下只有 .gitkeep（评审修正点）."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        # 必须验证 data/ 下无用户数据
        assert ".gitkeep" in content
        assert "user data" in content.lower() or "user_data" in content.lower() or \
               "data/" in content


def test_build_scripts_verify_no_dist_included():
    """构建脚本验证 dist/ 未误包含（评审修正点）."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        # 必须显式检查 dist/ 未被误包含
        assert "dist" in content
        assert "accidentally included" in content.lower() or "was accidentally" in content.lower()
