from __future__ import annotations

from app.xninetzy.core.security import redact_jids_in_text, sanitize_tool_output


def test_masks_user_jid_keeping_domain():
    out = redact_jids_in_text("Target: 628123456789@s.whatsapp.net siap")
    assert "628123456789" not in out
    assert "@s.whatsapp.net" in out
    assert out.startswith("Target: 6281")


def test_masks_group_jid():
    out = redact_jids_in_text("grup 120363012345678901@g.us aktif")
    assert "120363012345678901" not in out
    assert "@g.us" in out


def test_masks_device_suffix():
    out = redact_jids_in_text("pesan dari 628123456789:13@s.whatsapp.net")
    assert "628123456789" not in out
    assert ":13" not in out


def test_leaves_email_untouched():
    text = "kontak admin@example.com dan user@gmail.com"
    assert redact_jids_in_text(text) == text


def test_leaves_plain_numbers_and_citations():
    text = "cmid 1725 sitasi [K1] total 20260824"
    assert redact_jids_in_text(text) == text


def test_masks_status_broadcast():
    out = redact_jids_in_text("status@broadcast diterima")
    assert "status@" not in out
    assert out.endswith("@broadcast diterima")


def test_masks_multiple_jids_in_one_text():
    out = redact_jids_in_text(
        "dari 628123456789@s.whatsapp.net ke 628987654321@s.whatsapp.net"
    )
    assert "628123456789" not in out
    assert "628987654321" not in out


def test_sanitize_recurses_into_containers():
    payload = {
        "chat": "628123456789@s.whatsapp.net",
        "items": ["ok", "120363012345678901@g.us"],
        "count": 2,
    }
    cleaned = sanitize_tool_output(payload)
    assert "628123456789" not in str(cleaned)
    assert "120363012345678901" not in str(cleaned)
    assert cleaned["count"] == 2
    assert cleaned["items"][0] == "ok"


def test_sanitize_passthrough_non_string_scalars():
    assert sanitize_tool_output(5) == 5
    assert sanitize_tool_output(None) is None
    assert sanitize_tool_output(3.14) == 3.14
