from __future__ import annotations

import pytest

from xninetzy.os.hitl import approval_service, approval_tools


@pytest.fixture
def pending_approval(tmp_path, monkeypatch):
    from xninetzy.core.config import get_settings
    from xninetzy.db.sqlite import init_db
    from xninetzy.db.migrations import run_migrations

    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "approvals.sqlite3"))
    monkeypatch.setenv("APP_TIMEZONE", "UTC")
    monkeypatch.setenv("ADMIN_NAMES", "Synthetic Owner")
    for flag in ("LIGHTNING_ENABLED", "AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED"):
        monkeypatch.setenv(flag, "false")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    effects = []
    monkeypatch.setattr(approval_service, "_execute_approved_action", lambda row: effects.append(row) or "effect")
    approval_id = approval_service.request_approval(
        "synthetic-chat", "synthetic-owner", "synthetic_operation", "Fixture", "Fixture",
        {"target": "synthetic-target"},
    )
    yield approval_id, effects
    get_settings.cache_clear()


def assert_unchanged(approval_id, effects):
    row = approval_service.get_approval_status(approval_id)
    assert row["status"] == "pending"
    assert row["approved_at"] is None
    assert row["execution_at"] is None
    assert effects == []


def test_model_tool_cannot_approve_by_supplied_owner_identity(pending_approval):
    approval_id, effects = pending_approval
    result = approval_tools.hitl_approve.invoke({
        "approval_id": approval_id, "sender_id": "synthetic-owner", "sender_name": "Synthetic Owner",
    })

    assert "approval_channel_unverified" in result
    assert_unchanged(approval_id, effects)


@pytest.mark.asyncio
async def test_mcp_injected_principal_does_not_prove_human_approval(pending_approval):
    from xninetzy.interfaces.mcp_tool_adapter import MCPPrincipal, langchain_tool_as_mcp_callable

    approval_id, effects = pending_approval
    call = langchain_tool_as_mcp_callable(approval_tools.hitl_approve, MCPPrincipal(
        sender_id="synthetic-owner", sender_name="Synthetic Owner", chat_id="synthetic-chat",
    ))
    result = await call(approval_id=approval_id, sender_id="spoof", sender_name="Synthetic Owner")

    assert "approval_channel_unverified" in result
    assert_unchanged(approval_id, effects)
