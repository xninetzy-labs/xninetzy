from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RouteDecision(str, Enum):
    AGENT = "agent"
    DIRECT = "direct"
    CLARIFY = "clarify"


class OrchestratorOutput(BaseModel):
    route: RouteDecision = Field(description="Where to route this message")
    reasoning: str = Field(max_length=300, description="Short reason for routing decision")
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question to ask user if route=clarify",
    )


def derive_idempotency_key(tool_name: str, args: dict[str, Any], chat_id: str) -> str:
    canonical = json.dumps(args, sort_keys=True, default=str, ensure_ascii=False)
    seed = f"{tool_name}|{chat_id}|{canonical}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


class ToolInvokeRequest(BaseModel):
    args: dict[str, Any] = Field(default_factory=dict)
    chat_id: str = "debug"
    idempotency_key: str | None = Field(
        default=None,
        description="Optional client-supplied key; server auto-generates for WRITE/FINAL if absent.",
    )
