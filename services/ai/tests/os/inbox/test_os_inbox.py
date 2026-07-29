from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.ecosystem.context_builder import build_personal_context
from app.xninetzy.os.inbox.service import (
    build_attention_queue,
    capture_item,
    capture_summary,
    infer_capture_kind,
    list_captures,
    triage_capture,
)
from app.xninetzy.os.life.task_manager import create_task


def _prepare(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "os-inbox.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()


@pytest.mark.parametrize(
    ("content", "kind"),
    [
        ("kerjakan tugas APSI besok", "task"),
        ("belajar distributed systems", "learning"),
        ("ide membuat local-first sync", "idea"),
        ("https://example.com/reference", "reference"),
        ("catatan penting tentang arsitektur", "note"),
        ("hmm", "unknown"),
    ],
)
def test_capture_kind_is_deterministic(content, kind):
    assert infer_capture_kind(content) == kind


def test_capture_idempotency_replays_without_duplicate_event(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)

    first, created = capture_item(
        "belajar event sourcing",
        chat_id="owner",
        idempotency_key="message-1",
    )
    replay, replay_created = capture_item(
        "belajar event sourcing",
        chat_id="owner",
        idempotency_key="message-1",
    )

    assert created is True
    assert replay_created is False
    assert replay["id"] == first["id"]
    with connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM os_inbox_items").fetchone()[0] == 1
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM ecosystem_events WHERE event_type='os_capture_created'"
            ).fetchone()[0]
            == 1
        )


def test_idempotency_key_rejects_different_capture(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    capture_item("ide pertama", idempotency_key="same")
    with pytest.raises(ValueError, match="capture berbeda"):
        capture_item("ide kedua", idempotency_key="same")


def test_triage_to_task_is_atomic_and_replay_safe(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    capture, _ = capture_item("belajar queue architecture", chat_id="owner")

    first = triage_capture(
        capture["id"],
        target="task",
        priority="high",
        due_at="2026-07-30T20:00:00+07:00",
        chat_id="owner",
    )
    replay = triage_capture(capture["id"], target="task", chat_id="owner")

    assert first["replayed"] is False
    assert replay["replayed"] is True
    assert replay["target_id"] == first["target_id"]
    with connect() as conn:
        task = conn.execute(
            "SELECT * FROM tasks WHERE source=?", (f"os_capture:{capture['id']}",)
        ).fetchone()
        assert task["domain"] == "learning"
        assert task["priority"] == "high"
        assert conn.execute(
            "SELECT COUNT(*) FROM entity_links WHERE source_type='os_capture' AND source_id=?",
            (str(capture["id"]),),
        ).fetchone()[0] == 1
        event = conn.execute(
            "SELECT id FROM ecosystem_events WHERE event_type='os_capture_promoted' AND entity_id=?",
            (str(capture["id"]),),
        ).fetchone()
        assert event is not None
        assert conn.execute(
            "SELECT COUNT(*) FROM ecosystem_event_consumptions WHERE event_id=?",
            (event["id"],),
        ).fetchone()[0] == 1


def test_archive_removes_capture_from_pending_inbox(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    capture, _ = capture_item("mungkin nanti", chat_id="owner")

    result = triage_capture(capture["id"], target="archive", chat_id="owner")

    assert result["status"] == "archived"
    assert list_captures() == []
    assert capture_summary()["archived"] == 1


def test_attention_queue_prefers_overdue_commitment(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    create_task("Task critical tanpa deadline", priority="critical")
    overdue = create_task(
        "Task overdue",
        priority="low",
        due_at="2026-07-28T09:00:00+07:00",
    )
    capture_item("ide untuk nanti")

    queue = build_attention_queue(
        now=datetime(2026, 7, 29, 8, 0, tzinfo=ZoneInfo("Asia/Jakarta"))
    )

    assert queue[0]["kind"] == "task"
    assert queue[0]["id"] == overdue["id"]
    assert "overdue" in queue[0]["reason"]


def test_personal_context_contains_os_attention_and_inbox(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    capture_item("ide membangun knowledge graph", chat_id="owner")

    context = build_personal_context("owner", "apa fokus hari ini")

    assert context["os_inbox_count"] == 1
    assert context["attention_queue"]
