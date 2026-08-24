from __future__ import annotations

from app.xninetzy.os.academic.mahasiswa_portal.session_watchdog import (
    build_watchdog_message,
    evaluate_session_health,
    format_session_age,
)


def test_missing_session_is_reported():
    assert evaluate_session_health({"exists": False}, 3600) == "missing"


def test_fresh_session_within_threshold():
    info = {"exists": True, "age_seconds": 120}
    assert evaluate_session_health(info, 3600) == "fresh"


def test_stale_session_beyond_threshold():
    info = {"exists": True, "age_seconds": 7200}
    assert evaluate_session_health(info, 3600) == "stale"


def test_unknown_age_is_flagged():
    info = {"exists": True, "age_seconds": None}
    assert evaluate_session_health(info, 3600) == "unknown_age"


def test_message_includes_command_and_age():
    message = build_watchdog_message("UACC SSO", "stale", "/uacc-login", 90000)
    assert "/uacc-login" in message
    assert "25 jam" in message


def test_missing_message_mentions_login_flow():
    message = build_watchdog_message("Cyber Campus", "missing", "/cyber-login", None)
    assert "/cyber-login" in message
    assert "session belum ada" in message


def test_format_session_age_hours_and_minutes():
    assert format_session_age(9000) == "2 jam 30 menit"
    assert format_session_age(59) == "0 menit"
    assert format_session_age(None) == "tidak diketahui"
