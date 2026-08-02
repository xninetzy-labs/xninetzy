from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing-container-mount"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    get_settings.cache_clear()
    from app.xninetzy.db.sqlite import init_db

    init_db()
    from app.xninetzy.db.migrations import run_migrations

    run_migrations()
    yield
    get_settings.cache_clear()


def test_goal_flow_create_list_update_review(db):
    from app.xninetzy.tools.ecosystem.goal_tools import (
        goal_create,
        goal_list,
        goal_review,
        goal_update_progress,
    )

    created = goal_create.invoke(
        {
            "title": "Lulus APSI",
            "description": "Selesaikan semua tugas",
            "domain": "learning",
            "horizon": "quarterly",
            "priority": "high",
            "due_date": "2026-12-31",
            "chat_id": "test-user",
        }
    )
    assert "Goal dibuat" in created
    assert "Lulus APSI" in created
    assert "ID:" in created

    listed = goal_list.invoke({"status": "active"})
    assert "Goals (active)" in listed
    assert "Lulus APSI" in listed

    completed = goal_list.invoke({"status": "completed"})
    assert "Tidak ada goal dengan status 'completed'" in completed

    updated = goal_update_progress.invoke(
        {"goal_id": 1, "log_text": "Selesai bab 1", "delta": 1, "mood": 4}
    )
    assert "dicatat" in updated
    assert "Lulus APSI" in updated

    reviewed = goal_review.invoke({"goal_id": 1})
    assert "Lulus APSI" in reviewed
    assert "Selesai bab 1" in reviewed
    assert "Status: active" in reviewed


def test_goal_create_defaults_domain_and_horizon(db):
    from app.xninetzy.tools.ecosystem.goal_tools import goal_create, goal_list

    created = goal_create.invoke({"title": "Goal Tanpa Detail"})
    assert "Goal dibuat" in created

    listed = goal_list.invoke({})
    assert "Goal Tanpa Detail" in listed
    assert "personal" in listed
    assert "monthly" in listed


def test_goal_list_domain_filter(db):
    from app.xninetzy.tools.ecosystem.goal_tools import goal_create, goal_list

    goal_create.invoke({"title": "Goal Learning", "domain": "learning"})
    goal_create.invoke({"title": "Goal Health", "domain": "health"})

    learning = goal_list.invoke({"status": "active", "domain": "learning"})
    assert "Goal Learning" in learning
    assert "Goal Health" not in learning


def test_goal_update_progress_missing_goal(db):
    from app.xninetzy.tools.ecosystem.goal_tools import goal_update_progress

    result = goal_update_progress.invoke({"goal_id": 999, "log_text": "test"})
    assert "tidak ditemukan" in result


def test_goal_review_missing_goal(db):
    from app.xninetzy.tools.ecosystem.goal_tools import goal_review

    result = goal_review.invoke({"goal_id": 999})
    assert "tidak ditemukan" in result


def test_goal_create_writes_event(db):
    from app.xninetzy.ecosystem.event_bus import recent_events
    from app.xninetzy.tools.ecosystem.goal_tools import goal_create

    goal_create.invoke({"title": "Goal Event", "chat_id": "goal-chat-1"})
    events = recent_events(chat_id="goal-chat-1", event_type="goal_created")
    assert len(events) == 1
    assert events[0]["entity_type"] == "goal"


def test_goal_tools_registered_in_registry():
    from app.xninetzy.tools.registry import get_all_tools

    names = {t.name for t in get_all_tools()}
    assert {"goal_create", "goal_list", "goal_review", "goal_update_progress"} <= names
