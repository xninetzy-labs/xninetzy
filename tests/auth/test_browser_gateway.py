from __future__ import annotations

from xninetzy.os.auth.browser.gateway import (
    AuthState,
    BrowserBackend,
    BrowserGateway,
    default_gateway,
)


def test_default_gateway_capability_snapshot_shape() -> None:
    snap = default_gateway().capability_snapshot()
    assert "browser_available" in snap
    assert "backends" in snap
    assert "active_backend" in snap
    assert isinstance(snap["backends"], list)


def test_select_backend_raises_when_unavailable() -> None:
    gateway = BrowserGateway()
    gateway._backends = []
    try:
        gateway.select_backend()
    except Exception as exc:
        assert "no browser backend available" in str(exc)
    else:
        raise AssertionError("expected exception")


def test_profile_dir_creates_owner_scoped_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    gateway = BrowserGateway()
    profile = gateway.profile_dir("owner-123", "kaggle")
    assert profile.exists()
    assert profile.is_dir()
    assert "owner-123" in str(profile)
    assert "kaggle" in str(profile)


def test_browser_backend_enum_values() -> None:
    assert BrowserBackend.NONE.value == "none"
    assert BrowserBackend.LOCAL.value == "local"
    assert BrowserBackend.CDP.value == "cdp"
    assert BrowserBackend.REMOTE.value == "remote"


def test_auth_state_enum_values() -> None:
    assert AuthState.UNKNOWN.value == "unknown"
    assert AuthState.AUTHENTICATED.value == "authenticated"
    assert AuthState.REQUIRES_MFA.value == "requires_mfa"
