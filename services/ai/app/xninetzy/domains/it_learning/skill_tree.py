"""Skill tree for the IT Learning OS domain.

Used by the domain classifier / roadmap planner to anchor IT learning topics.
This is data only — it introduces no behavior change to existing flows.
"""
from __future__ import annotations

IT_SKILL_TREE: dict[str, list[str]] = {
    "programming": ["python", "typescript", "javascript"],
    "backend": ["rest_api", "auth", "database", "queue"],
    "infrastructure": ["docker", "nginx", "vps", "observability"],
    "ai_engineering": ["llm", "agent", "rag", "graph_rag", "evaluation"],
    "machine_learning": ["supervised_learning", "deep_learning", "embeddings"],
}


def all_skills() -> list[str]:
    """Flat list of every leaf skill across the tree."""
    return [skill for skills in IT_SKILL_TREE.values() for skill in skills]


def branch_for(skill: str) -> str | None:
    """Return the top-level branch a leaf skill belongs to, if any."""
    skill = skill.strip().lower()
    for branch, skills in IT_SKILL_TREE.items():
        if skill in skills:
            return branch
    return None
