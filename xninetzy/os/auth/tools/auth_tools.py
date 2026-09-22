from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.os.auth.browser.gateway import (
    BrowserGatewayUnavailable,
    active_external_handles,
    close_external_browser,
    connect_cdp,
    connect_remote,
    default_gateway,
)
from xninetzy.os.auth.oauth.providers import (
    build_authorization_url,
    list_providers,
    get_provider,
)
from xninetzy.os.auth.oauth.pkce import generate_pkce
from xninetzy.os.auth.policies.redaction import redact_payload
from xninetzy.os.auth.policies.url_policy import URLBlockedError, assert_safe_url
from xninetzy.os.auth.providers.adapters import (
    get_provider_adapter,
    list_provider_adapters,
)
from xninetzy.os.auth.sessions.state import (
    AuthSessionStatus,
    create_session,
    find_active_connection,
    get_session,
    list_sessions,
    new_state_token,
    transition,
)
from xninetzy.os.auth.secrets.store import (
    SecretStore,
    default_secret_store,
)
from xninetzy.tools.tool_results import to_tool_result


def _uid(sender_id: str | None, chat_id: str | None) -> str:
    return (sender_id or chat_id or "default").strip() or "default"


@tool
def auth_capabilities() -> str:
    """Report runtime auth + browser capability matrix."""
    snap = default_gateway().capability_snapshot()
    providers = [
        {**p.to_safe_dict(), "oauth_supported": get_provider(p.provider_id) is not None}
        for p in list_provider_adapters()
    ]
    return to_tool_result({
        "auth": {
            "secret_store": True,
            "session_state_machine": True,
            "pkce": True,
        },
        "browser": snap,
        "providers": providers,
        "oauth_providers": [
            p.to_safe_dict() for p in list_providers()
        ],
    })


@tool
def auth_providers_list() -> str:
    """List provider adapters known to Xninetzy (Kaggle, Google, GitHub)."""
    return to_tool_result(
        {"providers": [p.to_safe_dict() for p in list_provider_adapters()]}
    )


@tool
def auth_connections_list(
    sender_id: str = "",
    chat_id: str = "",
) -> str:
    """List authenticated connections owned by the calling principal.

    Returns safe metadata only (no tokens).
    """
    owner = _uid(sender_id, chat_id)
    records = list_sessions(owner=owner, state=AuthSessionStatus.AUTHENTICATED, limit=50)
    return to_tool_result(
        {"owner": owner, "count": len(records), "connections": [r.to_safe_dict() for r in records]}
    )


@tool
def auth_session_create(
    provider: str,
    method: str = "auto",
    account: str = "default",
    scopes: list[str] | None = None,
    sender_id: str = "",
    chat_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Create a new auth session for ``provider``. Method can be
    ``oauth``, ``browser``, or ``auto``. Returns the session id and
    the authorization URL when OAuth is requested.
    """
    if get_provider_adapter(provider) is None:
        return to_tool_result({"error": f"unknown provider: {provider}"})
    owner = _uid(sender_id, chat_id)
    chosen_method = method if method != "auto" else "oauth"
    if chosen_method == "oauth" and get_provider(provider) is None:
        return to_tool_result({"error": f"oauth not configured for provider: {provider}"})
    pkce = generate_pkce() if chosen_method == "oauth" else None
    state = new_state_token()
    authorization_url: str | None = None
    provider_def = get_provider(provider) if chosen_method == "oauth" else None
    if chosen_method == "oauth" and provider_def is not None and pkce is not None:
        try:
            authorization_url = build_authorization_url(
                provider_def,
                state=state,
                code_challenge=pkce.code_challenge,
                scopes=tuple(scopes or ()),
            )
            assert_safe_url(authorization_url, provider_def.allowed_origins)
        except URLBlockedError as exc:
            return to_tool_result({"error": f"url policy blocked: {exc}"})
    record = create_session(
        owner=owner,
        provider=provider,
        account=account,
        method=chosen_method,
        scopes=tuple(scopes or ()),
        state_token=state if chosen_method == "oauth" else None,
        pkce_verifier=pkce.code_verifier if pkce is not None else None,
        authorization_url=authorization_url,
        ttl_seconds=900,
    )
    return to_tool_result(record.to_safe_dict())


@tool
def auth_session_status(session_id: str) -> str:
    """Return the current safe record for an auth session."""
    record = get_session(session_id)
    if record is None:
        return to_tool_result({"error": f"unknown session: {session_id}"})
    return to_tool_result(record.to_safe_dict())


@tool
def auth_session_cancel(session_id: str) -> str:
    """Cancel an in-flight auth session. No-op for terminal sessions."""
    record = transition(session_id, to=AuthSessionStatus.CANCELLED, error_code="USER_CANCELLED")
    if record is None:
        return to_tool_result({"error": f"unknown session: {session_id}"})
    return to_tool_result(record.to_safe_dict())


@tool
def auth_session_revoke(session_id: str) -> str:
    """Revoke an authenticated connection. Clears the credential reference."""
    record = transition(session_id, to=AuthSessionStatus.REVOKED)
    if record is None:
        return to_tool_result({"error": f"unknown session: {session_id}"})
    if record.credential_ref:
        default_secret_store().revoke(record.credential_ref)
    return to_tool_result(record.to_safe_dict())


@tool
def auth_identity_get(
    provider: str,
    account: str = "default",
    sender_id: str = "",
    chat_id: str = "",
) -> str:
    """Return the safe identity metadata for an active connection, if any."""
    owner = _uid(sender_id, chat_id)
    record = find_active_connection(owner, provider, account)
    if record is None:
        return to_tool_result({"error": "no active connection"})
    safe_identity = {
        "provider": record.identity.get("provider", provider),
        "subject": record.identity.get("subject", ""),
        "email": record.identity.get("email", ""),
        "display_name": record.identity.get("display_name", ""),
        "scopes": list(record.scopes),
        "authenticated_at": record.authenticated_at,
        "last_validated_at": record.last_validated_at,
    }
    return to_tool_result(redact_payload(safe_identity))


@tool
def browser_capabilities() -> str:
    """Report browser backend capability snapshot (LOCAL/CDP/REMOTE)."""
    return to_tool_result(default_gateway().capability_snapshot())


@tool
def browser_session_status(
    provider: str,
    account: str = "default",
    sender_id: str = "",
    chat_id: str = "",
) -> str:
    """Return safe status for the browser session associated with a
    provider + account, or an empty result if no session exists."""
    owner = _uid(sender_id, chat_id)
    return to_tool_result({
        "provider": provider,
        "account": account,
        "owner": owner,
        "status": "no_active_session",
        "action_required": None,
        "external_handles": {
            sid: h for sid, h in active_external_handles().items()
        },
    })


def browser_connect_cdp_tool(
    session_id: str,
    sender_id: str = "",
    chat_id: str = "",
) -> dict[str, object]:
    """Attach to an existing Chromium browser via CDP
    (XNINETZY_BROWSER_CDP_ENDPOINT). Never expose the endpoint value to the
    model — only metadata describing the connection outcome."""
    owner = _uid(sender_id, chat_id)
    try:
        import asyncio

        payload = asyncio.run(
            connect_cdp(session_id=session_id, owner=owner)
        )
        return to_tool_result(
            {
                "status": "connected",
                "backend": "cdp",
                **payload,
                "owner": owner,
            }
        )
    except BrowserGatewayUnavailable as exc:
        return to_tool_result({"status": "unavailable", "error": str(exc), "owner": owner})
    except Exception as exc:
        return to_tool_result({"status": "error", "error": str(exc), "owner": owner})


def browser_connect_remote_tool(
    session_id: str,
    sender_id: str = "",
    chat_id: str = "",
) -> dict[str, object]:
    """Attach to a remote Playwright worker
    (XNINETZY_BROWSER_REMOTE_ENDPOINT). Endpoint value never surfaces."""
    owner = _uid(sender_id, chat_id)
    try:
        import asyncio

        payload = asyncio.run(
            connect_remote(session_id=session_id, owner=owner)
        )
        return to_tool_result(
            {
                "status": "connected",
                "backend": "remote",
                **payload,
                "owner": owner,
            }
        )
    except BrowserGatewayUnavailable as exc:
        return to_tool_result({"status": "unavailable", "error": str(exc), "owner": owner})
    except Exception as exc:
        return to_tool_result({"status": "error", "error": str(exc), "owner": owner})


def browser_close_tool(
    session_id: str,
    sender_id: str = "",
    chat_id: str = "",
) -> dict[str, object]:
    """Close a previously opened CDP/REMOTE browser handle. Safe output only."""
    owner = _uid(sender_id, chat_id)
    try:
        import asyncio

        closed = asyncio.run(close_external_browser(session_id=session_id))
    except Exception as exc:
        return to_tool_result({"status": "error", "error": str(exc), "owner": owner})
    return to_tool_result(
        {
            "status": "closed" if closed else "not_found",
            "session_id": session_id,
            "owner": owner,
        }
    )


@tool
def oauth_provider_list() -> str:
    """List OAuth providers registered in the OAuth provider registry."""
    return to_tool_result(
        {"providers": [p.to_safe_dict() for p in list_providers()]}
    )


@tool
def oauth_provider_get(provider: str) -> str:
    """Return the OAuth provider definition for one provider id."""
    p = get_provider(provider)
    if p is None:
        return to_tool_result({"error": f"unknown provider: {provider}"})
    return to_tool_result(p.to_safe_dict())


__all__ = [
    "auth_capabilities",
    "auth_providers_list",
    "auth_connections_list",
    "auth_session_create",
    "auth_session_status",
    "auth_session_cancel",
    "auth_session_revoke",
    "auth_identity_get",
    "browser_capabilities",
    "browser_session_status",
    "oauth_provider_list",
    "oauth_provider_get",
    "SecretStore",
]
