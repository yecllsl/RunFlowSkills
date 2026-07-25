"""GitHub Actions workflow 测试."""

from pathlib import Path

import pytest

try:
    import yaml
except ImportError:
    yaml = None

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_WORKFLOWS_DIR = _PROJECT_ROOT / ".github" / "workflows"


def test_test_workflow_exists():
    """test.yml 存在."""
    assert (_WORKFLOWS_DIR / "test.yml").exists()


def test_release_workflow_exists():
    """release.yml 存在."""
    assert (_WORKFLOWS_DIR / "release.yml").exists()


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_test_workflow_valid_yaml():
    """test.yml 是有效 YAML."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert "jobs" in data
    assert "unit-tests" in data["jobs"]


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_test_workflow_matrix_python():
    """test.yml 含 Python 3.12/3.13 矩阵."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    matrix = data["jobs"]["unit-tests"]["strategy"]["matrix"]["python-version"]
    assert "3.12" in matrix
    assert "3.13" in matrix


def test_test_workflow_runs_pytest():
    """test.yml 运行 pytest."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    assert "pytest" in content
    assert "uv sync" in content


def test_test_workflow_has_e2e_job():
    """test.yml 含 E2E 测试 job."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    assert "e2e" in content.lower()
    assert "playwright" in content.lower()


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_release_workflow_valid_yaml():
    """release.yml 是有效 YAML."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert "jobs" in data
    assert "build-release" in data["jobs"]


def test_release_workflow_triggers_on_tag():
    """release.yml 在 push tag v*.*.* 时触发."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert "tags" in content
    assert "v*.*.*" in content


def test_release_workflow_runs_build_script():
    """release.yml 调用 build-release.sh."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert "build-release.sh" in content


def test_release_workflow_uploads_three_formats():
    """release.yml 上传三种格式."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert ".zip" in content
    assert ".tar.zst" in content
    assert ".tar.gz" in content


def test_release_workflow_uses_gh_release():
    """release.yml 使用 GitHub Release action."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert "gh-release" in content or "github-release" in content.lower()
