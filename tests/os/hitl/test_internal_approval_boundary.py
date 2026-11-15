from __future__ import annotations

import pytest

from xninetzy.core.config import get_settings
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect, init_db
from xninetzy.os.hitl import approval_service as service
from xninetzy.os.policy.action_policy import action_hash


@pytest.fixture
def isolated_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "internal.sqlite3"))
    monkeypatch.setenv("ADMIN_NAMES", "Fixture Owner")
    monkeypatch.setenv("OWNER_PHONE_NUMBER", "628123456789")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    effects = []
    monkeypatch.setattr(service, "_execute_approved_action", lambda row: effects.append(row) or "done")
    payload = {"target": "fixture-resource"}
    identifier = service.request_approval("fixture-chat", "fixture-owner", "fixture-action", "Test", "Test", payload)
    yield identifier, payload, effects
    get_settings.cache_clear()


@pytest.mark.parametrize("sender,name", [(None, "Fixture Owner"), ("untrusted", "Fixture Owner"), ("628123456789", "Fixture Owner")])
def test_raw_service_identity_cannot_authenticate_human_approval(isolated_approval, sender, name):
    identifier, _, effects = isolated_approval
    ok, message = service.set_approval_status(identifier, "approved", sender, name)
    assert not ok
    assert "approval_channel_unverified" in message
    assert service.get_approval_status(identifier)["status"] == "pending"
    assert effects == []


def test_legacy_approved_record_is_not_authorization_evidence(isolated_approval):
    identifier, payload, _ = isolated_approval
    with connect() as conn:
        conn.execute("UPDATE approval_requests SET status='approved',approved_at=? WHERE id=?", ("2026-01-01T00:00:00+00:00", identifier))
    with pytest.raises(ValueError, match="approval_channel_unverified"):
        service.validate_approval(identifier, "fixture-action", action_hash("fixture-action", payload))
    assert service.get_approval_status(identifier)["status"] == "approved"


def test_display_name_cannot_reject_another_request(isolated_approval):
    identifier, _, effects = isolated_approval
    ok, _ = service.set_approval_status(identifier, "rejected", "untrusted", "Fixture Owner")
    assert not ok
    assert service.get_approval_status(identifier)["status"] == "pending"
    assert effects == []


def test_configured_owner_can_reject_without_authorizing_effect(isolated_approval):
    identifier, _, effects = isolated_approval
    assert service.set_approval_status(identifier, "rejected", "628123456789", "untrusted name")[0]
    assert service.get_approval_status(identifier)["status"] == "rejected"
    assert effects == []


def test_local_stdio_principal_can_reject_with_inbox_only_configuration(isolated_approval, monkeypatch):
    identifier, _, effects = isolated_approval
    for setting in ("MCP_PRINCIPAL_ID", "OWNER_PHONE_NUMBER", "ADMIN_JID", "OWNER_ALLOWED_IDS", "OWNER_ALLOWED_JIDS"):
        monkeypatch.setenv(setting, "")
    monkeypatch.setenv("OWNER_CHAT_ID", "fixture-inbox")
    get_settings.cache_clear()
    assert service.set_approval_status(identifier, "rejected", "mcp:local-owner", None)[0]
    assert effects == []


@pytest.mark.asyncio
@pytest.mark.parametrize("plan", [True, False])
@pytest.mark.parametrize("delivered", [True, False])
async def test_request_reports_actual_inbox_and_unavailable_approval_channel(isolated_approval, monkeypatch, plan, delivered):
    from xninetzy.os.hitl import approval_tools

    async def notify(*args, **kwargs):
        return delivered

    monkeypatch.setattr(approval_tools, "notify_admin_approval", notify)
    if plan:
        result = await approval_tools.hitl_request_plan_approval.ainvoke({"plan_id": "fixture-plan", "final_steps": ["fixture-step"]})
    else:
        result = await approval_tools.hitl_request_approval.ainvoke({"action_type": "fixture-action", "title": "Test", "summary": "Test"})
    assert "approval_channel_unverified" in result
    assert ("tersimpan di inbox" in result) is delivered
    assert "WA Engine" not in result
    assert "Tombol" not in result
    assert "/approve" not in result
