from __future__ import annotations

from xninetzy.core.config import Settings, get_settings


def normalize_chat_id(value: str | None) -> str:
    """Normalize any owner/chat identifier into a deterministic canonical form.

    Replaces the legacy WhatsApp-JID normalizer. Handles phone numbers,
    bare usernames, and existing fully-qualified identifiers without
    imposing a WhatsApp-shaped suffix.
    """
    raw = (value or "").strip().casefold()
    if not raw:
        return ""
    if "@" not in raw:
        digits = "".join(character for character in raw if character.isdigit())
        return digits or raw
    local, domain = raw.split("@", 1)
    return f"{local.split(':', 1)[0]}@{domain}"


def normalize_whatsapp_jid(value: str | None) -> str:
    """Backwards-compatible alias for normalize_chat_id.

    Deprecated: callers should use normalize_chat_id directly.
    """
    return normalize_chat_id(value)


def redact_chat_id(value: str | None, label: str = "owner") -> str:
    """Redact a chat identifier by hashing visible digits only."""
    raw = (value or "").strip()
    if not raw:
        return label
    local = raw.split("@", 1)[0].split(":", 1)[0]
    digits = "".join(character for character in local if character.isdigit())
    if len(digits) < 6:
        return label
    return f"{digits[:4]}{'*' * (len(digits) - 6)}{digits[-2:]}"


def redact_whatsapp_jid(value: str | None, label: str = "owner") -> str:
    """Backwards-compatible alias for redact_chat_id."""
    return redact_chat_id(value, label=label)


def configured_owner_ids(settings: Settings | None = None) -> frozenset[str]:
    """Resolve every identifier form that represents the deployment owner."""
    current = settings or get_settings()
    values = [
        current.OWNER_PHONE_NUMBER,
        current.OWNER_CHAT_ID,
        *current.OWNER_ALLOWED_IDS.split(","),
    ]
    normalized = (normalize_chat_id(value) for value in values)
    return frozenset(value for value in normalized if value)


def configured_owner_jids(settings: Settings | None = None) -> frozenset[str]:
    """Backwards-compatible alias for configured_owner_ids."""
    return configured_owner_ids(settings)
