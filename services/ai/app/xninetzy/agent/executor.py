from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.xninetzy.agent.prompts import AGENT_PROMPT
from app.xninetzy.agent.state import AgentState
from app.xninetzy.core.config import get_settings
from app.xninetzy.interfaces.api.chat_events import emit_chat_event
from app.xninetzy.core.llm import get_llm_pro
from app.xninetzy.core.providers import LLMProfile, profile_from_metadata
from app.xninetzy.tools.internal.datetime_info import get_now_info
from app.xninetzy.tools.registry import get_all_tools


@lru_cache(maxsize=16)
def _get_react_agent(profile: LLMProfile | None = None):
    return create_react_agent(
        model=get_llm_pro(profile),
        tools=get_all_tools(),
    )


async def agent_node(state: AgentState) -> dict:
    """Run the ReAct agent with full Xninetzy tool access."""
    settings = get_settings()
    now = get_now_info()
    metadata = state.get("metadata") or {}

    # Deterministic context routing hint (domain/intent/mode), best-effort.
    context_routing = ""
    context_packet = None
    try:
        from app.xninetzy.context.builder import build_context_packet

        packet = build_context_packet(state.get("message", ""), metadata)
        context_packet = packet
        context_routing = (
            "\n[Context Routing]\n"
            f"domain={packet.domain} intent={packet.intent} mode={packet.mode}\n"
        )
    except Exception:
        pass

    grounding_context = ""
    try:
        from app.xninetzy.os.knowledge.retrieval import (
            build_agent_grounding_context,
            should_auto_ground,
        )

        if context_packet and should_auto_ground(
            context_packet.domain,
            context_packet.intent,
            state.get("message", ""),
        ):
            grounding_context = build_agent_grounding_context(state.get("message", ""))
    except Exception:
        pass

    skills_context = ""
    try:
        from app.xninetzy.skills.prompting import build_relevant_skill_context

        skills_context = build_relevant_skill_context(state.get("message", ""))
    except Exception:
        pass

    # Build personal context (best-effort, silent on failure)
    personal_context = ""
    try:
        from app.xninetzy.ecosystem.context_builder import (
            build_personal_context,
            format_context_for_prompt,
        )

        ctx = build_personal_context(state.get("chat_id", ""), state.get("message", ""))
        personal_context = format_context_for_prompt(ctx)
    except Exception:
        pass

    # Build media context so the agent knows a file is attached and how to read it.
    # Falls back to a quoted file (user replied to an earlier image/document and
    # asked about it), so "jelasin file ini" on a reply still works.
    media_context = ""
    media = metadata.get("media") or {}
    quoted_media = metadata.get("quotedMedia") or {}
    effective_media = media if media.get("hasMedia") else quoted_media
    if effective_media.get("hasMedia"):
        is_quoted = not media.get("hasMedia")
        msg_id = effective_media.get("messageId") or metadata.get("messageId") or ""
        media_type = effective_media.get("mediaType")
        label = "Media Attached (quoted)" if is_quoted else "Media Attached"
        if media_type == "document":
            instruction = (
                f"Call media_read_document(chat_id='{state.get('chat_id', '')}', "
                f"message_id='{msg_id}') before answering questions about its content."
            )
        elif media_type == "image":
            instruction = (
                f"Call media_read_image(chat_id='{state.get('chat_id', '')}', "
                f"message_id='{msg_id}') before answering questions about text in the image."
            )
        elif media_type == "audio":
            instruction = (
                f"Call media_read_audio(chat_id='{state.get('chat_id', '')}', "
                f"message_id='{msg_id}') before answering questions about the audio."
            )
        else:
            instruction = "Explain honestly that this media type is not supported yet."
        media_context = (
            f"\n[{label}]\n"
            f"type={media_type} filename={effective_media.get('filename') or '-'} "
            f"mime={effective_media.get('mimetype') or '-'} message_id={msg_id}\n"
            f"{instruction}\n"
        )

    preloaded_media_context = metadata.get("_media_prompt_context")
    if isinstance(preloaded_media_context, str) and preloaded_media_context:
        media_context = preloaded_media_context

    # Inject user rules + style profile (defense system), best-effort
    user_key = state.get("sender_id") or state.get("chat_id") or "default"
    rules_context = ""
    style_context = ""
    try:
        from app.xninetzy.os.rules.store import (
            format_rules_for_prompt,
            get_active_rules,
        )

        rules_context = format_rules_for_prompt(get_active_rules(user_key, limit=20))
    except Exception:
        pass
    try:
        from app.xninetzy.os.style.store import format_style_for_prompt

        style_context = format_style_for_prompt(user_key)
    except Exception:
        pass

    # Inject relevant semantic memory for this message, best-effort
    memory_context = ""
    try:
        from app.xninetzy.os.memory.memory_store import (
            format_memories_for_prompt,
            search_memories,
        )

        memory_context = format_memories_for_prompt(
            search_memories(user_key, state.get("message", ""), limit=5)
        )
    except Exception:
        pass

    quoted_text = metadata.get("quotedMessageText") or ""
    system_content = AGENT_PROMPT.format(
        bot_name=settings.BOT_NAME,
        bot_owner=settings.BOT_OWNER,
        sender_name=state.get("sender_name") or "User",
        sender_id=state.get("sender_id") or "",
        chat_id=state.get("chat_id", ""),
        chat_type=state.get("chat_type", "private"),
        group_name=state.get("group_name") or "-",
        current_datetime=now["human_datetime"],
        quoted_message_id=metadata.get("quotedMessageId") or "",
        quoted_participant=metadata.get("quotedParticipantJid")
        or metadata.get("participantJid")
        or "",
        quoted_message_text=quoted_text,
        is_reply_to_bot=metadata.get("isReplyToBot", False),
        context_routing=context_routing,
        skills_context=skills_context,
        personal_context=personal_context,
        media_context=media_context,
        rules_context=rules_context,
        style_context=style_context,
        memory_context=memory_context,
        grounding_context=grounding_context,
    )

    messages_with_system = [SystemMessage(content=system_content)] + list(
        state.get("messages") or []
    )

    profile = profile_from_metadata(metadata)
    emit_chat_event("phase", "Preparing contextual evidence")
    react = _get_react_agent(profile)
    emit_chat_event("agent", "Running ReAct agent")
    try:
        result = await react.ainvoke({"messages": messages_with_system})
        emit_chat_event("agent", "ReAct agent completed", "completed")
    except Exception as exc:
        emit_chat_event("agent", "ReAct agent failed, using safe fallback", "failed")
        fallback_llm = get_llm_pro(profile)
        fallback_prompt = SystemMessage(
            content=(
                "Tool execution is temporarily unavailable. Answer honestly using "
                "the available context and do not claim that tools were executed. "
                f"Failure class: {type(exc).__name__}."
            )
        )
        fallback = await fallback_llm.ainvoke(
            [fallback_prompt, *list(state.get("messages") or [])]
        )
        content = fallback.content if isinstance(fallback.content, str) else str(fallback.content)
        return {"messages": [fallback], "response": content.strip()}

    for message in result.get("messages", []):
        for call in getattr(message, "tool_calls", None) or []:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                emit_chat_event("tool", f"Tool completed: {name}", "completed")

    final_msg = next(
        (
            m
            for m in reversed(result["messages"])
            if isinstance(m, AIMessage) and m.content
        ),
        None,
    )
    response = (
        final_msg.content
        if final_msg
        else "Maaf, aku tidak bisa memproses request ini."
    )
    if not isinstance(response, str):
        response = str(response)

    return {
        "messages": result["messages"],
        "response": response.strip(),
    }
