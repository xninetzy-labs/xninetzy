from __future__ import annotations

from uuid import uuid4

from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.roadmap_models import RoadmapDraft
from app.xninetzy.domains.it_learning.roadmap_store import (
    activate_roadmap,
    get_roadmap,
    save_roadmap_draft,
)
from app.xninetzy.ecosystem.context_builder import build_personal_context
from app.xninetzy.ecosystem.event_bus import record_event
from app.xninetzy.os.life.goal_manager import create_goal, get_goal, get_goal_logs
from app.xninetzy.os.life.habit_manager import log_habit
from app.xninetzy.os.life.task_manager import create_task
from app.xninetzy.os.life.workout_manager import log_workout
from app.xninetzy.tools.ecosystem.life_tools import task_complete


def _prepare_database() -> None:
    init_db()
    run_migrations()


def test_roadmap_activation_links_tasks_and_completion_closes_loop():
    _prepare_database()
    marker = uuid4().hex
    roadmap_id = save_roadmap_draft(
        RoadmapDraft(
            topic=f"Closed Loop {marker}",
            duration_days=2,
            target="Finish both tasks",
            milestones=["Complete"],
            first_day_tasks=[f"Read {marker}", f"Practice {marker}"],
        ),
        chat_id=f"chat-{marker}",
    )

    assert activate_roadmap(roadmap_id)
    assert activate_roadmap(roadmap_id)
    with connect() as conn:
        linked = conn.execute(
            """
            SELECT CAST(l.target_id AS INTEGER) AS task_id
            FROM entity_links l
            JOIN learning_tasks lt ON lt.id=CAST(l.source_id AS INTEGER)
            WHERE lt.roadmap_id=? ORDER BY lt.id
            """,
            (roadmap_id,),
        ).fetchall()
    assert len(linked) == 2

    first = task_complete.invoke(
        {"task_id": linked[0]["task_id"], "chat_id": f"chat-{marker}"}
    )
    assert "selesai" in first
    assert get_roadmap(roadmap_id)["status"] == "active"

    second = task_complete.invoke(
        {"task_id": linked[1]["task_id"], "chat_id": f"chat-{marker}"}
    )
    assert "selesai" in second
    assert get_roadmap(roadmap_id)["status"] == "completed"

    repeated = task_complete.invoke(
        {"task_id": linked[1]["task_id"], "chat_id": f"chat-{marker}"}
    )
    assert "sudah selesai" in repeated
    with connect() as conn:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM learning_progress WHERE roadmap_id=?",
                (roadmap_id,),
            ).fetchone()[0]
            == 2
        )


def test_linked_goal_progress_is_idempotent():
    _prepare_database()
    marker = uuid4().hex
    goal = create_goal(f"Goal {marker}", target_metric="tasks", target_value=3)
    task = create_task(f"Task {marker}", goal_id=goal["id"])

    task_complete.invoke({"task_id": task["id"], "chat_id": f"chat-{marker}"})
    task_complete.invoke({"task_id": task["id"], "chat_id": f"chat-{marker}"})

    assert get_goal(goal["id"])["current_value"] == 1
    assert len(get_goal_logs(goal["id"])) == 1


def test_personal_context_v2_contains_learning_and_life_signals():
    _prepare_database()
    marker = uuid4().hex
    chat_id = f"context-{marker}"
    roadmap_id = save_roadmap_draft(
        RoadmapDraft(
            topic=f"Context Topic {marker}",
            duration_days=1,
            target="Context target",
            milestones=["One"],
            first_day_tasks=["One task"],
        ),
        chat_id=chat_id,
    )
    activate_roadmap(roadmap_id)
    log_habit(f"Habit {marker}")
    log_workout("mobility", duration=7)
    record_event(chat_id, "context_probe", "test", "probe", marker)

    context = build_personal_context(chat_id, "status hari ini")

    assert any(marker in item for item in context["active_roadmaps"])
    assert any(marker in item for item in context["habit_status"])
    assert context["workout_summary"]
    assert "context_probe:probe" in context["recent_events"]
