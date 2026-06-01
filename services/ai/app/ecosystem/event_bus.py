from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db


def record_event(
    chat_id: str,
    event_type: str,
    source: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict | None = None,
) -> None:
    """Record a lifecycle event to the ecosystem timeline."""
    init_db()
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO ecosystem_events
              (chat_id, event_type, source, entity_type, entity_id, payload_json, created_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (chat_id, event_type, source, entity_type, entity_id,
             json.dumps(payload or {}, ensure_ascii=False), now),
        )


def recent_events(chat_id: str, limit: int = 20, event_type: str | None = None) -> list[dict]:
    init_db()
    with connect() as conn:
        if event_type:
            rows = conn.execute(
                "SELECT * FROM ecosystem_events WHERE chat_id=? AND event_type=? ORDER BY id DESC LIMIT ?",
                (chat_id, event_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ecosystem_events WHERE chat_id=? ORDER BY id DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()
    return [dict(r) for r in rows]
