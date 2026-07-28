from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


def record_event(
    chat_id: str,
    event_type: str,
    source: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict | None = None,
) -> int:
    """Record a lifecycle event to the ecosystem timeline."""
    init_db()
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
    with connect() as conn:
        result = conn.execute(
            """
            INSERT INTO ecosystem_events
              (chat_id, event_type, source, entity_type, entity_id, payload_json, created_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                chat_id,
                event_type,
                source,
                entity_type,
                entity_id,
                json.dumps(payload or {}, ensure_ascii=False),
                now,
            ),
        )
        event_id = int(result.lastrowid)
    try:
        from app.xninetzy.ecosystem.reducers import consume_event

        consume_event(event_id)
    except Exception:
        logger.exception("Ecosystem reducer failed for event %s", event_id)
    return event_id


def recent_events(
    chat_id: str, limit: int = 20, event_type: str | None = None
) -> list[dict]:
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
