from __future__ import annotations

from app.xninetzy.core.identity import redact_whatsapp_jid


def test_redact_masks_full_jid():
    redacted = redact_whatsapp_jid("628123456789@s.whatsapp.net")
    assert redacted == "6281******89"
    assert "@s.whatsapp.net" not in redacted


def test_redact_drops_middle_digits():
    redacted = redact_whatsapp_jid("628123456789@s.whatsapp.net")
    assert "2345" not in redacted
    assert redacted.startswith("6281")
    assert redacted.endswith("89")


def test_redact_handles_lid_device_suffix():
    assert redacted_has_no_full_number(
        redact_whatsapp_jid("628123456789:12@s.whatsapp.net")
    )


def test_redact_bare_number_without_domain():
    redacted = redact_whatsapp_jid("628123456789")
    assert redacted == "6281******89"


def test_redact_empty_returns_label():
    assert redact_whatsapp_jid("") == "owner"
    assert redact_whatsapp_jid(None) == "owner"
    assert redact_whatsapp_jid("   ") == "owner"


def test_redact_short_or_nonjid_returns_label():
    assert redact_whatsapp_jid("12345") == "owner"
    assert redact_whatsapp_jid("group@g.us") == "owner"


def test_redact_custom_label():
    assert redact_whatsapp_jid(None, label="admin") == "admin"


def redacted_has_no_full_number(value: str) -> bool:
    return "628123456789" not in value
