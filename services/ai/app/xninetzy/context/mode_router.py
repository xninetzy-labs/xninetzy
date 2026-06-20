"""Mode router: pick an interaction mode from domain + intent + text."""
from __future__ import annotations


def route_mode(domain: str, intent: str, text: str) -> str:
    lowered = (text or "").lower()

    if intent == "research" or "deep research" in lowered:
        return "research"
    if domain == "it_learning" and intent in {"create_roadmap", "create_study_plan", "explain"}:
        return "study"
    if any(k in lowered for k in ("analisis mendalam", "thinking", "arsitektur", "debug kompleks")):
        return "deep_think"
    if domain == "life":
        return "life"
    return "quick"
