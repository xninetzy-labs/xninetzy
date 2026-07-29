from app.xninetzy.ecosystem.command_router import parse_command


def test_skill_command():
    assert parse_command("/skill research") == ("skill_get", {"name": "research"})


def test_approve_command():
    assert parse_command("/approve 1") == ("hitl_approve", {"approval_id": 1})


def test_hebat_debug_command():
    assert parse_command("/hebat-debug") == ("hebat_debug_login", {})


def test_grade_command_preserves_requested_period():
    assert parse_command("/nilai") == (
        "portal_grades",
        {"academic_period": "latest"},
    )
    assert parse_command("/nilai 287") == (
        "portal_grades",
        {"academic_period": "287"},
    )
