from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.config import get_settings
from app.db.sqlite import init_db
from app.db.migrations import run_migrations
from app.reminders.reminder_service import ReminderService


NOW = datetime(2026, 6, 3, 9, 0, tzinfo=ZoneInfo("Asia/Jakarta"))


@pytest.fixture(autouse=True)
def sqlite_tmp(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "reminders.sqlite3"))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def test_create_explicit_reminder():
    res = ReminderService().create_from_message("chat1", "user1", "ingatkan aku 30 menit lagi buat cek docker logs", now=NOW)
    assert res["created"] is True
    assert res["status"] == "pending"
    assert res["reminder_type"] == "explicit"
    assert res["title"] == "Cek Docker Logs"
    assert res["raw_user_message"] == "ingatkan aku 30 menit lagi buat cek docker logs"
    assert res["remind_at"] == "2026-06-03T09:30:00+07:00"


def test_create_deadline_offset_reminder():
    res = ReminderService().create_from_message(
        "chat1", "user1", "buat reminder tugas A h-2 jam dari deadline jam 10 malam", now=NOW
    )
    assert res["created"] is True
    assert res["deadline_at"] == "2026-06-03T22:00:00+07:00"
    assert res["remind_at"] == "2026-06-03T20:00:00+07:00"
    assert res["offset_unit"] == "hours"
    assert res["title"] == "Kerjakan Tugas A"
    assert res["description"]


def test_skip_duplicate():
    svc = ReminderService()
    first = svc.create_from_message("chat1", "user1", "ingatkan aku 30 menit lagi buat cek docker logs", now=NOW)
    second = svc.create_from_message("chat1", "user1", "ingatkan aku 30 menit lagi buat cek docker logs", now=NOW)
    assert first["created"] is True
    assert second["created"] is False
    assert second["duplicate"] is True


def test_skip_remind_at_in_past():
    past = (NOW - timedelta(minutes=5)).isoformat()
    res = ReminderService().create_from_parsed(
        chat_id="chat1",
        user_id="user1",
        parsed={
            "title": "Past",
            "description": None,
            "deadline_at": None,
            "remind_at": past,
            "timezone": "Asia/Jakarta",
            "priority": "normal",
            "reminder_type": "explicit",
            "offset_value": None,
            "offset_unit": None,
            "metadata": {},
        },
        now=NOW,
    )
    assert res["created"] is False
    assert res["reason"] == "remind_at_passed"


def test_auto_create_h_minus_one_and_h_minus_two_if_valid():
    res = ReminderService().create_auto_from_context(
        chat_id="chat1",
        user_id="user1",
        text="bikin planning tugas APSI deadline tanggal 5 Juni jam 10 malam",
        title="Tugas APSI",
        now=NOW,
    )
    made = [r for r in res if r.get("created")]
    assert len(made) == 2
    assert {r["offset_unit"] for r in made} == {"days", "hours"}


def test_auto_skip_h_minus_one_if_already_passed():
    now = datetime(2026, 6, 4, 23, 0, tzinfo=ZoneInfo("Asia/Jakarta"))
    res = ReminderService().create_auto_from_context(
        chat_id="chat1",
        user_id="user1",
        text="bikin planning tugas APSI deadline tanggal 5 Juni jam 10 malam",
        title="Tugas APSI",
        now=now,
    )
    made = [r for r in res if r.get("created")]
    assert len(made) == 1
    assert made[0]["offset_value"] == 2
    assert made[0]["offset_unit"] == "hours"
