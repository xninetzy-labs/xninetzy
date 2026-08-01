from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.academic.mahasiswa_portal.krs_war import (
    KrsPlan,
    KrsPlanCourse,
    KrsWarCalibrationStore,
    KrsWarStore,
    _classes_to_try,
    auto_calibrate_if_needed,
    krs_war_status_text,
    parse_krs_plan_markdown,
    run_krs_war_if_armed,
)
from app.xninetzy.os.academic.mahasiswa_portal.krs_watcher import KrsAnnouncement
from app.xninetzy.os.notifications.notification_policy import (
    ADMIN_EVENTS,
    should_notify_admin,
)
from app.xninetzy.os.notifications.notification_templates import (
    format_admin_notification,
)

PLAN_TEXT = """# KRS Plan Semester 5

| # | MK | Kode | SKS | Kelas Target |
|---|---|---|---|---|
| 1 | Kewirausahaan & Bisnis SI | MNW409 | 2 | I1 |
| 2 | PAP Praktikum | SIA302 | 1 | I1 |
"""

ANNOUNCEMENT = KrsAnnouncement("2026-08-10", "2026-08-20")
WINDOW = "2026-08-10|2026-08-20"
NOW = datetime(2026, 8, 14, 9, 0, tzinfo=UTC)

FRAGMENT_HTML = (
    "<table><tr><td>1</td><td>MNW409</td><td>Kewirausahaan</td>"
    "<td><a href='proses/_akademik-krs-simpan.php?aksi=tambah&kode=MNW409'>Ambil</a></td></tr></table>"
)


@pytest.fixture
def store(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "krs-calibration.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    return KrsWarStore()


def _plan() -> KrsPlan:
    return parse_krs_plan_markdown(PLAN_TEXT, source_path="Akademik/KRS_Plan_Semester_5.md")


def test_calibration_store_roundtrip(store):
    cal = KrsWarCalibrationStore()
    targets = {
        "MNW409": (
            "https://mahasiswa.unair.ac.id/proses/_akademik-krs-simpan.php"
            "?aksi=tambah&kode=MNW409"
        )
    }
    cal.save(WINDOW, targets, "fragment_bs4", "ok", 1)
    row = cal.get(WINDOW)
    assert row is not None
    assert row["window"] == WINDOW
    assert json.loads(row["targets_json"]) == targets
    assert row["strategy"] == "fragment_bs4"
    assert row["target_count"] == 1
    assert row["status"] == "ok"
    assert row["attempts"] == 1
    assert row["last_attempt_at"] is not None
    cal.save(WINDOW, {}, "none", "empty", 3)
    row = cal.get(WINDOW)
    assert row["attempts"] == 3
    assert row["target_count"] == 0
    assert json.loads(row["targets_json"]) == {}
    assert cal.bump_attempt(WINDOW) == 4
    assert cal.get(WINDOW)["attempts"] == 4
    assert cal.get("other-window") is None


@pytest.mark.asyncio
async def test_auto_calibrate_skips_when_no_window(store):
    result = await auto_calibrate_if_needed(
        announcement=None, store=KrsWarCalibrationStore()
    )
    assert result["calibration"]["skipped"] == "no_window"


@pytest.mark.asyncio
async def test_auto_calibrate_skips_already_calibrated(store, monkeypatch):
    cal = KrsWarCalibrationStore()
    cal.save(WINDOW, {"MNW409": "url"}, "dom", "ok", 1)

    class FakeSessionManager:
        def load_storage_state(self, site_slug):
            raise AssertionError("browser must not be opened")

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.SessionManager",
        FakeSessionManager,
    )
    result = await auto_calibrate_if_needed(announcement=ANNOUNCEMENT, store=cal)
    assert result["calibration"]["skipped"] == "already_calibrated"
    assert result["calibration"]["window"] == WINDOW
    assert result["calibration"]["strategy"] == "dom"
    assert result["calibration"]["target_count"] == 1


@pytest.mark.asyncio
async def test_auto_calibrate_skips_at_max_attempts(store, monkeypatch):
    cal = KrsWarCalibrationStore()
    cal.save(WINDOW, {}, "none", "empty", 8)

    class FakeSessionManager:
        def load_storage_state(self, site_slug):
            raise AssertionError("browser must not be opened")

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.SessionManager",
        FakeSessionManager,
    )
    result = await auto_calibrate_if_needed(announcement=ANNOUNCEMENT, store=cal)
    assert result["calibration"]["skipped"] == "max_attempts"
    assert result["calibration"]["attempts"] == 8


class FakeResponse:
    status = 200


class FakePage:
    def __init__(self, panel_endpoints, fragment_html):
        self.urls = []
        self.panel_endpoints = panel_endpoints
        self.fragment_html = fragment_html

    async def goto(self, url, **kwargs):
        self.urls.append(url)
        return FakeResponse()

    async def content(self):
        return "<html><body>OK</body></html>"

    async def evaluate(self, script, arg=None):
        if "codePattern" in script:
            return {}
        if "const found = []" in script:
            return self.panel_endpoints
        return self.fragment_html


@pytest.mark.asyncio
async def test_auto_calibrate_ok_via_fragment_path(store, monkeypatch):
    page = FakePage(
        panel_endpoints=["proses/_akademik-penawaran_tampil.php"],
        fragment_html=FRAGMENT_HTML,
    )

    async def fake_open():
        return None, None, None, page

    notifications = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append((event_type, payload))
        return True

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._open_krs_page",
        fake_open,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin",
        fake_notify,
    )
    result = await auto_calibrate_if_needed(
        announcement=ANNOUNCEMENT, store=KrsWarCalibrationStore()
    )
    cal = result["calibration"]
    assert cal["status"] == "ok"
    assert cal["strategy"] == "fragment_bs4"
    assert cal["target_count"] == 1
    assert cal["attempts"] == 1
    assert cal["window"] == WINDOW
    assert notifications == [("krs_war_calibrated", {"window": WINDOW, "strategy": "fragment_bs4", "target_count": 1, "status": "ok"})]
    row = KrsWarCalibrationStore().get(WINDOW)
    assert row is not None
    assert row["target_count"] == 1
    assert json.loads(row["targets_json"])["MNW409"].endswith("kode=MNW409")


@pytest.mark.asyncio
async def test_auto_calibrate_empty_no_notification(store, monkeypatch):
    page = FakePage(panel_endpoints=[], fragment_html="<html><body>kosong</body></html>")

    async def fake_open():
        return None, None, None, page

    notifications = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._open_krs_page",
        fake_open,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin",
        fake_notify,
    )
    result = await auto_calibrate_if_needed(
        announcement=ANNOUNCEMENT, store=KrsWarCalibrationStore()
    )
    cal = result["calibration"]
    assert cal["status"] == "empty"
    assert cal["strategy"] == "none"
    assert cal["target_count"] == 0
    assert cal["attempts"] == 1
    assert notifications == []
    row = KrsWarCalibrationStore().get(WINDOW)
    assert row is not None
    assert row["status"] == "empty"
    assert row["attempts"] == 1


@pytest.mark.asyncio
async def test_auto_calibrate_retries_after_empty(store, monkeypatch):
    page = FakePage(
        panel_endpoints=["proses/_akademik-penawaran_tampil.php"],
        fragment_html=FRAGMENT_HTML,
    )

    async def fake_open():
        return None, None, None, page

    notifications = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    cal = KrsWarCalibrationStore()
    cal.save(WINDOW, {}, "none", "empty", 3)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._open_krs_page",
        fake_open,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin",
        fake_notify,
    )
    result = await auto_calibrate_if_needed(announcement=ANNOUNCEMENT, store=cal)
    assert result["calibration"]["status"] == "ok"
    assert result["calibration"]["attempts"] == 4
    assert "krs_war_calibrated" in notifications


def test_classes_to_try_dedup_order(store):
    plan = _plan()
    assert _classes_to_try(plan.find("SIA302")) == ("I1", "I2", "I3", "I4")
    assert _classes_to_try(plan.find("MNW409")) == ("I1", "I2")
    dup = KrsPlanCourse("X1", "x", "2", "I1", ("I1", "I2"))
    assert _classes_to_try(dup) == ("I1", "I2")


@pytest.mark.asyncio
async def test_run_war_partial_retries_then_done(monkeypatch, store):
    store.set_armed(True, _plan())
    calls = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        return True

    async def fake_append(vault_service, result, window, now):
        return None

    async def partial_take(plan, window, dry_run=False, store=None):
        calls.append(window)
        return {
            "window": window,
            "status": "done",
            "taken": [],
            "already_taken": [],
            "skipped": [{"code": "SIA302", "reason": "target not found"}],
            "final_taken_codes": [],
            "dry_run": False,
            "summary": f"KRS war {window}: skipped=1",
        }

    async def ok_take(plan, window, dry_run=False, store=None):
        calls.append(window)
        return {
            "window": window,
            "status": "done",
            "taken": [],
            "already_taken": [],
            "skipped": [],
            "final_taken_codes": [],
            "dry_run": False,
            "summary": f"KRS war {window}: taken=0",
        }

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin",
        fake_notify,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._append_war_log",
        fake_append,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.take_krs_plan",
        partial_take,
    )
    first = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert first["war"]["status"] == "done"
    assert store.get()["last_status"] == "partial"
    assert calls == [WINDOW]
    second = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert second["war"]["status"] == "done"
    assert calls == [WINDOW, WINDOW]
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.take_krs_plan",
        ok_take,
    )
    third = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert third["war"]["status"] == "done"
    assert store.get()["last_status"] == "done"
    fourth = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert fourth == {"war": {"skipped": "already_run", "window": WINDOW}}


@pytest.mark.asyncio
async def test_run_war_verify_failed_is_partial(monkeypatch, store):
    store.set_armed(True, _plan())
    calls = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        return True

    async def fake_append(vault_service, result, window, now):
        return None

    async def partial_take(plan, window, dry_run=False, store=None):
        calls.append(window)
        return {
            "window": window,
            "status": "done",
            "taken": [],
            "already_taken": [],
            "skipped": [{"code": "SIA302", "reason": "verify failed"}],
            "final_taken_codes": [],
            "dry_run": False,
            "summary": f"KRS war {window}: skipped=1",
        }

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin",
        fake_notify,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._append_war_log",
        fake_append,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.take_krs_plan",
        partial_take,
    )
    await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert store.get()["last_status"] == "partial"


@pytest.mark.asyncio
async def test_status_text_includes_calibration(store):
    KrsWarCalibrationStore().save(WINDOW, {"MNW409": "url"}, "fragment_bs4", "ok", 2)
    text = await krs_war_status_text()
    assert "Calibration" in text
    assert WINDOW in text
    assert "targets: 1" in text
    assert "attempts: 2" in text


def test_calibrated_notification_policy_and_template():
    assert "krs_war_calibrated" in ADMIN_EVENTS
    assert should_notify_admin("krs_war_calibrated", "high") is True
    text = format_admin_notification(
        "krs_war_calibrated",
        {"window": WINDOW, "strategy": "dom", "target_count": 5, "status": "ok"},
    )
    assert "KRS War Kalibrasi" in text
    assert WINDOW in text
    assert "Strategi: dom" in text
    assert "Target ditemukan: 5 MK" in text
    assert "Status: ok" in text
