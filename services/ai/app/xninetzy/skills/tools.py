from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.research.permissions import is_owner_admin
from app.xninetzy.skills.registry import (
    SkillValidationError,
    install_skill,
    list_skills,
    parse_skill_markdown,
    rank_skills,
    read_skill_markdown,
)


def _trusted_installer(
    sender_id: str,
    sender_name: str,
    metadata: dict | None,
) -> bool:
    context = metadata or {}
    return is_owner_admin(sender_id, sender_name) or (
        context.get("source") == "mcp" and context.get("principal") == "local-owner"
    )


@tool
def skill_list() -> str:
    """Daftar skill Xninetzy yang ditemukan secara dinamis."""
    skills = list_skills()
    if not skills:
        return "Belum ada skill Xninetzy yang valid."
    lines = ["*Xninetzy Skills*"]
    for skill in skills:
        lines.append(f"• `{skill.name}` [{skill.source}] — {skill.description}")
    return "\n".join(lines)


@tool
def skill_get(name: str) -> str:
    """Muat body SKILL.md berdasarkan nama untuk progressive disclosure."""
    body = read_skill_markdown(name)
    if body is None:
        return f"Skill `{name}` tidak ditemukan atau tidak valid."
    return body


@tool
def skill_suggest_for_request(request: str, limit: int = 3) -> str:
    """Ranking skill secara deterministik berdasarkan nama dan description."""
    matches = rank_skills(request, limit)
    if not matches:
        return "Tidak ada skill yang cukup relevan. Gunakan tool OS secara langsung."
    lines = ["*Skill yang relevan*"]
    for match in matches:
        evidence = ", ".join(match.matched_terms) or "nama skill eksplisit"
        lines.append(
            f"• `{match.skill.name}` — score {match.score}; cocok: {evidence}"
        )
    return "\n".join(lines)


@tool
def skill_validate(skill_markdown: str) -> str:
    """Validasi Agent Skills SKILL.md tanpa menyimpannya."""
    try:
        skill, _ = parse_skill_markdown(skill_markdown)
    except SkillValidationError as exc:
        return f"❌ SKILL.md tidak valid: {exc}"
    return (
        f"✅ SKILL.md valid: `{skill.name}`\n"
        f"Description: {skill.description}\n"
        f"SHA-256: `{skill.content_hash}`"
    )


@tool
def skill_install(
    skill_markdown: str,
    replace: bool = False,
    idempotency_key: str = "",
    sender_id: str = "",
    sender_name: str = "",
    metadata: dict | None = None,
) -> str:
    """Instal atau perbarui skill owner ke katalog runtime tanpa perubahan kode."""
    if not _trusted_installer(sender_id, sender_name, metadata):
        return "❌ Instalasi skill hanya tersedia untuk owner lokal terverifikasi."
    try:
        skill, action = install_skill(
            skill_markdown,
            replace=replace,
            idempotency_key=idempotency_key,
        )
    except (OSError, SkillValidationError, ValueError) as exc:
        return f"❌ Skill tidak dapat diinstal: {exc}"
    labels = {
        "installed": "diinstal",
        "updated": "diperbarui",
        "unchanged": "sudah sama",
    }
    return (
        f"✅ Skill `{skill.name}` {labels[action]}. "
        "Skill langsung tersedia untuk LangGraph dan MCP melalui skill_list/skill_get."
    )
