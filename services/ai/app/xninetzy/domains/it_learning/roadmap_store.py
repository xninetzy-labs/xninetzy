from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect
from app.xninetzy.domains.it_learning.roadmap_models import RoadmapDraft


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def save_roadmap_draft(
    draft: RoadmapDraft, chat_id: str | None = None, status: str = "draft"
) -> int:
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO learning_roadmaps
              (chat_id, title, topic, target, duration_days, status, metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                chat_id,
                f"Roadmap {draft.topic}",
                draft.topic,
                draft.target,
                draft.duration_days,
                status,
                json.dumps(draft.model_dump(), ensure_ascii=False),
                now,
                now,
            ),
        )
        roadmap_id = int(cur.lastrowid)
        for idx, milestone in enumerate(draft.milestones, 1):
            conn.execute(
                "INSERT INTO learning_milestones (roadmap_id, title, position, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (roadmap_id, milestone, idx, "draft", now, now),
            )
        for idx, task in enumerate(draft.first_day_tasks, 1):
            conn.execute(
                "INSERT INTO learning_tasks (roadmap_id, title, day_index, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (roadmap_id, task, idx, "draft", now, now),
            )
        return roadmap_id


def list_roadmaps(chat_id: str | None = None) -> list[dict]:
    with connect() as conn:
        if chat_id:
            rows = conn.execute(
                "SELECT * FROM learning_roadmaps WHERE chat_id=? ORDER BY id DESC LIMIT 20",
                (chat_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM learning_roadmaps ORDER BY id DESC LIMIT 20"
            ).fetchall()
    return [dict(row) for row in rows]


def list_roadmaps_with_progress(
    chat_id: str | None = None, status: str | None = "active", limit: int = 5
) -> list[dict]:
    conditions = []
    params: list[object] = []
    if chat_id:
        conditions.append("r.chat_id=?")
        params.append(chat_id)
    if status:
        conditions.append("r.status=?")
        params.append(status)
    where = " AND ".join(conditions) if conditions else "1=1"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT r.*,
                   COUNT(t.id) AS task_count,
                   SUM(CASE WHEN t.status='done' THEN 1 ELSE 0 END) AS completed_tasks
            FROM learning_roadmaps r
            LEFT JOIN learning_tasks t ON t.roadmap_id=r.id
            WHERE {where}
            GROUP BY r.id
            ORDER BY r.updated_at DESC, r.id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def get_roadmap(roadmap_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM learning_roadmaps WHERE id=?", (roadmap_id,)
        ).fetchone()
    return dict(row) if row else None


def activate_roadmap(roadmap_id: int) -> bool:
    """Activate a roadmap and release its draft milestones/tasks."""
    now = _now()
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM learning_roadmaps WHERE id=?", (roadmap_id,)
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "UPDATE learning_roadmaps SET status='active', updated_at=? WHERE id=?",
            (now, roadmap_id),
        )
        conn.execute(
            """
            UPDATE learning_milestones
            SET status='pending', updated_at=?
            WHERE roadmap_id=? AND status='draft'
            """,
            (now, roadmap_id),
        )
        conn.execute(
            """
            UPDATE learning_tasks
            SET status='pending', updated_at=?
            WHERE roadmap_id=? AND status='draft'
            """,
            (now, roadmap_id),
        )
        roadmap = conn.execute(
            "SELECT chat_id FROM learning_roadmaps WHERE id=?", (roadmap_id,)
        ).fetchone()
        learning_tasks = conn.execute(
            "SELECT id, title FROM learning_tasks WHERE roadmap_id=? ORDER BY day_index, id",
            (roadmap_id,),
        ).fetchall()
        for learning_task in learning_tasks:
            linked = conn.execute(
                """
                SELECT target_id FROM entity_links
                WHERE source_type='learning_task' AND source_id=?
                  AND relation='represented_by' AND target_type='task'
                """,
                (str(learning_task["id"]),),
            ).fetchone()
            if linked:
                continue
            task = conn.execute(
                """
                INSERT INTO tasks
                  (title, description, status, priority, domain, due_at, source, created_at, updated_at)
                VALUES (?, '', 'inbox', 'medium', 'learning', NULL, ?, ?, ?)
                """,
                (
                    learning_task["title"],
                    f"learning_roadmap:{roadmap_id}",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO entity_links
                  (chat_id, source_type, source_id, relation, target_type, target_id, metadata_json, created_at)
                VALUES (?, 'learning_task', ?, 'represented_by', 'task', ?, ?, ?)
                """,
                (
                    roadmap["chat_id"] if roadmap else None,
                    str(learning_task["id"]),
                    str(task.lastrowid),
                    json.dumps({"roadmap_id": roadmap_id}),
                    now,
                ),
            )
    return True
