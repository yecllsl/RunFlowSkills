"""mcp.json 配置文件测试."""
import json
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_MCP_JSON = _PROJECT_ROOT / ".trae" / "mcp.json"


def test_mcp_json_exists():
    """mcp.json 文件存在."""
    assert _MCP_JSON.exists(), f"{_MCP_JSON} 不存在"


def test_mcp_json_valid_format():
    """mcp.json 是有效 JSON."""
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    assert "mcpServers" in data


def test_mcp_json_registers_run_flow_skills():
    """注册了 run-flow-skills-mcp server."""
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    assert "run-flow-skills-mcp" in data["mcpServers"]
    server = data["mcpServers"]["run-flow-skills-mcp"]
    assert server["command"] == "uv"
    assert "run" in server["args"]


def test_mcp_json_uses_workspace_folder():
    """使用 ${workspaceFolder} 变量（Trae 自动替换）."""
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    server = data["mcpServers"]["run-flow-skills-mcp"]
    args_str = " ".join(server["args"])
    assert "${workspaceFolder}" in args_str
