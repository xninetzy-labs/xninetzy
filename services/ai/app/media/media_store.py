from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def save_media_item(
    *,
    chat_id: str | None,
    message_id: str | None,
    sender_id: str | None,
    media_type: str,
    mime_type: str | None,
    file_name: str | None,
    local_path: str,
    caption: str | None = None,
    extracted_text: str | None = None,
    summary: str | None = None,
    metadata: dict | None = None,
) -> int:
    """Upsert a media item keyed by message_id (best-effort)."""
    init_db()
    now = _now()
    media_id = message_id or f"{chat_id}:{file_name}:{now}"
    with connect() as conn:
        row = conn.execute("SELECT id FROM media_items WHERE media_id=?", (media_id,)).fetchone()
        if row:
            conn.execute(
                """
                UPDATE media_items SET media_type=?, mime_type=?, file_name=?, local_path=?,
                  caption=?, extracted_text=COALESCE(?, extracted_text),
                  summary=COALESCE(?, summary), metadata_json=?, updated_at=?
                WHERE media_id=?
                """,
                (media_type, mime_type, file_name, local_path, caption, extracted_text,
                 summary, json.dumps(metadata or {}, ensure_ascii=False), now, media_id),
            )
            return int(row["id"])
        cur = conn.execute(
            """
            INSERT INTO media_items
              (media_id, chat_id, message_id, sender_id, media_type, mime_type,
               file_name, local_path, caption, extracted_text, summary, metadata_json,
               created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (media_id, chat_id, message_id, sender_id, media_type, mime_type, file_name,
             local_path, caption, extracted_text, summary,
             json.dumps(metadata or {}, ensure_ascii=False), now, now),
        )
        return int(cur.lastrowid)


def get_media_item(message_id: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM media_items WHERE media_id=?", (message_id,)).fetchone()
    return dict(row) if row else None
