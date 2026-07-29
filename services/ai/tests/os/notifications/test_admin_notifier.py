from types import SimpleNamespace

import pytest

from app.xninetzy.os.notifications import admin_notifier


@pytest.mark.asyncio
async def test_approval_uses_whatsapp_admin_buttons(monkeypatch):
    calls = []

    async def fake_call(tool_name, payload):
        calls.append((tool_name, payload))
        return {"success": True}

    monkeypatch.setattr(
        admin_notifier,
        "get_settings",
        lambda: SimpleNamespace(ADMIN_JID="628123@s.whatsapp.net"),
    )
    from app.xninetzy.interfaces.whatsapp import client

    monkeypatch.setattr(client, "call_wa_tool", fake_call)

    sent = await admin_notifier.notify_admin_approval(
        approval_id=42,
        action_type="krs_apply",
        title="Terapkan KRS",
        summary="Tambahkan tujuh mata kuliah.",
    )

    assert sent is True
    assert calls[0][0] == "send_verification_buttons"
    assert calls[0][1]["jid"] == "628123@s.whatsapp.net"
    assert calls[0][1]["approval_id"] == "42"
    assert "/approve 42" in calls[0][1]["text"]
    assert "/reject 42" in calls[0][1]["text"]


@pytest.mark.asyncio
async def test_approval_falls_back_to_whatsapp_text(monkeypatch):
    calls = []

    async def fake_call(tool_name, payload):
        calls.append((tool_name, payload))
        if tool_name == "send_verification_buttons":
            raise RuntimeError("buttons unavailable")
        return {"success": True}

    monkeypatch.setattr(
        admin_notifier,
        "get_settings",
        lambda: SimpleNamespace(ADMIN_JID="628123"),
    )
    from app.xninetzy.interfaces.whatsapp import client

    monkeypatch.setattr(client, "call_wa_tool", fake_call)

    sent = await admin_notifier.notify_admin_approval(7, "upload", "Upload", "Cek file")

    assert sent is True
    assert [name for name, _ in calls] == [
        "send_verification_buttons",
        "send_text_message",
    ]
    assert calls[1][1]["jid"] == "628123@s.whatsapp.net"
    assert "/approve 7" in calls[1][1]["text"]


@pytest.mark.asyncio
async def test_approval_fails_closed_without_admin_jid(monkeypatch):
    monkeypatch.setattr(
        admin_notifier,
        "get_settings",
        lambda: SimpleNamespace(ADMIN_JID=""),
    )
    assert await admin_notifier.notify_admin_approval(1, "write", "Write", "Summary") is False
