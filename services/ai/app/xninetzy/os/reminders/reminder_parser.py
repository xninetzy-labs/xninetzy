from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.reminders.reminder_policy import Offset, ReminderPolicy


class ReminderParseError(ValueError):
    pass


class ParsedReminder(BaseModel):
    raw_text: str
    task_text: str
    title_hint: str | None = None
    deadline_at: datetime | None = None
    remind_at: datetime
    offset_value: int | None = None
    offset_unit: str | None = None
    reminder_type: str
    priority: str
    confidence: float = 0.9


_MONTHS = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "maret": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "agt": 8,
    "september": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "desember": 12, "des": 12,
}


def parse_reminder(message: str, *, now: datetime | None = None) -> dict:
    tz = ZoneInfo(get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE)
    current = _normalize_now(now, tz)
    text = message.casefold()

    offset = _extract_offset(text)
    explicit_offset = _extract_relative_offset(text)
    deadline_at = _extract_deadline(text, current)
    explicit_at = _extract_explicit_remind_at(text, current)
    priority = ReminderPolicy.classify_priority(message)

    reminder_type = "deadline_offset" if deadline_at and offset else "explicit"
    if deadline_at and offset:
        remind_at = deadline_at - offset.delta()
    elif explicit_at:
        remind_at = explicit_at
    elif deadline_at:
        offsets = ReminderPolicy.default_offsets({"deadline_at": deadline_at, "text": message}, current)
        if not offsets:
            raise ReminderParseError("Deadline sudah lewat atau terlalu dekat untuk membuat reminder.")
        offset = offsets[0]
        reminder_type = "deadline_offset"
        remind_at = current + timedelta(minutes=1) if offset.unit == "minutes" else deadline_at - offset.delta()
    else:
        raise ReminderParseError("Waktu reminder masih ambigu. Sebutin tanggal/jamnya ya, misalnya 'besok jam 8'.")

    if remind_at <= current:
        if deadline_at and deadline_at > current and deadline_at - current < timedelta(hours=2):
            remind_at = current + timedelta(minutes=1)
            offset = Offset(1, "minutes")
            priority = "urgent"
        else:
            raise ReminderParseError("Waktu reminder sudah lewat. Pilih waktu yang masih valid.")

    title = _clean_title(message)
    task_text = _clean_task_text(message)
    output_offset = offset or explicit_offset
    return {
        "raw_text": message,
        "task_text": task_text or title or message,
        "title_hint": task_text or title or None,
        "title": title or "Reminder",
        "description": None,
        "deadline_at": deadline_at.isoformat() if deadline_at else None,
        "remind_at": remind_at.isoformat(),
        "timezone": get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE,
        "priority": priority,
        "reminder_type": reminder_type,
        "offset_value": output_offset.value if output_offset else None,
        "offset_unit": output_offset.unit if output_offset else None,
        "confidence": 0.95 if task_text else 0.75,
        "metadata": {"source_text": message, "raw_text": message},
    }


def infer_deadline(message: str, *, now: datetime | None = None) -> datetime | None:
    tz = ZoneInfo(get_settings().REMINDER_DEFAULT_TIMEZONE or get_settings().APP_TIMEZONE)
    return _extract_deadline(message.casefold(), _normalize_now(now, tz))


def _normalize_now(now: datetime | None, tz: ZoneInfo) -> datetime:
    if now is None:
        return datetime.now(tz)
    return now.astimezone(tz) if now.tzinfo else now.replace(tzinfo=tz)


def _extract_offset(text: str) -> Offset | None:
    patterns = (
        r"\bh\s*-\s*(\d+)\s*(menit|minute|minutes|min|jam|hour|hours|hari|day|days)\b",
        r"\b(\d+)\s*(menit|minute|minutes|min|jam|hour|hours|hari|day|days)\s+sebelum\s+deadline\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = int(match.group(1))
        unit = _unit(match.group(2))
        return Offset(value, unit)
    return None


def _extract_relative_offset(text: str) -> Offset | None:
    rel = re.search(r"\b(\d+)\s*(menit|minute|minutes|min|jam|hour|hours|hari|day|days)\s+lagi\b", text)
    if not rel:
        return None
    return Offset(int(rel.group(1)), _unit(rel.group(2)))


def _unit(raw: str) -> str:
    raw = raw.casefold()
    if raw in {"menit", "minute", "minutes", "min"}:
        return "minutes"
    if raw in {"hari", "day", "days"}:
        return "days"
    return "hours"


def _extract_deadline(text: str, now: datetime) -> datetime | None:
    date_part = _extract_date(text, now)
    time_part = _extract_time(text, default_hour=22 if "malam" in text else 10)

    if re.search(r"\b(deadline|dikumpulkan|batas|tenggat)\b", text):
        if date_part and time_part:
            return date_part.replace(hour=time_part[0], minute=time_part[1], second=0, microsecond=0)
        if date_part:
            return date_part.replace(hour=23, minute=59, second=0, microsecond=0)
        if time_part:
            candidate = now.replace(hour=time_part[0], minute=time_part[1], second=0, microsecond=0)
            return candidate if candidate > now else candidate + timedelta(days=1)

    return None


def _extract_explicit_remind_at(text: str, now: datetime) -> datetime | None:
    rel = re.search(r"\b(\d+)\s*(menit|minute|minutes|min|jam|hour|hours|hari|day|days)\s+lagi\b", text)
    if rel:
        return now + Offset(int(rel.group(1)), _unit(rel.group(2))).delta()

    if "besok pagi" in text:
        return (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    if "nanti malam" in text or "malam ini" in text:
        candidate = now.replace(hour=19, minute=0, second=0, microsecond=0)
        return candidate if candidate > now else candidate + timedelta(days=1)

    date_part = _extract_date(text, now)
    time_part = _extract_time(text)
    if date_part and time_part:
        return date_part.replace(hour=time_part[0], minute=time_part[1], second=0, microsecond=0)
    if date_part:
        return date_part.replace(hour=8, minute=0, second=0, microsecond=0)
    if time_part:
        candidate = now.replace(hour=time_part[0], minute=time_part[1], second=0, microsecond=0)
        return candidate if candidate > now else candidate + timedelta(days=1)
    return None


def _extract_date(text: str, now: datetime) -> datetime | None:
    if "besok" in text:
        return now + timedelta(days=1)
    if "hari ini" in text:
        return now

    match = re.search(r"\btanggal\s+(\d{1,2})\s+([a-zA-Z]+)(?:\s+(\d{4}))?", text)
    if not match:
        match = re.search(r"\b(\d{1,2})\s+([a-zA-Z]+)(?:\s+(\d{4}))?", text)
    if not match:
        return None

    day = int(match.group(1))
    month = _MONTHS.get(match.group(2).casefold())
    if not month:
        return None
    year = int(match.group(3) or now.year)
    candidate = now.replace(year=year, month=month, day=day)
    if candidate.date() < now.date() and not match.group(3):
        candidate = candidate.replace(year=year + 1)
    return candidate


def _extract_time(text: str, default_hour: int | None = None) -> tuple[int, int] | None:
    match = re.search(r"\bjam\s+(\d{1,2})(?:[:.](\d{2}))?\s*(pagi|siang|sore|malam)?", text)
    if not match:
        return (default_hour, 0) if default_hour is not None else None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3)
    if period == "malam" and hour < 12:
        hour += 12
    elif period == "sore" and hour < 12:
        hour += 12
    elif period == "siang" and hour < 11:
        hour += 12
    elif period == "pagi" and hour == 12:
        hour = 0
    elif not period and "malam" in text and hour < 12:
        hour += 12
    return hour, minute


def _clean_title(message: str) -> str:
    cleaned = _clean_task_text(message)
    return cleaned[:1].upper() + cleaned[1:] if cleaned else ""


def _clean_task_text(message: str) -> str:
    cleaned = message
    cleaned = re.sub(r"(?i)\b(ingatkan aku|ingetin aku|remind aku|reminder|buatkan saya reminder|buatkan reminder|buat reminder|remind)\b", " ", cleaned)
    cleaned = re.sub(r"(?i)\bdari\s+(deadline|dikumpulkan|batas|tenggat)\b.*", " ", cleaned)
    cleaned = re.sub(r"(?i)\b(deadline|dikumpulkan|batas|tenggat)\b", " ", cleaned)
    cleaned = re.sub(r"(?i)\bh\s*-\s*\d+\s*(menit|jam|hari)\b", " ", cleaned)
    cleaned = re.sub(r"(?i)\b\d+\s*(menit|jam|hari)\s+(lagi|sebelum deadline)\b", " ", cleaned)
    cleaned = re.sub(r"(?i)\b(besok|nanti|hari ini|malam ini|nanti malam|jam|tanggal|buat|untuk|dari|pagi|siang|sore|malam)\b", " ", cleaned)
    cleaned = re.sub(r"(?i)\b\d{1,2}([:.]\d{2})?\b", " ", cleaned)
    cleaned = re.sub(r"(?i)\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b", " ", cleaned)
    cleaned = " ".join(cleaned.split()).strip(" ,.-")
    return cleaned
