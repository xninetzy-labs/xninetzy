from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.concept_graph import concept_map
from app.xninetzy.domains.it_learning.recall import (
    create_recall_card,
    due_recall_cards,
    keyword_coverage,
    learning_due_recall,
    learning_submit_recall_answer,
    recall_quality,
    recall_summary,
    submit_recall_answer,
)
from app.xninetzy.domains.it_learning.progress_tracker import build_today_plan
from app.xninetzy.domains.it_learning.roadmap_models import RoadmapDraft
from app.xninetzy.domains.it_learning.roadmap_store import (
    activate_roadmap,
    save_roadmap_draft,
)
from app.xninetzy.interfaces.mcp_tool_adapter import (
    MCPPrincipal,
    langchain_tool_as_mcp_callable,
)
from app.xninetzy.os.inbox.service import build_attention_queue


@pytest.fixture(autouse=True)
def isolated_learning_database(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "recall.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def _clock(day: int = 29) -> datetime:
    return datetime(2026, 7, day, 10, 0, tzinfo=ZoneInfo("Asia/Jakarta"))


def _concept() -> tuple[int, int]:
    roadmap_id = save_roadmap_draft(
        RoadmapDraft(
            topic="Machine Learning",
            duration_days=2,
            target="Pahami supervised learning",
            milestones=["Supervised learning", "Evaluasi"],
            first_day_tasks=["Pelajari label", "Latihan prediksi"],
        ),
        chat_id="owner",
    )
    assert activate_roadmap(roadmap_id)
    return roadmap_id, concept_map(roadmap_id)[0]["id"]


def _card(now: datetime | None = None) -> tuple[int, int, int]:
    roadmap_id, concept_id = _concept()
    card, _ = create_recall_card(
        concept_id,
        "Apa ciri utama supervised learning?",
        "Model belajar dari data berlabel untuk membuat prediksi.",
        ["data berlabel", "model", "prediksi"],
        "xninetzy://knowledge/source/1",
        "card-1",
        now or _clock(),
    )
    return roadmap_id, concept_id, card["id"]


def test_recall_card_is_immutable_idempotent_and_due_immediately():
    roadmap_id, concept_id, card_id = _card()
    repeated, created = create_recall_card(
        concept_id,
        "Apa ciri utama supervised learning?",
        "Model belajar dari data berlabel untuk membuat prediksi.",
        ["data berlabel", "model", "prediksi"],
        "xninetzy://knowledge/source/1",
        "card-1",
        _clock(),
    )

    assert created is False
    assert repeated["id"] == card_id
    assert [row["id"] for row in due_recall_cards(roadmap_id, now=_clock())] == [
        card_id
    ]
    with pytest.raises(ValueError, match="recall card berbeda"):
        create_recall_card(
            concept_id,
            "Pertanyaan berubah",
            "Jawaban berubah",
            ["jawaban"],
            idempotency_key="card-1",
            now=_clock(),
        )


def test_due_tool_never_exposes_expected_answer():
    _, _, _ = _card()

    result = learning_due_recall.invoke({})

    assert "Apa ciri utama supervised learning?" in result
    assert "Model belajar dari data berlabel" not in result
    assert "/recall answer" in result


def test_keyword_grading_handles_phrases_and_quality_bands():
    coverage = keyword_coverage(
        "Model membuat prediksi dari DATA BERLABEL.",
        ["data berlabel", "model", "prediksi", "training"],
    )

    assert coverage == pytest.approx(0.75)
    assert recall_quality(coverage) == 4
    assert recall_quality(0.5) == 3
    assert recall_quality(0.25) == 2
    assert recall_quality(0) == 0


def test_successful_recall_is_atomic_replay_safe_and_updates_mastery():
    _, concept_id, card_id = _card()

    attempt, created, card, concept = submit_recall_answer(
        card_id,
        "Model belajar memakai data berlabel untuk membuat prediksi.",
        confidence=4,
        chat_id="owner",
        now=_clock(),
    )
    replay, replay_created, replay_card, replay_concept = submit_recall_answer(
        card_id,
        "Model belajar memakai data berlabel untuk membuat prediksi.",
        confidence=4,
        chat_id="owner",
        now=_clock(),
    )

    assert created is True
    assert replay_created is False
    assert replay["id"] == attempt["id"]
    assert attempt["keyword_coverage"] == pytest.approx(1)
    assert attempt["quality"] == 5
    assert card["interval_days"] == replay_card["interval_days"] == 1
    assert concept["mastery"] == replay_concept["mastery"] == pytest.approx(1)
    with connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM learning_recall_attempts").fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM learning_concept_evidence WHERE concept_id=?",
            (concept_id,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM ecosystem_events WHERE event_type='learning_recall_completed'"
        ).fetchone()[0] == 1


def test_failed_recall_resets_repetition_and_tracks_lapse():
    _, _, card_id = _card()
    first, _, first_card, _ = submit_recall_answer(
        card_id,
        "Model belajar dari data berlabel untuk prediksi.",
        5,
        "attempt-1",
        now=_clock(),
    )
    second_time = _clock() + timedelta(days=1)
    second, _, second_card, concept = submit_recall_answer(
        card_id,
        "Saya lupa jawabannya.",
        1,
        "attempt-2",
        now=second_time,
    )

    assert first["quality"] == 5
    assert first_card["repetitions"] == 1
    assert second["quality"] == 0
    assert second_card["repetitions"] == 0
    assert second_card["lapse_count"] == 1
    assert second_card["interval_days"] == 1
    assert concept["mastery"] == pytest.approx(0.4)


def test_explicit_attempt_key_rejects_payload_reuse():
    _, _, card_id = _card()
    submit_recall_answer(
        card_id,
        "Model data berlabel prediksi",
        3,
        "attempt-fixed",
        now=_clock(),
    )

    with pytest.raises(ValueError, match="jawaban berbeda"):
        submit_recall_answer(
            card_id,
            "Jawaban lain",
            2,
            "attempt-fixed",
            now=_clock(),
        )


def test_recall_summary_tracks_due_attempts_coverage_and_lapses():
    roadmap_id, _, card_id = _card()
    submit_recall_answer(
        card_id,
        "Tidak ingat",
        1,
        "summary-1",
        now=_clock(),
    )

    summary = recall_summary(roadmap_id, days=7, now=_clock())

    assert summary["attempts"] == 1
    assert summary["average_coverage"] == pytest.approx(0)
    assert summary["lapses"] == 1
    assert summary["due"] == 0


def test_mcp_submit_schema_hides_chat_identity_and_keeps_idempotency():
    principal = MCPPrincipal(
        sender_id="owner", sender_name="Owner", chat_id="owner-chat"
    )
    callable_tool = langchain_tool_as_mcp_callable(
        learning_submit_recall_answer,
        principal,
    )

    assert "chat_id" not in callable_tool.__signature__.parameters
    assert "idempotency_key" in callable_tool.__signature__.parameters


def test_due_recall_preempts_new_study_and_enters_attention_queue():
    roadmap_id, _, card_id = _card()

    plan = build_today_plan(roadmap_id, now=_clock())
    attention = build_attention_queue(limit=5, now=_clock())

    assert plan["mode"] == "recall"
    assert plan["recall_card_id"] == card_id
    recall_item = next(item for item in attention if item["kind"] == "recall")
    assert recall_item["id"] == card_id
    assert recall_item["score"] == 75


def test_answered_recall_releases_today_plan_until_next_due_date():
    roadmap_id, _, card_id = _card()
    submit_recall_answer(
        card_id,
        "Model belajar dari data berlabel untuk membuat prediksi",
        4,
        "release-plan",
        now=_clock(),
    )

    plan = build_today_plan(roadmap_id, now=_clock())

    assert plan["mode"] != "recall"
    assert plan["recall_card_id"] is None
