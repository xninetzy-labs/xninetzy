from datetime import UTC, datetime

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.academic.mahasiswa_portal.krs_watcher import (
    KrsAnnouncement,
    KrsWatchSignal,
    KrsWatcherStore,
    _next_interval,
    krs_fingerprint,
    krs_watcher_tick,
    parse_krs_announcement,
)


@pytest.fixture
def store(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "krs-watcher.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    return KrsWatcherStore()


def test_parse_krs_announcement_valid():
    parsed = parse_krs_announcement(
        "Jadwal KRS saudara di mulai tanggal 26-01-2026 - 04-02-2026 "
        "pada pukul 08.00 s.d 16.00 WIB."
    )
    assert parsed == KrsAnnouncement(
        period_start="2026-01-26", period_end="2026-02-04"
    )


def test_parse_krs_announcement_missing():
    assert parse_krs_announcement("Tidak ada pengumuman.") is None


def test_fingerprint_changes_with_inputs():
    base = ("SIA301", "SID303")
    first = krs_fingerprint(
        KrsAnnouncement("2026-01-26", "2026-02-04"), base
    )
    second = krs_fingerprint(
        KrsAnnouncement("2026-08-10", "2026-08-20"), base
    )
    third = krs_fingerprint(
        KrsAnnouncement("2026-08-10", "2026-08-20"), base + ("SIS309",)
    )
    assert first != second
    assert second != third
    assert (
        krs_fingerprint(KrsAnnouncement("2026-08-10", "2026-08-20"), base)
        == second
    )


def test_announcement_contains():
    announcement = KrsAnnouncement("2026-08-10", "2026-08-20")
    assert announcement.contains(datetime(2026, 8, 14, 9, 0, tzinfo=UTC))
    assert not announcement.contains(datetime(2026, 9, 1, 9, 0, tzinfo=UTC))


def test_store_enabled_roundtrip(store):
    store.set_enabled(True, 300)
    state = store.get()
    assert state["enabled"] == 1
    assert state["interval_seconds"] == 300
    store.set_enabled(False)
    assert store.get()["enabled"] == 0


def test_next_interval_logic(store):
    store.set_enabled(True, 1200)
    assert _next_interval({"enabled": False}, store) == 600
    assert _next_interval({"enabled": True, "in_window": True}, store) == 10
    assert _next_interval({"enabled": True, "near_window": True}, store) == 30
    assert _next_interval({"enabled": True, "in_window": False}, store) == 1200
    store.set_enabled(False)


@pytest.mark.asyncio
async def test_tick_disabled_returns_early(store):
    store.set_enabled(False)
    result = await krs_watcher_tick()
    assert result == {"enabled": False}


@pytest.mark.asyncio
async def test_tick_notifies_once_on_change(monkeypatch, store):
    store.set_enabled(True, 600)
    notifications = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def fake_capture():
        return KrsWatchSignal(
            announcement=KrsAnnouncement("2026-08-10", "2026-08-20"),
            mk_count=5,
            fingerprint="fp-new",
        )

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.notify_admin",
        fake_notify,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.capture_krs_signal",
        fake_capture,
    )
    result = await krs_watcher_tick()
    assert result["changed"] is True
    assert notifications == ["krs_watcher_change"]
    assert store.get()["last_notified_fingerprint"] == "fp-new"
    result = await krs_watcher_tick()
    assert result["changed"] is False
    assert notifications == ["krs_watcher_change"]
    store.set_enabled(False)


@pytest.mark.asyncio
async def test_tick_session_expired_notifies_once(monkeypatch, store):
    from app.xninetzy.os.academic.mahasiswa_portal.reader import (
        AcademicPortalReadError,
    )

    store.set_enabled(True, 600)
    notifications = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def fake_capture():
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.notify_admin",
        fake_notify,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.capture_krs_signal",
        fake_capture,
    )
    result = await krs_watcher_tick()
    assert result["expired"] is True
    assert notifications == ["krs_watcher_session_expired"]
    assert store.get()["session_expired_notified"] == 1
    result = await krs_watcher_tick()
    assert notifications == ["krs_watcher_session_expired"]
    store.set_enabled(False)
