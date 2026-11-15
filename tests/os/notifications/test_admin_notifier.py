from types import SimpleNamespace

import pytest

from xninetzy.os.inbox import service as inbox_service
from xninetzy.os.notifications import admin_notifier


def _settings(chat_id: str = "628123") -> SimpleNamespace:
    return SimpleNamespace(OWNER_CHAT_ID=chat_id, ADMIN_JID=chat_id)


@pytest.mark.asyncio
async def test_approval_persists_to_owner_inbox(monkeypatch):
    captured: list[dict] = []

    def fake_capture_item(text, *, kind="auto", chat_id="system", idempotency_key=None):
        captured.append({"text": text, "kind": kind, "chat_id": chat_id})

    monkeypatch.setattr(admin_notifier, "get_settings", lambda: _settings())
    monkeypatch.setattr(inbox_service, "capture_item", fake_capture_item)

    sent = await admin_notifier.notify_admin_approval(
        approval_id=42,
        action_type="krs_apply",
        title="Terapkan KRS",
        summary="Tambahkan tujuh mata kuliah.",
    )

    assert sent is True
    assert captured, "capture_item should have been invoked"
    record = captured[0]
    assert record["chat_id"] == "628123"
    assert record["kind"] == "note"
    assert "#42" in record["text"]
    assert "approval_channel_unverified" in record["text"]
    assert "/approve" not in record["text"]
    assert "/reject" not in record["text"]


@pytest.mark.asyncio
async def test_failed_inbox_notification_does_not_log_private_content(monkeypatch, caplog):
    def failed(*args, **kwargs):
        raise RuntimeError("password=synthetic-exception-private")

    monkeypatch.setattr(admin_notifier, "get_settings", lambda: _settings())
    monkeypatch.setattr(inbox_service, "capture_item", failed)
    with caplog.at_level("INFO"):
        assert not await admin_notifier.notify_admin_approval(42, "fixture-action", "synthetic-private-title", "synthetic-private-summary")
    assert "synthetic-exception-private" not in caplog.text
    assert "synthetic-private-title" not in caplog.text
    assert "synthetic-private-summary" not in caplog.text


@pytest.mark.asyncio
async def test_approval_succeeds_via_text_fallback(monkeypatch):
    """After the pivot there is no separate button fallback; both end up in inbox.

    We still verify that an inbox failure is reported as ``False`` instead of
    pretending success.
    """
    delivered = {"ok": True}

    def fake_capture_item(text, *, kind="auto", chat_id="system", idempotency_key=None):
        if not delivered["ok"]:
            raise RuntimeError("inbox down")
        return ({}, True)

    monkeypatch.setattr(admin_notifier, "get_settings", lambda: _settings())
    monkeypatch.setattr(inbox_service, "capture_item", fake_capture_item)

    sent_ok = await admin_notifier.notify_admin_approval(7, "upload", "Upload", "Cek file")
    assert sent_ok is True

    delivered["ok"] = False
    sent_fail = await admin_notifier.notify_admin_approval(8, "upload", "Upload", "Cek file")
    assert sent_fail is False


@pytest.mark.asyncio
async def test_approval_fails_closed_without_owner_chat_id(monkeypatch):
    monkeypatch.setattr(
        admin_notifier,
        "get_settings",
        lambda: SimpleNamespace(OWNER_CHAT_ID="", ADMIN_JID=""),
    )
    assert await admin_notifier.notify_admin_approval(1, "write", "Write", "Summary") is False


@pytest.mark.asyncio
async def test_notify_admin_routes_to_inbox(monkeypatch):
    captured: list[dict] = []

    def fake_capture_item(text, *, kind="auto", chat_id="system", idempotency_key=None):
        captured.append({"text": text, "kind": kind, "chat_id": chat_id})

    monkeypatch.setattr(admin_notifier, "get_settings", lambda: _settings())
    monkeypatch.setattr(admin_notifier, "should_notify_admin", lambda *args, **kwargs: True)
    monkeypatch.setattr(inbox_service, "capture_item", fake_capture_item)

    sent = await admin_notifier.notify_admin(
        event_type="os_job_done", payload={"title": "ok", "status": "ok"}, impact="low"
    )
    assert sent is True
    assert captured and captured[0]["chat_id"] == "628123"
