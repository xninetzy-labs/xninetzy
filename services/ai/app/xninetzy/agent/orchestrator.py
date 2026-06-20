from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.xninetzy.agent.prompts import ORCHESTRATOR_PROMPT
from app.xninetzy.agent.state import AgentState
from app.xninetzy.core.config import get_settings
from app.xninetzy.core.llm import get_llm_flash
from app.xninetzy.schemas.routing import OrchestratorOutput, RouteDecision
from app.xninetzy.tools.internal.datetime_info import get_now_info


async def orchestrator_node(state: AgentState) -> dict:
    """Determine routing: agent, direct, or clarify."""
    settings = get_settings()
    now = get_now_info()

    system_content = ORCHESTRATOR_PROMPT.format(
        bot_name=settings.BOT_NAME,
        sender_name=state.get("sender_name") or "User",
        chat_type=state.get("chat_type", "private"),
        group_name=state.get("group_name") or "-",
        current_datetime=now["human_datetime"],
    )

    # Deterministic routing hint (domain/intent/mode), best-effort.
    routing_hint = ""
    try:
        from app.xninetzy.context.builder import build_context_packet
        packet = build_context_packet(state["message"], state.get("metadata") or {})
        routing_hint = f"Domain: {packet.domain}\nIntent: {packet.intent}\nMode: {packet.mode}\n"
    except Exception:
        pass

    user_content = (
        f"Sender: {state.get('sender_name') or state.get('sender_id') or 'User'}\n"
        f"{routing_hint}"
        f"Pesan: {state['message']}"
    )

    # Use last 6 messages as context window for routing decision
    history = (state.get("messages") or [])[-6:]
    orchestrator_messages = [
        SystemMessage(content=system_content),
        *history,
        HumanMessage(content=user_content),
    ]

    llm = get_llm_flash()

    try:
        structured_llm = llm.with_structured_output(OrchestratorOutput)
        result: OrchestratorOutput = await structured_llm.ainvoke(orchestrator_messages)
    except Exception:
        result = await _fallback_route(llm, orchestrator_messages)

    # Append the real user message to state messages
    user_msg = HumanMessage(content=state["message"])

    return {
        "route": result.route.value,
        "clarification_question": result.clarification_question,
        "messages": [user_msg],
    }


async def _fallback_route(llm, messages) -> OrchestratorOutput:
    """JSON string fallback when structured output fails."""
    fallback_msg = messages + [
        HumanMessage(
            content=(
                'Balas dengan JSON saja: {"route": "agent"|"direct"|"clarify", '
                '"reasoning": "singkat", "clarification_question": null}'
            )
        )
    ]
    try:
        resp = await llm.ainvoke(fallback_msg)
        text = resp.content if isinstance(resp.content, str) else ""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return OrchestratorOutput(**data)
    except Exception:
        pass
    return OrchestratorOutput(route=RouteDecision.DIRECT, reasoning="fallback to direct")


def route_from_orchestrator(state: AgentState) -> str:
    return state.get("route", "direct")
