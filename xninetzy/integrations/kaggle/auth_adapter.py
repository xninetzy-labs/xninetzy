from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
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


_CLI_CREDENTIAL_FILES: tuple[tuple[str, str], ...] = (
    ("access_token", "cli_access_token"),
    ("kaggle.json", "cli_kaggle_json"),
    ("credentials.json", "cli_credentials"),
)


def kaggle_config_dir() -> Path:
    override = os.environ.get("KAGGLE_CONFIG_DIR", "").strip()
    return Path(override).expanduser() if override else Path.home() / ".kaggle"


def local_credential_source() -> str | None:
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return "env_credentials"
    if os.environ.get("KAGGLE_API_TOKEN"):
        return "env_token"
    directory = kaggle_config_dir()
    for filename, source in _CLI_CREDENTIAL_FILES:
        try:
            candidate = directory / filename
            if candidate.is_file() and candidate.stat().st_size > 0:
                return source
        except OSError:
            continue
    return None


def resolve_kaggle_auth(
    *,
    owner: str,
    account: str = "default",
) -> KaggleAuthContext:
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
    local = local_credential_source()
    if local is not None:
        return KaggleAuthContext(
            authenticated=True,
            source=local,
            bearer_token=None,
            active_session_id=None,
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
            "Kaggle authentication is required. Run `kaggle auth login` or place "
            "an access token in ~/.kaggle/access_token, set KAGGLE_API_TOKEN, or use "
            "auth_session_create with provider='kaggle'. Never send username, "
            "password or key via tool arguments."
        ),
        "next_steps": [
            "kaggle_auth_status",
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
    "kaggle_config_dir",
    "local_credential_source",
    "resolve_kaggle_auth",
]
