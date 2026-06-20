"""ContextPacket — normalized input passed from interfaces into the agent.

Skeleton for the input-preprocessing layer. Not yet wired into the agent graph;
adding it does not change existing behavior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Domain = Literal["it_learning", "academic", "knowledge", "research", "life", "general"]
Mode = Literal["quick", "study", "deep_think", "research", "life"]
Source = Literal["whatsapp", "api", "media"]


@dataclass
class ContextPacket:
    """A single normalized turn of user input plus routing metadata."""

    text: str
    chat_id: str | None = None
    source: Source = "api"
    domain: Domain = "general"
    mode: Mode = "quick"
    intent: str = "chat"
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
