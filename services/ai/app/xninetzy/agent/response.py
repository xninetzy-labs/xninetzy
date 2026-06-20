from __future__ import annotations

import re

from langchain_core.messages import AIMessage, SystemMessage

from app.xninetzy.agent.prompts import DIRECT_PROMPT
from app.xninetzy.agent.state import AgentState
from app.xninetzy.core.config import get_settings
from app.xninetzy.core.llm import get_llm_flash
from app.xninetzy.tools.internal.datetime_info import get_now_info


async def direct_node(state: AgentState) -> dict:
    """Handle direct responses (casual chat, explanations) using flash model."""
    settings = get_settings()
    now = get_now_info()

    system_content = DIRECT_PROMPT.format(
        bot_name=settings.BOT_NAME,
        bot_owner=settings.BOT_OWNER,
        sender_name=state.get("sender_name") or "User",
        chat_type=state.get("chat_type", "private"),
        group_name=state.get("group_name") or "-",
        current_datetime=now["human_datetime"],
    )

    messages = [SystemMessage(content=system_content)] + list(state.get("messages") or [])

    llm = get_llm_flash()
    result = await llm.ainvoke(messages)
    response = result.content if isinstance(result.content, str) else str(result.content)

    return {
        "messages": [AIMessage(content=response)],
        "response": response.strip(),
    }


async def clarify_node(state: AgentState) -> dict:
    """Return clarification question."""
    question = state.get("clarification_question") or "Bisa diperjelas maksudnya?"
    return {
        "messages": [AIMessage(content=question)],
        "response": question,
    }


def format_node(state: AgentState) -> dict:
    """Clean up response for WhatsApp format."""
    response = state.get("response") or ""
    response = _clean_for_whatsapp(response)
    return {"response": response}


def _clean_for_whatsapp(text: str) -> str:
    # Strip markdown heading (# H1, ## H2, etc.)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Strip blockquote
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # Strip markdown links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Strip markdown table rows (lines with |)
    text = re.sub(r"^\|.*\|$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-|: ]+$", "", text, flags=re.MULTILINE)
    # Remove excessive blank lines (more than 2)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
