from __future__ import annotations

import inspect
import json
import time
from dataclasses import dataclass
from typing import Any, Iterable

from langchain_core.tools import BaseTool
from mcp.server.fastmcp import FastMCP
from pydantic_core import PydanticUndefined

from xninetzy.core.config import Settings, get_settings
from xninetzy.core.security import sanitize_tool_output


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


def _auto_memory_record(tool_name: str, arguments: dict[str, Any], result: Any, owner: str) -> None:
    settings = get_settings()
    if not settings.AUTO_MEMORY_ENABLED:
        return
    if settings.AUTO_MEMORY_SAMPLE_RATE <= 0:
        return
    if tool_name.startswith(("memory_", "lightning_", "improvement_", "graph_", "observability_")):
        return
    try:
        import random

        if random.random() > settings.AUTO_MEMORY_SAMPLE_RATE:
            return
        arg_preview = json.dumps(arguments, default=str, ensure_ascii=False)[:400]
        result_preview = (
            result if isinstance(result, str) else json.dumps(result, default=str, ensure_ascii=False)
        )[:600]
        content = f"mcp:{tool_name} args={arg_preview} out={result_preview}"
        if len(content) < settings.AUTO_MEMORY_MIN_CONTENT_CHARS:
            return
        from xninetzy.os.memory.memory_store import add_memory

        add_memory(user_id=owner, content=content, source="mcp_auto")
    except Exception:
        pass


def _auto_graph_record(
    tool_name: str,
    arguments: dict[str, Any],
    result: Any,
    risk_class: str,
    owner: str,
) -> None:
    settings = get_settings()
    if not settings.AUTO_GRAPH_ENABLED:
        return
    if settings.AUTO_GRAPH_WRITE_ONLY and risk_class not in ("write", "final"):
        return
    if tool_name.startswith(("graph_", "lightning_", "improvement_", "observability_")):
        return
    try:
        from xninetzy.os.graph.graph_store import add_edge, add_node, search_nodes

        result_text = (
            result if isinstance(result, str) else json.dumps(result, default=str, ensure_ascii=False)
        )[:400]
        topic = f"mcp:{tool_name}"
        existing = search_nodes(topic, limit=1)
        if existing:
            node_id = int(existing[0]["id"])
        else:
            node_id = add_node(
                node_type="mcp_tool_invocation",
                title=topic,
                content=f"Auto-recorded MCP tool calls for {tool_name}",
                metadata={"owner": owner, "risk_class": risk_class},
            )
        semantic_type = _semantic_node_type(tool_name) or "mcp_tool_artifact"
        artifact_id = add_node(
            node_type=semantic_type,
            title=f"{tool_name}@{int(time.time() * 1000)}",
            content=result_text,
            metadata={
                "tool": tool_name,
                "args_preview": json.dumps(arguments, default=str)[:200],
                "owner": owner,
                "semantic_node_type": semantic_type,
            },
        )
        add_edge(node_id, artifact_id, "produced_artifact", {"semantic_type": semantic_type})
        related = search_nodes(tool_name.split("_")[0], limit=3)
        for rel in related:
            try:
                rel_id = int(rel["id"])
                if rel_id == node_id or rel_id == artifact_id:
                    continue
                if rel.get("node_type") in (semantic_type, "mcp_tool_invocation", "mcp_tool_artifact"):
                    continue
                add_edge(artifact_id, rel_id, "mentions_topic")
            except Exception:
                continue
    except Exception:
        pass


def _auto_improve_record(
    tool_name: str,
    arguments: dict[str, Any],
    exc: BaseException | None,
    owner: str,
) -> None:
    settings = get_settings()
    if not settings.AUTO_IMPROVE_ENABLED:
        return
    if settings.AUTO_IMPROVE_ERROR_ONLY and exc is None:
        return
    if tool_name.startswith(("improvement_", "lightning_", "memory_", "graph_", "observability_")):
        return
    try:
        from xninetzy.tools.ecosystem.improvement_tools import improvement_detect

        signal = (
            f"tool_error:{type(exc).__name__}:{tool_name}"
            if exc is not None
            else f"tool_success_pattern:{tool_name}"
        )
        improvement_detect(
            scope="tool",
            signal=signal,
            target_id=tool_name,
            notes=str(exc)[:500] if exc else "",
            owner=owner,
            chat_id=owner,
            sender_id=owner,
        )
    except Exception:
        pass


_DOMAIN_NODE_TYPE: dict[str, str] = {
    "career": "job_application",
    "research": "research_paper",
    "deep_research": "research_topic",
    "web": "web_evidence",
    "hebat": "course",
    "portal": "academic_record",
    "learning": "learning_concept",
    "goal": "goal",
    "task": "task",
    "habit": "habit",
    "money": "transaction",
    "workout": "workout",
    "memory": "memory_note",
    "knowledge": "knowledge_chunk",
    "obsidian": "obsidian_note",
    "document": "document",
    "image": "image",
    "youtube": "media",
    "media": "media",
    "repo": "code_symbol",
    "security": "security_finding",
    "rule": "rule",
    "rules": "rule",
    "graph": "graph_artifact",
    "skill": "skill",
    "improvement": "improvement_proposal",
    "harness": "plan_step",
    "lightning": "lightning_event",
    "qa": "qa_submission",
    "uacc": "uacc_action",
}


def _semantic_node_type(tool_name: str) -> str | None:
    for prefix, node_type in _DOMAIN_NODE_TYPE.items():
        if tool_name.startswith(f"{prefix}_"):
            return node_type
    return None


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
        risk_class = "write"
        try:
            settings = get_settings()
            if settings.LIGHTNING_ENABLED and not tool.name.startswith("lightning_episode_"):
                from xninetzy.os.lightning.rl import start_episode
                from xninetzy.tools.manifest import manifest_for

                manifest = manifest_for(tool.name)
                risk_class = manifest.risk.value
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
            result = sanitize_tool_output(result)
            if episode_id:
                from xninetzy.os.lightning.rl import record_action, record_outcome

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
            _auto_memory_record(tool.name, arguments, result, trusted_context["sender_id"])
            _auto_graph_record(tool.name, arguments, result, risk_class, trusted_context["sender_id"])
            _auto_improve_record(tool.name, arguments, None, trusted_context["sender_id"])
            return result
        except Exception as exc:
            if episode_id:
                try:
                    from xninetzy.os.lightning.rl import record_action, record_outcome

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
            _auto_improve_record(tool.name, arguments, exc, trusted_context["sender_id"])
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
        from xninetzy.tools.registry import get_all_tools

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
