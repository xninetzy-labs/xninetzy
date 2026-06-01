from app.ecosystem.command_router import parse_command


def test_memory_commands():
    assert parse_command("/remember aku belajar APSI") == (
        "memory_add", {"content": "aku belajar APSI"},
    )
    assert parse_command("/memory") == ("memory_list", {})
    assert parse_command("/memory search jaringan") == (
        "memory_search", {"query": "jaringan"},
    )
    assert parse_command("/memory delete 4") == ("memory_forget", {"memory_id": 4})
    assert parse_command("/forget-memory 7") == ("memory_forget", {"memory_id": 7})


def test_lightning_commands():
    assert parse_command("/feedback tadi salah, harusnya ringkas") == (
        "lightning_feedback", {"feedback_text": "tadi salah, harusnya ringkas"},
    )
    assert parse_command("/fix-agent kenapa tadi salah") == (
        "lightning_feedback", {"feedback_text": "kenapa tadi salah"},
    )
    assert parse_command("/agent-proposals") == ("lightning_list_proposals", {})
    assert parse_command("/agent-improve") == ("lightning_improve", {})
    assert parse_command("/agent-approve 2") == ("lightning_approve", {"proposal_id": 2})
    assert parse_command("/agent-reject 2") == ("lightning_reject", {"proposal_id": 2})
    assert parse_command("/agent-errors") == ("lightning_errors", {})
    assert parse_command("/test-lightning") == ("lightning_healthcheck", {})


def test_tools_registered():
    from app.tools.registry import get_tool_names

    names = get_tool_names()
    for t in ("memory_add", "memory_search", "memory_list", "memory_forget",
              "memory_get_context", "lightning_feedback", "lightning_list_proposals",
              "lightning_improve", "lightning_approve", "lightning_reject",
              "lightning_errors", "lightning_healthcheck"):
        assert t in names
