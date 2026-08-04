from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.os.academic.mahasiswa_portal.krs_war import (
    KrsPlan,
    KrsWarStore,
    _classes_to_try,
    _extract_take_targets,
    _is_flexible_goal,
    _read_plan_file_text,
    _upgrade_cooldown_ok,
    _with_class_param,
    load_krs_plan,
    parse_krs_plan_markdown,
    plan_from_json,
    plan_to_json,
    run_krs_war_if_armed,
)
from app.xninetzy.os.academic.mahasiswa_portal.krs_watcher import KrsAnnouncement

PLAN_TEXT = """---
tags: [akademik, krs, semester5]
---

# KRS Plan Semester 5 — Ganjil 2026/2027

| # | MK | Kode | SKS | Dosen | Kelas Target |
|---|---|---|---|---|---|
| 1 | Kewirausahaan & Bisnis SI | MNW409 | 2 | Barry Nugoba | I1 |
| 2 | Perencanaan Arsitektur Perusahaan (PAP) | SIA301 | 2 | Ira Puspitasari | I1 |
| 3 | PAP Praktikum | SIA302 | 1 | Eva Hariyanti, Nania Nuzulita | I1 |
| 4 | Desain Interaksi | SII208 | 2 | Endah Purwanti, Nania Nuzulita | I1 |
| 5 | Desain Interaksi Praktikum | SII209 | 1 | Barry Nugoba | I1 |
| 6 | Pembangunan Perangkat Lunak (PPL) | SIB18 | 2 | Dr. Indra Kharisma | I1 |
| 7 | PPL Praktikum | SII319 | 1 | Dr. Indra Kharisma | I1 |
| 8 | Keamanan Sistem Informasi | SIS309 | 3 | Taufik | I1 |

Matematika Diskrit (MAL204) dibuang — sudah pernah diambil (nilai AB).
| - | Matematika Diskrit | MAL204 | 2 | Faried Effendy | I | ⛔ tidak diambil |
"""

ANNOUNCEMENT = KrsAnnouncement("2026-08-10", "2026-08-20")
NOW = datetime(2026, 8, 14, 9, 0, tzinfo=UTC)


@pytest.fixture
def store(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "krs-war.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    return KrsWarStore()


def _plan() -> KrsPlan:
    return parse_krs_plan_markdown(PLAN_TEXT, source_path="Akademik/KRS_Plan_Semester_5.md")


def test_parse_plan_courses_allowlist_and_find():
    plan = _plan()
    codes = [course.code for course in plan.courses]
    assert codes == [
        "MNW409",
        "SIA301",
        "SIA302",
        "SII208",
        "SII209",
        "SIB18",
        "SII319",
        "SIS309",
    ]
    assert "MAL204" not in plan.allowlist()
    assert plan.allowlist() == frozenset(codes)
    assert plan.source_path == "Akademik/KRS_Plan_Semester_5.md"
    assert plan.semester_label == "Semester 5"
    assert plan.find("SIA301") is not None
    assert plan.find("SIA301").name == "Perencanaan Arsitektur Perusahaan (PAP)"
    assert plan.find("MAL204") is None
    assert plan.find("TIDAKADA") is None


def test_parse_plan_fallbacks():
    plan = _plan()
    assert plan.find("SIA302").fallback_classes == ("I2", "I3", "I4")
    assert plan.find("SII209").fallback_classes == ("I2", "I3", "I4")
    assert plan.find("SII319").fallback_classes == ("I2", "I3", "I4")
    assert plan.find("MNW409").fallback_classes == ("I2",)
    assert plan.find("SIS309").fallback_classes == ("I2",)
    assert plan.find("SIA302").credits == "1"
    assert plan.find("SIS309").credits == "3"
    assert plan.find("SIA302").target_class == "I1"


def test_parse_plan_hash_deterministic():
    first = parse_krs_plan_markdown(PLAN_TEXT)
    second = parse_krs_plan_markdown(PLAN_TEXT + "\n")
    changed = parse_krs_plan_markdown(PLAN_TEXT.replace("MNW409", "MNW410"))
    assert first.source_hash == second.source_hash
    assert first.source_hash != changed.source_hash


def test_parse_plan_without_table_rows():
    plan = parse_krs_plan_markdown("# KRS Plan Semester 5\n\nTidak ada tabel.\n")
    assert plan.courses == ()
    assert plan.semester_label == "Semester 5"


def test_plan_json_roundtrip():
    plan = _plan()
    restored = plan_from_json(plan_to_json(plan))
    assert restored is not None
    assert restored == plan


def test_plan_from_json_invalid():
    assert plan_from_json("") is None
    assert plan_from_json("not json") is None


def test_with_class_param_adds_and_replaces():
    url = "https://mahasiswa.unair.ac.id/proses/_akademik-krs-simpan.php?aksi=tambah&kode=SIA301"
    assert _with_class_param(url, "I1") == f"{url}&kelas=I1"
    replaced = url + "&kelas=I2"
    assert _with_class_param(replaced, "I1") == f"{url}&kelas=I1"


def test_extract_take_targets_from_fragment():
    html = (
        "<table>"
        "<tr><td>1</td><td>MNW409</td><td>Kewirausahaan</td>"
        "<td><a href='proses/_akademik-krs-simpan.php?aksi=tambah&kode=MNW409'>Ambil</a></td></tr>"
        "<tr><td>2</td><td>SIA301</td><td>PAP</td>"
        "<td><a href='proses/_akademik-krs-simpan.php?aksi=tambah&kode=SIA301'>Ambil</a></td></tr>"
        "</table>"
    )
    targets = _extract_take_targets(html, "https://mahasiswa.unair.ac.id")
    assert targets == {
        "MNW409": (
            "https://mahasiswa.unair.ac.id/proses/_akademik-krs-simpan.php"
            "?aksi=tambah&kode=MNW409"
        ),
        "SIA301": (
            "https://mahasiswa.unair.ac.id/proses/_akademik-krs-simpan.php"
            "?aksi=tambah&kode=SIA301"
        ),
    }


def test_store_default_state(store):
    state = store.get()
    assert state["armed"] == 0
    assert state["plan_hash"] is None
    assert state["last_status"] == "idle"
    assert state["last_run_window"] is None


def test_store_armed_roundtrip(store):
    plan = _plan()
    store.set_armed(True, plan)
    state = store.get()
    assert state["armed"] == 1
    assert state["plan_hash"] == plan.source_hash
    assert state["plan_json"] == plan_to_json(plan)
    assert state["last_armed_at"] is not None
    store.set_armed(False)
    state = store.get()
    assert state["armed"] == 0
    assert state["plan_hash"] == plan.source_hash


def test_store_update_run(store):
    store.update_run(
        window="2026-08-10|2026-08-20", status="done", summary="taken=2"
    )
    state = store.get()
    assert state["last_run_window"] == "2026-08-10|2026-08-20"
    assert state["last_status"] == "done"
    assert state["last_summary"] == "taken=2"
    assert state["last_run_at"] is not None


def test_store_record_action(store):
    store.record_action("w1", "taken", "SIA301", "I1", "detail x")
    store.record_action("w1", "take_skipped", "SIB18", "", "target not found")
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT action, course_code, class_code, detail, window
            FROM krs_war_actions ORDER BY id
            """
        ).fetchall()
    assert len(rows) == 2
    assert rows[0]["window"] == "w1"
    assert rows[0]["action"] == "taken"
    assert rows[0]["course_code"] == "SIA301"
    assert rows[0]["class_code"] == "I1"
    assert rows[1]["action"] == "take_skipped"
    assert rows[1]["detail"] == "target not found"


@pytest.mark.asyncio
async def test_load_plan_db_fallback(monkeypatch, store):
    plan = _plan()
    store.set_armed(True, plan)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._read_plan_file_text",
        lambda vault_service: None,
    )
    loaded = await load_krs_plan(store=store)
    assert loaded is not None
    assert loaded.source_hash == plan.source_hash
    assert loaded.courses == plan.courses


@pytest.mark.asyncio
async def test_load_plan_file_wins_on_change(monkeypatch, store):
    plan = _plan()
    store.set_armed(True, plan)
    changed_text = PLAN_TEXT.replace("MNW409", "MNW410")
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._read_plan_file_text",
        lambda vault_service: changed_text,
    )
    loaded = await load_krs_plan(store=store)
    assert loaded is not None
    assert loaded.source_hash != plan.source_hash
    assert loaded.find("MNW410") is not None


@pytest.mark.asyncio
async def test_load_plan_none_when_unreadable_and_no_db(monkeypatch, store):
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._read_plan_file_text",
        lambda vault_service: None,
    )
    assert await load_krs_plan(store=store) is None


@pytest.mark.asyncio
async def test_load_plan_empty_file_falls_back_to_db(monkeypatch, store):
    plan = _plan()
    store.set_armed(True, plan)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._read_plan_file_text",
        lambda vault_service: "# KRS Plan Semester 5\n\nno table\n",
    )
    loaded = await load_krs_plan(store=store)
    assert loaded is not None
    assert loaded.source_hash == plan.source_hash


@pytest.mark.asyncio
async def test_run_skipped_when_not_armed(monkeypatch, store):
    notifications = []
    calls = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def fake_take(plan, window, dry_run=False, store=None):
        calls.append(window)
        return {"status": "done", "taken": [], "already_taken": [], "skipped": [], "summary": "ok"}

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin", fake_notify
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.take_krs_plan", fake_take
    )
    result = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert result == {"war": {"skipped": "not_armed"}}
    assert calls == []
    assert notifications == []


@pytest.mark.asyncio
async def test_run_skipped_when_no_window(store):
    store.set_armed(True, _plan())
    result = await run_krs_war_if_armed(now=NOW, store=store)
    assert result == {"war": {"skipped": "no_window"}}


@pytest.mark.asyncio
async def test_run_once_per_window(monkeypatch, store):
    store.set_armed(True, _plan())
    notifications = []
    calls = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def fake_take(plan, window, dry_run=False, store=None):
        calls.append(window)
        return {
            "window": window,
            "status": "done",
            "taken": [{"code": "SIS309", "class": "I1"}],
            "already_taken": ["SIA301"],
            "skipped": [{"code": "SIA302", "reason": "not in allowlist"}],
            "final_taken_codes": ["SIA301", "SIS309"],
            "dry_run": False,
            "summary": f"KRS war {window}: taken=1, already_taken=1, skipped=1",
        }

    async def fake_append(vault_service, result, window, now):
        return None

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin", fake_notify
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.take_krs_plan", fake_take
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._append_war_log", fake_append
    )
    first = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert first["war"]["status"] == "done"
    assert first["war"]["taken"] == [{"code": "SIS309", "class": "I1"}]
    second = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert second == {"war": {"skipped": "already_run", "window": "2026-08-10|2026-08-20"}}
    assert calls == ["2026-08-10|2026-08-20"]
    assert "krs_war_started" in notifications
    assert "krs_war_taken" in notifications
    assert store.get()["last_status"] == "done"
    assert store.get()["last_run_window"] == "2026-08-10|2026-08-20"


@pytest.mark.asyncio
async def test_run_error_retries_next_tick(monkeypatch, store):
    store.set_armed(True, _plan())
    notifications = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def failing_take(plan, window, dry_run=False, store=None):
        raise RuntimeError("boom")

    async def ok_take(plan, window, dry_run=False, store=None):
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

    async def fake_append(vault_service, result, window, now):
        return None

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin", fake_notify
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.take_krs_plan", failing_take
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war._append_war_log", fake_append
    )
    result = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert result["war"]["status"] == "error"
    assert "boom" in result["war"]["error"]
    assert store.get()["last_status"] == "error"
    assert "krs_war_error" in notifications
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.take_krs_plan", ok_take
    )
    retried = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert retried["war"]["status"] == "done"


@pytest.mark.asyncio
async def test_run_no_plan_fails_closed(monkeypatch, store):
    store.set_armed(True, _plan())
    notifications = []

    async def fake_notify(event_type, payload=None, impact="medium"):
        notifications.append(event_type)
        return True

    async def fake_load(vault_service=None, store=None):
        return None

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.notify_admin", fake_notify
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.load_krs_plan", fake_load
    )
    result = await run_krs_war_if_armed(now=NOW, announcement=ANNOUNCEMENT, store=store)
    assert result == {"war": {"skipped": "no_plan"}}
    assert "krs_war_error" in notifications
    assert store.get()["last_status"] == "error"


def test_parse_plan_bae112_multiclass():
    text = (
        "# KRS Plan Semester 5\n\n"
        "| # | MK | Kode | SKS | Dosen | Kelas Target |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | Bahasa Inggris II | BAE112 | 2 | UPT Bahasa | BCDLITS6, BCDLITS5, BCDLITS4, BCDLITS3 |\n"
    )
    plan = parse_krs_plan_markdown(text)
    course = plan.find("BAE112")
    assert course is not None
    assert course.target_class == "BCDLITS6"
    assert course.fallback_classes == ("BCDLITS5", "BCDLITS4", "BCDLITS3")


def test_classes_to_try_bae112_always_safe_order():
    course = parse_krs_plan_markdown(
        "# KRS Plan Semester 5\n\n"
        "| # | MK | Kode | SKS | Dosen | Kelas Target |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | Bahasa Inggris II | BAE112 | 2 | UPT Bahasa | BCDLITS2, BCDLITS1 |\n"
    ).find("BAE112")
    assert _is_flexible_goal(course) is True
    assert _classes_to_try(course) == (
        "BCDLITS6",
        "BCDLITS5",
        "BCDLITS4",
        "BCDLITS3",
    )


def test_classes_to_try_regular_course_keeps_goal_order():
    course = parse_krs_plan_markdown(
        "# KRS Plan Semester 5\n\n"
        "| # | MK | Kode | SKS | Dosen | Kelas Target |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | Kewirausahaan & Bisnis SI | MNW409 | 2 | Barry Nugoba | I2 |\n"
    ).find("MNW409")
    assert _is_flexible_goal(course) is False
    assert _classes_to_try(course) == ("I2",)


def test_read_plan_file_falls_back_to_container_vault(monkeypatch, tmp_path):
    vault_dir = tmp_path / "obsidian-vault"
    vault_dir.mkdir()
    plan_file = vault_dir / "Akademik"
    plan_file.mkdir()
    (plan_file / "KRS_Plan_Semester_5.md").write_text(
        "# KRS Plan Semester 5\n\n| kode | kelas |\n| BAE112 | BCDLITS6 |\n",
        encoding="utf-8",
    )

    class FakeSettings:
        OBSIDIAN_VAULT_HOST_PATH = "/nonexistent-host-path"
        OBSIDIAN_VAULT_PATH = str(vault_dir)

    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.krs_war.get_settings",
        lambda: FakeSettings(),
    )
    text = _read_plan_file_text(None)
    assert text is not None
    assert "BAE112" in text


def test_upgrade_cooldown(store):
    assert _upgrade_cooldown_ok(store, "w1", "SII209") is True
    store.record_action("w1", "upgrade_attempt", "SII209", "I2")
    assert _upgrade_cooldown_ok(store, "w1", "SII209") is False
    assert _upgrade_cooldown_ok(store, "w1", "MNW409") is True
