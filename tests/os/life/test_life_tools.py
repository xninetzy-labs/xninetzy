from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings

PAST_DUE = "2000-01-01T09:00:00"


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


# ─── Tasks ────────────────────────────────────────────────────────────────────


def test_task_flow_capture_list_today_complete(db):
    from app.xninetzy.tools.ecosystem.life_tools import (
        task_capture,
        task_complete,
        task_list,
        task_today,
    )

    captured = task_capture.invoke(
        {
            "title": "Kerjakan laporan APSI",
            "description": "Bab 1-3",
            "priority": "high",
            "due_at": PAST_DUE,
            "chat_id": "test-user",
        }
    )
    assert "Task dicatat" in captured
    assert "Kerjakan laporan APSI" in captured

    listed = task_list.invoke({})
    assert "Kerjakan laporan APSI" in listed

    today = task_today.invoke({})
    assert "Hari ini" in today
    assert "Kerjakan laporan APSI" in today

    done = task_complete.invoke({"task_id": 1, "chat_id": "test-user"})
    assert "selesai" in done

    done_list = task_list.invoke({"status": "done"})
    assert "Kerjakan laporan APSI" in done_list

    active_list = task_list.invoke({})
    assert "Kerjakan laporan APSI" not in active_list


def test_task_list_empty(db):
    from app.xninetzy.tools.ecosystem.life_tools import task_list

    result = task_list.invoke({})
    assert "Tidak ada task" in result


def test_task_complete_missing_task(db):
    from app.xninetzy.tools.ecosystem.life_tools import task_complete

    result = task_complete.invoke({"task_id": 999})
    assert "tidak ditemukan" in result


# ─── Habit ────────────────────────────────────────────────────────────────────


def test_habit_flow_log_and_today(db):
    from app.xninetzy.tools.ecosystem.life_tools import habit_log, habit_today

    logged = habit_log.invoke(
        {"name": "belajar", "value": 1, "notes": "pagi", "chat_id": "test-user"}
    )
    assert "dicatat" in logged
    assert "belajar" in logged

    today = habit_today.invoke({})
    assert "Habit hari ini" in today
    assert "belajar" in today


def test_habit_today_empty(db):
    from app.xninetzy.tools.ecosystem.life_tools import habit_today

    result = habit_today.invoke({})
    assert "Belum ada habit" in result


# ─── Money ────────────────────────────────────────────────────────────────────


def test_money_flow_transactions_and_summary(db):
    from app.xninetzy.tools.ecosystem.life_tools import (
        money_add_transaction,
        money_summary,
    )

    income = money_add_transaction.invoke(
        {
            "amount": 10000,
            "tx_type": "income",
            "category": "lain-lain",
            "description": "jajan",
            "chat_id": "test-user",
        }
    )
    assert "+Rp 10,000" in income

    expense = money_add_transaction.invoke(
        {
            "amount": 3000,
            "tx_type": "expense",
            "category": "makan",
            "description": "nasi goreng",
            "chat_id": "test-user",
        }
    )
    assert "-Rp 3,000" in expense

    summary = money_summary.invoke({"period": "month"})
    assert "Ringkasan month" in summary
    assert "Pemasukan: Rp 10,000" in summary
    assert "Pengeluaran: Rp 3,000" in summary
    assert "Net: +Rp 7,000" in summary


def test_money_summary_empty(db):
    from app.xninetzy.tools.ecosystem.life_tools import money_summary

    summary = money_summary.invoke({"period": "month"})
    assert "Pemasukan: Rp 0" in summary
    assert "Pengeluaran: Rp 0" in summary


# ─── Workout ──────────────────────────────────────────────────────────────────


def test_workout_flow_log_and_summary(db):
    from app.xninetzy.tools.ecosystem.life_tools import workout_log, workout_summary

    logged = workout_log.invoke(
        {
            "workout_type": "gym",
            "exercises": "bench press 3x10",
            "duration": 45,
            "intensity": "high",
            "chat_id": "test-user",
        }
    )
    assert "Workout dicatat" in logged
    assert "gym" in logged

    summary = workout_summary.invoke({"period": "week"})
    assert "Workout week" in summary
    assert "Sesi: 1" in summary
    assert "45 menit" in summary
    assert "gym" in summary


def test_workout_summary_empty(db):
    from app.xninetzy.tools.ecosystem.life_tools import workout_summary

    result = workout_summary.invoke({"period": "week"})
    assert "Belum ada workout" in result


# ─── Daily ────────────────────────────────────────────────────────────────────


def test_daily_checkin_stores_mood_energy_focus(db):
    from app.xninetzy.os.life.journal_manager import get_review
    from app.xninetzy.tools.ecosystem.life_tools import daily_checkin

    result = daily_checkin.invoke(
        {
            "mood": 4,
            "energy": 3,
            "focus": 5,
            "summary": "Hari produktif mengerjakan tugas",
            "chat_id": "test-user",
        }
    )
    assert "Check-in" in result
    assert "Mood: 4/5" in result
    assert "Energi: 3/5" in result
    assert "Fokus: 5/5" in result

    stored = get_review()
    assert stored is not None
    assert stored["mood"] == 4
    assert stored["energy"] == 3
    assert stored["focus"] == 5


def test_daily_review_generate_uses_checkin_and_tasks(db):
    from app.xninetzy.tools.ecosystem.life_tools import (
        daily_checkin,
        daily_review_generate,
        task_capture,
        task_complete,
    )

    task_capture.invoke({"title": "Selesaiin makalah", "chat_id": "test-user"})
    task_complete.invoke({"task_id": 1, "chat_id": "test-user"})
    daily_checkin.invoke(
        {"mood": 4, "energy": 3, "focus": 5, "summary": "oke", "chat_id": "test-user"}
    )

    review = daily_review_generate.invoke({"chat_id": "test-user"})
    assert "Review" in review
    assert "Selesaiin makalah" in review
    assert "Ringkasan" in review
    assert "Mood 4/5, Fokus 5/5" in review

    again = daily_review_generate.invoke({"chat_id": "test-user"})
    assert "Review" in again


def test_daily_review_generate_empty(db):
    from app.xninetzy.tools.ecosystem.life_tools import daily_review_generate

    result = daily_review_generate.invoke({"chat_id": "test-user"})
    assert "Belum ada task selesai dicatat" in result
    assert "Belum ada goal aktif" in result


# ─── Dashboard ────────────────────────────────────────────────────────────────


def test_life_dashboard_combines_goal_task_habit(db):
    from app.xninetzy.tools.ecosystem.goal_tools import goal_create
    from app.xninetzy.tools.ecosystem.life_tools import (
        habit_log,
        life_dashboard,
        task_capture,
    )

    goal_create.invoke({"title": "Goal Dashboard", "domain": "personal"})
    task_capture.invoke({"title": "Task Dashboard", "due_at": PAST_DUE})
    habit_log.invoke({"name": "olahraga"})

    dashboard = life_dashboard.invoke({"chat_id": "test-user"})
    assert "Dashboard" in dashboard
    assert "Goals aktif" in dashboard
    assert "Goal Dashboard" in dashboard
    assert "Task hari ini" in dashboard
    assert "Task Dashboard" in dashboard
    assert "Habits" in dashboard
    assert "olahraga" in dashboard


def test_life_dashboard_empty(db):
    from app.xninetzy.tools.ecosystem.life_tools import life_dashboard

    result = life_dashboard.invoke({"chat_id": "test-user"})
    assert "Dashboard" in result
    assert "tidak ada yang due hari ini" in result


# ─── Registry ─────────────────────────────────────────────────────────────────


def test_life_tools_registered_in_registry():
    from app.xninetzy.tools.registry import get_all_tools

    names = {t.name for t in get_all_tools()}
    expected = {
        "task_capture",
        "task_list",
        "task_today",
        "task_complete",
        "habit_log",
        "habit_today",
        "money_add_transaction",
        "money_summary",
        "workout_log",
        "workout_summary",
        "daily_checkin",
        "daily_review_generate",
        "life_dashboard",
    }
    assert expected <= names
