from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.os.reminders.reminder_parser import parse_reminder


NOW = datetime(2026, 6, 3, 9, 0, tzinfo=ZoneInfo("Asia/Jakarta"))


def test_parse_h_minus_two_hours_from_deadline():
    parsed = parse_reminder("buatkan saya reminder untuk tugas A h-2 jam dari deadline jam 10 malam", now=NOW)
    assert parsed["title"] == "Tugas A"
    assert parsed["deadline_at"] == "2026-06-03T22:00:00+07:00"
    assert parsed["remind_at"] == "2026-06-03T20:00:00+07:00"
    assert parsed["offset_value"] == 2
    assert parsed["offset_unit"] == "hours"
    assert parsed["reminder_type"] == "deadline_offset"


def test_parse_h_minus_one_day():
    parsed = parse_reminder("deadline tugas APSI tanggal 5 Juni jam 10 malam, remind h-1 hari", now=NOW)
    assert parsed["title"] == "Tugas APSI"
    assert parsed["deadline_at"] == "2026-06-05T22:00:00+07:00"
    assert parsed["remind_at"] == "2026-06-04T22:00:00+07:00"
    assert parsed["offset_value"] == 1
    assert parsed["offset_unit"] == "days"


def test_parse_relative_minutes():
    parsed = parse_reminder("ingatkan aku 30 menit lagi buat cek docker logs", now=NOW)
    assert parsed["title"] == "Cek docker logs"
    assert parsed["deadline_at"] is None
    assert parsed["remind_at"] == "2026-06-03T09:30:00+07:00"


def test_parse_tomorrow_at_hour():
    parsed = parse_reminder("ingatkan aku besok jam 8 buat belajar", now=NOW)
    assert parsed["title"] == "Belajar"
    assert parsed["deadline_at"] is None
    assert parsed["remind_at"] == "2026-06-04T08:00:00+07:00"


def test_parse_explicit_date_timezone():
    parsed = parse_reminder("reminder tugas database tanggal 5 Juni jam 20.30", now=NOW)
    assert parsed["remind_at"] == "2026-06-05T20:30:00+07:00"
    assert parsed["timezone"] == "Asia/Jakarta"
