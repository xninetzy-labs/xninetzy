from __future__ import annotations


def normalize_whatsapp_jid(value: str | None) -> str:
    raw = (value or "").strip().casefold()
    if not raw:
        return ""
    if "@" not in raw:
        digits = "".join(character for character in raw if character.isdigit())
        return f"{digits}@s.whatsapp.net" if digits else raw
    local, domain = raw.split("@", 1)
    return f"{local.split(':', 1)[0]}@{domain}"
