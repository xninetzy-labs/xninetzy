from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from xninetzy.core.config import get_settings


class BrowserBackend(StrEnum):
    NONE = "none"
    LOCAL = "local"
    CDP = "cdp"
    REMOTE = "remote"


class AuthState(StrEnum):
    UNKNOWN = "unknown"
    LOGGED_OUT = "logged_out"
    AUTHENTICATED = "authenticated"
    REQUIRES_MFA = "requires_mfa"
    REQUIRES_CAPTCHA = "requires_captcha"
    REQUIRES_CONSENT = "requires_consent"


@dataclass(frozen=True, slots=True)
class BrowserSessionRecord:
    session_id: str
    owner: str
    backend: BrowserBackend
    profile_ref: str
    current_url: str | None
    auth_state: AuthState
    storage_state_path: str | None
    created_at: str
    last_used_at: str
    expires_at: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "owner": self.owner,
            "backend": self.backend.value,
            "profile_ref": self.profile_ref,
            "current_url": self.current_url,
            "auth_state": self.auth_state.value,
            "storage_state_path": self.storage_state_path,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "expires_at": self.expires_at,
        }


class BrowserBackendAdapter(Protocol):
    name: BrowserBackend

    def is_available(self) -> bool: ...

    def capability_snapshot(self) -> dict[str, Any]: ...


class LocalPlaywrightBackend:
    name = BrowserBackend.LOCAL

    def is_available(self) -> bool:
        try:
            from playwright.async_api import async_playwright

            async_playwright  # noqa: B018
            return True
        except Exception:
            return False

    def capability_snapshot(self) -> dict[str, Any]:
        available = self.is_available()
        snapshot: dict[str, Any] = {
            "backend": self.name.value,
            "available": available,
            "headless_supported": available,
            "headed_supported": available,
            "persistent_profiles": available,
        }
        if available:
            try:
                from playwright._impl._driver import compute_driver_executable

                snapshot["driver_executable"] = compute_driver_executable()
            except Exception:
                snapshot["driver_executable"] = None
        return snapshot


_LOCAL_OPEN_HANDLES: dict[str, Any] = {}
_OPEN_HANDLES: dict[str, Any] = {}


async def launch_local_browser(
    *,
    session_id: str,
    owner: str,
    headless: bool = False,
    profile_dir: Path | None = None,
) -> dict[str, Any]:
    from xninetzy.os.auth.policies.url_policy import assert_safe_url

    backend = LocalPlaywrightBackend()
    if not backend.is_available():
        raise BrowserGatewayUnavailable("playwright is not installed in this deployment")
    from playwright.async_api import async_playwright

    safe_owner = "".join(c if c.isalnum() or c in "-_" else "_" for c in owner)
    safe_session = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    resolved_dir = profile_dir or (
        Path.home() / ".local" / "share" / "xninetzy" / "auth" / "profiles" / safe_owner / safe_session
    )
    resolved_dir.mkdir(parents=True, exist_ok=True)
    try:
        resolved_dir.chmod(0o700)
    except OSError:
        pass
    url_check = assert_safe_url
    _ = url_check
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=str(resolved_dir),
        headless=headless,
    )
    _LOCAL_OPEN_HANDLES[session_id] = {"pw": pw, "context": context, "profile_dir": resolved_dir}
    _OPEN_HANDLES[session_id] = {
        "backend": "local",
        "pw": pw,
        "context": context,
        "profile_dir": resolved_dir,
    }
    page = context.pages[0] if context.pages else await context.new_page()
    return {
        "session_id": session_id,
        "owner": owner,
        "backend": "local",
        "headless": headless,
        "profile_dir": str(resolved_dir),
        "url": page.url,
        "pages_open": len(context.pages),
    }


async def close_local_browser(*, session_id: str) -> bool:
    handle = _LOCAL_OPEN_HANDLES.pop(session_id, None)
    if not handle:
        return False
    pw = handle.get("pw")
    context = handle.get("context")
    if context is not None:
        try:
            await context.close()
        except Exception:
            pass
    if pw is not None:
        try:
            await pw.stop()
        except Exception:
            pass
    _OPEN_HANDLES.pop(session_id, None)
    return True


def active_local_handles() -> dict[str, dict[str, Any]]:
    return {
        sid: {
            "profile_dir": str(h.get("profile_dir")) if h.get("profile_dir") else None,
            "open_pages": len(h["context"].pages) if h.get("context") else 0,
        }
        for sid, h in _LOCAL_OPEN_HANDLES.items()
    }


class CDPBackend:
    name = BrowserBackend.CDP

    def __init__(self) -> None:
        s = get_settings()
        self._endpoint = (
            s.XNINETZY_BROWSER_CDP_ENDPOINT.strip()
            if hasattr(s, "XNINETZY_BROWSER_CDP_ENDPOINT")
            else ""
        )

    def is_available(self) -> bool:
        return bool(self._endpoint)

    def capability_snapshot(self) -> dict[str, Any]:
        return {
            "backend": self.name.value,
            "available": self.is_available(),
            "endpoint": self._endpoint,
        }


class RemotePlaywrightBackend:
    name = BrowserBackend.REMOTE

    def __init__(self) -> None:
        s = get_settings()
        self._endpoint = (
            s.XNINETZY_BROWSER_REMOTE_ENDPOINT.strip()
            if hasattr(s, "XNINETZY_BROWSER_REMOTE_ENDPOINT")
            else ""
        )

    def is_available(self) -> bool:
        return bool(self._endpoint)

    def capability_snapshot(self) -> dict[str, Any]:
        return {
            "backend": self.name.value,
            "available": self.is_available(),
            "endpoint": self._endpoint,
        }


def _validate_endpoint(endpoint: str) -> None:
    from xninetzy.os.auth.policies.url_policy import assert_safe_url

    if not endpoint:
        raise BrowserGatewayUnavailable("browser endpoint is empty")
    assert_safe_url(endpoint)


async def connect_cdp(
    *,
    session_id: str,
    owner: str,
) -> dict[str, Any]:
    backend = CDPBackend()
    if not backend.is_available():
        raise BrowserGatewayUnavailable("XNINETZY_BROWSER_CDP_ENDPOINT is not configured")
    _validate_endpoint(backend._endpoint)
    from playwright.async_api import async_playwright

    safe_session = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    safe_owner = "".join(c if c.isalnum() or c in "-_" else "_" for c in owner)
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(backend._endpoint)
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = context.pages[0] if context.pages else await context.new_page()
    handle = {
        "backend": "cdp",
        "pw": pw,
        "browser": browser,
        "context": context,
        "endpoint": backend._endpoint,
    }
    _OPEN_HANDLES[safe_session] = handle
    return {
        "session_id": safe_session,
        "owner": safe_owner,
        "backend": "cdp",
        "endpoint": backend._endpoint,
        "url": page.url,
        "pages_open": len(context.pages),
        "context_count": len(browser.contexts),
    }


async def connect_remote(
    *,
    session_id: str,
    owner: str,
) -> dict[str, Any]:
    backend = RemotePlaywrightBackend()
    if not backend.is_available():
        raise BrowserGatewayUnavailable("XNINETZY_BROWSER_REMOTE_ENDPOINT is not configured")
    _validate_endpoint(backend._endpoint)
    from playwright.async_api import async_playwright

    safe_session = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    safe_owner = "".join(c if c.isalnum() or c in "-_" else "_" for c in owner)
    pw = await async_playwright().start()
    browser = await pw.chromium.connect(backend._endpoint)
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = context.pages[0] if context.pages else await context.new_page()
    handle = {
        "backend": "remote",
        "pw": pw,
        "browser": browser,
        "context": context,
        "endpoint": backend._endpoint,
    }
    _OPEN_HANDLES[safe_session] = handle
    return {
        "session_id": safe_session,
        "owner": safe_owner,
        "backend": "remote",
        "endpoint": backend._endpoint,
        "url": page.url,
        "pages_open": len(context.pages),
        "context_count": len(browser.contexts),
    }


async def close_external_browser(*, session_id: str) -> bool:
    handle = _OPEN_HANDLES.pop(session_id, None)
    if handle is None:
        return False
    browser = handle.get("browser")
    pw = handle.get("pw")
    if browser is not None:
        try:
            await browser.close()
        except Exception:
            pass
    if pw is not None:
        try:
            await pw.stop()
        except Exception:
            pass
    return True


def active_external_handles() -> dict[str, dict[str, Any]]:
    return {
        sid: {
            "backend": h.get("backend"),
            "endpoint": h.get("endpoint"),
            "open_pages": len(h["context"].pages) if h.get("context") else 0,
            "context_count": len(h["browser"].contexts) if h.get("browser") else 0,
        }
        for sid, h in _OPEN_HANDLES.items()
    }


class BrowserGateway:
    """Browser gateway abstraction.

    The gateway routes browser operations to the active backend. The
    gateway NEVER returns raw credential material; redacted summaries
    are produced for the model.
    """

    def __init__(self) -> None:
        self._backends: list[BrowserBackendAdapter] = [
            LocalPlaywrightBackend(),
            CDPBackend(),
            RemotePlaywrightBackend(),
        ]
        self._active_backend: BrowserBackendAdapter | None = None

    def capability_snapshot(self) -> dict[str, Any]:
        available = [b.capability_snapshot() for b in self._backends if b.is_available()]
        return {
            "browser_available": bool(available),
            "backends": available,
            "active_backend": self._active_backend.name.value if self._active_backend else None,
        }

    def select_backend(self) -> BrowserBackendAdapter:
        for backend in self._backends:
            if backend.is_available():
                self._active_backend = backend
                return backend
        self._active_backend = None
        raise BrowserGatewayUnavailable("no browser backend available in this deployment")

    def active_backend(self) -> BrowserBackendAdapter | None:
        return self._active_backend

    def profile_dir(self, owner: str, profile_ref: str) -> Path:
        safe_owner = "".join(c if c.isalnum() or c in "-_" else "_" for c in owner)
        safe_ref = "".join(c if c.isalnum() or c in "-_" else "_" for c in profile_ref)
        root = Path.home() / ".local" / "share" / "xninetzy" / "auth" / "profiles"
        target = root / safe_owner / safe_ref
        target.mkdir(parents=True, exist_ok=True)
        try:
            target.chmod(0o700)
        except OSError:
            pass
        return target


class BrowserGatewayUnavailable(RuntimeError):
    pass


_DEFAULT_GATEWAY: BrowserGateway | None = None


def default_gateway() -> BrowserGateway:
    global _DEFAULT_GATEWAY
    if _DEFAULT_GATEWAY is None:
        _DEFAULT_GATEWAY = BrowserGateway()
    return _DEFAULT_GATEWAY


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def session_record_from_payload(
    *,
    session_id: str,
    owner: str,
    backend: BrowserBackend,
    profile_ref: str,
    current_url: str | None,
    auth_state: AuthState,
    storage_state_path: str | None,
    expires_at: str | None,
) -> BrowserSessionRecord:
    now = _utcnow()
    return BrowserSessionRecord(
        session_id=session_id,
        owner=owner,
        backend=backend,
        profile_ref=profile_ref,
        current_url=current_url,
        auth_state=auth_state,
        storage_state_path=storage_state_path,
        created_at=now,
        last_used_at=now,
        expires_at=expires_at,
    )


__all__ = [
    "AuthState",
    "BrowserBackend",
    "BrowserBackendAdapter",
    "BrowserGateway",
    "BrowserGatewayUnavailable",
    "BrowserSessionRecord",
    "CDPBackend",
    "LocalPlaywrightBackend",
    "RemotePlaywrightBackend",
    "active_external_handles",
    "active_local_handles",
    "close_external_browser",
    "close_local_browser",
    "connect_cdp",
    "connect_remote",
    "default_gateway",
    "launch_local_browser",
    "session_record_from_payload",
]
