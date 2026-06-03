from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.config import get_settings
from app.db.sqlite import init_db
from app.db.migrations import run_migrations
from app.reminders.reminder_store import ReminderStore
from app.reminders.scheduler import format_reminder_message, run_scheduler_tick
from app.reminders.reminder_service import ReminderService


NOW = datetime(2026, 6, 3, 9, 0, tzinfo=ZoneInfo("Asia/Jakarta"))


@pytest.fixture(autouse=True)
def sqlite_tmp(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "scheduler.sqlite3"))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def _create_due(store: ReminderStore, *, status: str = "pending", remind_at: datetime | None = None, deadline_at: str | None = None):
    return store.create_reminder(
        chat_id="chat1",
        user_id="user1",
        title="Cek docker logs",
        remind_at=(remind_at or (NOW - timedelta(minutes=1))).isoformat(),
        deadline_at=deadline_at,
        status=status,
    )


@pytest.mark.asyncio
async def test_due_reminder_sent_once():
    store = ReminderStore()
    _create_due(store)
    sent: list[str] = []

    async def sender(reminder):
        sent.append(reminder["title"])

    first = await run_scheduler_tick(now=NOW, store=store, sender=sender)
    second = await run_scheduler_tick(now=NOW + timedelta(minutes=1), store=store, sender=sender)
    assert first["sent"] == 1
    assert second["sent"] == 0
    assert sent == ["Cek docker logs"]
    assert store.list_reminders("chat1")[0]["status"] == "sent"


@pytest.mark.asyncio
async def test_sent_and_closed_reminders_not_sent_again():
    store = ReminderStore()
    _create_due(store, status="sent")
    _create_due(store, status="closed")
    sent: list[str] = []

    async def sender(reminder):
        sent.append(reminder["title"])

    result = await run_scheduler_tick(now=NOW, store=store, sender=sender)
    assert result["sent"] == 0
    assert sent == []


@pytest.mark.asyncio
async def test_expired_reminder_not_sent():
    store = ReminderStore()
    reminder = _create_due(store, remind_at=NOW - timedelta(hours=25))
    sent: list[str] = []

    async def sender(reminder):
        sent.append(reminder["title"])

    result = await run_scheduler_tick(now=NOW, store=store, sender=sender)
    assert result["expired"] == 1
    assert sent == []
    assert store.get_reminder(reminder["id"])["status"] == "expired"


@pytest.mark.asyncio
async def test_failed_send_does_not_retry_infinite():
    store = ReminderStore()
    reminder = _create_due(store)

    async def sender(reminder):
        raise RuntimeError("wa down")

    first = await run_scheduler_tick(now=NOW, store=store, sender=sender)
    second = await run_scheduler_tick(now=NOW + timedelta(minutes=1), store=store, sender=sender)
    row = store.get_reminder(reminder["id"])
    assert first["failed"] == 1
    assert second["failed"] == 0
    assert row["status"] == "failed"
    assert row["attempt_count"] == 1
    assert "wa down" in row["last_error"]


def test_atomic_claim_prevents_double_send():
    store = ReminderStore()
    reminder = _create_due(store)
    first = store.atomic_claim_due_reminder(reminder["id"], NOW.isoformat())
    second = store.atomic_claim_due_reminder(reminder["id"], NOW.isoformat())
    assert first is not None
    assert second is None


def test_wa_message_uses_normalized_title_and_context():
    reminder = ReminderService().create_from_message(
        "chat1", "user1", "ingatkan aku 30 menit lagi buat cek docker logs", now=NOW
    )
    message = format_reminder_message(reminder)
    assert "📌 Cek Docker Logs" in message
    assert "Periksa log container" in message
    assert "🕒 Waktu:" in message
    assert "✅ Reminder ini dikirim sekali saja" in message


def test_wa_message_not_only_raw_task_text():
    reminder = ReminderService().create_from_message(
        "chat1", "user1", "ingatkan aku 30 menit lagi buat cek docker logs", now=NOW
    )
    message = format_reminder_message(reminder)
    assert message.strip() != "⏰ Reminder\n\ndocker logs"
    assert len(message.splitlines()) > 6
