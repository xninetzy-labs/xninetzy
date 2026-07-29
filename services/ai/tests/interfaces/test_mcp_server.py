import os
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.xninetzy.interfaces.mcp_server import mcp
from app.xninetzy.tools.registry import get_all_tools


def test_mcp_server_exposes_all_registered_xninetzy_tools():
    names = {tool.name for tool in mcp._tool_manager.list_tools()}
    registry_names = {tool.name for tool in get_all_tools()}

    assert names == registry_names
    assert "deep_research_topic" in names
    assert "hebat_sync_courses" in names
    assert "hebat_list_courses" in names
    assert "portal_schedule" in names
    assert "coding_agent_run" in names
    assert "os_capture" in names
    assert "os_today" in names

    coding_tool = mcp._tool_manager.get_tool("coding_agent_run")
    assert coding_tool is not None
    assert "sender_id" not in coding_tool.parameters["properties"]
    assert "sender_name" not in coding_tool.parameters["properties"]
    assert "chat_id" not in coding_tool.parameters["properties"]


@pytest.mark.asyncio
async def test_mcp_stdio_transport_lists_tools():
    ai_root = Path(__file__).resolve().parents[2]
    parameters = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--directory",
            str(ai_root),
            "python",
            "-m",
            "app.xninetzy.interfaces.mcp_server",
        ],
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
    assert len(tools.tools) == len(get_all_tools())
    assert any(tool.name == "deep_research_topic" for tool in tools.tools)
    assert any(tool.name == "hebat_sync_courses" for tool in tools.tools)


@pytest.mark.asyncio
async def test_mcp_stdio_host_mode_can_read_tasks_without_app_path(
    tmp_path: Path,
):
    ai_root = Path(__file__).resolve().parents[2]
    excluded = {
        "DATA_DIR",
        "SQLITE_PATH",
        "VECTOR_DATA_DIR",
        "WEB_ANALYSIS_DATA_DIR",
        "HEBAT_DATA_DIR",
        "HEBAT_DOWNLOAD_DIR",
    }
    child_env = {key: value for key, value in os.environ.items() if key not in excluded}
    child_env.update(
        {
            "MCP_RUNTIME_MODE": "host",
            "MCP_HOST_DATA_DIR": str(tmp_path),
        }
    )
    parameters = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--directory",
            str(ai_root),
            "python",
            "-m",
            "app.xninetzy.interfaces.mcp_server",
        ],
        env=child_env,
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("task_today", {})
            capture_result = await session.call_tool(
                "os_capture",
                {"content": "ide MCP capture", "idempotency_key": "mcp-capture-1"},
            )
            inbox_result = await session.call_tool("os_inbox", {})

    text = "\n".join(
        getattr(item, "text", "")
        for item in result.content
        if getattr(item, "text", "")
    )
    assert "Permission denied" not in text
    assert "Hari ini" in text
    capture_text = "\n".join(
        getattr(item, "text", "")
        for item in capture_result.content
        if getattr(item, "text", "")
    )
    inbox_text = "\n".join(
        getattr(item, "text", "")
        for item in inbox_result.content
        if getattr(item, "text", "")
    )
    assert "OS Inbox" in capture_text
    assert "ide MCP capture" in inbox_text
