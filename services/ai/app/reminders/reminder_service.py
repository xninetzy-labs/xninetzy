from __future__ import annotations

from app.reminders.reminder_parser import parse_reminder
from app.reminders.reminder_store import ReminderStore


class ReminderService:
    def __init__(self) -> None:
        self.store = ReminderStore()

    def create_from_message(self, chat_id: str, sender_id: str | None, message: str) -> dict:
        parsed = parse_reminder(message)
        return self.store.create(
            chat_id=chat_id,
            sender_id=sender_id,
            title=parsed["title"],
            description=parsed["description"],
            remind_at=parsed["remind_at"],
        )

    def list_pending(self, chat_id: str | None = None) -> list[dict]:
        return self.store.list_pending(chat_id)

    def cancel(self, reminder_id: int) -> None:
        self.store.cancel(reminder_id)
