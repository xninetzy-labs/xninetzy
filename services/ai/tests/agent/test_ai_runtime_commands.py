from app.xninetzy.ecosystem.command_router import parse_command


def test_llm_commands():
    assert parse_command("/llm") == ("ai_provider_status", {})
    assert parse_command("/llm list") == ("ai_provider_list", {})
    assert parse_command("/llm use openrouter vendor/model") == (
        "ai_provider_use",
        {"provider": "openrouter", "model": "vendor/model"},
    )


def test_coding_agent_commands():
    assert parse_command("/agent") == ("coding_agent_status", {})
    assert parse_command("/agent list") == ("coding_agent_list", {})
    assert parse_command("/agent use claude-code") == (
        "coding_agent_use",
        {"runtime": "claude-code"},
    )
    assert parse_command("/code perbaiki test ini") == (
        "coding_agent_run",
        {"task": "perbaiki test ini"},
    )


def test_existing_agent_proposals_command_is_not_shadowed():
    assert parse_command("/agent-proposals") == ("lightning_list_proposals", {})
