from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.ecosystem.event_bus import record_event
from app.xninetzy.os.jobs.service import (
    build_weekly_review,
    get_data_freshness,
    run_os_job_tick,
)
from app.xninetzy.os.jobs.store import JobStore

NOW = datetime(2026, 7, 29, 8, 0, tzinfo=ZoneInfo("Asia/Jakarta"))


@pytest.fixture(autouse=True)
def isolated_scheduler(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("ADMIN_JID", "628123456789@s.whatsapp.net")
    monkeypatch.setenv("OS_NOTIFY_CHAT_ID", "628123456789@s.whatsapp.net")
    monkeypatch.setenv("OS_SCHEDULER_ENABLED", "true")
    monkeypatch.setenv("MORNING_BRIEFING_ENABLED", "false")
    monkeypatch.setenv("EVENING_CHECKIN_ENABLED", "false")
    monkeypatch.setenv("WEEKLY_REVIEW_ENABLED", "false")
    monkeypatch.setenv("HEBAT_PERIODIC_SYNC_ENABLED", "false")
    monkeypatch.setenv("HEBAT_SYNC_INTERVAL_MINUTES", "60")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def test_job_claim_uses_lease_and_delivery_state_is_terminal():
    store = JobStore()
    first = store.claim(
        job_key="briefing:lease",
        job_type="morning_briefing",
        owner_id="owner",
        scheduled_for=NOW.isoformat(),
        now=NOW,
        lease_seconds=60,
    )
    assert first is not None
    assert (
        store.claim(
            job_key="briefing:lease",
            job_type="morning_briefing",
            owner_id="owner",
            scheduled_for=NOW.isoformat(),
            now=NOW + timedelta(seconds=30),
            lease_seconds=60,
        )
        is None
    )
    reclaimed = store.claim(
        job_key="briefing:lease",
        job_type="morning_briefing",
        owner_id="owner",
        scheduled_for=NOW.isoformat(),
        now=NOW + timedelta(seconds=61),
        lease_seconds=60,
    )
    assert reclaimed["attempts"] == 2
    assert store.start_delivery(
        reclaimed["id"], "prepared", NOW + timedelta(seconds=61)
    )
    assert (
        store.claim(
            job_key="briefing:lease",
            job_type="morning_briefing",
            owner_id="owner",
            scheduled_for=NOW.isoformat(),
            now=NOW + timedelta(hours=1),
            lease_seconds=60,
        )
        is None
    )
    assert store.reconcile_orphaned_deliveries(NOW + timedelta(hours=1)) == 1
    assert store.get("briefing:lease")["status"] == "delivery_uncertain"


@pytest.mark.asyncio
async def test_morning_briefing_delivered_at_most_once(monkeypatch):
    monkeypatch.setenv("MORNING_BRIEFING_ENABLED", "true")
    monkeypatch.setenv("MORNING_BRIEFING_HOUR", "7")
    get_settings.cache_clear()
    sent: list[tuple[str, str]] = []

    async def sender(jid: str, message: str) -> None:
        sent.append((jid, message))

    first = await run_os_job_tick(now=NOW, sender=sender)
    second = await run_os_job_tick(now=NOW + timedelta(minutes=5), sender=sender)

    assert first["delivered"] == 1
    assert second["delivered"] == 0
    assert len(sent) == 1
    assert "Morning Briefing" in sent[0][1]
    assert "Freshness data" in sent[0][1]
    assert JobStore().get("morning_briefing:2026-07-29")["status"] == "delivered"


@pytest.mark.asyncio
async def test_ambiguous_delivery_is_not_retried(monkeypatch):
    monkeypatch.setenv("MORNING_BRIEFING_ENABLED", "true")
    get_settings.cache_clear()
    attempts = 0

    async def failing_sender(jid: str, message: str) -> None:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("socket response lost")

    first = await run_os_job_tick(now=NOW, sender=failing_sender)
    second = await run_os_job_tick(now=NOW + timedelta(hours=2), sender=failing_sender)

    assert first["failed"] == 1
    assert second["claimed"] == 0
    assert attempts == 1
    job = JobStore().get("morning_briefing:2026-07-29")
    assert job["status"] == "delivery_uncertain"
    assert "socket response lost" in job["last_error"]


@pytest.mark.asyncio
async def test_periodic_hebat_sync_has_one_run_per_interval(monkeypatch):
    monkeypatch.setenv("HEBAT_PERIODIC_SYNC_ENABLED", "true")
    get_settings.cache_clear()
    calls: list[str] = []

    async def hebat_runner(chat_id: str) -> str:
        calls.append(chat_id)
        return "sync ok"

    first = await run_os_job_tick(now=NOW, hebat_runner=hebat_runner)
    second = await run_os_job_tick(
        now=NOW + timedelta(minutes=30), hebat_runner=hebat_runner
    )

    assert first["succeeded"] == 1
    assert second["succeeded"] == 0
    assert calls == ["628123456789@s.whatsapp.net"]
    assert JobStore().list_recent(1)[0]["status"] == "succeeded"


@pytest.mark.asyncio
async def test_failed_hebat_sync_retries_after_persisted_backoff(monkeypatch):
    monkeypatch.setenv("HEBAT_PERIODIC_SYNC_ENABLED", "true")
    monkeypatch.setenv("OS_JOB_RETRY_DELAY_SECONDS", "300")
    get_settings.cache_clear()
    calls = 0

    async def flaky_runner(chat_id: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("HEBAT session expired")
        return "sync recovered"

    first = await run_os_job_tick(now=NOW, hebat_runner=flaky_runner)
    early = await run_os_job_tick(
        now=NOW + timedelta(minutes=4), hebat_runner=flaky_runner
    )
    recovered = await run_os_job_tick(
        now=NOW + timedelta(minutes=6), hebat_runner=flaky_runner
    )

    assert first["failed"] == 1
    assert early["claimed"] == 0
    assert recovered["succeeded"] == 1
    assert calls == 2
    latest = JobStore().list_recent(1)[0]
    assert latest["status"] == "succeeded"
    assert latest["attempts"] == 2


def test_freshness_and_weekly_review_use_persisted_events():
    old = NOW - timedelta(minutes=180)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO hebat_courses
              (moodle_course_id, fullname, course_url, last_synced_at)
            VALUES ('freshness-course', 'Course', 'https://example.invalid', ?)
            """,
            (old.isoformat(),),
        )
    record_event("owner", "task_completed", "test", "task", "999")
    record_event("owner", "habit_logged", "test", "habit", "study")

    freshness = get_data_freshness(NOW)
    review = build_weekly_review("owner", NOW)

    assert freshness["hebat"]["status"] == "stale"
    assert freshness["hebat"]["age_minutes"] == 180
    assert "Task selesai: *1*" in review
    assert "Habit dicatat: *1*" in review
