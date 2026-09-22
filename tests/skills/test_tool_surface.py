from xninetzy.tools.registry import get_tool_names


def test_storm_tools_registered() -> None:
    names = get_tool_names()
    expected = [
        "research_storm_start",
        "research_storm_perspectives",
        "research_storm_questions",
        "research_storm_advance",
        "research_storm_packet",
        "research_storm_capabilities",
    ]
    for name in expected:
        assert name in names, f"missing {name}"


def test_learning_companion_tools_registered() -> None:
    names = get_tool_names()
    expected = [
        "learning_session_start",
        "learning_attempt_submit",
        "learning_hint",
        "learning_misconception_check",
        "learning_calibration",
        "learning_independence",
        "learning_next_action",
        "learning_capabilities",
    ]
    for name in expected:
        assert name in names, f"missing {name}"


def test_skill_routing_tools_registered() -> None:
    names = get_tool_names()
    expected = [
        "skill_route",
        "skill_compose",
        "skill_validate_output",
        "skill_validate_anti_slop",
        "skill_validate_submission_readiness",
        "skill_capabilities",
    ]
    for name in expected:
        assert name in names, f"missing {name}"
