"""Domain-level helpers for inferring IT Learning workflow intent.

These are *hints* for the workflow planner — they do not replace the workflow
engine in ``app/xninetzy/workflow/``. Deterministic and rule-based.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ITLearningWorkflowIntent:
    topic: str
    wants_roadmap: bool = False
    wants_study_plan: bool = False
    wants_research: bool = False
    wants_note: bool = False
    wants_reminder: bool = False


_IT_KEYWORDS = (
    "python", "javascript", "typescript", "go", "backend", "frontend",
    "database", "sql", "docker", "api", "rest", "graphql", "system design",
    "rag", "graph rag", "llm", "agent", "machine learning", "deep learning",
    "pytorch", "fastapi", "nestjs", "laravel",
)


def is_it_learning_topic(text: str) -> bool:
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in _IT_KEYWORDS)


def infer_it_learning_intent(text: str) -> ITLearningWorkflowIntent:
    lowered = (text or "").lower().strip()
    return ITLearningWorkflowIntent(
        topic=lowered[:120] or "it learning",
        wants_roadmap=any(k in lowered for k in ("roadmap", "learning path", "belajar", "kurikulum")),
        wants_study_plan=any(k in lowered for k in ("study plan", "rencana belajar", "jadwal belajar", "hari ini")),
        wants_research=any(k in lowered for k in ("riset", "research", "referensi", "paper", "youtube", "sumber")),
        wants_note=any(k in lowered for k in ("catat", "obsidian", "note", "knowledge")),
        wants_reminder=any(k in lowered for k in ("ingatkan", "reminder", "deadline", "besok", "nanti")),
    )


__all__ = [
    "ITLearningWorkflowIntent",
    "is_it_learning_topic",
    "infer_it_learning_intent",
]
