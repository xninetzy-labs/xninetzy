from __future__ import annotations

from dataclasses import dataclass

from app.xninetzy.core.config import Settings, get_settings


@dataclass(frozen=True)
class OwnerDecision:
    allowed: bool
    reason: str


def _normalize_jid(value: str | None) -> str:
    raw = (value or "").strip().casefold()
    if not raw:
        return ""
    if "@" not in raw:
        digits = "".join(character for character in raw if character.isdigit())
        return f"{digits}@s.whatsapp.net" if digits else raw
    local, domain = raw.split("@", 1)
    return f"{local.split(':', 1)[0]}@{domain}"


def configured_owner_jids(settings: Settings | None = None) -> frozenset[str]:
    current = settings or get_settings()
    values = [current.ADMIN_JID, *current.OWNER_ALLOWED_JIDS.split(",")]
    normalized = (_normalize_jid(value) for value in values)
    return frozenset(value for value in normalized if value)


def authorize_owner(
    sender_id: str | None, settings: Settings | None = None
) -> OwnerDecision:
    current = settings or get_settings()
    if not current.SINGLE_OWNER_MODE:
        return OwnerDecision(True, "single_owner_disabled")
    owners = configured_owner_jids(current)
    if not owners:
        return OwnerDecision(False, "owner_not_configured")
    if _normalize_jid(sender_id) in owners:
        return OwnerDecision(True, "owner_jid")
    return OwnerDecision(False, "not_owner")


def owner_denied_message(reason: str = "not_owner") -> str:
    if reason == "owner_not_configured":
        return (
            "Xninetzy OS belum memiliki identitas owner. "
            "Atur ADMIN_JID atau OWNER_ALLOWED_JIDS pada environment service."
        )
    return (
        "Xninetzy OS sedang berjalan dalam mode single-owner. "
        "Akun ini tidak memiliki akses ke data dan tools pribadi owner."
    )
