from __future__ import annotations

from app.xninetzy.core.config import get_settings


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _admin_names() -> list[str]:
    return [n.strip().lower() for n in get_settings().ADMIN_NAMES.split(",") if n.strip()]


def is_owner_admin(sender_id: str | None, sender_name: str | None) -> bool:
    settings = get_settings()
    admin_jid = _norm(settings.ADMIN_JID)
    return bool(admin_jid and _norm(sender_id) == admin_jid) or is_sender_named_misbahul(sender_name)


def is_sender_named_misbahul(sender_name: str | None) -> bool:
    name = _norm(sender_name)
    if not name:
        return False
    return any(admin_name and admin_name in name for admin_name in _admin_names())


def is_group_admin(metadata: dict | None) -> bool:
    metadata = metadata or {}
    if metadata.get("isGroupAdmin") is True or metadata.get("senderIsGroupAdmin") is True:
        return True

    participant = _norm(
        metadata.get("participantJid")
        or metadata.get("senderJid")
        or metadata.get("sender_id")
    )
    admins = metadata.get("groupAdmins") or metadata.get("group_admins") or []
    if participant and isinstance(admins, list):
        return participant in {_norm(str(admin)) for admin in admins}
    return False


def can_run_deep_research(
    sender_id: str | None,
    sender_name: str | None,
    chat_type: str,
    metadata: dict | None = None,
) -> tuple[bool, str]:
    settings = get_settings()
    if not settings.DEEP_RESEARCH_ADMIN_ONLY:
        return True, "deep_research_open"

    if _norm(settings.ADMIN_JID) and _norm(sender_id) == _norm(settings.ADMIN_JID):
        return True, "admin_jid"

    if settings.DEEP_RESEARCH_ALLOW_ADMIN_NAMES and is_sender_named_misbahul(sender_name):
        return True, "admin_name"

    if (
        settings.DEEP_RESEARCH_ALLOW_GROUP_ADMINS
        and _norm(chat_type) == "group"
        and is_group_admin(metadata)
    ):
        return True, "group_admin"

    return False, "not_admin"


def deep_research_denied_message(reason: str = "not_admin") -> str:
    return (
        "Maaf, *deep research* hanya bisa dijalankan oleh admin utama, Misbahul, "
        "atau admin grup.\n\n"
        "Kamu masih bisa pakai search ringan:\n"
        "• /research <topik>\n"
        "• cari web tentang ...\n"
        "• cari YouTube tentang ...\n"
        "• jelaskan ringkas ..."
    )
