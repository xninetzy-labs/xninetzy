from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.concept_graph import (
    concept_map,
    define_concept,
    learning_record_concept_evidence,
    mastery_focus,
    next_ready_concept,
    record_concept_evidence,
)
from app.xninetzy.domains.it_learning.progress_tracker import build_today_plan
from app.xninetzy.domains.it_learning.roadmap_models import RoadmapDraft
from app.xninetzy.domains.it_learning.roadmap_store import (
    activate_roadmap,
    save_roadmap_draft,
)
from app.xninetzy.domains.it_learning.study_session import (
    complete_study_session,
    start_study_session,
)
from app.xninetzy.interfaces.mcp_tool_adapter import (
    MCPPrincipal,
    langchain_tool_as_mcp_callable,
)


@pytest.fixture(autouse=True)
def isolated_learning_database(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "concepts.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def _roadmap() -> int:
    roadmap_id = save_roadmap_draft(
        RoadmapDraft(
            topic="Machine Learning",
            duration_days=3,
            target="Bangun model terukur",
            milestones=["Data dan baseline", "Training", "Evaluasi"],
            first_day_tasks=["Siapkan data", "Latih model", "Ukur model"],
        ),
        chat_id="owner",
    )
    assert activate_roadmap(roadmap_id)
    return roadmap_id


def test_roadmap_seeds_ordered_concepts_and_entity_links():
    roadmap_id = _roadmap()

    concepts = concept_map(roadmap_id)

    assert [item["title"] for item in concepts] == [
        "Data dan baseline",
        "Training",
        "Evaluasi",
    ]
    assert concepts[0]["prerequisite_ids"] == []
    assert concepts[1]["prerequisite_ids"] == [concepts[0]["id"]]
    assert concepts[2]["prerequisite_ids"] == [concepts[1]["id"]]
    assert [item["milestone_count"] for item in concepts] == [1, 1, 1]
    assert [item["task_count"] for item in concepts] == [1, 1, 1]


def test_define_concept_is_idempotent_and_rejects_dependency_cycles():
    roadmap_id = _roadmap()
    first, created = define_concept(roadmap_id, "Feature Engineering")
    repeated, repeated_created = define_concept(
        roadmap_id, "Feature Engineering", "Transformasi fitur"
    )
    second, _ = define_concept(
        roadmap_id,
        "Model Selection",
        prerequisite_ids=[first["id"]],
    )

    assert created is True
    assert repeated_created is False
    assert repeated["id"] == first["id"]
    with pytest.raises(ValueError, match="cycle"):
        define_concept(
            roadmap_id,
            "Feature Engineering",
            prerequisite_ids=[second["id"]],
        )


def test_evidence_is_replay_safe_and_updates_mastery_once():
    roadmap_id = _roadmap()
    concept_id = concept_map(roadmap_id)[0]["id"]

    _, created, first = record_concept_evidence(
        concept_id,
        "quiz",
        "xninetzy://quiz/1",
        0.6,
        "message-1",
        "Enam dari sepuluh benar",
        "owner",
    )
    _, replay_created, replay = record_concept_evidence(
        concept_id,
        "quiz",
        "xninetzy://quiz/1",
        0.6,
        "message-1",
        "Enam dari sepuluh benar",
        "owner",
    )
    _, second_created, second = record_concept_evidence(
        concept_id,
        "project",
        "obsidian://Learning/model.md",
        1.0,
        "message-2",
        "Model berhasil dievaluasi",
        "owner",
    )

    assert created is True
    assert replay_created is False
    assert second_created is True
    assert first["mastery"] == replay["mastery"] == pytest.approx(0.6)
    assert second["mastery"] == pytest.approx(0.84)
    assert second["evidence_count"] == 2
    assert second["status"] == "mastered"
    with pytest.raises(ValueError, match="evidence berbeda"):
        record_concept_evidence(
            concept_id,
            "quiz",
            "xninetzy://quiz/changed",
            0.2,
            "message-1",
        )


def test_study_session_closes_loop_into_concept_mastery_and_next_focus():
    roadmap_id = _roadmap()
    initial_concepts = concept_map(roadmap_id)
    first_id = initial_concepts[0]["id"]
    second_id = initial_concepts[1]["id"]
    session, _ = start_study_session(
        roadmap_id=roadmap_id,
        idempotency_key="session-1",
        chat_id="owner",
    )

    complete_study_session(
        session["id"],
        actual_minutes=30,
        mastery_after=0.9,
        reflection="Dapat menjelaskan baseline tanpa catatan",
        evidence=["obsidian://Learning/baseline.md"],
    )
    complete_study_session(session["id"], actual_minutes=99, mastery_after=0.1)

    with connect() as conn:
        first = conn.execute(
            "SELECT * FROM learning_concepts WHERE id=?", (first_id,)
        ).fetchone()
        evidence_count = conn.execute(
            "SELECT COUNT(*) FROM learning_concept_evidence WHERE concept_id=?",
            (first_id,),
        ).fetchone()[0]
        ready = next_ready_concept(conn, roadmap_id)
    plan = build_today_plan(roadmap_id)

    assert first["mastery"] == pytest.approx(0.9)
    assert first["evidence_count"] == evidence_count == 1
    assert ready["id"] == second_id
    assert plan["mode"] == "advance"
    assert plan["concept_id"] == second_id


def test_migration_backfills_existing_roadmap_without_duplicate_concepts():
    with connect() as conn:
        roadmap = conn.execute(
            """
            INSERT INTO learning_roadmaps
              (title, topic, target, duration_days, status, metadata_json, created_at, updated_at)
            VALUES ('Legacy', 'Legacy', '', 7, 'active', '{}', '2026-01-01', '2026-01-01')
            """
        )
        roadmap_id = int(roadmap.lastrowid)
        conn.execute(
            "INSERT INTO learning_milestones (roadmap_id, title, position, status, created_at, updated_at) VALUES (?,?,1,'pending','2026-01-01','2026-01-01')",
            (roadmap_id, "Legacy foundation"),
        )
    run_migrations()
    run_migrations()

    assert len(concept_map(roadmap_id)) == 1


def test_mcp_evidence_schema_hides_chat_identity_and_keeps_idempotency():
    principal = MCPPrincipal(
        sender_id="owner", sender_name="Owner", chat_id="owner-chat"
    )
    callable_tool = langchain_tool_as_mcp_callable(
        learning_record_concept_evidence,
        principal,
    )

    assert "chat_id" not in callable_tool.__signature__.parameters
    assert "idempotency_key" in callable_tool.__signature__.parameters


def test_mastery_focus_prioritizes_weak_active_concepts():
    roadmap_id = _roadmap()
    concepts = concept_map(roadmap_id)
    record_concept_evidence(
        concepts[0]["id"],
        "quiz",
        "xninetzy://quiz/mastered",
        0.9,
        "focus-1",
    )

    focus = mastery_focus(roadmap_id, limit=2)

    assert [item["id"] for item in focus] == [concepts[1]["id"], concepts[2]["id"]]
