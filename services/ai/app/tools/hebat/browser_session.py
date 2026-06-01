from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import logging
from app.tools.hebat.parsers import is_logged_out, parse_login_page
from app.tools.hebat.storage import audit_log, mark_session_checked, upsert_session

logger = logging.getLogger(__name__)

_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


def _profile_dir(chat_id: str) -> Path:
    s = get_settings()
    path = Path(s.HEBAT_DATA_DIR) / "browser-profiles" / _safe_dir(chat_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _storage_state_path(chat_id: str) -> Path:
    return _profile_dir(chat_id) / "storage_state.json"


def _safe_dir(chat_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in chat_id)


async def login_with_credentials(chat_id: str, username: str, password: str) -> bool:
    """Login to HEBAT using username/password via Playwright. Returns True on success."""
    if not _PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright not installed — cannot login")
        return False

    s = get_settings()
    storage_path = _storage_state_path(chat_id)
    logger.info("Starting HEBAT login for chat_id=%s", chat_id)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=s.HEBAT_BROWSER_HEADLESS)
        try:
            ctx = await browser.new_context(
                storage_state=str(storage_path) if storage_path.exists() else None
            )
            page = await ctx.new_page()

            # Navigate to login page
            await page.goto(s.HEBAT_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            html = await page.content()
            info = parse_login_page(html)

            if info["already_logged_in"]:
                profile_name = await _get_profile_name(page)
                await ctx.storage_state(path=str(storage_path))
                upsert_session(chat_id, profile_name=profile_name,
                               storage_state_path=str(storage_path), is_active=True)
                audit_log(chat_id, "login_reuse", "success")
                return True

            if not info["has_username_field"]:
                logger.error("Login form not found on page")
                return False

            # Fill and submit form
            await page.fill("input[name='username']", username)
            await page.fill("input[name='password']", password)
            await page.click("#loginbtn", timeout=10_000)
            await page.wait_for_load_state("domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)

            # Check success
            current_url = page.url
            html_after = await page.content()

            if is_logged_out(html_after) or "/login/" in current_url:
                logger.warning("Login failed for chat_id=%s — still on login page", chat_id)
                audit_log(chat_id, "login_credentials", "failed",
                          detail={"reason": "still_on_login_page"})
                return False

            profile_name = await _get_profile_name(page)
            await ctx.storage_state(path=str(storage_path))
            upsert_session(
                chat_id,
                profile_name=profile_name,
                storage_state_path=str(storage_path),
                is_active=True,
            )
            audit_log(chat_id, "login_credentials", "success",
                      detail={"profile_name": profile_name})
            logger.info("HEBAT login successful for chat_id=%s, profile=%s", chat_id, profile_name)
            return True

        finally:
            await browser.close()


async def check_session_valid(chat_id: str) -> tuple[bool, str | None]:
    """Returns (is_valid, profile_name). Uses stored cookies — no password."""
    if not _PLAYWRIGHT_AVAILABLE:
        return False, None

    s = get_settings()
    storage_path = _storage_state_path(chat_id)
    if not storage_path.exists():
        mark_session_checked(chat_id, False)
        return False, None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(storage_state=str(storage_path))
            page = await ctx.new_page()
            await page.goto(
                s.HEBAT_BASE_URL + "/my/courses.php",
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            html = await page.content()

            if is_logged_out(html):
                mark_session_checked(chat_id, False)
                return False, None

            profile_name = await _get_profile_name(page)
            mark_session_checked(chat_id, True)
            return True, profile_name

        except Exception as e:
            logger.warning("Session check failed for %s: %s", chat_id, e)
            mark_session_checked(chat_id, False)
            return False, None
        finally:
            await browser.close()


async def get_page_html(chat_id: str, url: str) -> str | None:
    """Fetch a Moodle page with stored session. Returns HTML or None if session invalid."""
    if not _PLAYWRIGHT_AVAILABLE:
        return None

    s = get_settings()
    storage_path = _storage_state_path(chat_id)
    if not storage_path.exists():
        return None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(storage_state=str(storage_path))
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            return await page.content()
        except Exception as e:
            logger.warning("get_page_html failed for %s: %s", url, e)
            return None
        finally:
            await browser.close()


async def get_cookies_for_httpx(chat_id: str) -> list[dict]:
    """Extract cookies from stored Playwright session for use with httpx."""
    storage_path = _storage_state_path(chat_id)
    if not storage_path.exists():
        return []
    try:
        data = json.loads(storage_path.read_text(encoding="utf-8"))
        return data.get("cookies", [])
    except Exception:
        return []


async def _get_profile_name(page) -> str | None:
    """Try to extract the logged-in user's name from the page."""
    try:
        el = await page.query_selector(".usermenu .usertext, .userinfo .fullname, [data-key='myprofile']")
        if el:
            return (await el.inner_text()).strip() or None
    except Exception:
        pass
    return None
