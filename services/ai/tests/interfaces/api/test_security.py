from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.xninetzy.core.config import Settings
from app.xninetzy.interfaces.api.deps import auth
from app.xninetzy.interfaces.api.deps.auth import require_api_key
from app.xninetzy.interfaces.api.owner_policy import authorize_owner
from app.xninetzy.interfaces.api.routes.chat import router as chat_router
from app.xninetzy.interfaces.api.routes.debug import router as debug_router


@pytest.mark.asyncio
async def test_api_auth_rejects_missing_or_wrong_bearer(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(AI_API_KEY="secret", AI_API_AUTH_REQUIRED=True),
    )

    with pytest.raises(HTTPException) as missing:
        await require_api_key(None)
    with pytest.raises(HTTPException) as wrong:
        await require_api_key("Bearer wrong")

    assert missing.value.status_code == 401
    assert wrong.value.status_code == 401
    await require_api_key("Bearer secret")


@pytest.mark.asyncio
async def test_api_auth_fails_closed_when_required_key_is_unconfigured(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(AI_API_KEY="", AI_API_AUTH_REQUIRED=True),
    )

    with pytest.raises(HTTPException) as error:
        await require_api_key(None)

    assert error.value.status_code == 503


def test_chat_and_debug_routers_require_api_authentication():
    assert any(item.dependency is require_api_key for item in chat_router.dependencies)
    assert any(item.dependency is require_api_key for item in debug_router.dependencies)


def test_single_owner_policy_accepts_admin_and_rejects_other_sender():
    settings = Settings(
        _env_file=None,
        SINGLE_OWNER_MODE=True,
        ADMIN_JID="628123@s.whatsapp.net",
        OWNER_ALLOWED_JIDS="99123@lid",
    )

    assert authorize_owner("628123:7@s.whatsapp.net", settings).allowed is True
    assert authorize_owner("99123@lid", settings).allowed is True
    decision = authorize_owner("628999@s.whatsapp.net", settings)
    assert decision.allowed is False
    assert decision.reason == "not_owner"


def test_single_owner_policy_fails_closed_without_owner_identity():
    settings = Settings(
        _env_file=None,
        SINGLE_OWNER_MODE=True,
        ADMIN_JID="",
        OWNER_ALLOWED_JIDS="",
    )

    decision = authorize_owner("someone@s.whatsapp.net", settings)

    assert decision.allowed is False
    assert decision.reason == "owner_not_configured"
