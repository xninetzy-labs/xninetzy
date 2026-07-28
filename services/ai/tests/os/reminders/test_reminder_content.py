from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.os.reminders.reminder_content import ReminderContentNormalizer, generate_clean_title
from app.xninetzy.os.reminders.reminder_parser import parse_reminder


NOW = datetime(2026, 6, 3, 20, 0, tzinfo=ZoneInfo("Asia/Jakarta"))


def test_normalize_docker_logs_reminder():
    raw = "ingatkan aku 30 menit lagi buat cek docker logs"
    parsed = parse_reminder(raw, now=NOW)
    output = ReminderContentNormalizer.normalize(raw, parsed, {"now": NOW})
    assert output.title == "Cek Docker Logs"
    assert "log container" in output.description.lower()
    assert output.display_time_label == "Hari ini, 20:30"


def test_normalize_assignment_deadline_reminder():
    raw = "remind h-2 jam tugas APSI deadline jam 10 malam"
    parsed = parse_reminder(raw, now=datetime(2026, 6, 3, 19, 0, tzinfo=ZoneInfo("Asia/Jakarta")))
    output = ReminderContentNormalizer.normalize(raw, parsed, {"now": NOW})
    assert output.title == "Kerjakan Tugas APSI"
    assert output.offset_label == "H-2 jam sebelum deadline"


def test_raw_text_not_used_as_final_title():
    raw = "ingatkan aku nanti malam buat docker logs"
    parsed = parse_reminder(raw, now=datetime(2026, 6, 3, 9, 0, tzinfo=ZoneInfo("Asia/Jakarta")))
    output = ReminderContentNormalizer.normalize(raw, parsed)
    assert output.title != "docker logs"
    assert output.title == "Cek Docker Logs"


def test_auto_planning_reminder_has_readable_title():
    output = ReminderContentNormalizer.normalize(
        "Pahami instruksi & kumpulkan bahan",
        {
            "task_text": "Pahami instruksi & kumpulkan bahan",
            "title": "Tugas",
            "remind_at": "2026-06-04T22:00:00+07:00",
            "deadline_at": "2026-06-05T22:00:00+07:00",
            "offset_value": 1,
            "offset_unit": "days",
            "reminder_type": "deadline_offset",
        },
        {"source": "planning", "title": "Tugas", "deadline_at": "2026-06-05T22:00:00+07:00", "offset_unit": "days"},
    )
    assert output.title in [
        "Mulai Kerjakan Tugas",
        "Mulai Kumpulkan Bahan Tugas",
        "Mulai Persiapan Tugas",
    ]


def test_generate_clean_title_examples():
    assert generate_clean_title("docker logs") == "Cek Docker Logs"
    assert generate_clean_title("tugas APSI") == "Kerjakan Tugas APSI"
    assert generate_clean_title("submit form") == "Submit Form"
    assert generate_clean_title("review materi ai") == "Review Materi AI"
