from __future__ import annotations

import asyncio
import json
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Awaitable, Callable

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.reminders.reminder_content import ReminderContentNormalizer
from app.xninetzy.os.reminders.reminder_store import ReminderStore

logger = logging.getLogger(__name__)

Sender = Callable[[dict], Awaitable[None]]


async def reminder_loop() -> None:
    settings = get_settings()
    if not settings.REMINDER_ENABLED:
        return
    interval = settings.REMINDER_SCHEDULER_INTERVAL_SECONDS or settings.REMINDER_POLL_INTERVAL_SECONDS
    while True:
        await run_scheduler_tick()
        await asyncio.sleep(interval)


async def run_scheduler_tick(
    *,
    now: datetime | None = None,
    store: ReminderStore | None = None,
    sender: Sender | None = None,
    limit: int = 50,
) -> dict:
    settings = get_settings()
    st = store or ReminderStore()
    current = _now(now)
    due = st.get_due_reminders(current.isoformat(), limit=limit)
    stats = {"sent": 0, "expired": 0, "failed": 0, "skipped": 0}

    for reminder in due:
        claimed = st.atomic_claim_due_reminder(reminder["id"], current.isoformat())
        if not claimed:
            stats["skipped"] += 1
            continue
        if _is_expired(claimed, current, settings.REMINDER_EXPIRE_AFTER_HOURS):
            st.mark_expired(claimed["id"], current.isoformat())
            stats["expired"] += 1
            continue
        try:
            await (sender or send_reminder)(claimed)
            st.mark_sent(claimed["id"], current.isoformat())
            stats["sent"] += 1
        except Exception as error:
            logger.warning("Failed to send reminder %s: %s", claimed["id"], error)
            st.mark_failed(claimed["id"], str(error))
            stats["failed"] += 1
    return stats


async def send_reminder(reminder: dict) -> None:
    payload = {
        "tool": "send_text_message",
        "input": {"jid": reminder["chat_id"], "text": format_reminder_message(reminder)},
    }
    await asyncio.to_thread(_post_mcp_call, payload)


def format_reminder_message(reminder: dict) -> str:
    normalized = _normalized(reminder)
    lines = [
        "⏰ Reminder",
        "",
        f"📌 {normalized['title']}",
    ]
    if normalized.get("description"):
        lines += ["", normalized["description"]]
    lines += ["", "🕒 Waktu:", normalized.get("display_time_label") or _human_dt(reminder["remind_at"])]
    if normalized.get("deadline_label"):
        lines += ["", "📅 Deadline:", normalized["deadline_label"]]
    if normalized.get("offset_label"):
        lines += ["", "⏳ Jenis reminder:", normalized["offset_label"]]
    lines += ["", "✅ Reminder ini dikirim sekali saja dan setelah itu otomatis ditutup."]
    return "\n".join(lines).strip()


def _post_mcp_call(payload: dict) -> None:
    settings = get_settings()
    request = urllib.request.Request(
        f"{settings.WA_MCP_BASE_URL.rstrip('/')}/mcp/call",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **_auth_header()},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status >= 400:
            raise RuntimeError(f"WA MCP returned HTTP {response.status}")


def _auth_header() -> dict[str, str]:
    key = get_settings().WA_MCP_API_KEY
    return {"Authorization": f"Bearer {key}"} if key else {}


def _now(now: datetime | None = None) -> datetime:
    tz = ZoneInfo(get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE)
    if now is None:
        return datetime.now(tz)
    return now.astimezone(tz) if now.tzinfo else now.replace(tzinfo=tz)


def _is_expired(reminder: dict, now: datetime, expire_after_hours: int) -> bool:
    remind_at = datetime.fromisoformat(reminder["remind_at"])
    deadline_raw = reminder.get("deadline_at")
    if now > remind_at + timedelta(hours=expire_after_hours):
        return True
    if deadline_raw and now > datetime.fromisoformat(deadline_raw):
        return True
    return False


def _offset_label(reminder: dict) -> str | None:
    value = reminder.get("offset_value")
    unit = reminder.get("offset_unit")
    if not value or not unit:
        return None
    unit_id = {"minutes": "menit", "hours": "jam", "days": "hari"}.get(unit, unit)
    return f"H-{value} {unit_id} sebelum deadline"


def _human_dt(value: str) -> str:
    dt = datetime.fromisoformat(value)
    return dt.strftime("%d %B %Y, %H:%M")


def _normalized(reminder: dict) -> dict:
    if reminder.get("display_time_label") or reminder.get("context_summary"):
        return {
            "title": reminder.get("title") or "Reminder",
            "description": reminder.get("description"),
            "display_time_label": reminder.get("display_time_label"),
            "deadline_label": reminder.get("deadline_label"),
            "offset_label": reminder.get("offset_label") or _offset_label(reminder),
        }
    normal = ReminderContentNormalizer.normalize(
        reminder.get("raw_user_message") or reminder.get("normalized_task_text") or reminder.get("title") or "",
        {
            "title": reminder.get("title"),
            "task_text": reminder.get("normalized_task_text") or reminder.get("title"),
            "remind_at": reminder.get("remind_at"),
            "deadline_at": reminder.get("deadline_at"),
            "offset_value": reminder.get("offset_value"),
            "offset_unit": reminder.get("offset_unit"),
            "reminder_type": reminder.get("reminder_type") or "explicit",
        },
    )
    return normal.model_dump()
