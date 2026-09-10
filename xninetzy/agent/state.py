from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # === Input from API ===
    chat_id: str
    sender_id: str | None
    sender_name: str | None
    message: str
    chat_type: str
    group_name: str | None
    metadata: dict[str, Any]

    # === LangGraph managed message history ===
    messages: Annotated[list[BaseMessage], add_messages]

    # === Orchestrator decision ===
    route: str
    clarification_question: str | None

    # === Final output ===
    response: str
