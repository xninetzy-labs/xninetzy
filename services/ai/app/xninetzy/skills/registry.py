from __future__ import annotations

from pathlib import Path

from app.xninetzy.skills.models import SkillDefinition

SKILLS: dict[str, SkillDefinition] = {
    "learning": SkillDefinition(name="learning", summary="roadmap belajar, study plan, task belajar", path="learning/skill.md", tools=["learning_create_roadmap"]),
    "research": SkillDefinition(name="research", summary="web/YT/deep research", path="research/skill.md", tools=["research_light", "deep_research_topic"]),
    "management": SkillDefinition(name="management", summary="goal, task, reminder, daily review", path="management/skill.md", tools=["task_today", "daily_review_generate"]),
    "hebat": SkillDefinition(name="hebat", summary="course, deadline, materi kuliah", path="hebat/skill.md", tools=["hebat_academic_digest", "hebat_debug_login"]),
    "obsidian": SkillDefinition(name="obsidian", summary="catatan markdown dan vault", path="obsidian/skill.md", tools=["obsidian_create", "obsidian_search"]),
    "graph_rag": SkillDefinition(name="graph_rag", summary="relasi knowledge, topik, goal, task", path="graph_rag/skill.md", tools=["graph_search"]),
}


def list_skills() -> list[SkillDefinition]:
    return list(SKILLS.values())


def get_skill(name: str) -> SkillDefinition | None:
    return SKILLS.get(name)


def read_skill_markdown(name: str) -> str | None:
    skill = get_skill(name)
    if not skill:
        return None
    path = Path(__file__).parent / skill.path
    return path.read_text(encoding="utf-8") if path.exists() else None
