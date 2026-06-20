from __future__ import annotations

import re

_NEG_KW = ("salah", "harusnya", "kurang", "jangan", "terlalu", "bukan", "gagal", "ngaco", "wrong", "keliru")
_POS_KW = ("bagus", "mantap", "makasih", "thanks", "betul", "benar", "helpful", "keren")


def classify_feedback(text: str) -> dict:
    """Classify feedback and, when it implies a behavior rule, suggest one."""
    t = text.strip()
    low = t.lower()

    if any(k in low for k in _POS_KW) and not any(k in low for k in _NEG_KW):
        ftype, severity = "praise", "low"
    elif any(k in low for k in _NEG_KW):
        ftype, severity = "correction", "high" if ("salah" in low or "gagal" in low) else "medium"
    else:
        ftype, severity = "instruction", "medium"

    suggested_rule = _suggest_rule(t, low)
    return {
        "feedback_type": ftype,
        "severity": severity,
        "suggested_rule": suggested_rule,
        "implies_change": ftype in ("correction", "instruction") and bool(suggested_rule),
    }


def _suggest_rule(text: str, low: str) -> str | None:
    """Derive a concise, durable rule from corrective feedback (heuristic)."""
    # "harusnya X" / "seharusnya X" -> selalu X
    m = re.search(r"(?:se)?harusnya\s+(.+)", low)
    if m:
        return f"Selalu {m.group(1).strip().rstrip('.')}"
    # contains an explicit prohibition
    m = re.search(r"(jangan\s+.+)", low)
    if m:
        return m.group(1).strip().rstrip(".")
    # "terlalu panjang/pendek/formal" -> style guidance
    if "terlalu panjang" in low:
        return "Jawab lebih ringkas, jangan terlalu panjang"
    if "terlalu pendek" in low:
        return "Beri jawaban lebih lengkap saat dibutuhkan"
    if "terlalu formal" in low:
        return "Jawab dengan gaya lebih santai"
    return None
