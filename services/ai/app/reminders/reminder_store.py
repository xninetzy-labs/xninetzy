from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect


class ReminderStore:
    def create(self, chat_id: str, sender_id: str | None, title: str, remind_at: str, description: str | None = None, repeat_rule: str | None = None) -> dict:
        now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
        with connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reminders
                (chat_id, sender_id, title, description, remind_at, timezone, status, repeat_rule, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (chat_id, sender_id, title, description, remind_at, get_settings().APP_TIMEZONE, repeat_rule, now, now),
            )
            reminder_id = cursor.lastrowid
        return {"id": reminder_id, "chat_id": chat_id, "title": title, "description": description, "remind_at": remind_at, "status": "pending"}

    def list_pending(self, chat_id: str | None = None) -> list[dict]:
        query = "SELECT * FROM reminders WHERE status = 'pending'"
        params: tuple = ()
        if chat_id:
            query += " AND chat_id = ?"
            params = (chat_id,)
        query += " ORDER BY remind_at ASC"
        with connect() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def due(self, now_iso: str) -> list[dict]:
        with connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM reminders WHERE status = 'pending' AND remind_at <= ? ORDER BY remind_at ASC", (now_iso,)).fetchall()]

    def mark_done(self, reminder_id: int) -> None:
        now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
        with connect() as conn:
            conn.execute("UPDATE reminders SET status = 'done', updated_at = ? WHERE id = ?", (now, reminder_id))

    def cancel(self, reminder_id: int) -> None:
        now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
        with connect() as conn:
            conn.execute("UPDATE reminders SET status = 'cancelled', updated_at = ? WHERE id = ?", (now, reminder_id))
