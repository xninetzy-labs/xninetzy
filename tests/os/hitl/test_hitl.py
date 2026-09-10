from uuid import uuid4

from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.domains.it_learning.roadmap_models import RoadmapDraft
from app.xninetzy.domains.it_learning.roadmap_store import (
    get_roadmap,
    save_roadmap_draft,
)
from app.xninetzy.os.hitl.approval_service import request_approval, set_approval_status


def test_approval_only_admin(monkeypatch):
    init_db()
    run_migrations()
    approval_id = request_approval("chat", "sender", "test", "Title", "Summary")
    ok, msg = set_approval_status(approval_id, "approved", "user", "Regular")
    assert not ok
    assert "admin" in msg.lower()
    ok, _ = set_approval_status(approval_id, "approved", "user", "Misbahul")
    assert ok


def test_approval_activates_learning_roadmap_and_tasks():
    init_db()
    run_migrations()
    topic = f"Data Analytics {uuid4()}"
    roadmap_id = save_roadmap_draft(
        RoadmapDraft(
            topic=topic,
            duration_days=28,
            target="Selesaikan mini project.",
            milestones=["Fondasi", "Praktik"],
            first_day_tasks=["Baca materi", "Buat notebook"],
        ),
        chat_id="mcp",
    )
    approval_id = request_approval(
        "mcp",
        None,
        "activate_learning_roadmap",
        f"Aktifkan {topic}",
        "Aktifkan roadmap dan task.",
        {"roadmap_id": roadmap_id},
    )

    ok, message = set_approval_status(approval_id, "approved", None, "Misbahul")

    assert ok
    assert "diaktifkan" in message
    assert get_roadmap(roadmap_id)["status"] == "active"
    with connect() as conn:
        task_statuses = {
            row["status"]
            for row in conn.execute(
                "SELECT status FROM learning_tasks WHERE roadmap_id=?",
                (roadmap_id,),
            ).fetchall()
        }
        linked_task_count = conn.execute(
            """
            SELECT COUNT(*) FROM entity_links l
            JOIN learning_tasks lt ON lt.id=CAST(l.source_id AS INTEGER)
            WHERE lt.roadmap_id=? AND l.source_type='learning_task'
              AND l.relation='represented_by' AND l.target_type='task'
            """,
            (roadmap_id,),
        ).fetchone()[0]
    assert task_statuses == {"pending"}
    assert linked_task_count == 2
