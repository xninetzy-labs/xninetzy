from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderAdapter:
    provider_id: str
    login_url: str
    auth_check_url: str
    identity_url: str | None
    allowed_origins: tuple[str, ...]
    logout_url: str | None = None
    requires_user_interaction: bool = True
    supports_oauth: bool = True
    supports_browser_session: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "login_url": self.login_url,
            "auth_check_url": self.auth_check_url,
            "identity_url": self.identity_url,
            "allowed_origins": list(self.allowed_origins),
            "logout_url": self.logout_url,
            "requires_user_interaction": self.requires_user_interaction,
            "supports_oauth": self.supports_oauth,
            "supports_browser_session": self.supports_browser_session,
        }


_KAGGLE = ProviderAdapter(
    provider_id="kaggle",
    login_url="https://www.kaggle.com/account/login",
    auth_check_url="https://www.kaggle.com/api/v1/users/me",
    identity_url="https://www.kaggle.com/api/v1/users/me",
    allowed_origins=("kaggle.com", "www.kaggle.com"),
    logout_url="https://www.kaggle.com/account/logout",
    supports_oauth=True,
    supports_browser_session=True,
)

_GOOGLE = ProviderAdapter(
    provider_id="google",
    login_url="https://accounts.google.com/ServiceLogin",
    auth_check_url="https://openidconnect.googleapis.com/v1/userinfo",
    identity_url="https://openidconnect.googleapis.com/v1/userinfo",
    allowed_origins=("accounts.google.com", "google.com", "googleapis.com"),
    logout_url="https://accounts.google.com/Logout",
    supports_oauth=True,
    supports_browser_session=True,
)

_GITHUB = ProviderAdapter(
    provider_id="github",
    login_url="https://github.com/login",
    auth_check_url="https://api.github.com/user",
    identity_url="https://api.github.com/user",
    allowed_origins=("github.com", "api.github.com"),
    logout_url="https://github.com/logout",
    supports_oauth=True,
    supports_browser_session=True,
)

_ADAPTERS: dict[str, ProviderAdapter] = {
    "kaggle": _KAGGLE,
    "google": _GOOGLE,
    "github": _GITHUB,
}


def get_provider_adapter(provider_id: str) -> ProviderAdapter | None:
    return _ADAPTERS.get(provider_id)


def list_provider_adapters() -> list[ProviderAdapter]:
    return list(_ADAPTERS.values())


def register_adapter(adapter: ProviderAdapter) -> None:
    _ADAPTERS[adapter.provider_id] = adapter


__all__ = [
    "ProviderAdapter",
    "get_provider_adapter",
    "list_provider_adapters",
    "register_adapter",
]
