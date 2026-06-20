"""Mode router: pick an interaction mode from text + domain."""
from __future__ import annotations

from app.xninetzy.context.packet import Domain, Mode


def route_mode(text: str, domain: Domain = "general") -> Mode:
    lowered = (text or "").lower()
    if any(kw in lowered for kw in ("deep research", "riset mendalam", "deep dive")):
        return "research"
    if any(kw in lowered for kw in ("pikirkan", "analisa", "deep think", "reasoning")):
        return "deep_think"
    if domain == "research":
        return "research"
    if domain == "it_learning":
        return "study"
    if domain == "life":
        return "life"
    return "quick"
