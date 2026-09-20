from __future__ import annotations

from langchain_core.tools import StructuredTool


def _make_echo(captured: dict) -> StructuredTool:
    def echo(value: str, chat_id: str = "default") -> str:
        captured["chat_id"] = chat_id
        return f"{value}:{chat_id}"

    return StructuredTool.from_function(
        echo,
        name="sample_echo",
        description="Echo value with chat_id capture",
    )


def _make_dict_tool() -> StructuredTool:
    def echo_dict(query: str, chat_id: str = "default") -> dict:
        return {"query": query, "chat_id": chat_id, "result": "ok"}

    return StructuredTool.from_function(
        echo_dict,
        name="sample_dict",
        description="Return dict with query and chat_id",
    )


def test_trusted_context_overrides_caller_chat_id():
    import asyncio

    from xninetzy.interfaces.mcp_tool_adapter import MCPPrincipal
    from xninetzy.interfaces.mcp_tool_adapter import langchain_tool_as_mcp_callable

    captured: dict = {}
    sample_echo = _make_echo(captured)
    principal = MCPPrincipal(
        sender_id="owner-1",
        sender_name="Owner",
        chat_id="trusted-chat",
    )
    callable_tool = langchain_tool_as_mcp_callable(sample_echo, principal=principal)
    result = asyncio.run(
        callable_tool(value="hello", chat_id="caller-attacker-chat")
    )
    assert captured["chat_id"] == "trusted-chat"
    assert result.endswith(":trusted-chat")


def test_trusted_context_not_exposed_in_output_when_tool_returns_dict():
    import asyncio

    from xninetzy.interfaces.mcp_tool_adapter import MCPPrincipal
    from xninetzy.interfaces.mcp_tool_adapter import langchain_tool_as_mcp_callable

    sample_dict = _make_dict_tool()
    principal = MCPPrincipal(
        sender_id="owner-1",
        sender_name="Owner",
        chat_id="trusted-chat",
    )
    callable_tool = langchain_tool_as_mcp_callable(sample_dict, principal=principal)
    out = asyncio.run(callable_tool(query="x"))
    assert isinstance(out, dict)
    assert "chat_id" not in out
    assert out["query"] == "x"
    assert out["result"] == "ok"
