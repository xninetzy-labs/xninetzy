from __future__ import annotations

import asyncio
import json
import time
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

from xninetzy.ecosystem.command_router import (
    parse_captcha_reply,
    parse_command,
)
from xninetzy.os.memory.chat_store import ChatStore
from xninetzy.os.ai_preferences import resolve_user_profile
from xninetzy.schemas.chat import ChatRequest, ChatResponse
from xninetzy.interfaces.api.deps.auth import require_api_key
from xninetzy.interfaces.api.chat_events import bind_chat_event_queue, emit_chat_event
from xninetzy.interfaces.api.owner_policy import (
    authorize_owner,
    owner_denied_message,
)
from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"], dependencies=[Depends(require_api_key)])
CHAT_STREAM_HEARTBEAT_SECONDS = 15.0


def _has_media(metadata: dict | None) -> bool:
    data = metadata or {}
    media = data.get("media") or {}
    quoted = data.get("quotedMedia") or {}
    return bool(media.get("hasMedia") or quoted.get("hasMedia"))


async def _prepare_media_metadata(request: ChatRequest) -> dict:
    metadata = dict(request.metadata or {})
    if not _has_media(metadata):
        return metadata
    try:
        from xninetzy.interfaces.media.media_tools import build_media_prompt_context

        context = await build_media_prompt_context(request.chat_id, metadata)
    except Exception as exc:
        context = f"\n[Media Extraction Error]\nError internal: {exc}\n"
    if context:
        metadata["_media_prompt_context"] = context
    return metadata


def _format_direct_tool_result(tool_name: str, result: object) -> str:
    if tool_name == "tool_catalog" and isinstance(result, list):
        lines = [f"Xninetzy tool catalog · {len(result)} tools"]
        for item in result:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "unknown")
            pack = str(
                getattr(item.get("feature_pack"), "value", item.get("feature_pack") or "core")
            )
            risk = str(
                getattr(item.get("risk"), "value", item.get("risk") or "read")
            )
            description = str(item.get("description") or "").strip()
            lines.append(f"- {name} · {pack} · {risk}\n  {description}")
        return "\n".join(lines)
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False, default=str, indent=2)


async def _invoke_tool_directly(
    tool_name: str, kwargs: dict, request: ChatRequest
) -> str:
    """Invoke a single MCP tool directly.

    The pivot to MCP-only removed the LangGraph agent loop; HTTP clients
    (Codex, Claude Code, OpenCode) now route requests straight through
    the canonical MCP tool registry.
    """
    from xninetzy.tools.registry import get_all_tools

    if tool_name == "__portal_grade_token_submit":
        from xninetzy.os.academic.mahasiswa_portal.tools import (
            submit_grade_token,
        )

        return await submit_grade_token(
            challenge_id=str(kwargs.get("challenge_id") or ""),
            token=str(kwargs.get("token") or ""),
            sender_id=request.sender_id,
            sender_name=request.sender_name,
        )

    tools = {t.name: t for t in get_all_tools()}
    tool = tools.get(tool_name)
    if not tool:
        return f"Command tidak dikenali: `{tool_name}`"
    try:
        kwargs.setdefault("chat_id", request.chat_id)
        kwargs.setdefault("sender_id", request.sender_id)
        kwargs.setdefault("sender_name", request.sender_name)
        kwargs.setdefault("chat_type", request.chat_type)
        kwargs.setdefault("metadata", request.metadata)
        timeout_seconds = (
            get_settings().XNINETZY_DEEP_RESEARCH_TIMEOUT_SECONDS
            if tool_name == "deep_research_topic"
            else get_settings().XNINETZY_TOOL_TIMEOUT_SECONDS
        )
        async with asyncio.timeout(timeout_seconds):
            result = await tool.ainvoke(kwargs)
        return _format_direct_tool_result(tool_name, result)
    except Exception as e:
        return f"Error menjalankan command: {e}"


def _lightning_episode_start(request: ChatRequest) -> tuple[str | None, float]:
    started = time.perf_counter()
    if not get_settings().LIGHTNING_ENABLED:
        return None, started
    try:
        from xninetzy.os.lightning.rl import start_episode

        episode = start_episode(
            owner_scope=request.sender_id or request.chat_id,
            interface=str((request.metadata or {}).get("source", "api")),
            chat_id=request.chat_id,
            message_id=(request.metadata or {}).get("messageId"),
            task_type="chat",
            context={
                "domain": "chat",
                "intent": "request",
                "modality": "text",
                "risk_class": "read",
            },
            state={"message_length": len(request.message or "")},
            idempotency_key=(request.metadata or {}).get("messageId"),
        )
        return episode["episode_id"], started
    except Exception:
        return None, started


def _lightning_episode_finish(
    episode_id: str | None,
    request: ChatRequest,
    *,
    route: str,
    status: str,
    response: str,
    started: float,
    error_type: str | None = None,
) -> None:
    if not episode_id:
        return
    try:
        from xninetzy.os.lightning.rl import (
            finish_episode,
            record_action,
            record_outcome,
        )

        owner_scope = request.sender_id or request.chat_id
        record_action(
            episode_id=episode_id,
            owner_scope=owner_scope,
            action_type="route",
            action_name=route or "unknown",
            output_data={"response_length": len(response or "")},
            status="ok" if status in {"ok", "completed"} else "error",
            error_type=error_type,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        record_outcome(
            episode_id=episode_id,
            owner_scope=owner_scope,
            success=status in {"ok", "completed", "failover"},
            outcome_code=route or status,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
    except Exception:
        try:
            finish_episode(
                episode_id=episode_id,
                owner_scope=request.sender_id or request.chat_id,
                status="failed",
                outcome_code=error_type or "lightning_recording_error",
            )
        except Exception:
            pass


async def _maybe_run_workflow(request: ChatRequest) -> str | None:
    """Run the multi-action workflow engine for compound requests, else None.

    Best-effort: any failure falls through to the direct-tool path so a
    workflow bug can never take down regular chat.
    """
    if _has_media(request.metadata):
        return None
    try:
        from xninetzy.core.config import get_settings

        if not get_settings().WORKFLOW_ENABLED:
            return None
        from xninetzy.workflow.plan import is_multi_action_request

        if not is_multi_action_request(request.message):
            return None
        from xninetzy.workflow.executor import run_workflow

        return await run_workflow(
            request.chat_id,
            request.message,
            context={"chat_type": request.chat_type},
        )
    except Exception:
        return None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """HTTP MCP bridge endpoint.

    Receives a chat request, parses slash commands and CAPTCHA replies,
    routes compound requests through the workflow engine, and otherwise
    dispatches to a single canonical MCP tool. Direct conversational
    agent loops have been removed in the MCP-only pivot; clients that
    need multi-turn reasoning should call MCP tools directly.
    """
    owner = (
        authorize_owner(
            request.sender_id,
            local_client=False,
        )
        if (request.metadata or {}).get("channel") == "whatsapp"
        else None
    )
    if owner is not None and not owner.allowed:
        return ChatResponse(reply=owner_denied_message(owner.reason))

    episode_id, episode_started = _lightning_episode_start(request)
    emit_chat_event("phase", "Routing request")

    tool_name, kwargs = parse_command(request.message)
    if not tool_name:
        tool_name, kwargs = parse_captcha_reply(
            request.message, request.metadata or {}
        )
    if tool_name:
        emit_chat_event("activity", "Executing direct command")
        reply = await _invoke_tool_directly(tool_name, kwargs, request)
        emit_chat_event("activity", "Direct command completed", "completed")
        _lightning_episode_finish(
            episode_id,
            request,
            route=tool_name,
            status="completed" if not reply.startswith("Error") else "failed",
            response=reply,
            started=episode_started,
            error_type="direct_tool_error" if reply.startswith("Error") else None,
        )
        return ChatResponse(reply=reply)

    emit_chat_event("phase", "Checking workflow")
    workflow_reply = await _maybe_run_workflow(request)
    if workflow_reply is not None:
        _lightning_episode_finish(
            episode_id,
            request,
            route="workflow",
            status="completed",
            response=workflow_reply,
            started=episode_started,
        )
        return ChatResponse(reply=workflow_reply)

    # No slash command, no workflow: in MCP-only mode we acknowledge and
    # recommend direct tool invocation rather than running a hidden agent
    # loop on the server side.
    settings = get_settings()
    user_key = request.sender_id or request.chat_id
    store = ChatStore()
    history = store.get_recent(request.chat_id)
    fallback_reply = (
        "Xninetzy MCP tidak lagi menjalankan agent loop server-side. "
        "Gunakan slash command (mis. /today, /helper, /tasks, /hebat) atau "
        "panggil MCP tool langsung dari klien MCP-aware (Codex/Claude Code/OpenCode)."
    )
    fallback_messages = [
        HumanMessage(content=request.message),
        AIMessage(content=fallback_reply),
    ]
    store.save_messages(request.chat_id, fallback_messages)
    _lightning_episode_finish(
        episode_id,
        request,
        route="mcp_only_acknowledgement",
        status="completed",
        response=fallback_reply,
        started=episode_started,
    )
    _log_trace(
        request,
        {"response": fallback_reply, "route": "mcp_only_acknowledgement"},
        fallback_messages,
        status="ok",
    )
    if not settings.LIGHTNING_ENABLED:
        # Stay quiet — placeholder for future hookups.
        pass
    return ChatResponse(reply=fallback_reply)


def _sse(event_type: str, payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False)
    return f"event: {event_type}\ndata: {encoded}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    metadata = dict(request.metadata or {})
    request_id = str(metadata.get("clientRequestId") or uuid.uuid4().hex)[:128]

    async def events():
        queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()
        with bind_chat_event_queue(queue):
            task = asyncio.create_task(chat(request))
            last_heartbeat = time.perf_counter()
            try:
                yield _sse("run_started", {"requestId": request_id})
                while not task.done() or not queue.empty():
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=0.1)
                    except asyncio.TimeoutError:
                        now = time.perf_counter()
                        if now - last_heartbeat >= CHAT_STREAM_HEARTBEAT_SECONDS:
                            yield _sse("heartbeat", {})
                            last_heartbeat = now
                        continue
                    event_type = event.pop("type", "activity")
                    yield _sse(event_type, event)
                response = await task
                yield _sse(
                    "phase",
                    {"label": "Rendering response", "status": "active"},
                )
                for offset in range(0, len(response.reply), 96):
                    payload = {"delta": response.reply[offset : offset + 96]}
                    yield _sse("delta", payload)
                    await asyncio.sleep(0.015)
                yield _sse(
                    "phase", {"label": "Response completed", "status": "completed"}
                )
                yield _sse("done", {})
            except asyncio.CancelledError:
                task.cancel()
                raise
            except Exception:
                logger.exception("Chat stream failed")
                yield _sse("phase", {"label": "Request failed", "status": "failed"})
                yield _sse("done", {})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _log_trace(
    request: ChatRequest,
    result: dict,
    new_messages: list,
    status: str = "ok",
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    """Best-effort Lightning trace logging — must never break the chat flow."""
    try:
        from xninetzy.os.lightning.store import log_trace

        tools_used: list[str] = []
        for m in new_messages or []:
            for call in getattr(m, "tool_calls", None) or []:
                name = (
                    call.get("name")
                    if isinstance(call, dict)
                    else getattr(call, "name", None)
                )
                if name:
                    tools_used.append(name)
        log_trace(
            user_id=request.sender_id,
            chat_id=request.chat_id,
            message_id=(request.metadata or {}).get("messageId"),
            input_text=request.message,
            response_text=result.get("response", ""),
            intent=result.get("route"),
            tools_used=tools_used,
            status=status,
            error_type=error_type,
            error_message=error_message,
        )
    except Exception:
        pass
