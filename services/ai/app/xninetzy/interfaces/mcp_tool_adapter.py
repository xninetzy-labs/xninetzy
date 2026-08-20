from __future__ import annotations

import inspect
import time
from dataclasses import dataclass
from typing import Any, Iterable

from langchain_core.tools import BaseTool
from mcp.server.fastmcp import FastMCP
from pydantic_core import PydanticUndefined

from app.xninetzy.core.config import Settings, get_settings


TRUSTED_CONTEXT_FIELDS = frozenset(
    {"chat_id", "sender_id", "sender_name", "chat_type", "group_name", "metadata"}
)


@dataclass(frozen=True)
class MCPPrincipal:
    sender_id: str
    sender_name: str
    chat_id: str
    chat_type: str = "private"
    group_name: str = ""

    def as_tool_context(self) -> dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "chat_id": self.chat_id,
            "chat_type": self.chat_type,
            "group_name": self.group_name,
            "metadata": {"source": "mcp", "principal": "local-owner"},
        }


def mcp_principal(settings: Settings | None = None) -> MCPPrincipal:
    """Resolve the trusted local owner represented by stdio MCP clients."""
    current = settings or get_settings()
    sender_id = (
        current.MCP_PRINCIPAL_ID or current.OWNER_PHONE_NUMBER or current.ADMIN_JID
    ).strip()
    sender_name = (current.MCP_PRINCIPAL_NAME or current.OWNER_ALIAS or sender_id).strip() or "local-owner"
    stable_owner = sender_id or "mcp:local-owner"
    chat_id = (current.MCP_DEFAULT_CHAT_ID or sender_id or stable_owner).strip()
    return MCPPrincipal(
        sender_id=stable_owner,
        sender_name=sender_name or "Local owner",
        chat_id=chat_id,
    )


def _parameter_default(field: Any) -> Any:
    if field.default is PydanticUndefined:
        return inspect.Parameter.empty
    return field.default


def langchain_tool_as_mcp_callable(
    tool: BaseTool, principal: MCPPrincipal | None = None
) -> Any:
    """Adapt a tool and inject authoritative identity context server-side."""

    trusted_context = (principal or mcp_principal()).as_tool_context()

    async def invoke(**kwargs: Any) -> Any:
        arguments = dict(kwargs)
        for name, value in trusted_context.items():
            if name in tool.args_schema.model_fields:
                arguments[name] = value
        episode_id = None
        started = time.perf_counter()
        try:
            settings = get_settings()
            if settings.LIGHTNING_ENABLED and not tool.name.startswith("lightning_episode_"):
                from app.xninetzy.os.lightning.rl import start_episode
                from app.xninetzy.tools.manifest import manifest_for

                manifest = manifest_for(tool.name)
                episode = start_episode(
                    owner_scope=trusted_context["sender_id"],
                    interface="mcp",
                    chat_id=trusted_context["chat_id"],
                    task_type=tool.name,
                    context={
                        "domain": "mcp",
                        "intent": tool.name,
                        "risk_class": manifest.risk.value,
                    },
                    strategy_id=f"mcp:{tool.name}",
                    idempotency_key=(
                        (arguments.get("metadata") or {}).get("idempotency_key")
                        if isinstance(arguments.get("metadata"), dict)
                        else None
                    ),
                )
                episode_id = episode["episode_id"]
            result = await tool.ainvoke(arguments)
            if episode_id:
                from app.xninetzy.os.lightning.rl import record_action, record_outcome

                record_action(
                    episode_id=episode_id,
                    owner_scope=trusted_context["sender_id"],
                    action_type="mcp_tool",
                    action_name=tool.name,
                    input_data=arguments,
                    output_data={"result_type": type(result).__name__},
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
                record_outcome(
                    episode_id=episode_id,
                    owner_scope=trusted_context["sender_id"],
                    success=True,
                    outcome_code=tool.name,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
            return result
        except Exception as exc:
            if episode_id:
                try:
                    from app.xninetzy.os.lightning.rl import record_action, record_outcome

                    record_action(
                        episode_id=episode_id,
                        owner_scope=trusted_context["sender_id"],
                        action_type="mcp_tool",
                        action_name=tool.name,
                        input_data=arguments,
                        status="error",
                        error_type=type(exc).__name__,
                        latency_ms=(time.perf_counter() - started) * 1000,
                    )
                    record_outcome(
                        episode_id=episode_id,
                        owner_scope=trusted_context["sender_id"],
                        success=False,
                        outcome_code=type(exc).__name__,
                        latency_ms=(time.perf_counter() - started) * 1000,
                    )
                except Exception:
                    pass
            raise

    parameters = [
        inspect.Parameter(
            name,
            inspect.Parameter.KEYWORD_ONLY,
            default=_parameter_default(field),
            annotation=field.annotation or Any,
        )
        for name, field in tool.args_schema.model_fields.items()
        if name not in TRUSTED_CONTEXT_FIELDS
    ]
    invoke.__name__ = tool.name
    invoke.__doc__ = tool.description or ""
    invoke.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    return invoke


def expose_xninetzy_tools(
    server: FastMCP,
    tools: Iterable[BaseTool] | None = None,
    principal: MCPPrincipal | None = None,
) -> tuple[str, ...]:
    """Expose every tool from the central Xninetzy registry through MCP."""

    if tools is None:
        from app.xninetzy.tools.registry import get_all_tools

        tools = get_all_tools()

    for tool in tools:
        if server._tool_manager.get_tool(tool.name) is not None:
            server._tool_manager.remove_tool(tool.name)
        server.add_tool(
            langchain_tool_as_mcp_callable(tool, principal),
            name=tool.name,
            description=tool.description or "",
        )
    return tuple(sorted(tool.name for tool in server._tool_manager.list_tools()))
