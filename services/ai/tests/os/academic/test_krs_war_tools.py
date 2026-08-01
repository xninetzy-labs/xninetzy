from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.ecosystem.command_router import (
    KRS_WAR_PATTERN,
    SLASH_COMMANDS,
    parse_command,
)
from app.xninetzy.os.academic.mahasiswa_portal import tools as portal_tools
from app.xninetzy.os.academic.mahasiswa_portal.krs_war import (
    KrsPlan,
    KrsPlanCourse,
    KrsWarStore,
    parse_krs_plan_markdown,
)
from app.xninetzy.os.notifications.notification_policy import (
    ADMIN_EVENTS,
    should_notify_admin,
)
from app.xninetzy.os.notifications.notification_templates import (
    format_admin_notification,
)
from app.xninetzy.tools.registry import get_all_tools, get_tool_groups

PLAN_TEXT = """# KRS Plan Semester 5

| # | MK | Kode | SKS | Kelas Target |
|---|---|---|---|---|
| 1 | Kewirausahaan & Bisnis SI | MNW409 | 2 | I1 |
| 2 | PAP Praktikum | SIA302 | 1 | I1 |
| 3 | Keamanan Sistem Informasi | SIS309 | 3 | I1 |
"""

WAR_TOOL_NAMES = [
    "portal_krs_war_status",
    "portal_krs_war_arm",
    "portal_krs_war_disarm",
    "portal_krs_war_plan",
    "portal_krs_war_dry_run",
]


@pytest.fixture
def store(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "krs-war-tools.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    return KrsWarStore()


def _plan() -> KrsPlan:
    return parse_krs_plan_markdown(
        PLAN_TEXT, source_path="Akademik/KRS_Plan_Semester_5.md"
    )


def test_war_tools_registered_in_registry():
    names = {tool.name for tool in get_all_tools()}
    for name in WAR_TOOL_NAMES:
        assert name in names
    groups = get_tool_groups()["academic"]
    for name in WAR_TOOL_NAMES:
        assert name in groups


def test_krs_war_slash_command_mapping():
    assert SLASH_COMMANDS["/krs-war"] == "portal_krs_war_status"
    assert parse_command("/krs-war") == ("portal_krs_war_status", {})
    assert parse_command("/krs-war status") == ("portal_krs_war_status", {})
    assert parse_command("/krs-war arm") == ("portal_krs_war_arm", {})
    assert parse_command("/krs-war disarm") == ("portal_krs_war_disarm", {})
    assert parse_command("/krs-war plan") == ("portal_krs_war_plan", {})
    assert parse_command("/krs-war dry-run") == ("portal_krs_war_dry_run", {})


def test_krs_war_pattern_matches_subcommands():
    for text in ["/krs-war", "/krs-war status", "/krs-war arm", "/krs-war disarm",
                 "/krs-war plan", "/krs-war dry-run", "/KRS-WAR ARM"]:
        assert KRS_WAR_PATTERN.match(text) is not None
    assert KRS_WAR_PATTERN.match("/krs-war foo") is None
    assert KRS_WAR_PATTERN.match("/krs-watcher") is None


def test_war_events_are_admin_notified():
    for event in ["krs_war_started", "krs_war_taken", "krs_war_error"]:
        assert event in ADMIN_EVENTS
        assert should_notify_admin(event, "high") is True


def test_war_notification_templates_render_payloads():
    started = format_admin_notification(
        "krs_war_started", {"window": "2026-08-10|2026-08-20", "courses": 8,
                            "semester": "Semester 5"}
    )
    assert "2026-08-10" in started and "8" in started
    taken = format_admin_notification(
        "krs_war_taken",
        {"window": "w", "taken": 1, "already_taken": 2, "skipped": 1,
         "summary": "KRS war w: taken=1"},
    )
    assert "Diambil: 1" in taken
    assert "Sudah terambil: 2" in taken
    assert "Dilewati: 1" in taken
    assert "KRS war w: taken=1" in taken
    error = format_admin_notification(
        "krs_war_error", {"window": "w", "error": "boom"}
    )
    assert "boom" in error


@pytest.mark.asyncio
async def test_arm_sets_armed_and_plan(monkeypatch, store):
    async def fake_load(vault_service=None, store=None):
        return _plan()

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: True)
    monkeypatch.setattr(portal_tools, "load_krs_plan", fake_load)

    result = await portal_tools.portal_krs_war_arm.ainvoke(
        {"chat_id": "chat", "sender_id": "628123@s.whatsapp.net"}
    )

    assert "KRS War Aktif" in result
    assert "3 MK, 6 SKS" in result
    state = store.get()
    assert state["armed"] == 1
    assert state["plan_hash"] == _plan().source_hash


@pytest.mark.asyncio
async def test_arm_denied_for_non_admin(monkeypatch, store):
    async def unexpected_load(vault_service=None, store=None):
        raise AssertionError("load_krs_plan must not be called for non-admin")

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: False)
    monkeypatch.setattr(portal_tools, "load_krs_plan", unexpected_load)

    result = await portal_tools.portal_krs_war_arm.ainvoke(
        {"chat_id": "chat", "sender_id": "stranger@s.whatsapp.net"}
    )

    assert "admin" in result
    assert store.get()["armed"] == 0


@pytest.mark.asyncio
async def test_arm_fails_closed_when_plan_missing(monkeypatch, store):
    async def fake_load(vault_service=None, store=None):
        return None

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: True)
    monkeypatch.setattr(portal_tools, "load_krs_plan", fake_load)

    result = await portal_tools.portal_krs_war_arm.ainvoke({})

    assert "tidak diaktifkan" in result
    assert store.get()["armed"] == 0


def test_disarm_sets_armed_off(monkeypatch, store):
    plan = _plan()
    store.set_armed(True, plan)
    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: True)

    result = portal_tools.portal_krs_war_disarm.invoke(
        {"chat_id": "chat", "sender_id": "628123@s.whatsapp.net"}
    )

    assert "dinonaktifkan" in result
    assert store.get()["armed"] == 0


def test_disarm_denied_for_non_admin(monkeypatch, store):
    store.set_armed(True, _plan())
    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: False)

    result = portal_tools.portal_krs_war_disarm.invoke(
        {"chat_id": "chat", "sender_id": "stranger@s.whatsapp.net"}
    )

    assert "admin" in result
    assert store.get()["armed"] == 1


@pytest.mark.asyncio
async def test_plan_lists_courses(monkeypatch, store):
    async def fake_load(vault_service=None, store=None):
        return _plan()

    monkeypatch.setattr(portal_tools, "load_krs_plan", fake_load)

    result = await portal_tools.portal_krs_war_plan.ainvoke({})

    assert "MNW409" in result
    assert "SIA302" in result
    assert "target I1" in result


@pytest.mark.asyncio
async def test_plan_reports_missing_plan(monkeypatch, store):
    async def fake_load(vault_service=None, store=None):
        return None

    monkeypatch.setattr(portal_tools, "load_krs_plan", fake_load)

    result = await portal_tools.portal_krs_war_plan.ainvoke({})

    assert "belum tersedia" in result


@pytest.mark.asyncio
async def test_dry_run_reports_would_take(monkeypatch, store):
    async def fake_load(vault_service=None, store=None):
        return _plan()

    async def fake_take(plan, window, dry_run=False, store=None):
        assert dry_run is True
        return {
            "window": window,
            "status": "done",
            "taken": [],
            "already_taken": ["SIA302"],
            "skipped": [{"code": "SIS309", "reason": "target not found"}],
            "final_taken_codes": ["SIA302"],
            "dry_run": True,
            "summary": f"KRS war {window}: taken=0, already_taken=1, skipped=1",
        }

    class FakeWatcherStore:
        def get(self):
            return {"last_announcement": "2026-08-10|2026-08-20"}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: True)
    monkeypatch.setattr(portal_tools, "load_krs_plan", fake_load)
    monkeypatch.setattr(portal_tools, "take_krs_plan", fake_take)
    monkeypatch.setattr(portal_tools, "KrsWatcherStore", FakeWatcherStore)

    result = await portal_tools.portal_krs_war_dry_run.ainvoke(
        {"chat_id": "chat", "sender_id": "628123@s.whatsapp.net"}
    )

    assert "Dry Run" in result
    assert "2026-08-10 s.d. 2026-08-20" in result
    assert "akan diambil → kelas I1" in result
    assert "sudah terambil" in result
    assert "dilewati: target not found" in result


@pytest.mark.asyncio
async def test_dry_run_uses_today_window_without_announcement(monkeypatch, store):
    async def fake_load(vault_service=None, store=None):
        return _plan()

    async def fake_take(plan, window, dry_run=False, store=None):
        return {
            "window": window,
            "status": "done",
            "taken": [],
            "already_taken": [],
            "skipped": [],
            "final_taken_codes": [],
            "dry_run": True,
            "summary": f"KRS war {window}: taken=0",
        }

    class EmptyWatcherStore:
        def get(self):
            return {"last_announcement": None}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: True)
    monkeypatch.setattr(portal_tools, "load_krs_plan", fake_load)
    monkeypatch.setattr(portal_tools, "take_krs_plan", fake_take)
    monkeypatch.setattr(portal_tools, "KrsWatcherStore", EmptyWatcherStore)

    result = await portal_tools.portal_krs_war_dry_run.ainvoke({})

    assert "Dry Run" in result
    assert "s.d." in result


@pytest.mark.asyncio
async def test_dry_run_returns_error_string_on_session_failure(monkeypatch, store):
    async def fake_load(vault_service=None, store=None):
        return _plan()

    async def failing_take(plan, window, dry_run=False, store=None):
        raise RuntimeError("Session Cyber Campus belum tersedia.")

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda s, n: True)
    monkeypatch.setattr(portal_tools, "load_krs_plan", fake_load)
    monkeypatch.setattr(portal_tools, "take_krs_plan", failing_take)

    result = await portal_tools.portal_krs_war_dry_run.ainvoke({})

    assert "Simulasi KRS War gagal" in result
    assert "belum tersedia" in result


def test_plan_summary_counts_credits():
    plan = KrsPlan(
        courses=(
            KrsPlanCourse(
                code="MNW409",
                name="Kewirausahaan",
                credits="2",
                target_class="I1",
                fallback_classes=("I2",),
            ),
            KrsPlanCourse(
                code="SIS309",
                name="Keamanan SI",
                credits="3",
                target_class="I1",
                fallback_classes=("I2",),
            ),
        ),
        source_path="p",
        source_hash="h",
        semester_label="Semester 5",
    )
    assert portal_tools._plan_summary(plan) == "2 MK, 5 SKS"
