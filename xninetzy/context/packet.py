"""ContextPacket — deterministic routing metadata for one user turn.

Rule-based input-preprocessing layer (no LLM calls). Built by
``app.xninetzy.context.builder.build_context_packet`` and injected into the
agent/orchestrator as a lightweight routing hint.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextPacket:
    """A single normalized turn of user input plus routing metadata."""

    raw_message: str
    normalized_message: str
    domain: str = "general"
    intent: str = "chat"
    mode: str = "quick"
    metadata: dict[str, Any] = field(default_factory=dict)
