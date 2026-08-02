from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.tools.internal.datetime_info import datetime_now, get_now_info


def test_datetime_now_returns_human_string():
    result = datetime_now.invoke({})
    assert result.startswith("Sekarang:")
    assert "ISO:" in result


def test_datetime_now_contains_today_iso_date():
    result = datetime_now.invoke({})
    expected = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d")
    assert expected in result


def test_get_now_info_has_expected_keys():
    info = get_now_info()
    assert set(info) == {
        "iso",
        "timezone",
        "date",
        "time",
        "day_name",
        "human_date",
        "human_datetime",
    }


def test_get_now_info_iso_parses_and_matches_date():
    info = get_now_info()
    parsed = datetime.fromisoformat(info["iso"])
    assert parsed.date().isoformat() == info["date"]


def test_get_now_info_timezone_override():
    info = get_now_info("UTC")
    assert info["timezone"] == "UTC"
    parsed = datetime.fromisoformat(info["iso"])
    assert parsed.tzinfo is not None


def test_get_now_info_uses_app_timezone_by_default():
    info = get_now_info()
    assert info["timezone"] == "Asia/Jakarta"
