from __future__ import annotations

from xninetzy.core.security import (
    redact_jids_in_text,
    sanitize_tool_output,
    strip_trusted_context,
)


def test_masks_user_jid_keeping_domain():
    out = redact_jids_in_text("Target: 628123456789@chat.local siap")
    assert "628123456789" not in out
    assert "@chat.local" in out
    assert out.startswith("Target: 6281")


def test_masks_group_jid():
    out = redact_jids_in_text("grup 120363012345678901@group.local aktif")
    assert "120363012345678901" not in out
    assert "@group.local" in out


def test_masks_device_suffix():
    out = redact_jids_in_text("pesan dari 628123456789:13@chat.local")
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
        "dari 628123456789@chat.local ke 628987654321@chat.local"
    )
    assert "628123456789" not in out
    assert "628987654321" not in out


def test_sanitize_recurses_into_containers():
    payload = {
        "chat": "628123456789@chat.local",
        "items": ["ok", "120363012345678901@group.local"],
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


def test_strip_trusted_context_removes_identity_keys():
    payload = {
        "ok": True,
        "chat_id": "private-owner-1",
        "sender_id": "owner-1",
        "sender_name": "Local owner",
        "data": {"chat_type": "private", "value": 42},
    }
    cleaned = strip_trusted_context(payload)
    assert "chat_id" not in cleaned
    assert "sender_id" not in cleaned
    assert "sender_name" not in cleaned
    assert cleaned["ok"] is True
    assert cleaned["data"]["value"] == 42
    assert "chat_type" not in cleaned["data"]


def test_strip_trusted_context_preserves_non_identity_keys():
    payload = {"chat_id": "x", "tool": "demo", "result": [1, 2, 3]}
    cleaned = strip_trusted_context(payload)
    assert cleaned == {"tool": "demo", "result": [1, 2, 3]}


def test_strip_trusted_context_handles_lists_and_nesting():
    payload = [{"chat_id": "a", "k": "v"}, {"sender_id": "b", "nested": {"chat_type": "p"}}]
    cleaned = strip_trusted_context(payload)
    assert cleaned[0] == {"k": "v"}
    assert cleaned[1] == {"nested": {}}
