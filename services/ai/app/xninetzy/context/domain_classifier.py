"""Lightweight domain classifier.

Priority order (IT Learning OS first):
    it_learning > academic > knowledge > research > life > general

Keyword-based and deliberately simple — it is a routing hint, not the agent's
reasoning. Biology / neuroscience are intentionally NOT classified yet.
"""
from __future__ import annotations

from app.xninetzy.context.packet import Domain

# Ordered by priority. First branch with a keyword hit wins.
_KEYWORDS: list[tuple[Domain, tuple[str, ...]]] = [
    ("it_learning", (
        "code", "coding", "program", "python", "javascript", "typescript",
        "backend", "api", "database", "sql", "docker", "nginx", "vps",
        "system design", "llm", "agent", "rag", "graph rag", "machine learning",
        "deep learning", "embedding", "roadmap belajar", "belajar ngoding",
    )),
    ("academic", ("hebat", "moodle", "tugas kuliah", "assignment", "submission", "course", "dosen", "kuliah")),
    ("knowledge", ("ingest", "knowledge base", "catatan", "dokumen", "pdf", "rangkum")),
    ("research", ("research", "riset", "cari paper", "deep research", "literatur", "youtube")),
    ("life", ("habit", "jurnal", "journal", "workout", "uang", "money", "goal", "tugas harian", "reminder")),
]


def classify_domain(text: str) -> Domain:
    lowered = (text or "").lower()
    for domain, keywords in _KEYWORDS:
        if any(kw in lowered for kw in keywords):
            return domain
    return "general"
