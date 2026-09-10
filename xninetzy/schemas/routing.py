from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RouteDecision(str, Enum):
    AGENT = "agent"
    DIRECT = "direct"
    CLARIFY = "clarify"


class OrchestratorOutput(BaseModel):
    """Structured output from the orchestrator LLM call."""

    route: RouteDecision = Field(description="Where to route this message")
    reasoning: str = Field(max_length=300, description="Short reason for routing decision")
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question to ask user if route=clarify",
    )


class ToolInvokeRequest(BaseModel):
    """Request body for debug tool invocation endpoint."""

    args: dict[str, Any] = Field(default_factory=dict)
    chat_id: str = "debug"
