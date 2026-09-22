from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from urllib.parse import urlencode


class OAuthMethod(StrEnum):
    AUTHORIZATION_CODE = "authorization_code"
    PKCE = "pkce"
    IMPLICIT = "implicit"
    CLIENT_CREDENTIALS = "client_credentials"
    DEVICE_CODE = "device_code"


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    provider_id: str
    display_name: str
    authorization_endpoint: str
    token_endpoint: str
    issuer: str | None = None
    identity_endpoint: str | None = None
    revoke_endpoint: str | None = None
    discovery_endpoint: str | None = None
    default_scopes: tuple[str, ...] = ()
    supports_pkce: bool = True
    supports_refresh: bool = True
    client_id_env: str = ""
    client_secret_env: str = ""
    redirect_uri: str = "http://127.0.0.1:8765/auth/callback"
    allowed_origins: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "authorization_endpoint": self.authorization_endpoint,
            "token_endpoint": self.token_endpoint,
            "issuer": self.issuer,
            "identity_endpoint": self.identity_endpoint,
            "revoke_endpoint": self.revoke_endpoint,
            "default_scopes": list(self.default_scopes),
            "supports_pkce": self.supports_pkce,
            "supports_refresh": self.supports_refresh,
            "redirect_uri": self.redirect_uri,
            "allowed_origins": list(self.allowed_origins),
        }


_GOOGLE: ProviderDefinition = ProviderDefinition(
    provider_id="google",
    display_name="Google",
    authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    issuer="https://accounts.google.com",
    identity_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    revoke_endpoint="https://oauth2.googleapis.com/revoke",
    discovery_endpoint="https://accounts.google.com/.well-known/openid-configuration",
    default_scopes=("openid", "email", "profile"),
    supports_pkce=True,
    supports_refresh=True,
    client_id_env="XNINETZY_GOOGLE_CLIENT_ID",
    client_secret_env="XNINETZY_GOOGLE_CLIENT_SECRET",
    allowed_origins=("accounts.google.com", "google.com", "googleapis.com"),
)

_GITHUB: ProviderDefinition = ProviderDefinition(
    provider_id="github",
    display_name="GitHub",
    authorization_endpoint="https://github.com/login/oauth/authorize",
    token_endpoint="https://github.com/login/oauth/access_token",
    identity_endpoint="https://api.github.com/user",
    default_scopes=("read:user", "user:email", "repo"),
    supports_pkce=True,
    supports_refresh=False,
    client_id_env="XNINETZY_GITHUB_CLIENT_ID",
    client_secret_env="XNINETZY_GITHUB_CLIENT_SECRET",
    allowed_origins=("github.com", "api.github.com"),
)

_KAGGLE: ProviderDefinition = ProviderDefinition(
    provider_id="kaggle",
    display_name="Kaggle",
    authorization_endpoint="https://www.kaggle.com/oauth/authorize",
    token_endpoint="https://www.kaggle.com/oauth/token",
    identity_endpoint="https://www.kaggle.com/api/v1/users/me",
    default_scopes=("public", "private", "read"),
    supports_pkce=True,
    supports_refresh=True,
    client_id_env="XNINETZY_KAGGLE_CLIENT_ID",
    client_secret_env="XNINETZY_KAGGLE_CLIENT_SECRET",
    allowed_origins=("kaggle.com", "www.kaggle.com", "api.kaggle.com"),
)

_PROVIDERS: dict[str, ProviderDefinition] = {
    "google": _GOOGLE,
    "github": _GITHUB,
    "kaggle": _KAGGLE,
}


def register_provider(definition: ProviderDefinition) -> None:
    _PROVIDERS[definition.provider_id] = definition


def get_provider(provider_id: str) -> ProviderDefinition | None:
    return _PROVIDERS.get(provider_id)


def list_providers() -> list[ProviderDefinition]:
    return list(_PROVIDERS.values())


def build_authorization_url(
    provider: ProviderDefinition,
    *,
    state: str,
    code_challenge: str | None = None,
    code_challenge_method: str = "S256",
    scopes: tuple[str, ...] = (),
    extra: dict[str, str] | None = None,
) -> str:
    params: list[tuple[str, str]] = [
        ("response_type", "code"),
        ("client_id", _env(provider.client_id_env) or "xninetzy-public"),
        ("redirect_uri", provider.redirect_uri),
        ("state", state),
    ]
    final_scopes = scopes or provider.default_scopes
    if final_scopes:
        params.append(("scope", " ".join(final_scopes)))
    if provider.supports_pkce and code_challenge:
        params.append(("code_challenge", code_challenge))
        params.append(("code_challenge_method", code_challenge_method))
    if extra:
        params.extend(extra.items())
    return f"{provider.authorization_endpoint}?{urlencode(params)}"


def _env(name: str) -> str:
    import os

    return os.environ.get(name, "").strip()


def fingerprint_state(state_token: str) -> str:
    return hashlib.sha256(state_token.encode("utf-8")).hexdigest()[:16]


def is_callback_for_provider(
    callback_url: str,
    provider: ProviderDefinition,
) -> bool:
    from urllib.parse import urlparse

    parsed = urlparse(callback_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return any(origin == f"https://{a}" or origin == f"http://{a}" for a in provider.allowed_origins)


def token_endpoint_url(provider: ProviderDefinition) -> str:
    return provider.token_endpoint


__all__ = [
    "OAuthMethod",
    "ProviderDefinition",
    "build_authorization_url",
    "fingerprint_state",
    "get_provider",
    "is_callback_for_provider",
    "list_providers",
    "register_provider",
    "token_endpoint_url",
]
