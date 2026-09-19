from __future__ import annotations

from xninetzy.core.identity import redact_chat_id


def test_redact_masks_full_jid():
    redacted = redact_chat_id("628123456789@chat.local")
    assert redacted == "6281******89"
    assert "@chat.local" not in redacted


def test_redact_drops_middle_digits():
    redacted = redact_chat_id("628123456789@chat.local")
    assert "2345" not in redacted
    assert redacted.startswith("6281")
    assert redacted.endswith("89")


def test_redact_handles_lid_device_suffix():
    assert redacted_has_no_full_number(
        redact_chat_id("628123456789:12@chat.local")
    )


def test_redact_bare_number_without_domain():
    redacted = redact_chat_id("628123456789")
    assert redacted == "6281******89"


def test_redact_empty_returns_label():
    assert redact_chat_id("") == "owner"
    assert redact_chat_id(None) == "owner"
    assert redact_chat_id("   ") == "owner"


def test_redact_short_or_nonjid_returns_label():
    assert redact_chat_id("12345") == "owner"
    assert redact_chat_id("group@group.local") == "owner"


def test_redact_custom_label():
    assert redact_chat_id(None, label="admin") == "admin"


def redacted_has_no_full_number(value: str) -> bool:
    return "628123456789" not in value
