"""发布就绪测试：验证 v0.1.0 所有必要文件存在."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestReleaseReadiness:
    """验证发布包所需的所有文件就绪."""

    # ─────────── .trae 配置 ───────────
    def test_mcp_json_exists(self):
        assert (_PROJECT_ROOT / ".trae" / "mcp.json").exists()

    @pytest.mark.parametrize("skill", [
        "runflow-import", "runflow-analyze", "runflow-plan",
        "runflow-review", "runflow-coach", "runflow-stats",
    ])
    def test_skill_exists(self, skill):
        assert (_PROJECT_ROOT / ".trae" / "skills" / skill / "SKILL.md").exists()

    @pytest.mark.parametrize("rule", [
        "calculation-rules.md", "analysis-rules.md", "coaching-rules.md",
        "data-safety-rules.md", "interaction-rules.md",
    ])
    def test_rule_exists(self, rule):
        assert (_PROJECT_ROOT / ".trae" / "rules" / rule).exists()

    # ─────────── MCP Server ───────────
    def test_server_py_exists(self):
        path = _PROJECT_ROOT / "run-flow-skills-mcp" / "src" / "run_flow_skills_mcp" / "server.py"
        assert path.exists()

    def test_pyproject_toml_exists(self):
        assert (_PROJECT_ROOT / "run-flow-skills-mcp" / "pyproject.toml").exists()

    def test_uv_lock_exists(self):
        assert (_PROJECT_ROOT / "run-flow-skills-mcp" / "uv.lock").exists()

    # ─────────── Web ───────────
    def test_web_app_exists(self):
        path = _PROJECT_ROOT / "run-flow-skills-mcp" / "src" / "run_flow_skills_mcp" / "web" / "app.py"
        assert path.exists()

    def test_web_templates_exist(self):
        tmpl_dir = _PROJECT_ROOT / "run-flow-skills-mcp" / "src" / "run_flow_skills_mcp" / "web" / "templates"
        assert (tmpl_dir / "base.html").exists()
        assert (tmpl_dir / "partials" / "dashboard.html").exists()
        assert (tmpl_dir / "partials" / "import.html").exists()
        assert (tmpl_dir / "partials" / "settings.html").exists()

    # ─────────── 脚本和 CI/CD ───────────
    def test_install_scripts_exist(self):
        assert (_PROJECT_ROOT / "install.ps1").exists()
        assert (_PROJECT_ROOT / "install.sh").exists()

    def test_build_scripts_exist(self):
        assert (_PROJECT_ROOT / "scripts" / "build-release.ps1").exists()
        assert (_PROJECT_ROOT / "scripts" / "build-release.sh").exists()

    def test_workflows_exist(self):
        assert (_PROJECT_ROOT / ".github" / "workflows" / "test.yml").exists()
        assert (_PROJECT_ROOT / ".github" / "workflows" / "release.yml").exists()

    # ─────────── 文档 ───────────
    def test_docs_exist(self):
        for f in ["README.md", "QUICKSTART.md", "DEPLOY.md", "LICENSE"]:
            assert (_PROJECT_ROOT / f).exists(), f"{f} 不存在"

    # ─────────── .gitignore ───────────
    def test_gitignore_excludes_data(self):
        content = (_PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "data" in content or "data/" in content

    def test_gitignore_excludes_venv(self):
        content = (_PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert ".venv" in content or "venv" in content
