from __future__ import annotations

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.agent.prompts import AGENT_PROMPT
from app.agent.state import AgentState
from app.core.config import get_settings
from app.core.llm import get_llm_pro
from app.tools.internal.datetime_info import get_now_info
from app.tools.registry import get_all_tools

_react_agent = None


def _get_react_agent():
    global _react_agent
    if _react_agent is None:
        _react_agent = create_react_agent(
            model=get_llm_pro(),
            tools=get_all_tools(),
        )
    return _react_agent


async def agent_node(state: AgentState) -> dict:
    """Run ReAct agent with full tool access using deepseek-pro for complex reasoning."""
    settings = get_settings()
    now = get_now_info()
    metadata = state.get("metadata") or {}

    # Build personal context (best-effort, silent on failure)
    personal_context = ""
    try:
        from app.ecosystem.context_builder import build_personal_context, format_context_for_prompt
        ctx = build_personal_context(state.get("chat_id", ""), state.get("message", ""))
        personal_context = format_context_for_prompt(ctx)
    except Exception:
        pass

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
        quoted_participant=metadata.get("quotedParticipantJid") or metadata.get("participantJid") or "",
        is_reply_to_bot=metadata.get("isReplyToBot", False),
        personal_context=personal_context,
    )

    messages_with_system = [SystemMessage(content=system_content)] + list(state.get("messages") or [])

    react = _get_react_agent()
    result = await react.ainvoke({"messages": messages_with_system})

    final_msg = next(
        (m for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content),
        None,
    )
    response = final_msg.content if final_msg else "Maaf, aku tidak bisa memproses request ini."
    if not isinstance(response, str):
        response = str(response)

    return {
        "messages": result["messages"],
        "response": response.strip(),
    }
