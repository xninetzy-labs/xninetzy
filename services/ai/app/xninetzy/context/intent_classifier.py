"""Coarse intent classifier (routing hint only)."""
from __future__ import annotations

_INTENTS: list[tuple[str, tuple[str, ...]]] = [
    ("create_reminder", ("ingatkan", "remind", "jangan lupa")),
    ("plan", ("rencana", "plan", "roadmap", "jadwal", "schedule")),
    ("search", ("cari", "search", "temukan", "find")),
    ("summarize", ("rangkum", "ringkas", "summary", "tldr")),
    ("question", ("?", "apa", "bagaimana", "kenapa", "how", "what", "why")),
]


def classify_intent(text: str) -> str:
    lowered = (text or "").lower()
    for intent, keywords in _INTENTS:
        if any(kw in lowered for kw in keywords):
            return intent
    return "chat"
