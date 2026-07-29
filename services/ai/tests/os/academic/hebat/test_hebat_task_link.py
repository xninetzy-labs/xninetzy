from __future__ import annotations

from uuid import uuid4

from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.os.academic.hebat.models import (
    ActivityType,
    HebatActivity,
    HebatAssignment,
)
from app.xninetzy.os.academic.hebat.storage import (
    sync_assignment_task,
    upsert_activity,
    upsert_assignment,
)


def test_assignment_projects_to_one_shared_task_and_updates_it():
    init_db()
    run_migrations()
    marker = uuid4().hex
    activity_id = upsert_activity(
        HebatActivity(
            course_id=f"course-{marker}",
            cmid=f"cmid-{marker}",
            type=ActivityType.ASSIGN,
            title=f"Assignment {marker}",
            activity_url=f"https://example.invalid/mod/assign/view.php?id={marker}",
        )
    )
    assignment_id = upsert_assignment(
        HebatAssignment(
            activity_id=activity_id,
            title=f"Assignment {marker}",
            instruction_text="Analyze the dataset",
            due_at="2026-08-01T12:00:00+07:00",
        )
    )

    task_id, created = sync_assignment_task(f"chat-{marker}", assignment_id)
    same_task_id, created_again = sync_assignment_task(
        f"mcp-{marker}", assignment_id, normalized_due_at="2026-08-02T12:00:00+07:00"
    )

    assert created is True
    assert created_again is False
    assert same_task_id == task_id
    with connect() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        links = conn.execute(
            """
            SELECT COUNT(*) FROM entity_links
            WHERE source_type='hebat_assignment' AND source_id=?
              AND relation='represented_by' AND target_type='task'
            """,
            (str(assignment_id),),
        ).fetchone()[0]
    assert task["due_at"] == "2026-08-02T12:00:00+07:00"
    assert task["source"] == f"hebat_assignment:{assignment_id}"
    assert links == 1
