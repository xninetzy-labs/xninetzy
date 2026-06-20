from __future__ import annotations

import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect, init_db


ACTIVE_STATUSES = ("pending", "processing", "sent", "closed")


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE)).isoformat()


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").casefold()).strip()


def _ensure_db() -> None:
    init_db()
    try:
        from app.xninetzy.db.migrations import run_migrations
        run_migrations()
    except Exception:
        pass


class ReminderStore:
    def create_reminder(
        self,
        *,
        chat_id: str,
        user_id: str | None = None,
        sender_id: str | None = None,
        source: str = "user",
        source_ref_id: str | None = None,
        title: str,
        description: str | None = None,
        context_summary: str | None = None,
        action_label: str | None = None,
        display_time_label: str | None = None,
        deadline_label: str | None = None,
        offset_label: str | None = None,
        source_reason: str | None = None,
        raw_user_message: str | None = None,
        normalized_task_text: str | None = None,
        deadline_at: str | None = None,
        remind_at: str,
        timezone: str | None = None,
        status: str = "pending",
        priority: str = "normal",
        reminder_type: str = "explicit",
        offset_value: int | None = None,
        offset_unit: str | None = None,
        repeat_rule: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        _ensure_db()
        now = _now()
        tz = timezone or get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE
        with connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reminders
                  (chat_id, user_id, sender_id, source, source_ref_id, title, description,
                   context_summary, action_label, display_time_label, deadline_label,
                   offset_label, source_reason, raw_user_message, normalized_task_text,
                   deadline_at, remind_at, timezone, status, priority, reminder_type,
                   offset_value, offset_unit, repeat_rule, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id, user_id, sender_id, source, source_ref_id, title, description,
                    context_summary, action_label, display_time_label, deadline_label,
                    offset_label, source_reason, raw_user_message, normalized_task_text,
                    deadline_at, remind_at, tz, status, priority, reminder_type,
                    offset_value, offset_unit, repeat_rule, json.dumps(metadata or {}, ensure_ascii=False),
                    now, now,
                ),
            )
            reminder_id = cursor.lastrowid
        return self.get_reminder(int(reminder_id)) or {}

    # Backward-compatible alias used by HEBAT and old tools.
    def create(
        self,
        chat_id: str,
        sender_id: str | None,
        title: str,
        remind_at: str,
        description: str | None = None,
        repeat_rule: str | None = None,
        **kwargs,
    ) -> dict:
        return self.create_reminder(
            chat_id=chat_id,
            sender_id=sender_id,
            user_id=kwargs.get("user_id") or sender_id,
            source=kwargs.get("source", "user"),
            source_ref_id=kwargs.get("source_ref_id"),
            title=title,
            description=description,
            context_summary=kwargs.get("context_summary"),
            action_label=kwargs.get("action_label"),
            display_time_label=kwargs.get("display_time_label"),
            deadline_label=kwargs.get("deadline_label"),
            offset_label=kwargs.get("offset_label"),
            source_reason=kwargs.get("source_reason"),
            raw_user_message=kwargs.get("raw_user_message"),
            normalized_task_text=kwargs.get("normalized_task_text"),
            deadline_at=kwargs.get("deadline_at"),
            remind_at=remind_at,
            timezone=kwargs.get("timezone"),
            priority=kwargs.get("priority", "normal"),
            reminder_type=kwargs.get("reminder_type", "explicit"),
            offset_value=kwargs.get("offset_value"),
            offset_unit=kwargs.get("offset_unit"),
            repeat_rule=repeat_rule,
            metadata=kwargs.get("metadata"),
        )

    def get_reminder(self, reminder_id: int | str) -> dict | None:
        _ensure_db()
        with connect() as conn:
            row = conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        return self._row(row) if row else None

    def list_reminders(self, chat_id: str | None = None, status: str | None = None) -> list[dict]:
        _ensure_db()
        query = "SELECT * FROM reminders WHERE 1=1"
        params: list[Any] = []
        if chat_id:
            query += " AND chat_id = ?"
            params.append(chat_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY remind_at ASC"
        with connect() as conn:
            return [self._row(row) for row in conn.execute(query, tuple(params)).fetchall()]

    def list_pending(self, chat_id: str | None = None) -> list[dict]:
        return self.list_reminders(chat_id, "pending")

    def find_duplicate(
        self,
        *,
        chat_id: str,
        title: str,
        remind_at: str,
        deadline_at: str | None = None,
    ) -> dict | None:
        _ensure_db()
        normalized = _normalize_title(title)
        with connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM reminders
                WHERE chat_id = ?
                  AND remind_at = ?
                  AND COALESCE(deadline_at, '') = COALESCE(?, '')
                  AND status IN ('pending', 'processing', 'sent', 'closed')
                """,
                (chat_id, remind_at, deadline_at),
            ).fetchall()
        for row in rows:
            data = self._row(row)
            if _normalize_title(data["title"]) == normalized:
                return data
        return None

    def get_due_reminders(self, now_iso: str, limit: int = 50) -> list[dict]:
        _ensure_db()
        with connect() as conn:
            return [
                self._row(row)
                for row in conn.execute(
                    """
                    SELECT * FROM reminders
                    WHERE status = 'pending' AND remind_at <= ?
                    ORDER BY remind_at ASC
                    LIMIT ?
                    """,
                    (now_iso, limit),
                ).fetchall()
            ]

    def due(self, now_iso: str) -> list[dict]:
        return self.get_due_reminders(now_iso)

    def atomic_claim_due_reminder(self, reminder_id: int | str, now_iso: str) -> dict | None:
        _ensure_db()
        with connect() as conn:
            cursor = conn.execute(
                """
                UPDATE reminders
                SET status = 'processing', locked_at = ?, updated_at = ?,
                    attempt_count = COALESCE(attempt_count, 0) + 1
                WHERE id = ? AND status = 'pending' AND remind_at <= ?
                """,
                (now_iso, now_iso, reminder_id, now_iso),
            )
            if cursor.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        return self._row(row) if row else None

    def mark_sent(self, reminder_id: int | str, sent_at: str) -> None:
        with connect() as conn:
            conn.execute(
                "UPDATE reminders SET status = 'sent', sent_at = ?, locked_at = NULL, updated_at = ? WHERE id = ? AND status = 'processing'",
                (sent_at, sent_at, reminder_id),
            )

    def mark_closed(self, reminder_id: int | str) -> None:
        now = _now()
        with connect() as conn:
            conn.execute(
                "UPDATE reminders SET status = 'closed', locked_at = NULL, updated_at = ? WHERE id = ? AND status IN ('pending', 'processing', 'sent')",
                (now, reminder_id),
            )

    def mark_expired(self, reminder_id: int | str, expired_at: str) -> None:
        with connect() as conn:
            conn.execute(
                "UPDATE reminders SET status = 'expired', expired_at = ?, locked_at = NULL, updated_at = ? WHERE id = ? AND status IN ('pending', 'processing')",
                (expired_at, expired_at, reminder_id),
            )

    def mark_failed(self, reminder_id: int | str, error: str) -> None:
        now = _now()
        with connect() as conn:
            conn.execute(
                "UPDATE reminders SET status = 'failed', last_error = ?, locked_at = NULL, updated_at = ? WHERE id = ? AND status = 'processing'",
                (error[:1000], now, reminder_id),
            )

    def cancel_reminder(self, reminder_id: int | str) -> None:
        now = _now()
        with connect() as conn:
            conn.execute(
                "UPDATE reminders SET status = 'cancelled', locked_at = NULL, updated_at = ? WHERE id = ? AND status NOT IN ('sent', 'closed', 'expired')",
                (now, reminder_id),
            )

    def cancel(self, reminder_id: int | str) -> None:
        self.cancel_reminder(reminder_id)

    def mark_done(self, reminder_id: int | str) -> None:
        self.mark_sent(reminder_id, _now())

    def _row(self, row) -> dict:
        data = dict(row)
        raw = data.pop("metadata_json", None)
        try:
            data["metadata"] = json.loads(raw or "{}")
        except Exception:
            data["metadata"] = {}
        return data
