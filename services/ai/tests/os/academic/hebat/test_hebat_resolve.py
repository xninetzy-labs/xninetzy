"""Offline unit tests for HEBAT activity identifier resolution by name/cmid."""

from __future__ import annotations

from uuid import uuid4

from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.academic.hebat.models import ActivityType, HebatActivity
from app.xninetzy.os.academic.hebat.storage import (
    resolve_activity_by_identifier,
    upsert_activity,
)
from app.xninetzy.os.academic.hebat.tools import _resolve_activity_cmid


def _seed_activity(cmid: str, title: str, activity_type: ActivityType) -> int:
    return upsert_activity(
        HebatActivity(
            course_id="course-resolve-test",
            cmid=cmid,
            type=activity_type,
            title=title,
            activity_url=(
                f"https://hebat.elearning.unair.ac.id/mod/"
                f"{activity_type.value}/view.php?id={cmid}"
            ),
        )
    )


def test_resolve_by_cmid_digit():
    init_db()
    run_migrations()
    marker = str(uuid4().int)[:8]
    cmid = f"99{marker}"
    _seed_activity(cmid, f"Tugas {marker}", ActivityType.ASSIGN)
    resolved = resolve_activity_by_identifier(cmid)
    assert resolved is not None
    assert resolved["cmid"] == cmid


def test_resolve_by_exact_title_case_insensitive():
    init_db()
    run_migrations()
    marker = str(uuid4().int)[:8]
    _seed_activity(f"51{marker}", f"Tugas Data Exploration {marker}", ActivityType.ASSIGN)
    resolved = resolve_activity_by_identifier(
        f"tugas data exploration {marker}", activity_type="assign"
    )
    assert resolved is not None
    assert resolved["type"] == "assign"


def test_resolve_by_partial_title_with_type_filter():
    init_db()
    run_migrations()
    marker = str(uuid4().int)[:8]
    _seed_activity(f"52{marker}", f"Data Exploration {marker} Assignment", ActivityType.ASSIGN)
    _seed_activity(f"53{marker}", f"Data Exploration {marker} File", ActivityType.RESOURCE)
    resolved_assign = resolve_activity_by_identifier(
        f"data exploration {marker}", activity_type="assign"
    )
    resolved_resource = resolve_activity_by_identifier(
        f"data exploration {marker}", activity_type="resource"
    )
    assert resolved_assign is not None
    assert resolved_assign["type"] == "assign"
    assert resolved_resource is not None
    assert resolved_resource["type"] == "resource"


def test_resolve_unknown_returns_none():
    init_db()
    run_migrations()
    assert resolve_activity_by_identifier("tidak ada tugas ini 123xyz") is None


def test_tool_resolve_accepts_url_cmid_and_name():
    init_db()
    run_migrations()
    marker = str(uuid4().int)[:8]
    cmid = f"54{marker}"
    _seed_activity(cmid, f"Tugas Resolve {marker}", ActivityType.ASSIGN)

    by_url = _resolve_activity_cmid(
        f"https://hebat.elearning.unair.ac.id/mod/assign/view.php?id={cmid}",
        activity_type="assign",
    )
    assert by_url is not None
    assert by_url[0] == cmid

    by_cmid = _resolve_activity_cmid(cmid, activity_type="assign")
    assert by_cmid is not None
    assert by_cmid[0] == cmid
    assert by_cmid[1].endswith(f"/mod/assign/view.php?id={cmid}")

    by_name = _resolve_activity_cmid(f"Tugas Resolve {marker}", activity_type="assign")
    assert by_name is not None
    assert by_name[0] == cmid
    assert by_name[1] == (
        f"https://hebat.elearning.unair.ac.id/mod/assign/view.php?id={cmid}"
    )


def test_tool_resolve_unknown_returns_none():
    init_db()
    run_migrations()
    assert _resolve_activity_cmid("nama tugas tidak dikenal", activity_type="assign") is None
