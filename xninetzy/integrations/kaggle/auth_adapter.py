from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from xninetzy.os.auth.sessions.state import (
    AuthSessionStatus,
    find_active_connection,
)
from xninetzy.os.auth.secrets.store import default_secret_store


@dataclass(frozen=True, slots=True)
class KaggleAuthContext:
    authenticated: bool
    source: str
    bearer_token: str | None
    active_session_id: str | None
    provider: str
    account: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "authenticated": self.authenticated,
            "source": self.source,
            "active_session_id": self.active_session_id,
            "provider": self.provider,
            "account": self.account,
            "has_bearer": bool(self.bearer_token),
        }


def resolve_kaggle_auth(
    *,
    owner: str,
    account: str = "default",
) -> KaggleAuthContext:
    """Resolve a Kaggle auth context by checking Xninetzy's active
    auth session store first, then falling back to environment credentials.
    """
    try:
        record = find_active_connection(owner, "kaggle", account)
    except Exception:
        record = None
    if record is not None and record.state is AuthSessionStatus.AUTHENTICATED:
        bearer = (
            default_secret_store().get_bytes(record.credential_ref).decode("utf-8")
            if record.credential_ref
            else None
        )
        return KaggleAuthContext(
            authenticated=True,
            source="auth_session",
            bearer_token=bearer,
            active_session_id=record.session_id,
            provider="kaggle",
            account=account,
        )
    return KaggleAuthContext(
        authenticated=False,
        source="none",
        bearer_token=None,
        active_session_id=None,
        provider="kaggle",
        account=account,
    )


def kaggle_auth_required_error() -> dict[str, Any]:
    return {
        "error_code": "KAGGLE_AUTH_REQUIRED",
        "message": (
            "Kaggle authentication is required. Use auth_session_create "
            "with provider='kaggle' to start an OAuth or browser login flow, "
            "then retry. Never send username or password via tool arguments."
        ),
        "next_steps": [
            "auth_capabilities",
            "auth_providers_list",
            "auth_session_create(provider='kaggle', method='auto', account='default')",
            "auth_session_status(session_id=...)",
        ],
        "retryable": False,
    }


__all__ = [
    "KaggleAuthContext",
    "kaggle_auth_required_error",
    "resolve_kaggle_auth",
]
