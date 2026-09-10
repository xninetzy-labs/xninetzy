"""Message normalization (deterministic, no LLM)."""
from __future__ import annotations

import re


def normalize_message(text: str) -> str:
    """Collapse whitespace and trim. Tolerant of None."""
    text = text or ""
    text = re.sub(r"\s+", " ", text).strip()
    return text
