from __future__ import annotations

from app.xninetzy.core.config import get_settings

CONFIRMATION_REQUIRED_ACTIONS = {
    "upload_assignment",
    "delete_note",
    "overwrite_note",
    "delete_goal",
    "delete_transaction",
    "submit_form",
}

NEVER_LOG = {
    "password", "sesskey", "logintoken", "cookie",
    "token", "secret", "private_key", "credential",
}

ACADEMIC_INTEGRITY_NOTE = (
    "AI membantu mengelola, merapikan, dan mengirim file milik user. "
    "AI tidak boleh mengerjakan soal ujian/kuis live secara tidak sah."
)

MONEY_ADVICE_DISCLAIMER = (
    "Ini hanya pelacakan pribadi. Bukan nasihat keuangan profesional."
)

HEALTH_ADVICE_DISCLAIMER = (
    "Ini hanya pelacakan pribadi. Bukan nasihat medis profesional."
)


def requires_confirmation(action: str) -> bool:
    s = get_settings()
    if not s.REQUIRE_CONFIRMATION_FOR_IMPORTANT_ACTIONS:
        return False
    return action in CONFIRMATION_REQUIRED_ACTIONS


def sanitize_for_log(data: dict) -> dict:
    """Remove sensitive keys from a dict before logging."""
    return {
        k: "***" if any(blocked in k.lower() for blocked in NEVER_LOG) else v
        for k, v in data.items()
    }
