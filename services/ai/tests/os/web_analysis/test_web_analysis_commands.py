from app.xninetzy.ecosystem.command_router import parse_command
from app.xninetzy.tools.registry import get_tool_names


def test_local_portal_slash_commands():
    assert parse_command("/jadwal") == ("portal_schedule", {})
    assert parse_command("/portalinfo") == ("portal_info", {})
    assert parse_command("/krs-watcher") == ("portal_krs_watcher_status", {})
    assert parse_command("/web-analysis mahasiswa") == (
        "web_analysis_status",
        {"site_slug": "mahasiswa"},
    )
    assert parse_command("/web-refresh hebat") == (
        "web_analysis_refresh",
        {"site_slug": "hebat"},
    )


def test_new_tools_registered():
    names = get_tool_names()
    assert "web_analysis_status" in names
    assert "web_analysis_refresh" in names
    assert "portal_info" in names
    assert "portal_schedule" in names
    assert "portal_krs_watcher_status" in names
