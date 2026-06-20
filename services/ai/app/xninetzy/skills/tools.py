from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.skills.registry import get_skill, list_skills, read_skill_markdown


@tool
def skill_list() -> str:
    """List skill Xninetzy."""
    lines = ["*Xninetzy Skills*"]
    for skill in list_skills():
        lines.append(f"• {skill.name} - {skill.summary}")
    return "\n".join(lines)


@tool
def skill_get(name: str) -> str:
    """Ambil detail skill."""
    skill = get_skill(name)
    if not skill:
        return f"Skill `{name}` tidak ditemukan."
    body = read_skill_markdown(name) or skill.summary
    return body[:3000]


@tool
def skill_suggest_for_request(request: str) -> str:
    """Sarankan skill untuk request user."""
    text = request.lower()
    picks: list[str] = []
    if any(k in text for k in ["youtube", "research", "riset", "sumber"]):
        picks.append("research")
    if any(k in text for k in ["roadmap", "belajar", "study"]):
        picks.append("learning")
    if any(k in text for k in ["task", "goal", "review", "reminder"]):
        picks.append("management")
    if "hebat" in text or "moodle" in text:
        picks.append("hebat")
    if "obsidian" in text or "catatan" in text:
        picks.append("obsidian")
    if "graph" in text or "rag" in text:
        picks.append("graph_rag")
    return "Skill disarankan: " + (", ".join(dict.fromkeys(picks)) if picks else "management")
