from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def get_style(user_id: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM style_profiles WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def set_style(user_id: str, description: str) -> dict:
    """Store a free-text style description (kept in metadata_json['description'])."""
    init_db()
    now = _now()
    meta = json.dumps({"description": description.strip()}, ensure_ascii=False)
    with connect() as conn:
        row = conn.execute("SELECT id FROM style_profiles WHERE user_id=?", (user_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE style_profiles SET metadata_json=?, updated_at=? WHERE user_id=?",
                (meta, now, user_id),
            )
        else:
            conn.execute(
                "INSERT INTO style_profiles (user_id, metadata_json, created_at, updated_at) VALUES (?,?,?,?)",
                (user_id, meta, now, now),
            )
    return {"user_id": user_id, "description": description.strip()}


def reset_style(user_id: str) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute("DELETE FROM style_profiles WHERE user_id=?", (user_id,))
        return cur.rowcount > 0


def get_style_text(user_id: str) -> str:
    """Return the user's free-text style description, or '' if none set."""
    row = get_style(user_id)
    if not row:
        return ""
    try:
        meta = json.loads(row.get("metadata_json") or "{}")
    except Exception:
        meta = {}
    return (meta.get("description") or "").strip()


def format_style_for_prompt(user_id: str) -> str:
    text = get_style_text(user_id)
    if not text:
        return ""
    return "\n[Gaya jawaban yang diinginkan user]\n" + text + "\n"
