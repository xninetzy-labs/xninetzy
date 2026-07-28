from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db

REDUCER_NAME = "closed_loop_v1"


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def consume_event(event_id: int) -> bool:
    """Consume one ecosystem event exactly once inside a SQLite transaction."""
    init_db()
    with connect() as conn:
        _ensure_consumption_schema(conn)
        consumed = conn.execute(
            "SELECT 1 FROM ecosystem_event_consumptions WHERE event_id=? AND reducer=?",
            (event_id, REDUCER_NAME),
        ).fetchone()
        if consumed:
            return False
        event = conn.execute(
            "SELECT * FROM ecosystem_events WHERE id=?", (event_id,)
        ).fetchone()
        if not event:
            return False

        if event["event_type"] == "task_completed" and event["entity_id"]:
            _reduce_task_completed(conn, int(event["entity_id"]))

        conn.execute(
            "INSERT INTO ecosystem_event_consumptions (event_id, reducer, consumed_at) VALUES (?,?,?)",
            (event_id, REDUCER_NAME, _now()),
        )
    return True


def replay_unconsumed_events(limit: int = 100) -> int:
    """Replay events left behind if a reducer failed after event persistence."""
    init_db()
    with connect() as conn:
        _ensure_consumption_schema(conn)
        rows = conn.execute(
            """
            SELECT e.id FROM ecosystem_events e
            LEFT JOIN ecosystem_event_consumptions c
              ON c.event_id=e.id AND c.reducer=?
            WHERE c.event_id IS NULL
            ORDER BY e.id ASC LIMIT ?
            """,
            (REDUCER_NAME, limit),
        ).fetchall()
    return sum(1 for row in rows if consume_event(int(row["id"])))


def _ensure_consumption_schema(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ecosystem_event_consumptions (
            event_id INTEGER NOT NULL,
            reducer TEXT NOT NULL,
            consumed_at TEXT NOT NULL,
            PRIMARY KEY (event_id, reducer)
        )
        """
    )


def _reduce_task_completed(conn, task_id: int) -> None:
    task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not task:
        return
    now = _now()

    if task["goal_id"]:
        conn.execute(
            """
            INSERT INTO life_goal_logs
              (goal_id, log_text, progress_delta, created_at)
            VALUES (?,?,1,?)
            """,
            (task["goal_id"], f"Task selesai: {task['title']}", now),
        )
        conn.execute(
            """
            UPDATE life_goals
            SET current_value=current_value+1, updated_at=?
            WHERE id=?
            """,
            (now, task["goal_id"]),
        )

    links = conn.execute(
        """
        SELECT source_id, metadata_json FROM entity_links
        WHERE source_type='learning_task' AND relation='represented_by'
          AND target_type='task' AND target_id=?
        """,
        (str(task_id),),
    ).fetchall()
    for link in links:
        learning_task_id = int(link["source_id"])
        learning_task = conn.execute(
            "SELECT roadmap_id, status FROM learning_tasks WHERE id=?",
            (learning_task_id,),
        ).fetchone()
        if not learning_task or learning_task["status"] == "done":
            continue
        roadmap_id = int(learning_task["roadmap_id"])
        conn.execute(
            "UPDATE learning_tasks SET status='done', updated_at=? WHERE id=?",
            (now, learning_task_id),
        )
        conn.execute(
            "INSERT INTO learning_progress (roadmap_id, note, created_at) VALUES (?,?,?)",
            (roadmap_id, f"Task selesai: {task['title']}", now),
        )
        counts = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) AS done
            FROM learning_tasks WHERE roadmap_id=?
            """,
            (roadmap_id,),
        ).fetchone()
        if counts and counts["total"] and counts["done"] == counts["total"]:
            conn.execute(
                "UPDATE learning_roadmaps SET status='completed', updated_at=? WHERE id=?",
                (now, roadmap_id),
            )
            conn.execute(
                "UPDATE learning_milestones SET status='completed', updated_at=? WHERE roadmap_id=?",
                (now, roadmap_id),
            )
