"""Deterministic domain classifier (routing hint only).

Priority order (IT Learning OS first):
    it_learning > academic > knowledge > research > life > general

Notes:
- ``rag`` / ``graph rag`` are intentionally treated as IT learning topics so that
  "buat roadmap belajar RAG" routes to it_learning, not knowledge/research.
- HEBAT is an academic *connector* — only route to ``academic`` when the user is
  clearly talking about coursework, not when asking for a general IT roadmap.
- Biology / neuroscience are intentionally NOT classified yet.
"""
from __future__ import annotations

IT_LEARNING_KEYWORDS = (
    "python", "javascript", "typescript", "golang", " go ", "backend", "frontend",
    "database", "sql", "docker", "nginx", "vps", "api", "rest", "graphql",
    "system design", "rag", "graph rag", "llm", "agent", "machine learning",
    "deep learning", "pytorch", "fastapi", "nestjs", "laravel", "coding",
    "ngoding", "program", "belajar coding", "roadmap belajar", "belajar ngoding",
)

ACADEMIC_KEYWORDS = (
    "hebat", "moodle", "tugas", "deadline", "matkul", "kuliah", "assignment",
    "submission", "dosen", "course",
)

KNOWLEDGE_KEYWORDS = (
    "knowledge", "catatan", "obsidian", "note", "vault", "ingest", "dokumen",
)

RESEARCH_KEYWORDS = (
    "research", "riset", "paper", "jurnal", "referensi", "youtube", "sumber",
    "literatur",
)

LIFE_KEYWORDS = (
    "reminder", "ingatkan", "habit", "goal", "task", "todo", "uang", "money",
    "workout", "jurnal", "journal",
)


def classify_domain(text: str) -> str:
    lowered = (text or "").lower()

    if any(k in lowered for k in IT_LEARNING_KEYWORDS):
        return "it_learning"
    if any(k in lowered for k in ACADEMIC_KEYWORDS):
        return "academic"
    if any(k in lowered for k in KNOWLEDGE_KEYWORDS):
        return "knowledge"
    if any(k in lowered for k in RESEARCH_KEYWORDS):
        return "research"
    if any(k in lowered for k in LIFE_KEYWORDS):
        return "life"
    return "general"
