from __future__ import annotations

from langchain_core.tools import BaseTool, tool


@tool(description="Detect whether an external Playwright MCP server is reachable.")
def playwright_detect_tool() -> dict:
    return {"detected": False, "mode": "stub"}


@tool(description="Install instructions for the external Playwright MCP server.")
def playwright_install_tool() -> dict:
    return {"status": "not-installed", "instructions": "Run `xninetzy_external_mcp install playwright`."}


@tool(description="Enable the external Playwright MCP server.")
def playwright_enable_tool() -> dict:
    return {"status": "disabled"}


@tool(description="Bring the external Playwright MCP server up.")
def playwright_up_tool() -> dict:
    return {"status": "down"}


@tool(description="Check external Playwright MCP server status.")
def playwright_status_tool() -> dict:
    return {"status": "stub"}


@tool(description="Attach to an existing Playwright MCP session.")
def playwright_attach_session_tool() -> dict:
    return {"status": "no-session"}


@tool(description="Disable the external Playwright MCP server.")
def playwright_disable_tool() -> dict:
    return {"status": "disabled"}


@tool(description="List available external MCP servers.")
def external_mcp_list_tool() -> dict:
    return {"external": []}


@tool(description="Shut down the external MCP bridge.")
def external_mcp_shutdown_tool() -> dict:
    return {"status": "shutdown"}


EXTERNAL_MCP_TOOLS: list[BaseTool] = [
    playwright_detect_tool,
    playwright_install_tool,
    playwright_enable_tool,
    playwright_up_tool,
    playwright_status_tool,
    playwright_attach_session_tool,
    playwright_disable_tool,
    external_mcp_list_tool,
    external_mcp_shutdown_tool,
]


__all__ = ["EXTERNAL_MCP_TOOLS"]
