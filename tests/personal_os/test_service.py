from __future__ import annotations

import os
from pathlib import Path

import pytest

from xninetzy.context.personal_os import (
    LoopStatus,
    ProjectStatus,
    SkillStatus,
    generate_review,
    get_personal_os,
)
from xninetzy.context.personal_os.service import PersonalOS


@pytest.fixture
def personal_os(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PersonalOS:
    db_file = tmp_path / "personal.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg

    cfg.get_settings.cache_clear()
    import xninetzy.context.personal_os.service as svc

    svc._personal_os = None
    return get_personal_os()


def test_project_create_requires_next_action(personal_os: PersonalOS) -> None:
    p = personal_os.create_project(
        title="Ship data intelligence", objective="", next_action="add tests"
    )
    assert p.status == ProjectStatus.ACTIVE
    assert p.next_action == "add tests"


def test_project_list_filters_by_status(personal_os: PersonalOS) -> None:
    personal_os.create_project(title="A", next_action="x")
    personal_os.create_project(title="B", next_action="y")
    personal_os.update_project_status(
        next(p.project_id for p in personal_os.list_projects() if p.title == "A"),
        ProjectStatus.PAUSED,
    )
    active = personal_os.list_projects(status=ProjectStatus.ACTIVE)
    assert {p.title for p in active} == {"B"}


def test_open_loop_idempotent_on_title(personal_os: PersonalOS) -> None:
    a = personal_os.open_loop(title="decide BI provider")
    b = personal_os.open_loop(title="decide BI provider")
    assert a.loop_id == b.loop_id


def test_open_loop_resolve_removes_from_open_list(personal_os: PersonalOS) -> None:
    l = personal_os.open_loop(title="ship release")
    resolved = personal_os.resolve_loop(l.loop_id)
    assert resolved is not None
    assert resolved.status == LoopStatus.RESOLVED
    open_ids = {x.loop_id for x in personal_os.list_open_loops()}
    assert l.loop_id not in open_ids


def test_skill_register_idempotent_and_advance(personal_os: PersonalOS) -> None:
    s1 = personal_os.register_skill("polars")
    s2 = personal_os.register_skill("polars")
    assert s1.skill_id == s2.skill_id
    advanced = personal_os.advance_skill("polars", SkillStatus.PRACTICING)
    assert advanced.evidence_count == 1
    assert advanced.status == SkillStatus.PRACTICING


def test_review_detects_no_issues_when_clean(personal_os: PersonalOS) -> None:
    personal_os.create_project(title="only one", next_action="do it")
    review = generate_review("weekly")
    assert "No structural issues detected" in review.recommendations[0]


def test_review_detects_open_loop_overflow(personal_os: PersonalOS) -> None:
    for i in range(11):
        personal_os.open_loop(title=f"loop-{i}")
    review = generate_review("weekly")
    joined = " ".join(review.recommendations)
    assert "open loops" in joined


def test_review_detects_stalled_project(personal_os: PersonalOS) -> None:
    p = personal_os.create_project(title="stale", next_action="")
    personal_os.advance_skill("ignored", SkillStatus.UNKNOWN)
    import xninetzy.context.personal_os.service as svc

    with svc.connect() as conn:
        conn.execute(
            "UPDATE personal_projects SET last_activity=? WHERE project_id=?",
            ("2020-01-01T00:00:00+00:00", p.project_id),
        )
    review = generate_review("weekly")
    assert p.project_id in review.stalled_projects
