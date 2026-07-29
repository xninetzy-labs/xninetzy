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
    assert parse_command("/nilai changes") == (
        "portal_grade_changes",
        {"academic_period": ""},
    )
    assert parse_command("/nilai perubahan 2024/2025 - Ganjil") == (
        "portal_grade_changes",
        {"academic_period": "2024/2025 - Ganjil"},
    )


def test_cyber_campus_read_commands_use_shared_tools():
    assert parse_command("/cyber-profile") == ("portal_profile", {})
    assert parse_command("/status-akademik") == ("portal_academic_status", {})
    assert parse_command("/krs status") == ("portal_current_krs", {})


def test_concept_map_command_uses_shared_learning_tool():
    assert parse_command("/concepts 12") == (
        "learning_get_concept_map",
        {"roadmap_id": 12},
    )
