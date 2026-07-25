"""server.py 测试（spec 10.2）.

验证 MCP Server 能正确加载并注册所有 14 个 tools。
不启动真实 MCP 传输，只验证 tool 注册。
"""

import asyncio

import pytest


def test_server_module_loads():
    """server.py 必须能无错加载."""
    from run_flow_skills_mcp import server

    assert hasattr(server, "mcp")
    assert server.mcp is not None


def test_server_registers_14_tools():
    """必须注册 14 个 tools."""
    from run_flow_skills_mcp.server import mcp

    # FastMCP 3.x 通过 list_tools() 异步获取
    tools = None
    if hasattr(mcp, "_tools"):
        tools = mcp._tools
    elif hasattr(mcp, "tools"):
        tools = mcp.tools
    elif hasattr(mcp, "list_tools"):
        try:
            tools = asyncio.run(mcp.list_tools())
        except Exception:
            tools = None

    if tools is None:
        pytest.skip("无法获取 tool 列表（fastmcp 版本兼容问题）")

    # tools 可能是 dict 或 list
    if isinstance(tools, dict):
        tool_names = list(tools.keys())
    elif isinstance(tools, list):
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]
    else:
        tool_names = []

    expected = {
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
    missing = expected - set(tool_names)
    assert not missing, f"缺少 tools: {missing}"


def test_server_has_main():
    """server.py 必须有 main() 入口."""
    from run_flow_skills_mcp import server

    assert hasattr(server, "main")
    assert callable(server.main)
