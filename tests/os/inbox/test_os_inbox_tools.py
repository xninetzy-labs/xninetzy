from app.xninetzy.ecosystem.command_router import parse_command
from app.xninetzy.interfaces.mcp_tool_adapter import (
    MCPPrincipal,
    langchain_tool_as_mcp_callable,
)
from app.xninetzy.os.inbox.tools import os_capture
from app.xninetzy.tools.registry import get_tool_groups, get_tool_names


def test_os_commands_route_to_shared_tools():
    assert parse_command("/today") == ("os_today", {})
    assert parse_command("/inbox") == ("os_inbox", {})
    assert parse_command("/capture ide local first") == (
        "os_capture",
        {"content": "ide local first"},
    )
    assert parse_command("/triage 12 task") == (
        "os_triage",
        {"capture_id": 12, "target": "task"},
    )


def test_os_kernel_tools_are_in_central_registry():
    names = set(get_tool_names())
    expected = {"os_capture", "os_inbox", "os_triage", "os_today"}
    assert expected <= names
    assert expected <= set(get_tool_groups()["os_kernel"])


def test_mcp_adapter_hides_os_capture_identity():
    callable_tool = langchain_tool_as_mcp_callable(
        os_capture,
        MCPPrincipal(
            sender_id="owner",
            sender_name="Owner",
            chat_id="owner-chat",
        ),
    )
    assert "chat_id" not in callable_tool.__signature__.parameters
