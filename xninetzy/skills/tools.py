from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.research.permissions import is_owner_admin
from app.xninetzy.skills.registry import (
    SkillValidationError,
    install_skill,
    list_skill_resources,
    list_skills,
    rank_skills,
    read_skill_markdown,
    read_skill_resource,
    skill_catalog_health,
    validate_skill_markdown,
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
        warning = f" warnings={len(skill.quality_warnings)}" if skill.quality_warnings else ""
        lines.append(
            f"• `{skill.name}` [{skill.trust_level}] resources={len(skill.resource_paths)}{warning} — "
            f"{skill.description}"
        )
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
        reasons = ", ".join(match.selection_reasons) or "lexical"
        lines.append(
            f"• `{match.skill.name}` — confidence {match.confidence:.2f}; "
            f"cocok: {evidence}; alasan: {reasons}"
        )
    return "\n".join(lines)


@tool
def skill_validate(skill_markdown: str) -> str:
    """Validasi Agent Skills SKILL.md tanpa menyimpannya."""
    try:
        skill, warnings = validate_skill_markdown(skill_markdown)
    except SkillValidationError as exc:
        return f"❌ SKILL.md tidak valid: {exc}"
    warning_text = "\n".join(f"⚠️ {warning}" for warning in warnings)
    return (
        f"✅ SKILL.md valid: `{skill.name}`\n"
        f"Description: {skill.description}\n"
        f"Lines: {skill.line_count}; resources: {len(skill.resource_paths)}\n"
        f"SHA-256: `{skill.content_hash}`"
        + (f"\n{warning_text}" if warning_text else "")
    )


@tool
def skill_resource_list(name: str) -> str:
    """Daftar resource skill yang tersedia tanpa memuat isi seluruh skill."""
    resources = list_skill_resources(name)
    if not resources:
        return f"Skill `{name}` tidak memiliki resource yang dapat dimuat."
    return "\n".join([f"*Resources `{name}`*"] + [f"• `{path}`" for path in resources])


@tool
def skill_resource_read(name: str, relative_path: str) -> str:
    """Muat satu resource teks skill secara bounded dan path-confined."""
    try:
        return read_skill_resource(name, relative_path)
    except (OSError, SkillValidationError, UnicodeError) as exc:
        return f"❌ Resource skill tidak dapat dimuat: {exc}"


@tool
def skill_healthcheck() -> str:
    """Audit katalog skill untuk skill valid, invalid, warning, provenance, dan resource."""
    health = skill_catalog_health()
    lines = [
        "*Skill Catalog Health*",
        f"Valid: {health['valid_count']}",
        f"Invalid: {health['invalid_count']}",
        f"Warnings: {len(health['warnings'])}",
    ]
    for item in health["warnings"]:
        lines.append(f"⚠️ {item['name']}: {'; '.join(item['warnings'])}")
    for item in health["invalid"]:
        lines.append(f"❌ {item['path']}: {item['error']}")
    return "\n".join(lines)


@tool
def skill_install(
    skill_markdown: str,
    resources: dict[str, str] | None = None,
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
            resources=resources,
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
    warning_text = (
        " Peringatan: " + "; ".join(skill.quality_warnings)
        if skill.quality_warnings
        else ""
    )
    return (
        f"✅ Skill `{skill.name}` {labels[action]}.{warning_text} "
        "Skill langsung tersedia untuk LangGraph dan MCP melalui skill_list/skill_get."
    )
