from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, HumanMessage

from app.xninetzy.agent.graph import get_compiled_graph
from app.xninetzy.ecosystem.command_router import parse_command
from app.xninetzy.os.memory.chat_store import ChatStore
from app.xninetzy.os.ai_preferences import resolve_user_profile
from app.xninetzy.schemas.chat import ChatRequest, ChatResponse
from app.xninetzy.interfaces.api.deps.auth import require_api_key
from app.xninetzy.interfaces.api.owner_policy import (
    authorize_owner,
    owner_denied_message,
)
from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"], dependencies=[Depends(require_api_key)])


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
        from app.xninetzy.interfaces.media.media_tools import build_media_prompt_context

        context = await build_media_prompt_context(request.chat_id, metadata)
    except Exception as exc:
        context = f"\n[Media Extraction Error]\nError internal: {exc}\n"
    if context:
        metadata["_media_prompt_context"] = context
    return metadata


async def _invoke_tool_directly(
    tool_name: str, kwargs: dict, request: ChatRequest
) -> str:
    """Invoke a single tool directly, bypassing LangGraph (for slash commands)."""
    from app.xninetzy.tools.registry import get_all_tools

    if tool_name == "__portal_grade_token_submit":
        from app.xninetzy.os.academic.mahasiswa_portal.tools import (
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
        result = await tool.ainvoke(kwargs)
        return str(result)
    except Exception as e:
        return f"Error menjalankan command: {e}"


def _lightning_episode_start(request: ChatRequest) -> tuple[str | None, float]:
    started = time.perf_counter()
    if not get_settings().LIGHTNING_ENABLED:
        return None, started
    try:
        from app.xninetzy.os.lightning.rl import start_episode

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
        from app.xninetzy.os.lightning.rl import (
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

    Best-effort: any failure falls through to the normal LangGraph flow so a
    workflow bug can never take down regular chat.
    """
    if _has_media(request.metadata):
        return None
    try:
        from app.xninetzy.core.config import get_settings

        if not get_settings().WORKFLOW_ENABLED:
            return None
        from app.xninetzy.workflow.plan import is_multi_action_request

        if not is_multi_action_request(request.message):
            return None
        from app.xninetzy.workflow.executor import run_workflow

        from_wa = bool(
            (request.metadata or {}).get("messageId")
        ) or request.chat_type in ("private", "group")
        return await run_workflow(
            request.chat_id,
            request.message,
            context={"chat_type": request.chat_type},
            from_whatsapp=from_wa,
        )
    except Exception:
        return None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    owner = authorize_owner(request.sender_id)
    if not owner.allowed:
        return ChatResponse(reply=owner_denied_message(owner.reason))

    episode_id, episode_started = _lightning_episode_start(request)

    # 1. Check for slash command (deterministic routing, skip LangGraph)
    tool_name, kwargs = parse_command(request.message)
    if tool_name:
        reply = await _invoke_tool_directly(tool_name, kwargs, request)
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

    # 1b. Multi-action workflow (compound request → staged execution + WA progress)
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

    # 2. Normal LangGraph flow
    prepared_metadata = await _prepare_media_metadata(request)
    user_key = request.sender_id or request.chat_id
    prepared_metadata["_llm_profile"] = resolve_user_profile(user_key).as_dict()

    store = ChatStore()
    history = store.get_recent(request.chat_id)

    initial_state = {
        "chat_id": request.chat_id,
        "sender_id": request.sender_id,
        "sender_name": request.sender_name,
        "message": request.message,
        "chat_type": request.chat_type,
        "group_name": request.group_name,
        "metadata": prepared_metadata,
        "messages": history,
        "route": "",
        "clarification_question": None,
        "response": "",
    }

    graph = get_compiled_graph()
    try:
        result = await graph.ainvoke(initial_state)
    except Exception as exc:
        _log_trace(
            request,
            {"response": "", "route": "langgraph"},
            [],
            status="failed",
            error_type=type(exc).__name__,
            error_message=str(exc)[:500],
        )
        _lightning_episode_finish(
            episode_id,
            request,
            route="langgraph",
            status="failed",
            response="",
            started=episode_started,
            error_type=type(exc).__name__,
        )
        settings = get_settings()
        from_whatsapp = bool((request.metadata or {}).get("messageId"))
        should_failover = settings.CHAT_FAILOVER_ENABLED and (
            from_whatsapp or not settings.CHAT_FAILOVER_WHATSAPP_ONLY
        )
        if should_failover:
            from app.xninetzy.core.chat_failover import run_chat_failover

            fallback = await run_chat_failover(
                request.message,
                user_id=user_key,
                chat_id=request.chat_id,
                history=history,
                metadata=prepared_metadata,
            )
            if fallback.status == "completed" and fallback.output:
                reply = fallback.output
                if settings.CHAT_FAILOVER_SHOW_NOTICE:
                    reply = "_OpenCode failover aktif._\n\n" + reply
                fallback_messages = [
                    HumanMessage(content=request.message),
                    AIMessage(content=reply),
                ]
                store.save_messages(request.chat_id, fallback_messages)
                _log_trace(
                    request,
                    {"response": reply, "route": "opencode_failover"},
                    fallback_messages,
                    status="failover",
                    error_type=type(exc).__name__,
                )
                _lightning_episode_finish(
                    episode_id,
                    request,
                    route="opencode_failover",
                    status="failover",
                    response=reply,
                    started=episode_started,
                    error_type=type(exc).__name__,
                )
                return ChatResponse(reply=reply)
            logger.error(
                "OpenCode chat failover failed: status=%s error=%s",
                fallback.status,
                fallback.error,
            )
        error_reply = (
            "Maaf, agent utama sedang tidak tersedia dan failover aman belum "
            "berhasil. Coba ulangi sebentar lagi atau gunakan slash command."
        )
        _lightning_episode_finish(
            episode_id,
            request,
            route="langgraph",
            status="failed",
            response=error_reply,
            started=episode_started,
            error_type=type(exc).__name__,
        )
        return ChatResponse(reply=error_reply)

    new_messages = result["messages"][len(history) :]
    if new_messages:
        store.save_messages(request.chat_id, new_messages)

    _log_trace(request, result, new_messages, status="ok")
    _lightning_episode_finish(
        episode_id,
        request,
        route=result.get("route") or "langgraph",
        status="completed",
        response=result.get("response", ""),
        started=episode_started,
    )

    return ChatResponse(reply=result["response"])


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
        from app.xninetzy.os.lightning.store import log_trace

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
