from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Protocol

from bs4 import BeautifulSoup

from xninetzy.os.auth.browser.gateway import (
    BrowserGateway,
    BrowserGatewayUnavailable,
    close_local_browser,
    default_gateway,
    launch_local_browser,
)


logger = logging.getLogger(__name__)

_BROWSER_SCRAPING_ENV = "XNINETZY_BROWSER_SCRAPING_ENABLED"


def browser_scraping_enabled() -> bool:
    """Operator gate. Default ON; set XNINETZY_BROWSER_SCRAPING_ENABLED=0 to disable."""
    raw = os.environ.get(_BROWSER_SCRAPING_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


class BrowserSession(Protocol):
    async def get_html(
        self, url: str, *, wait_selector: str | None = None, timeout_ms: int = 15000
    ) -> str: ...

    async def close(self) -> None: ...


class _DisabledSession:
    """In-process stub used when browser scraping is disabled by operator config."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    async def get_html(
        self, url: str, *, wait_selector: str | None = None, timeout_ms: int = 15000
    ) -> str:
        raise BrowserGatewayUnavailable(self._reason)

    async def close(self) -> None:
        return None


class GatewayBrowserSession:
    """Persistent local Playwright session used for board scraping."""

    def __init__(
        self,
        *,
        owner: str = "career-scraper",
        gateway: BrowserGateway | None = None,
    ) -> None:
        self._owner = owner
        self._gateway = gateway or default_gateway()
        self._session_id = f"career-scraper-{uuid.uuid4().hex[:12]}"
        self._handle: dict | None = None
        self._lock = asyncio.Lock()
        self._page: object | None = None

    async def _ensure_started(self) -> None:
        if self._handle is not None:
            return
        async with self._lock:
            if self._handle is not None:
                return
            try:
                payload = await launch_local_browser(
                    session_id=self._session_id,
                    owner=self._owner,
                    headless=True,
                )
            except BrowserGatewayUnavailable as exc:
                logger.warning("scraper browser unavailable: %s", exc)
                raise
            self._handle = payload

    async def get_html(
        self, url: str, *, wait_selector: str | None = None, timeout_ms: int = 15000
    ) -> str:
        try:
            await self._ensure_started()
        except BrowserGatewayUnavailable:
            raise
        except Exception as exc:
            logger.warning("scraper browser start failed %s: %s", url, exc)
            raise BrowserGatewayUnavailable(f"browser start failed: {exc}") from exc
        try:
            from playwright.async_api import async_playwright  # noqa: F401
        except Exception as exc:
            raise BrowserGatewayUnavailable(f"playwright import failed: {exc}") from exc
        try:
            from xninetzy.os.auth.browser.gateway import _OPEN_HANDLES

            handle = _OPEN_HANDLES.get(self._session_id)
            if not handle:
                raise BrowserGatewayUnavailable("browser session lost")
            context = handle["context"]
            page = context.pages[0] if context.pages else await context.new_page()
            self._page = page
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass
            try:
                await page.wait_for_load_state("networkidle", timeout=min(8000, timeout_ms))
            except Exception:
                logger.debug("networkidle timeout on %s", url)
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=timeout_ms)
                except Exception:
                    logger.debug("wait_selector %s missed on %s", wait_selector, url)
            return await page.content()
        except BrowserGatewayUnavailable:
            raise
        except Exception as exc:
            logger.warning("scraper navigate failed %s: %s", url, exc)
            raise BrowserGatewayUnavailable(f"navigate failed: {exc}") from exc

    async def close(self) -> None:
        if self._handle is None:
            return
        try:
            await close_local_browser(session_id=self._session_id)
        except Exception:
            pass
        self._handle = None


class FakeBrowserSession:
    """In-memory session for tests."""

    def __init__(
        self,
        *,
        html_by_url: dict[str, str] | None = None,
        default_html: str | None = None,
    ) -> None:
        self.html_by_url = dict(html_by_url or {})
        self.default_html = default_html
        self.calls: list[tuple[str, str | None, int]] = []
        self.closed = False

    async def get_html(
        self, url: str, *, wait_selector: str | None = None, timeout_ms: int = 15000
    ) -> str:
        self.calls.append((url, wait_selector, timeout_ms))
        if url in self.html_by_url:
            return self.html_by_url[url]
        for pattern, html in self.html_by_url.items():
            if pattern in url:
                return html
        if self.default_html is not None:
            return self.default_html
        raise BrowserGatewayUnavailable(f"no canned html for {url}")

    async def close(self) -> None:
        self.closed = True


def html_to_text_blocks(html: str) -> list[BeautifulSoup]:
    return [BeautifulSoup(html, "lxml")]


_SHARED_SESSION: BrowserSession | None = None
_SHARED_LOCK = asyncio.Lock()


async def _get_or_create_shared_session() -> BrowserSession:
    global _SHARED_SESSION
    if _SHARED_SESSION is not None:
        return _SHARED_SESSION
    async with _SHARED_LOCK:
        if _SHARED_SESSION is not None:
            return _SHARED_SESSION
        if not browser_scraping_enabled():
            _SHARED_SESSION = _DisabledSession(
                "browser scraping disabled via XNINETZY_BROWSER_SCRAPING_ENABLED=0"
            )
            return _SHARED_SESSION
        _SHARED_SESSION = GatewayBrowserSession(owner="career-scraper-shared")
        return _SHARED_SESSION


def make_session(*, owner: str = "career-scraper") -> BrowserSession:
    """Return a SHARED BrowserSession used by all career browser adapters.

    Sharing prevents the EPIPE crash that happens when 4 adapters each
    spawn their own Playwright subprocess concurrently. The session is
    lazily created on first use and reused for all subsequent calls.

    Set XNINETZY_BROWSER_SCRAPING_ENABLED=0 to return a disabled stub
    that yields no results without launching a browser.
    """
    if not browser_scraping_enabled():
        return _DisabledSession(
            "browser scraping disabled via XNINETZY_BROWSER_SCRAPING_ENABLED=0"
        )
    if _SHARED_SESSION is None:
        return _DeferredSharedSession()
    return _SHARED_SESSION


class _DeferredSharedSession:
    """Returns a shared GatewayBrowserSession via async initialization."""

    def __init__(self) -> None:
        self._resolved: GatewayBrowserSession | None = None
        self._lock = asyncio.Lock()

    async def _ensure_resolved(self) -> BrowserSession:
        if self._resolved is not None:
            return self._resolved
        async with self._lock:
            if self._resolved is not None:
                return self._resolved
            self._resolved = await _get_or_create_shared_session()
            return self._resolved

    async def get_html(
        self, url: str, *, wait_selector: str | None = None, timeout_ms: int = 15000
    ) -> str:
        session = await self._ensure_resolved()
        return await session.get_html(url, wait_selector=wait_selector, timeout_ms=timeout_ms)

    async def close(self) -> None:
        if self._resolved is not None:
            await self._resolved.close()


__all__ = [
    "BrowserSession",
    "FakeBrowserSession",
    "GatewayBrowserSession",
    "browser_scraping_enabled",
    "html_to_text_blocks",
    "make_session",
]


def quote_url(value: str) -> str:
    from urllib.parse import quote_plus

    return quote_plus(value or "")
