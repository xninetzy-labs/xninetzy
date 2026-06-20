"""Context builder: assemble a fully-routed ContextPacket from raw input.

Composes normalizer + intent/domain classifiers + mode router. This is the
single entry point an interface can call before handing off to the agent.
"""
from __future__ import annotations

from typing import Any

from app.xninetzy.context.domain_classifier import classify_domain
from app.xninetzy.context.intent_classifier import classify_intent
from app.xninetzy.context.mode_router import route_mode
from app.xninetzy.context.normalizer import normalize
from app.xninetzy.context.packet import ContextPacket, Source


def build_context(payload: dict[str, Any], source: Source = "api") -> ContextPacket:
    packet = normalize(payload, source=source)
    packet.domain = classify_domain(packet.text)
    packet.intent = classify_intent(packet.text)
    packet.mode = route_mode(packet.text, packet.domain)
    return packet
