from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel


class NormalizedReminderContent(BaseModel):
    title: str
    description: str | None = None
    context_summary: str | None = None
    action_label: str
    display_time_label: str | None = None
    deadline_label: str | None = None
    offset_label: str | None = None
    source_reason: str | None = None


_FILLER_RE = re.compile(
    r"\b("
    r"ingatkan aku|ingetin aku|remind aku|reminder|remind|nanti|besok|hari ini|"
    r"jam|tanggal|deadline|buat|untuk|dong|ya|dari|sebelum|lagi|pagi|siang|sore|malam|"
    r"menit|jam|hari"
    r")\b",
    re.I,
)
_TIME_RE = re.compile(r"\bh\s*-\s*\d+\s*(menit|jam|hari)?\b|\b\d{1,2}([:.]\d{2})?\b", re.I)
_MONTH_RE = re.compile(
    r"\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b",
    re.I,
)
_SPECIAL_WORDS = {
    "ai": "AI",
    "api": "API",
    "apsi": "APSI",
    "cdm": "CDM",
    "dfd": "DFD",
    "pdm": "PDM",
    "sql": "SQL",
    "wa": "WA",
    "ui": "UI",
    "ux": "UX",
    "docker": "Docker",
    "compose": "Compose",
    "logs": "Logs",
}
_MONTHS_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


class ReminderContentNormalizer:
    @staticmethod
    def normalize(
        raw_user_message: str,
        parsed: dict | Any,
        context: dict | None = None,
    ) -> NormalizedReminderContent:
        context = context or {}
        get = parsed.get if isinstance(parsed, dict) else lambda key, default=None: getattr(parsed, key, default)
        task_text = get("task_text") or get("title_hint") or get("title") or raw_user_message
        reminder_type = get("reminder_type") or "explicit"
        title = generate_clean_title(str(task_text), context)
        description = generate_context_description(title, str(task_text), reminder_type, context)
        remind_at = _parse_dt(get("remind_at"))
        deadline_at = _parse_dt(get("deadline_at"))
        offset_label = generate_offset_label(get("offset_value"), get("offset_unit"), reminder_type)
        source_reason = _source_reason(reminder_type, context)
        context_summary = _context_summary(raw_user_message, title, reminder_type, context)
        return NormalizedReminderContent(
            title=title,
            description=description,
            context_summary=context_summary,
            action_label=_action_label(str(task_text), reminder_type),
            display_time_label=format_time_label(remind_at, context.get("now")) if remind_at else None,
            deadline_label=format_time_label(deadline_at, context.get("now")) if deadline_at else None,
            offset_label=offset_label,
            source_reason=source_reason,
        )


def generate_clean_title(task_text: str, context: dict | None = None) -> str:
    context = context or {}
    cleaned = _clean_task_text(task_text)
    lowered = cleaned.casefold()

    if context.get("source") == "planning" and context.get("deadline_at"):
        topic = _clean_task_text(str(context.get("title") or cleaned or "tugas"))
        prefix = "Review Final" if context.get("offset_unit") == "hours" else "Mulai Kerjakan"
        return _limit_words(f"{prefix} {topic}")

    if re.search(r"\b(docker\s+logs?|logs?|container)\b", lowered):
        return "Cek Docker Logs"
    if re.search(r"\bsubmit|kirim|kumpulkan|upload\b", lowered):
        return _limit_words(_title_case(_ensure_no_duplicate_verb(cleaned, "Submit")))
    if re.search(r"\btugas|assignment\b", lowered):
        return _limit_words(_title_case(_ensure_no_duplicate_verb(cleaned, "Kerjakan")))
    if re.search(r"\breview\b", lowered):
        return _limit_words(_title_case(_ensure_no_duplicate_verb(cleaned, "Review")))
    if re.search(r"\bbelajar|materi|roadmap\b", lowered):
        return _limit_words(_title_case(_ensure_no_duplicate_verb(cleaned, "Belajar")))
    if re.search(r"\bisi\b", lowered):
        return _limit_words(_title_case(cleaned))

    words = cleaned.split()
    if len(words) <= 2 and words:
        return _limit_words(_title_case(_ensure_no_duplicate_verb(cleaned, "Cek")))
    return _limit_words(_title_case(cleaned or "Lanjutkan Task"))


def generate_context_description(
    title: str,
    task_text: str,
    reminder_type: str,
    context: dict | None = None,
) -> str:
    blob = f"{title} {task_text} {(context or {}).get('source', '')}".casefold()
    if re.search(r"\b(docker\s+logs?|log|container)\b", blob):
        return "Periksa log container untuk memastikan service berjalan normal atau melihat error terbaru."
    if re.search(r"\b(tugas|assignment|deadline|apsi)\b", blob):
        if "review final" in blob:
            return "Cek ulang isi, format, dan kelengkapan sebelum deadline."
        if "mulai kerjakan" in blob:
            return "Mulai dari memahami instruksi dan menyusun kerangka agar pengerjaan tidak mepet."
        return "Selesaikan dan cek ulang tugas sebelum deadline agar masih ada waktu revisi."
    if re.search(r"\b(submit|kumpulkan|upload|form)\b", blob):
        return "Pastikan semua file atau form sudah lengkap sebelum dikirim."
    if re.search(r"\b(belajar|materi|roadmap)\b", blob):
        return "Lanjutkan sesi belajar sesuai rencana agar progres tetap berjalan."
    if re.search(r"\b(meeting|rapat|diskusi)\b", blob):
        return "Siapkan poin penting sebelum jadwal dimulai."
    return "Lanjutkan task ini sesuai rencana."


def generate_offset_label(value: Any, unit: Any, reminder_type: str = "explicit") -> str | None:
    if value is None or unit is None:
        return None
    unit_id = {"minutes": "menit", "hours": "jam", "days": "hari"}.get(str(unit), str(unit))
    if reminder_type == "deadline_offset":
        return f"H-{value} {unit_id} sebelum deadline"
    return f"{value} {unit_id} dari sekarang"


def format_time_label(value: datetime | None, now: datetime | None = None) -> str | None:
    if value is None:
        return None
    base = now.astimezone(value.tzinfo) if now and now.tzinfo and value.tzinfo else now
    if base and value.date() == base.date():
        return f"Hari ini, {value:%H:%M}"
    if base and value.date() == (base + timedelta(days=1)).date():
        return f"Besok, {value:%H:%M}"
    return f"{value.day} {_MONTHS_ID[value.month]} {value.year}, {value:%H:%M}"


def _clean_task_text(text: str) -> str:
    cleaned = str(text or "")
    cleaned = re.sub(r"\bdari\s+(deadline|dikumpulkan|batas|tenggat)\b.*", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\b(deadline|dikumpulkan|batas|tenggat)\b.*", " ", cleaned, flags=re.I)
    cleaned = _TIME_RE.sub(" ", cleaned)
    cleaned = _MONTH_RE.sub(" ", cleaned)
    cleaned = _FILLER_RE.sub(" ", cleaned)
    cleaned = re.sub(r"[,:;._-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _title_case(text: str) -> str:
    words = []
    for word in text.split():
        key = word.casefold()
        words.append(_SPECIAL_WORDS.get(key, word[:1].upper() + word[1:].lower()))
    return " ".join(words)


def _ensure_no_duplicate_verb(text: str, verb: str) -> str:
    return text if text.casefold().startswith(verb.casefold()) else f"{verb} {text}".strip()


def _limit_words(text: str, limit: int = 8) -> str:
    words = text.split()
    return " ".join(words[:limit]) or "Lanjutkan Task"


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _action_label(task_text: str, reminder_type: str) -> str:
    lowered = task_text.casefold()
    if re.search(r"\bsubmit|kumpulkan|upload\b", lowered):
        return "Submit sebelum deadline"
    if re.search(r"\btugas|assignment\b", lowered):
        return "Mulai kerjakan"
    if re.search(r"\breview\b", lowered):
        return "Review progress"
    if re.search(r"\bdocker\s+logs?|log|container\b", lowered):
        return "Cek sekarang"
    return "Lanjutkan task"


def _source_reason(reminder_type: str, context: dict) -> str:
    if reminder_type == "explicit":
        return "Diminta langsung oleh user"
    if context.get("source") == "planning":
        return "Dibuat otomatis karena planning memiliki deadline yang jelas"
    if context.get("source") == "goal":
        return "Dibuat otomatis dari goal yang punya waktu eksekusi"
    return "Dibuat otomatis karena ada deadline tugas"


def _context_summary(raw_user_message: str, title: str, reminder_type: str, context: dict) -> str:
    if context.get("source") == "planning":
        return "Reminder dibuat otomatis karena planning memiliki deadline yang jelas."
    if reminder_type == "explicit":
        return f"Reminder dibuat dari permintaan user untuk {title.casefold()}."
    return f"Reminder dibuat karena ada deadline untuk {title}."
