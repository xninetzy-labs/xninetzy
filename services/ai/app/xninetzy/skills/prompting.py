from __future__ import annotations

from app.xninetzy.skills.registry import list_skills


def build_skill_prompt() -> str:
    return "\n".join(f"- {skill.name}: {skill.summary}" for skill in list_skills())
