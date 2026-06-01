from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect


class WorkflowService:
    def create_draft(self, chat_id: str, workflow: dict) -> dict:
        now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
        with connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO workflows (chat_id, name, description, trigger_json, steps_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'draft', ?, ?)
                """,
                (
                    chat_id,
                    workflow.get("name", "Untitled workflow"),
                    workflow.get("description"),
                    json.dumps(workflow.get("trigger", []), ensure_ascii=False),
                    json.dumps(workflow.get("steps", []), ensure_ascii=False),
                    now,
                    now,
                ),
            )
        return {"id": cursor.lastrowid, "status": "draft"}
