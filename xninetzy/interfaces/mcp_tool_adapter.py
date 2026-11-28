from __future__ import annotations

import inspect
import asyncio
import json
import time
import logging
import hashlib
import uuid
import weakref
from dataclasses import dataclass
from typing import Any, Callable, Iterable, get_type_hints

from langchain_core.tools import BaseTool
from mcp.server.fastmcp import FastMCP
from pydantic_core import PydanticUndefined
from pydantic import TypeAdapter, ValidationError
from mcp.server.fastmcp.exceptions import ToolError

from xninetzy.core.config import Settings, get_settings
from xninetzy.core.security import sanitize_tool_output, strip_trusted_context
from xninetzy.observability.perf import measure

_TOOL_SLOTS = weakref.WeakKeyDictionary()


def _execution_slots(settings):
    loop = asyncio.get_running_loop()
    reference = _TOOL_SLOTS.get(loop)
    slots = reference() if reference else None
    if slots is None:
        slots = asyncio.Semaphore(max(1, min(int(settings.AI_CPU_THREADS), 8)))
        _TOOL_SLOTS[loop] = weakref.ref(slots)
    return slots


async def _bounded_invoke(tool, arguments, timeout, settings):
    """Keep timed-out workers counted until they actually finish.

    Cancellation cannot kill an arbitrary sync thread. Shield its task and
    retain the slot, preventing repeated deadlines from spawning more workers.
    """
    slots = _execution_slots(settings)
    async with asyncio.timeout(timeout):
        await slots.acquire()
        try:
            task = asyncio.create_task(tool.ainvoke(arguments))
        except BaseException:
            slots.release()
            raise

        def finished(done):
            slots.release()
            if not done.cancelled():
                done.exception()  # consume late errors without logging private messages

        task.add_done_callback(finished)
        return await asyncio.shield(task)


def _optional_record(function, **kwargs):
    """Observability must not turn a committed operation into a failed call."""
    try:
        return function(**kwargs)
    except Exception as exc:
        logging.getLogger(__name__).warning("Optional MCP telemetry failed (%s)", type(exc).__name__)
        return None


def _policy_denied(tool_name: str, code: str, owner: str) -> None:
    """Persist a bounded denial event without unvalidated input or credentials."""
    try:
        from xninetzy.context.policy.audit import record_audit_start, complete_audit_entry
        entry = record_audit_start(
            request_id="mcp-denied:" + uuid.uuid4().hex, provider_id="local:xninetzy",
            capability=tool_name, side_effect_class="irreversible", idempotency_key=None,
            approval_id=None, args_hash="", args_bytes=0,
            context_key=hashlib.sha256(owner.encode()).hexdigest(),
        )
        complete_audit_entry(audit_id=entry.id, outcome="blocked", error=code)
    except Exception as exc:
        logging.getLogger(__name__).warning("MCP denial audit unavailable (%s)", type(exc).__name__)


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
    if tool_name.startswith(("memory_", "lightning_", "improvement_", "graph_", "observability_", "harness_", "repo_", "web_analysis_")):
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
    except Exception as exc:
        try:
            from xninetzy.observability.trace import emit

            emit(
                "mcp_auto_memory_record_error",
                tool_name=tool_name,
                error_type=type(exc).__name__,
                error=type(exc).__name__,
            )
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
    if tool_name.startswith(("graph_", "lightning_", "improvement_", "observability_", "memory_session_")):
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
    except Exception as exc:
        try:
            from xninetzy.observability.trace import emit

            emit(
                "mcp_auto_graph_record_error",
                tool_name=tool_name,
                error_type=type(exc).__name__,
                error=type(exc).__name__,
            )
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
    except Exception as impro_exc:
        try:
            from xninetzy.observability.trace import emit

            emit(
                "mcp_auto_improve_record_error",
                tool_name=tool_name,
                error_type=type(impro_exc).__name__,
                error=type(impro_exc).__name__,
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


def _resolve_tool_entry(
    tool: Any,
    principal: MCPPrincipal | None,
) -> tuple[str, str, Callable[..., Any]]:
    if isinstance(tool, BaseTool):
        name = tool.name
        description = tool.description or ""
        return name, description, langchain_tool_as_mcp_callable(tool, principal)
    if callable(tool):
        name = getattr(tool, "__name__", "") or ""
        description = (getattr(tool, "__doc__", "") or "").strip()

        # Use the same validation, identity and policy boundary for callable
        # extensions. A plain callable must not become an unguarded backdoor.
        from langchain_core.tools import StructuredTool
        adapted = StructuredTool.from_function(
            func=None if inspect.iscoroutinefunction(tool) else tool,
            coroutine=tool if inspect.iscoroutinefunction(tool) else None,
            name=name, description=description or name,
        )
        return name, description, langchain_tool_as_mcp_callable(adapted, principal)
    raise TypeError(f"Unsupported tool entry: {type(tool).__name__}")


def _parameter_default(field: Any) -> Any:
    if field.default is PydanticUndefined:
        return inspect.Parameter.empty
    return field.default


def langchain_tool_as_mcp_callable(
    tool: BaseTool, principal: MCPPrincipal | None = None
) -> Any:
    """Adapt a tool and inject authoritative identity context server-side."""

    trusted_context = (principal or mcp_principal()).as_tool_context()
    from xninetzy.tools.manifest import manifest_for
    manifest = manifest_for(tool.name)
    output_validator = tool.get_output_schema()
    # StructuredTool's generic output schema is often RootModel[Any]. Use the
    # owned callable's declared return type when LangChain loses that contract.
    function = getattr(tool, "func", None) or getattr(tool, "coroutine", None)
    if function is not None:
        try:
            return_type = get_type_hints(function).get("return", Any)
            if return_type is not Any:
                output_validator = TypeAdapter(return_type)
        except (NameError, TypeError, ValueError):
            pass

    async def invoke(**kwargs: Any) -> Any:
        try:
            settings = get_settings()
        except Exception:
            raise ToolError("[SERVER_ERROR] tool_configuration_unavailable") from None
        if not manifest.policy_known:
            _policy_denied(tool.name, "unknown_tool_policy", trusted_context["sender_id"])
            raise ToolError("[POLICY_HELD] unknown_tool_policy")
        if settings.ACTION_POLICY_KILL_SWITCH:
            _policy_denied(tool.name, "policy_kill_switch", trusted_context["sender_id"])
            raise ToolError("[POLICY_HELD] policy_kill_switch")
        if manifest.requires_approval:
            _policy_denied(tool.name, "approval_channel_unverified", trusted_context["sender_id"])
            raise ToolError("[POLICY_HELD] approval_channel_unverified: consequential execution is unavailable without independently authenticated approval")
        from xninetzy.os.policy.action_policy import _overrides, ActionMode
        override = _overrides().get(tool.name)
        if override is ActionMode.MANUAL:
            _policy_denied(tool.name, "policy_manual", trusted_context["sender_id"])
            raise ToolError("[POLICY_HELD] policy_manual")
        if override is ActionMode.APPROVAL:
            _policy_denied(tool.name, "approval_channel_unverified", trusted_context["sender_id"])
            raise ToolError("[POLICY_HELD] approval_channel_unverified")
        if manifest.requires_idempotency:
            from xninetzy.os.policy.action_policy import evaluate_action
            decision = evaluate_action(tool.name)
            if not decision.allowed or decision.requires_approval:
                code = "policy_manual" if not decision.allowed else "approval_channel_unverified"
                _policy_denied(tool.name, code, trusted_context["sender_id"])
                raise ToolError(f"[POLICY_HELD] {code}")
        if not trusted_context["sender_id"]:
            raise ToolError("[POLICY_HELD] principal_required")
        arguments = dict(kwargs)
        gateway_key = arguments.get("idempotency_key", "")
        if manifest.requires_idempotency and (not isinstance(gateway_key, str) or not gateway_key.strip()):
            raise ToolError("[INVALID_INPUT] idempotency_key_required")
        if "idempotency_key" not in tool.args_schema.model_fields:
            arguments.pop("idempotency_key", None)
        for name, value in trusted_context.items():
            if name in tool.args_schema.model_fields:
                arguments[name] = value
        # Preserve the declared single-owner storage namespace while preventing
        # callers from selecting a different owner through body fields.
        for field in ("owner", "owner_id", "user_id"):
            if field in tool.args_schema.model_fields:
                default = tool.args_schema.model_fields[field].default
                arguments[field] = default if isinstance(default, str) and default else trusted_context["sender_id"]
        if len(json.dumps(arguments, default=str).encode()) > 65536:
            raise ToolError("[INVALID_INPUT] tool_input_limit_exceeded")
        if set(arguments) - set(tool.args_schema.model_fields):
            raise ToolError("[INVALID_INPUT] unexpected_tool_arguments")
        try:
            validated = tool.args_schema.model_validate(arguments)
            normalized = validated.model_dump(mode="json")
        except (ValidationError, ValueError, TypeError):
            raise ToolError("[INVALID_INPUT] tool_input_validation_failed") from None
        arguments = validated.model_dump()
        episode_id = None
        handler_started = False
        started = time.perf_counter()
        risk_class = manifest.risk.value
        try:
            record_episode = settings.LIGHTNING_ENABLED and not tool.name.startswith("lightning_")
            if record_episode:
                from xninetzy.os.lightning.rl import start_episode
                if risk_class == "read":
                    rate = settings.LIGHTNING_READ_SAMPLE_RATE
                    if rate <= 0:
                        record_episode = False
                    elif rate < 1.0:
                        import random
                        record_episode = random.random() < rate
            if record_episode:
                episode = _optional_record(start_episode,
                    owner_scope=trusted_context["sender_id"],
                    interface="mcp",
                    chat_id=trusted_context["chat_id"],
                    task_type=tool.name,
                    context={
                        "domain": "mcp",
                        "intent": tool.name,
                        "risk_class": risk_class,
                    },
                    strategy_id=f"mcp:{tool.name}",
                    idempotency_key=(
                        (arguments.get("metadata") or {}).get("idempotency_key")
                        if isinstance(arguments.get("metadata"), dict)
                        else None
                    ),
                )
                episode_id = episode["episode_id"] if episode else None
            with measure(f"mcp_tool:{tool.name}"):
                timeout = float(settings.XNINETZY_TOOL_TIMEOUT_SECONDS)
                if timeout <= 0 or timeout > 900:
                    raise ToolError("[INVALID_INPUT] invalid_tool_timeout")

                async def execute():
                    nonlocal handler_started
                    handler_started = True
                    try:
                        value = await _bounded_invoke(tool, arguments, timeout, settings)
                    except TimeoutError:
                        raise ToolError("[SERVER_ERROR] tool_timeout: mutation outcome may require reconciliation") from None
                    try:
                        if isinstance(output_validator, TypeAdapter):
                            value = output_validator.validate_python(value)
                        else:
                            output = output_validator.model_validate(value)
                            if getattr(output, "__pydantic_root_model__", False):
                                value = output.root
                    except ValidationError:
                        raise ToolError("[SERVER_ERROR] tool_output_validation_failed: verify operation state before retrying") from None
                    if hasattr(value, "model_dump"):
                        value = value.model_dump(mode="json")
                    value = strip_trusted_context(sanitize_tool_output(value))
                    encoded = json.dumps(value, default=str, ensure_ascii=False).encode()
                    if len(encoded) > manifest.max_output_bytes:
                        return "[SERVER_ERROR] output_limit_exceeded: operation returned; narrow the result query before verification"
                    if manifest.requires_idempotency:
                        safe_arguments = sanitize_tool_output(arguments)
                        context = {"tool_name": tool.name, "arguments": safe_arguments,
                                   "owner": trusted_context["sender_id"]}
                        _optional_record(_auto_memory_record, **context, result=value)
                        _optional_record(_auto_graph_record, **context, result=value, risk_class=risk_class)
                        _optional_record(_auto_improve_record, **context, exc=None)
                    return value

                if manifest.requires_idempotency:
                    from xninetzy.db.idempotency import idempotent_ainvoke
                    payload = {k: v for k, v in normalized.items() if k not in TRUSTED_CONTEXT_FIELDS and k != "idempotency_key"}
                    result = await idempotent_ainvoke(
                        json.dumps([trusted_context["sender_id"], tool.name]), gateway_key.strip(), payload, execute,
                    )
                else:
                    result = await execute()
            result = sanitize_tool_output(result)
            result = strip_trusted_context(result)
            if episode_id:
                from xninetzy.os.lightning.rl import record_action, record_outcome

                continuity = tool.name.startswith("memory_session_") and isinstance(result, dict)
                output_data = {"result_type": type(result).__name__}
                if continuity:
                    output_data.update({key: result[key] for key in ("status", "context_bytes", "graph_status", "truncated")
                                        if key in result})
                success = not continuity or result.get("status") in {"saved", "resumed"}
                _optional_record(record_action,
                    episode_id=episode_id,
                    owner_scope=trusted_context["sender_id"],
                    action_type="mcp_tool",
                    action_name=tool.name,
                    input_data={} if continuity else arguments,
                    output_data=output_data,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
                _optional_record(record_outcome,
                    episode_id=episode_id,
                    owner_scope=trusted_context["sender_id"],
                    success=success,
                    outcome_code=str(result["status"]) if continuity else tool.name,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
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
                        input_data={} if tool.name.startswith("memory_session_") else arguments,
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
            if handler_started and manifest.requires_idempotency:
                _optional_record(_auto_improve_record, tool_name=tool.name,
                                 arguments=sanitize_tool_output(arguments),
                                 exc=RuntimeError(type(exc).__name__), owner=trusted_context["sender_id"])
            if isinstance(exc, ToolError):
                raise
            from xninetzy.db.idempotency import IdempotencyPendingError
            if isinstance(exc, IdempotencyPendingError):
                raise ToolError("[POLICY_HELD] idempotency_pending: reconcile previous outcome") from None
            if isinstance(exc, ValueError) and str(exc) == "idempotency_payload_mismatch":
                raise ToolError("[POLICY_HELD] idempotency_payload_mismatch") from None
            raise ToolError(f"[SERVER_ERROR] tool_execution_failed ({type(exc).__name__})") from None

    parameters = [
        inspect.Parameter(
            name,
            inspect.Parameter.KEYWORD_ONLY,
            default=_parameter_default(field),
            annotation=field.annotation or Any,
        )
        for name, field in tool.args_schema.model_fields.items()
        if name not in TRUSTED_CONTEXT_FIELDS and name not in {"owner", "owner_id", "user_id"}
    ]
    if manifest.requires_idempotency and "idempotency_key" not in tool.args_schema.model_fields:
        parameters.append(inspect.Parameter("idempotency_key", inspect.Parameter.KEYWORD_ONLY, default="", annotation=str))
    invoke.__name__ = tool.name
    invoke.__doc__ = tool.description or ""
    invoke.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    return invoke


def expose_xninetzy_tools(
    server: FastMCP,
    tools: Iterable[Any] | None = None,
    principal: MCPPrincipal | None = None,
) -> tuple[str, ...]:
    if tools is None:
        from xninetzy.tools.registry import get_all_tools

        tools = get_all_tools()

    exposed: list[str] = []
    for tool in tools:
        name, description, fn = _resolve_tool_entry(tool, principal)
        if not name:
            continue
        if server._tool_manager.get_tool(name) is not None:
            server._tool_manager.remove_tool(name)
        from mcp.types import ToolAnnotations
        from xninetzy.tools.tool_meta import meta_for
        metadata = meta_for(name)
        server.add_tool(fn, name=name, description=description,
                        annotations=ToolAnnotations(**metadata["annotations"]),
                        meta={"xninetzy": metadata})
        exposed.append(name)
    return tuple(sorted(exposed))
