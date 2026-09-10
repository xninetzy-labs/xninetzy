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
    _request_login_captcha,
    krs_fingerprint,
    krs_watcher_tick,
    parse_kprs_status,
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


def test_parse_kprs_status_closed():
    assert parse_kprs_status("KRS anda belum di buka oleh dosen wali") is False


def test_parse_kprs_status_opened():
    assert parse_kprs_status("Pilih kelas dari penawaran berikut") is True
    assert parse_kprs_status("Daftar kelas tersedia: SIA301") is True


def test_parse_kprs_status_unknown():
    assert parse_kprs_status("Status Pengisian KRS") is None


def test_fingerprint_changes_with_kprs_opened():
    base = ("SIA301", "SID303")
    closed = krs_fingerprint(KrsAnnouncement("2026-08-10", "2026-08-20"), base, False)
    opened = krs_fingerprint(KrsAnnouncement("2026-08-10", "2026-08-20"), base, True)
    assert closed != opened
    assert krs_fingerprint(
        KrsAnnouncement("2026-08-10", "2026-08-20"), base, False
    ) == closed


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
    assert _next_interval({"enabled": True, "in_window": True}, store) == 7
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
async def test_tick_session_expired_triggers_login_captcha_once(monkeypatch, store):
    from app.xninetzy.os.academic.mahasiswa_portal.reader import (
        AcademicPortalReadError,
    )

    store.set_enabled(True, 600)
    notifications = []
    login_calls = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def fake_capture():
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )

    async def fake_login_request():
        login_calls.append(1)

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.notify_admin",
        fake_notify,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.capture_krs_signal",
        fake_capture,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher._request_login_captcha",
        fake_login_request,
    )
    result = await krs_watcher_tick()
    assert result["expired"] is True
    assert login_calls == [1]
    assert notifications == []
    assert store.get()["session_expired_notified"] == 1
    result = await krs_watcher_tick()
    assert login_calls == [1]
    assert notifications == []
    store.set_enabled(False)


@pytest.mark.asyncio
async def test_tick_session_expired_retriggers_after_recovery(monkeypatch, store):
    from app.xninetzy.os.academic.mahasiswa_portal.reader import (
        AcademicPortalReadError,
    )

    store.set_enabled(True, 600)
    notifications = []
    login_calls = []
    healthy = False

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def fake_capture():
        if healthy:
            return KrsWatchSignal(
                announcement=KrsAnnouncement("2026-08-10", "2026-08-20"),
                mk_count=5,
                fingerprint="fp-ok",
            )
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )

    async def fake_login_request():
        login_calls.append(1)

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.notify_admin",
        fake_notify,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.capture_krs_signal",
        fake_capture,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher._request_login_captcha",
        fake_login_request,
    )
    result = await krs_watcher_tick()
    assert result["expired"] is True
    assert login_calls == [1]
    assert store.get()["session_expired_notified"] == 1
    healthy = True
    result = await krs_watcher_tick()
    assert result["enabled"] is True
    assert store.get()["session_expired_notified"] == 0
    healthy = False
    result = await krs_watcher_tick()
    assert result["expired"] is True
    assert login_calls == [1, 1]
    assert store.get()["session_expired_notified"] == 1
    store.set_enabled(False)


@pytest.mark.asyncio
async def test_tick_session_expired_falls_back_to_notify(monkeypatch, store):
    from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
        CampusLoginError,
    )
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

    async def fake_login_request():
        raise CampusLoginError("Gagal membuat challenge.")

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.notify_admin",
        fake_notify,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.capture_krs_signal",
        fake_capture,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher._request_login_captcha",
        fake_login_request,
    )
    result = await krs_watcher_tick()
    assert result["expired"] is True
    assert notifications == ["krs_watcher_session_expired"]
    assert store.get()["session_expired_notified"] == 1
    result = await krs_watcher_tick()
    assert notifications == ["krs_watcher_session_expired"]
    store.set_enabled(False)


@pytest.mark.asyncio
async def test_request_login_captcha_sends_image(monkeypatch):
    sent = {}

    async def fake_send_image(tool_name, input_data):
        sent.update(input_data)
        return {"ok": True}

    class FakeCoordinator:
        def __init__(self):
            self.started = []

        async def start(self, owner_id):
            self.started.append(owner_id)
            return {
                "challenge_id": "ch-abc123",
                "expires_at": "2026-08-04T10:00:00+00:00",
            }

        async def captcha_png(self, challenge_id, owner_id):
            return b"\x89PNG\r\n\x1a\n-fake"

        async def cancel(self, challenge_id, owner_id):
            return True

    fake_coordinator = FakeCoordinator()
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.LOGIN_COORDINATOR",
        fake_coordinator,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.admin_jid",
        lambda: "62812345678@s.whatsapp.net",
    )
    monkeypatch.setattr(
        "app.xninetzy.interfaces.whatsapp.client.call_wa_tool",
        fake_send_image,
    )
    await _request_login_captcha()
    assert fake_coordinator.started == ["62812345678@s.whatsapp.net"]
    assert sent["jid"] == "62812345678@s.whatsapp.net"
    assert "ch-abc123" in sent["caption"]


@pytest.mark.asyncio
async def test_request_login_captcha_cancels_on_send_failure(monkeypatch):
    from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
        CampusLoginError,
    )
    from app.xninetzy.interfaces.whatsapp.client import WaToolError

    cancelled = []

    async def fake_send_image(tool_name, input_data):
        raise WaToolError("WA down")

    class FakeCoordinator:
        async def start(self, owner_id):
            return {
                "challenge_id": "ch-fail",
                "expires_at": "2026-08-04T10:00:00+00:00",
            }

        async def captcha_png(self, challenge_id, owner_id):
            return b"png"

        async def cancel(self, challenge_id, owner_id):
            cancelled.append(challenge_id)
            return True

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.LOGIN_COORDINATOR",
        FakeCoordinator(),
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_watcher.admin_jid",
        lambda: "62812345678@s.whatsapp.net",
    )
    monkeypatch.setattr(
        "app.xninetzy.interfaces.whatsapp.client.call_wa_tool",
        fake_send_image,
    )
    with pytest.raises(CampusLoginError):
        await _request_login_captcha()
    assert cancelled == ["ch-fail"]
