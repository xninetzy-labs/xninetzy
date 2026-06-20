"""Deterministic intent classifier (routing hint only)."""
from __future__ import annotations


def classify_intent(text: str) -> str:
    lowered = (text or "").lower()

    if any(k in lowered for k in ("roadmap", "learning path", "kurikulum")):
        return "create_roadmap"
    if any(k in lowered for k in ("study plan", "jadwal belajar", "rencana belajar")):
        return "create_study_plan"
    if any(k in lowered for k in ("riset", "research", "paper", "referensi", "youtube")):
        return "research"
    if any(k in lowered for k in ("catat", "simpan", "obsidian", "knowledge")):
        return "save_note"
    if any(k in lowered for k in ("ingatkan", "reminder", "deadline")):
        return "reminder"
    if any(k in lowered for k in ("jelaskan", "apa itu", "gimana", "bagaimana", "kenapa")):
        return "explain"
    return "chat"
