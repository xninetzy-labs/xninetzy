from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)


def record_event_in_transaction(
    conn,
    chat_id: str,
    event_type: str,
    source: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict | None = None,
    created_at: str | None = None,
) -> int:
    """Persist an ecosystem event using the caller's active transaction."""
    now = created_at or datetime.now(
        ZoneInfo(get_settings().APP_TIMEZONE)
    ).isoformat()
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
    return int(result.lastrowid)


def dispatch_recorded_event(event_id: int) -> None:
    """Run reducers after the transaction containing an event has committed."""
    try:
        from app.xninetzy.ecosystem.reducers import consume_event

        consume_event(event_id)
    except Exception:
        logger.exception("Ecosystem reducer failed for event %s", event_id)


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
    with connect() as conn:
        event_id = record_event_in_transaction(
            conn,
            chat_id,
            event_type,
            source,
            entity_type,
            entity_id,
            payload,
        )
    dispatch_recorded_event(event_id)
    return event_id


def recent_events(
    chat_id: str | None = None,
    limit: int = 20,
    event_type: str | None = None,
) -> list[dict]:
    init_db()
    with connect() as conn:
        if chat_id and event_type:
            rows = conn.execute(
                "SELECT * FROM ecosystem_events WHERE chat_id=? AND event_type=? ORDER BY id DESC LIMIT ?",
                (chat_id, event_type, limit),
            ).fetchall()
        elif chat_id:
            rows = conn.execute(
                "SELECT * FROM ecosystem_events WHERE chat_id=? ORDER BY id DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()
        elif event_type:
            rows = conn.execute(
                "SELECT * FROM ecosystem_events WHERE event_type=? ORDER BY id DESC LIMIT ?",
                (event_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ecosystem_events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]
