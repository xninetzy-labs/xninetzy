import os
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.xninetzy.interfaces.mcp_server import mcp


def test_mcp_server_exposes_curated_xninetzy_tools():
    names = {tool.name for tool in mcp._tool_manager.list_tools()}

    assert "obsidian_read" in names
    assert "obsidian_create" in names
    assert "knowledge_search" in names
    assert "task_capture" in names
    assert "reminder_create" in names
    assert "coding_agent_run" not in names


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
    assert len(tools.tools) == 22


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

    text = "\n".join(
        getattr(item, "text", "")
        for item in result.content
        if getattr(item, "text", "")
    )
    assert "Permission denied" not in text
    assert "Hari ini" in text
