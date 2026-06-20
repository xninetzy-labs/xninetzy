from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.academic.hebat.parsers import is_logged_out, looks_like_login_page, parse_login_page
from app.xninetzy.os.academic.hebat.storage import audit_log, mark_session_checked, upsert_session

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


async def login_with_credentials(
    chat_id: str, username: str, password: str, force: bool = False
) -> bool:
    """Login to HEBAT using username/password via Playwright. Returns True on success.

    When ``force`` is True the existing stored session is ignored so the login
    form is always presented (avoids a stale cookie hiding the username field).
    """
    if not _PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright not installed — cannot login")
        return False
    if not username or not password:
        logger.error("HEBAT credentials missing — set HEBAT_USERNAME and HEBAT_PASSWORD")
        return False

    s = get_settings()
    storage_path = _storage_state_path(chat_id)
    logger.info("Starting HEBAT login for chat_id=%s (force=%s)", chat_id, force)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=s.HEBAT_BROWSER_HEADLESS)
        try:
            ctx = await browser.new_context(
                storage_state=str(storage_path) if (storage_path.exists() and not force) else None
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


async def ensure_hebat_session(
    chat_id: str, username: str, password: str, attempts: int = 3
) -> tuple[bool, str | None, int]:
    """Guarantee a *working* HEBAT session.

    A session is only considered working if it can actually fetch courses (this
    catches stale cookies that pass ``check_session_valid`` but return no data).
    Falls back to a forced credential re-login, retrying with backoff.

    Returns ``(ok, profile_name, course_count)``.
    """
    from app.xninetzy.os.academic.hebat.moodle_client import fetch_courses
    from app.xninetzy.os.academic.hebat.storage import get_session

    last_profile: str | None = None
    delay = 5
    for attempt in range(1, attempts + 1):
        try:
            valid, profile = await check_session_valid(chat_id)
            last_profile = profile or last_profile
            if valid:
                courses = await fetch_courses(chat_id)
                if courses:
                    return True, last_profile, len(courses)
                logger.info("HEBAT: session valid but 0 courses — forcing re-login (attempt %d)", attempt)

            ok = await login_with_credentials(chat_id, username, password, force=True)
            if ok:
                courses = await fetch_courses(chat_id)
                if courses:
                    sess = get_session(chat_id)
                    last_profile = (sess or {}).get("profile_name") or last_profile
                    return True, last_profile, len(courses)
                logger.warning("HEBAT: login ok but courses empty (attempt %d)", attempt)
        except Exception as exc:
            logger.warning("HEBAT ensure_session attempt %d failed: %s", attempt, exc)

        if attempt < attempts:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)

    return False, last_profile, 0


async def debug_login_with_credentials(chat_id: str, username: str, password: str) -> dict:
    """Run a safe HEBAT login diagnostic without exposing secrets."""
    s = get_settings()
    result = {
        "login_url": s.HEBAT_LOGIN_URL,
        "env_username_read": bool(username),
        "env_password_available": bool(password),
        "playwright_available": _PLAYWRIGHT_AVAILABLE,
        "http_status": None,
        "redirect_chain": [],
        "login_token_found": False,
        "session_cookie_saved": False,
        "login_success_indicator": False,
        "parser_error": None,
        "final_url": None,
        "problem_guess": "",
    }
    if not _PLAYWRIGHT_AVAILABLE:
        result["problem_guess"] = "Playwright belum terinstall atau browser belum tersedia."
        return result
    storage_path = _storage_state_path(chat_id)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=s.HEBAT_BROWSER_HEADLESS)
        try:
            ctx = await browser.new_context()
            page = await ctx.new_page()
            responses: list[dict] = []

            def _track_response(response):
                if response.request.is_navigation_request():
                    responses.append({"url": response.url, "status": response.status})

            page.on("response", _track_response)
            response = await page.goto(s.HEBAT_LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            result["http_status"] = response.status if response else None
            result["redirect_chain"] = [r["url"] for r in responses[1:]]
            html = await page.content()
            try:
                info = parse_login_page(html)
                result["login_token_found"] = bool(info.get("logintoken"))
                if info.get("already_logged_in"):
                    result["login_success_indicator"] = True
            except Exception as exc:
                result["parser_error"] = str(exc)

            if result["env_username_read"] and result["env_password_available"] and not result["login_success_indicator"]:
                if not await page.query_selector("input[name='username']"):
                    result["problem_guess"] = "Field username tidak ditemukan; struktur login Moodle mungkin berubah."
                else:
                    await page.fill("input[name='username']", username)
                    await page.fill("input[name='password']", password)
                    await page.click("#loginbtn", timeout=10_000)
                    await page.wait_for_load_state("domcontentloaded", timeout=30_000)
                    await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
                    result["final_url"] = page.url
                    html_after = await page.content()
                    result["login_success_indicator"] = not (is_logged_out(html_after) or "/login/" in page.url)
                    await ctx.storage_state(path=str(storage_path))
                    cookies = await ctx.cookies()
                    result["session_cookie_saved"] = bool(cookies and storage_path.exists())
                    if result["login_success_indicator"]:
                        profile_name = await _get_profile_name(page)
                        upsert_session(chat_id, profile_name=profile_name, storage_state_path=str(storage_path), is_active=True)
                    else:
                        audit_log(chat_id, "debug_login", "failed", detail={"reason": "login_success_indicator_false"})
            if not result["problem_guess"]:
                if not result["env_username_read"] or not result["env_password_available"]:
                    result["problem_guess"] = "Credential env belum lengkap."
                elif not result["login_token_found"]:
                    result["problem_guess"] = "Login token tidak ditemukan; selector/parser Moodle perlu dicek."
                elif not result["login_success_indicator"]:
                    result["problem_guess"] = "Login ditolak atau redirect kembali ke halaman login."
                else:
                    result["problem_guess"] = "Login tampak berhasil."
            return result
        except Exception as exc:
            result["parser_error"] = str(exc)
            result["problem_guess"] = "Debug login gagal saat membuka atau submit halaman."
            return result
        finally:
            await browser.close()


async def relogin_hebat(chat_id: str) -> bool:
    """Force a fresh credential login using env credentials, ignoring stale cookies.

    Reads ``HEBAT_USERNAME`` / ``HEBAT_PASSWORD`` from settings (never logged) and
    rewrites ``storage_state.json`` on success. Emits structured events so the
    relogin path is observable in logs.
    """
    s = get_settings()
    if not s.HEBAT_USERNAME or not s.HEBAT_PASSWORD:
        logger.error(
            "hebat_relogin_failed chat_id=%s reason=missing_credentials "
            "(set HEBAT_USERNAME / HEBAT_PASSWORD or use SSO login)",
            chat_id,
        )
        return False

    logger.info("hebat_relogin_started chat_id=%s", chat_id)
    ok = await login_with_credentials(chat_id, s.HEBAT_USERNAME, s.HEBAT_PASSWORD, force=True)
    if ok:
        logger.info("hebat_relogin_success chat_id=%s", chat_id)
    else:
        logger.error("hebat_relogin_failed chat_id=%s reason=login_rejected", chat_id)
    return ok


async def clear_hebat_session(chat_id: str) -> None:
    """Drop the stored session so the next request is forced to log in cleanly."""
    storage_path = _storage_state_path(chat_id)
    try:
        if storage_path.exists():
            storage_path.unlink()
        logger.info("hebat_session_cleared chat_id=%s", chat_id)
        audit_log(chat_id, "session_cleared", "success")
    except Exception as exc:  # pragma: no cover - filesystem edge case
        logger.warning("clear_hebat_session failed for %s: %s", chat_id, exc)


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


async def get_page_html(
    chat_id: str,
    url: str,
    *,
    force_relogin: bool = False,
    retry_on_logout: bool = True,
) -> str | None:
    """Fetch a Moodle page with the stored session via Playwright.

    Returns rendered HTML, or ``None`` if the session is invalid and relogin
    fails. When ``retry_on_logout`` is set, a page that comes back as the Moodle
    login form triggers exactly one relogin + refetch (bounded, never loops).
    """
    if not _PLAYWRIGHT_AVAILABLE:
        return None

    s = get_settings()

    if force_relogin:
        if not await relogin_hebat(chat_id):
            return None

    storage_path = _storage_state_path(chat_id)
    if not storage_path.exists():
        # No session yet — try to establish one if creds are present.
        if retry_on_logout and await relogin_hebat(chat_id):
            return await get_page_html(chat_id, url, retry_on_logout=False)
        return None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=s.HEBAT_BROWSER_HEADLESS)
        try:
            ctx = await browser.new_context(storage_state=str(storage_path))
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            html = await page.content()
        except Exception as e:
            logger.warning("get_page_html failed for %s: %s", url, e)
            return None
        finally:
            await browser.close()

    # Rendered the login form instead of the page? Re-login once and refetch.
    if retry_on_logout and looks_like_login_page(html):
        logger.info("hebat_session_expired source=playwright url=%s", url)
        if await relogin_hebat(chat_id):
            logger.info("hebat_retry_original_url source=playwright url=%s", url)
            return await get_page_html(chat_id, url, retry_on_logout=False)
        logger.error("hebat_get_failed_after_relogin source=playwright url=%s", url)
        return None

    return html


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
