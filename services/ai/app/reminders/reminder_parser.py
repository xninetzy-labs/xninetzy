from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import get_settings


class ReminderParseError(ValueError):
    pass


def parse_reminder(message: str) -> dict:
    tz = ZoneInfo(get_settings().APP_TIMEZONE)
    now = datetime.now(tz)
    text = message.casefold()

    title = _clean_title(message)
    remind_at: datetime | None = None

    in_hours = re.search(r"(\d+)\s*jam lagi", text)
    if in_hours:
        remind_at = now + timedelta(hours=int(in_hours.group(1)))

    tomorrow_at = re.search(r"besok(?:\s+jam)?\s+(\d{1,2})(?:[:.](\d{2}))?", text)
    if tomorrow_at:
        hour = int(tomorrow_at.group(1))
        minute = int(tomorrow_at.group(2) or 0)
        remind_at = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)

    today_at = re.search(r"(?:nanti|hari ini)?\s*jam\s+(\d{1,2})(?:[:.](\d{2}))?", text)
    if today_at and remind_at is None:
        hour = int(today_at.group(1))
        minute = int(today_at.group(2) or 0)
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        remind_at = candidate if candidate > now else candidate + timedelta(days=1)

    if "besok pagi" in text and remind_at is None:
        remind_at = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

    if remind_at is None:
        raise ReminderParseError("Waktu reminder masih ambigu. Sebutin tanggal/jamnya ya, misalnya 'besok jam 8'.")

    return {"title": title or "Reminder", "description": None, "remind_at": remind_at.isoformat(), "timezone": get_settings().APP_TIMEZONE}


def _clean_title(message: str) -> str:
    cleaned = re.sub(r"(?i)\b(ingatkan aku|ingetin aku|remind aku|reminder|besok|nanti|hari ini|jam|buat|untuk)\b", " ", message)
    cleaned = re.sub(r"\d{1,2}([:.]\d{2})?|\d+\s*jam lagi", " ", cleaned)
    return " ".join(cleaned.split()).capitalize()
