from __future__ import annotations

from dataclasses import dataclass

from app.xninetzy.core.config import Settings, get_settings
from app.xninetzy.core.identity import configured_owner_jids, normalize_whatsapp_jid

__all__ = ["OwnerDecision", "authorize_owner", "configured_owner_jids"]


@dataclass(frozen=True)
class OwnerDecision:
    allowed: bool
    reason: str


def authorize_owner(
    sender_id: str | None, settings: Settings | None = None, local_client: bool = False
) -> OwnerDecision:
    current = settings or get_settings()
    if not current.SINGLE_OWNER_MODE:
        return OwnerDecision(True, "single_owner_disabled")
    if local_client and (sender_id or "").strip() in {"mcp:local-owner", "xninetzy-cli"}:
        return OwnerDecision(True, "trusted_local_cli")
    owners = configured_owner_jids(current)
    if not owners:
        return OwnerDecision(False, "owner_not_configured")
    if normalize_whatsapp_jid(sender_id) in owners:
        return OwnerDecision(True, "owner_jid")
    return OwnerDecision(False, "not_owner")


def owner_denied_message(reason: str = "not_owner") -> str:
    if reason == "owner_not_configured":
        return (
            "Xninetzy OS belum memiliki identitas owner. "
            "Atur OWNER_PHONE_NUMBER, ADMIN_JID, atau OWNER_ALLOWED_JIDS pada environment service."
        )
    return (
        "Xninetzy OS sedang berjalan dalam mode single-owner. "
        "Akun ini tidak memiliki akses ke data dan tools pribadi owner."
    )
