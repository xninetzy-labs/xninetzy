from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.reminders.reminder_content import ReminderContentNormalizer
from app.xninetzy.os.reminders.reminder_parser import parse_reminder, infer_deadline
from app.xninetzy.os.reminders.reminder_policy import ReminderPolicy
from app.xninetzy.os.reminders.reminder_store import ReminderStore


class ReminderService:
    def __init__(self, store: ReminderStore | None = None) -> None:
        self.store = store or ReminderStore()

    def create_from_message(
        self,
        chat_id: str,
        sender_id: str | None,
        message: str,
        *,
        source: str = "user",
        source_ref_id: str | None = None,
        now: datetime | None = None,
    ) -> dict:
        parsed = parse_reminder(message, now=now)
        return self.create_from_parsed(
            chat_id=chat_id,
            user_id=sender_id,
            sender_id=sender_id,
            source=source,
            source_ref_id=source_ref_id,
            parsed=parsed,
            context={"source": source, "now": now},
            now=now,
        )

    def create_from_parsed(
        self,
        *,
        chat_id: str,
        parsed: dict,
        user_id: str | None = None,
        sender_id: str | None = None,
        source: str = "user",
        source_ref_id: str | None = None,
        context: dict | None = None,
        now: datetime | None = None,
    ) -> dict:
        current = _now(now)
        remind_at = _parse_dt(parsed["remind_at"])
        deadline_at = _parse_dt(parsed["deadline_at"]) if parsed.get("deadline_at") else None
        raw = parsed.get("raw_text") or (parsed.get("metadata") or {}).get("source_text") or parsed.get("title") or ""
        normal = ReminderContentNormalizer.normalize(
            raw,
            parsed,
            {
                **(context or {}),
                "source": source,
                "now": current,
                "deadline_at": deadline_at,
                "title": parsed.get("title"),
                "offset_value": parsed.get("offset_value"),
                "offset_unit": parsed.get("offset_unit"),
            },
        )
        if deadline_at and deadline_at <= current:
            return {"created": False, "reason": "deadline_passed", "title": normal.title}
        if remind_at <= current:
            return {"created": False, "reason": "remind_at_passed", "title": normal.title}

        duplicate = self.store.find_duplicate(
            chat_id=chat_id,
            title=normal.title,
            deadline_at=deadline_at.isoformat() if deadline_at else None,
            remind_at=remind_at.isoformat(),
        )
        if duplicate:
            duplicate["created"] = False
            duplicate["duplicate"] = True
            return duplicate

        row = self.store.create_reminder(
            chat_id=chat_id,
            user_id=user_id,
            sender_id=sender_id,
            source=source,
            source_ref_id=source_ref_id,
            title=normal.title,
            description=normal.description,
            context_summary=normal.context_summary,
            action_label=normal.action_label,
            display_time_label=normal.display_time_label,
            deadline_label=normal.deadline_label,
            offset_label=normal.offset_label,
            source_reason=normal.source_reason,
            raw_user_message=raw,
            normalized_task_text=parsed.get("task_text") or parsed.get("title_hint") or normal.title,
            deadline_at=deadline_at.isoformat() if deadline_at else None,
            remind_at=remind_at.isoformat(),
            timezone=parsed.get("timezone"),
            priority=parsed.get("priority", "normal"),
            reminder_type=parsed.get("reminder_type", "explicit"),
            offset_value=parsed.get("offset_value"),
            offset_unit=parsed.get("offset_unit"),
            metadata={**(parsed.get("metadata") or {}), "normalized": normal.model_dump()},
        )
        row["created"] = True
        return row

    def create_auto_from_context(
        self,
        *,
        chat_id: str,
        user_id: str | None,
        text: str,
        title: str | None = None,
        description: str | None = None,
        source: str = "planning",
        source_ref_id: str | None = None,
        now: datetime | None = None,
    ) -> list[dict]:
        if not get_settings().REMINDER_AUTO_CREATE_ENABLED:
            return []
        current = _now(now)
        deadline_at = infer_deadline(text, now=current)
        if not ReminderPolicy.should_auto_create({"text": text, "deadline_at": deadline_at, "source": source}):
            return []
        if not deadline_at:
            remind_at = ReminderPolicy.next_work_session(current, text)
            candidates = [(None, None, remind_at)]
        else:
            if deadline_at <= current:
                return [{"created": False, "reason": "deadline_passed", "title": title or _title_from_text(text)}]
            candidates = []
            for offset in ReminderPolicy.default_offsets({"deadline_at": deadline_at, "text": text}, current)[:3]:
                remind_at = current + timedelta(minutes=1) if offset.unit == "minutes" else deadline_at - offset.delta()
                if remind_at > current:
                    candidates.append((offset.value, offset.unit, remind_at))

        created: list[dict] = []
        base_title = title or _title_from_text(text)
        max_candidates = 2 if source == "planning" else 3
        for offset_value, offset_unit, remind_at in candidates[:max_candidates]:
            parsed = {
                "title": base_title,
                "task_text": base_title,
                "title_hint": base_title,
                "description": description,
                "deadline_at": deadline_at.isoformat() if deadline_at else None,
                "remind_at": remind_at.isoformat(),
                "timezone": get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE,
                "priority": ReminderPolicy.classify_priority(text),
                "reminder_type": "deadline_offset" if deadline_at else ReminderPolicy.infer_reminder_type({"source": source}),
                "offset_value": offset_value,
                "offset_unit": offset_unit,
                "metadata": {"source_text": text, "auto_created": True},
            }
            created.append(self.create_from_parsed(
                chat_id=chat_id,
                user_id=user_id,
                sender_id=user_id,
                source=source,
                source_ref_id=source_ref_id,
                parsed=parsed,
                context={
                    "source": source,
                    "now": current,
                    "title": base_title,
                    "deadline_at": deadline_at,
                    "offset_value": offset_value,
                    "offset_unit": offset_unit,
                    "milestones": description,
                },
                now=current,
            ))
        return created

    def list_pending(self, chat_id: str | None = None) -> list[dict]:
        return self.store.list_pending(chat_id)

    def list_reminders(self, chat_id: str | None = None, status: str | None = None) -> list[dict]:
        return self.store.list_reminders(chat_id, status)

    def due(self, now_iso: str, limit: int = 50) -> list[dict]:
        return self.store.get_due_reminders(now_iso, limit)

    def close(self, reminder_id: int | str) -> None:
        self.store.mark_closed(reminder_id)

    def cancel(self, reminder_id: int | str) -> None:
        self.store.cancel_reminder(reminder_id)


def _now(now: datetime | None = None) -> datetime:
    tz = ZoneInfo(get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE)
    if now is None:
        return datetime.now(tz)
    return now.astimezone(tz) if now.tzinfo else now.replace(tzinfo=tz)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _title_from_text(text: str) -> str:
    cleaned = text
    for token in ("buat planning", "bikin planning", "buatkan planning", "todo list", "deadline"):
        cleaned = cleaned.replace(token, " ")
    cleaned = " ".join(cleaned.split()).strip(" ,.-")
    return (cleaned[:1].upper() + cleaned[1:])[:80] if cleaned else "Reminder"


def format_reminder_creation_response(reminder: dict) -> str:
    if not reminder.get("created") and reminder.get("duplicate"):
        header = "✅ Reminder sudah ada"
    elif not reminder.get("created"):
        return f"⚠️ Reminder tidak dibuat: {reminder.get('reason', 'waktu tidak valid')}"
    else:
        header = "✅ Reminder berhasil dibuat"

    lines = [
        header,
        "",
        "📌 Judul:",
        reminder.get("title") or "Reminder",
    ]
    description = reminder.get("description")
    if description:
        lines += ["", "🧠 Konteks:", description]
    lines += ["", "🕒 Akan diingatkan:", reminder.get("display_time_label") or reminder.get("remind_at", "-")]
    if reminder.get("deadline_label") or reminder.get("deadline_at"):
        lines += ["", "📅 Deadline:", reminder.get("deadline_label") or reminder["deadline_at"]]
    if reminder.get("offset_label"):
        lines += ["", "⏳ Reminder:", reminder["offset_label"]]
    lines += ["", "Reminder ini akan dikirim sekali saja, lalu otomatis ditutup."]
    return "\n".join(lines)


def format_auto_reminder_summary(reminders: list[dict], *, planning_created: bool = True) -> str:
    made = [r for r in reminders if r.get("created") or r.get("duplicate")]
    if not made:
        return (
            "✅ Planning berhasil dibuat\n\n"
            "Aku belum membuat reminder otomatis karena belum ada jadwal atau deadline yang jelas.\n"
            'Kalau mau, kamu bisa bilang: "ingatkan aku besok jam 8 malam".'
        )
    lines = [
        "✅ Planning berhasil dibuat",
        "",
        "Aku juga otomatis membuat reminder karena planning ini punya deadline yang jelas.",
        "",
    ]
    for r in made:
        label = r.get("offset_label") or "Reminder"
        when = r.get("display_time_label") or r.get("remind_at")
        lines += [f"📌 {r.get('title')}", f"- {label}: {when}", ""]
    lines.append("Reminder akan dikirim sekali saja, lalu otomatis ditutup.")
    return "\n".join(lines).strip()
