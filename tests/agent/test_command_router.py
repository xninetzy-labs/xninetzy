from app.xninetzy.ecosystem.command_router import parse_command


def test_skill_command():
    assert parse_command("/skill research") == ("skill_get", {"name": "research"})


def test_approve_command():
    assert parse_command("/approve 1") == ("hitl_approve", {"approval_id": 1})


def test_hebat_debug_command():
    assert parse_command("/hebat-debug") == ("hebat_debug_login", {})


def test_hebat_login_command_uses_shared_login_tool():
    assert parse_command("/hebat-login") == ("hebat_start_login", {})


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


def test_recall_commands_use_shared_learning_tools():
    assert parse_command("/recall") == (
        "learning_due_recall",
        {"roadmap_id": None},
    )
    assert parse_command("/recall 12") == (
        "learning_due_recall",
        {"roadmap_id": 12},
    )
    assert parse_command("/recall answer 7 4 model memakai data berlabel") == (
        "learning_submit_recall_answer",
        {
            "card_id": 7,
            "confidence": 4,
            "answer": "model memakai data berlabel",
        },
    )


def test_command_catalog_routes_to_shared_tool_catalog():
    assert parse_command("/commands research") == (
        "tool_catalog",
        {"feature_pack": "research"},
    )
    assert parse_command("/tools") == ("tool_catalog", {"feature_pack": ""})
