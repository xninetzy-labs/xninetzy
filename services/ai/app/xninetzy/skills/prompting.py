from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.skills.registry import list_skills, rank_skills, read_skill_markdown


def build_skill_prompt() -> str:
    return "\n".join(
        f"- {skill.name}: {skill.description}" for skill in list_skills()
    )


def build_relevant_skill_context(request: str) -> str:
    settings = get_settings()
    matches = [
        match
        for match in rank_skills(request, settings.XNINETZY_SKILL_AUTO_INJECT_LIMIT)
        if match.score >= settings.XNINETZY_SKILL_MATCH_THRESHOLD
    ]
    if not matches:
        return ""
    remaining = settings.XNINETZY_SKILL_AUTO_INJECT_MAX_CHARS
    sections: list[str] = []
    for match in matches:
        body = read_skill_markdown(match.skill.name) or ""
        if not body or remaining <= 0:
            continue
        bounded = body[:remaining]
        sections.append(f"[Skill: {match.skill.name}]\n{bounded}")
        remaining -= len(bounded)
    if not sections:
        return ""
    return "\n\n[RELEVANT XNINETZY SKILLS]\n" + "\n\n".join(sections) + "\n"
