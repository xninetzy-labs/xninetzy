from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect
from app.learning.roadmap_models import RoadmapDraft


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def save_roadmap_draft(draft: RoadmapDraft, chat_id: str | None = None, status: str = "draft") -> int:
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO learning_roadmaps
              (chat_id, title, topic, target, duration_days, status, metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (chat_id, f"Roadmap {draft.topic}", draft.topic, draft.target, draft.duration_days, status,
             json.dumps(draft.model_dump(), ensure_ascii=False), now, now),
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
            rows = conn.execute("SELECT * FROM learning_roadmaps WHERE chat_id=? ORDER BY id DESC LIMIT 20", (chat_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM learning_roadmaps ORDER BY id DESC LIMIT 20").fetchall()
    return [dict(row) for row in rows]


def get_roadmap(roadmap_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM learning_roadmaps WHERE id=?", (roadmap_id,)).fetchone()
    return dict(row) if row else None
