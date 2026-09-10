"""Context builder: assemble a routed ContextPacket from a raw message.

Composes normalizer + domain/intent classifiers + mode router. Deterministic and
rule-based (no LLM). This is the single entry point interfaces/agent call before
handing off to the agent graph.
"""
from __future__ import annotations

from typing import Any

from xninetzy.context.domain_classifier import classify_domain
from xninetzy.context.intent_classifier import classify_intent
from xninetzy.context.mode_router import route_mode
from xninetzy.context.normalizer import normalize_message
from xninetzy.context.packet import ContextPacket


def build_context_packet(message: str, metadata: dict[str, Any] | None = None) -> ContextPacket:
    normalized = normalize_message(message)
    domain = classify_domain(normalized)
    intent = classify_intent(normalized)
    mode = route_mode(domain, intent, normalized)

    return ContextPacket(
        raw_message=message or "",
        normalized_message=normalized,
        domain=domain,
        intent=intent,
        mode=mode,
        metadata=metadata or {},
    )
