from __future__ import annotations

import pytest
from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP

from app.xninetzy.interfaces.mcp_tool_adapter import (
    MCPPrincipal,
    expose_xninetzy_tools,
    langchain_tool_as_mcp_callable,
)


def test_adapter_preserves_langchain_tool_schema():
    @tool
    def sample_tool(required: str, limit: int = 3) -> str:
        """Tool contoh."""
        return f"{required}:{limit}"

    server = FastMCP("test")
    names = expose_xninetzy_tools(server, [sample_tool])
    exposed = server._tool_manager.get_tool("sample_tool")

    assert names == ("sample_tool",)
    assert exposed is not None
    assert exposed.parameters["required"] == ["required"]
    assert exposed.parameters["properties"]["limit"]["default"] == 3


@pytest.mark.asyncio
async def test_adapter_invokes_async_langchain_tool():
    @tool
    async def async_sample(value: int) -> str:
        """Tool async contoh."""
        return f"result:{value}"

    server = FastMCP("test")
    expose_xninetzy_tools(server, [async_sample])
    exposed = server._tool_manager.get_tool("async_sample")

    assert exposed is not None


@pytest.mark.asyncio
async def test_adapter_hides_and_injects_trusted_mcp_identity():
    @tool
    def identity_tool(value: str, chat_id: str = "", sender_id: str = "") -> str:
        """Return received identity."""
        return f"{value}:{chat_id}:{sender_id}"

    principal = MCPPrincipal(
        sender_id="owner-id",
        sender_name="Owner",
        chat_id="owner-chat",
    )
    callable_tool = langchain_tool_as_mcp_callable(identity_tool, principal)

    assert "chat_id" not in callable_tool.__signature__.parameters
    assert "sender_id" not in callable_tool.__signature__.parameters
    assert await callable_tool(value="ok") == "ok:owner-chat:owner-id"
