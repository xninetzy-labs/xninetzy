from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.progress_tracker import (
    build_today_plan,
    get_roadmap_progress,
)
from app.xninetzy.domains.it_learning.roadmap_models import RoadmapDraft
from app.xninetzy.domains.it_learning.roadmap_store import (
    activate_roadmap,
    save_roadmap_draft,
)
from app.xninetzy.domains.it_learning.study_session import (
    complete_study_session,
    learning_start_study_session,
    start_study_session,
)
from app.xninetzy.interfaces.mcp_tool_adapter import (
    MCPPrincipal,
    langchain_tool_as_mcp_callable,
)


@pytest.fixture(autouse=True)
def isolated_learning_database(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "learning.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def _active_roadmap() -> int:
    roadmap_id = save_roadmap_draft(
        RoadmapDraft(
            topic="Graph RAG",
            duration_days=2,
            target="Build a grounded graph pipeline",
            milestones=["Understand", "Build"],
            first_day_tasks=["Explain graph retrieval", "Build one retriever"],
        ),
        chat_id="wa-owner",
    )
    assert activate_roadmap(roadmap_id)
    return roadmap_id


def test_start_session_is_idempotent_and_single_active():
    roadmap_id = _active_roadmap()

    first, first_created = start_study_session(
        roadmap_id=roadmap_id,
        planned_minutes=30,
        energy_before=4,
        idempotency_key="wa-message-1",
        chat_id="wa-owner",
    )
    repeated, repeated_created = start_study_session(
        roadmap_id=roadmap_id,
        planned_minutes=45,
        energy_before=2,
        idempotency_key="wa-message-1",
        chat_id="wa-owner",
    )
    concurrent, concurrent_created = start_study_session(
        roadmap_id=roadmap_id,
        idempotency_key="mcp-request-2",
        chat_id="mcp-owner",
    )

    assert first_created is True
    assert repeated_created is False
    assert concurrent_created is False
    assert first["id"] == repeated["id"] == concurrent["id"]
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM learning_study_sessions").fetchone()[
            0
        ]
    assert count == 1


def test_completion_is_idempotent_and_records_one_progress_event():
    roadmap_id = _active_roadmap()
    session, _ = start_study_session(
        roadmap_id=roadmap_id,
        objective="Explain hybrid retrieval",
        idempotency_key="session-completion",
        chat_id="wa-owner",
    )

    completed, changed = complete_study_session(
        session["id"],
        actual_minutes=28,
        mastery_after=0.72,
        energy_after=3,
        reflection="RRF masih perlu latihan",
        evidence=["note://graph-rag/rrf"],
    )
    repeated, repeated_changed = complete_study_session(
        session["id"], actual_minutes=99, mastery_after=1
    )

    assert changed is True
    assert repeated_changed is False
    assert completed["actual_minutes"] == repeated["actual_minutes"] == 28
    with connect() as conn:
        progress_count = conn.execute(
            "SELECT COUNT(*) FROM learning_progress WHERE roadmap_id=?",
            (roadmap_id,),
        ).fetchone()[0]
        event_count = conn.execute(
            "SELECT COUNT(*) FROM ecosystem_events WHERE event_type='learning_session_completed' AND entity_id=?",
            (str(session["id"]),),
        ).fetchone()[0]
    assert progress_count == 1
    assert event_count == 1


def test_today_plan_adapts_after_session_mastery_and_energy():
    roadmap_id = _active_roadmap()
    initial = build_today_plan(roadmap_id)
    assert initial["mode"] == "start"
    assert initial["minutes"] == 25

    session, _ = start_study_session(
        roadmap_id=roadmap_id,
        objective="Explain graph retrieval",
        idempotency_key="adaptive-session",
        chat_id="wa-owner",
    )
    active = build_today_plan(roadmap_id)
    assert active["mode"] == "resume"
    assert active["session_id"] == session["id"]

    complete_study_session(
        session["id"], actual_minutes=20, mastery_after=0.45, energy_after=2
    )
    adapted = build_today_plan(roadmap_id)
    assert adapted["mode"] == "reinforce"
    assert adapted["focus"] == "Explain graph retrieval"
    assert adapted["minutes"] == 15

    progress = get_roadmap_progress(roadmap_id)
    assert progress["session_count"] == 1
    assert progress["total_minutes"] == 20
    assert progress["average_mastery"] == pytest.approx(0.45)


def test_mcp_schema_hides_chat_identity_and_keeps_idempotency_key():
    principal = MCPPrincipal(
        sender_id="owner", sender_name="Owner", chat_id="owner-chat"
    )
    callable_tool = langchain_tool_as_mcp_callable(
        learning_start_study_session, principal
    )

    assert "chat_id" not in callable_tool.__signature__.parameters
    assert "idempotency_key" in callable_tool.__signature__.parameters


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"planned_minutes": 0}, "planned_minutes"),
        ({"energy_before": 6}, "energy_before"),
        ({"mastery_before": 1.1}, "mastery_before"),
    ],
)
def test_start_session_validates_bounded_inputs(kwargs, message):
    roadmap_id = _active_roadmap()
    with pytest.raises(ValueError, match=message):
        start_study_session(roadmap_id=roadmap_id, **kwargs)
