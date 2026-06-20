from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.academic.hebat.browser_session import (
    get_cookies_for_httpx,
    get_page_html,
    relogin_hebat,
)
from app.xninetzy.os.academic.hebat.parsers import (
    is_logged_out,
    is_login_redirect,
    looks_like_login_page,
    parse_assignment_page,
    parse_course_activities,
    parse_courses,
)

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (X11; Linux x86_64) Xninetzy-AI-Bot/1.0"
# Moodle redirects use these codes when a session is gone.
_REDIRECT_CODES = {301, 302, 303, 307, 308}


def _httpx_cookies(raw_cookies: list[dict]) -> dict[str, str]:
    return {c["name"]: c["value"] for c in raw_cookies if "name" in c and "value" in c}


async def _get(chat_id: str, url: str, *, _relogin_attempt: int = 0) -> str | None:
    """HTTP GET a Moodle page with the stored session, healing expired cookies.

    Root cause this guards against: a stale cookie makes Moodle 302 the request
    to ``/login/index.php?loginredirect=1``; with ``follow_redirects=True`` httpx
    chases that until ``TooManyRedirects``. Here we disable auto-follow, detect a
    redirect *to login* (or a rendered login form), then re-login once and retry
    the original URL — bounded by ``HEBAT_SESSION_MAX_RELOGIN`` so it can never
    loop forever. Genuine non-login redirects are still followed normally.
    """
    s = get_settings()
    raw = await get_cookies_for_httpx(chat_id)
    cookies = _httpx_cookies(raw)
    if not cookies:
        # No stored cookies — let the Playwright path establish/repair a session.
        return await get_page_html(chat_id, url, retry_on_logout=True)

    headers = {"User-Agent": _UA}
    try:
        async with httpx.AsyncClient(
            cookies=cookies, headers=headers, follow_redirects=False, timeout=30
        ) as client:
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            resp = await client.get(url)

            if resp.status_code in _REDIRECT_CODES:
                location = resp.headers.get("location", "")
                if is_login_redirect(location):
                    logger.info(
                        "hebat_http_redirect_to_login url=%s status=%s location=%s",
                        url, resp.status_code, location,
                    )
                    return await _relogin_and_retry(chat_id, url, _relogin_attempt)
                # Legitimate redirect (e.g. resource → pluginfile): follow it once.
                resolved = urljoin(url, location)
                follow = await client.get(resolved, follow_redirects=True)
                follow.raise_for_status()
                return follow.text

            resp.raise_for_status()
            html = resp.text

            if looks_like_login_page(html):
                logger.info("hebat_session_expired url=%s (login form in body)", url)
                return await _relogin_and_retry(chat_id, url, _relogin_attempt)
            return html

    except httpx.TooManyRedirects:
        # Defensive: should not happen with follow_redirects=False, but if a
        # followed non-login redirect itself loops, treat it as an expired session.
        logger.warning("hebat_http_redirect_to_login url=%s reason=too_many_redirects", url)
        return await _relogin_and_retry(chat_id, url, _relogin_attempt)
    except Exception as e:
        logger.warning("HTTP GET failed for %s: %s — falling back to Playwright", url, e)
        return await get_page_html(chat_id, url, retry_on_logout=True)


async def _relogin_and_retry(chat_id: str, url: str, attempt: int) -> str | None:
    """Re-login (bounded) and retry the original URL; never loops."""
    s = get_settings()
    if attempt >= s.HEBAT_SESSION_MAX_RELOGIN:
        logger.error(
            "hebat_get_failed_after_relogin url=%s attempts=%d", url, attempt
        )
        return None
    if not await relogin_hebat(chat_id):
        return None
    logger.info("hebat_retry_original_url url=%s attempt=%d", url, attempt + 1)
    return await _get(chat_id, url, _relogin_attempt=attempt + 1)


async def fetch_courses(chat_id: str) -> list[dict]:
    s = get_settings()
    url = s.HEBAT_BASE_URL + "/my/courses.php"
    # The "My courses" page renders its course cards client-side via JavaScript,
    # so a raw httpx fetch returns 0 courses. Use the JS-capable Playwright path.
    html = await get_page_html(chat_id, url)
    if not html or is_logged_out(html):
        return []
    return parse_courses(html)


async def fetch_course_activities(chat_id: str, course_id: str) -> list[dict]:
    s = get_settings()
    url = f"{s.HEBAT_BASE_URL}/course/view.php?id={course_id}"
    html = await _get(chat_id, url)
    if not html or is_logged_out(html):
        return []
    return parse_course_activities(html, course_id)


async def fetch_assignment_detail(chat_id: str, cmid: str) -> dict:
    s = get_settings()
    url = f"{s.HEBAT_BASE_URL}/mod/assign/view.php?id={cmid}"
    html = await _get(chat_id, url)
    if not html:
        return {}
    return parse_assignment_page(html)


def _is_login_html_bytes(content_type: str, head: bytes) -> bool:
    """True if a "download" actually returned the Moodle login page.

    Guards against the classic failure where an expired cookie makes a file URL
    redirect to ``/login/index.php`` and we save the login HTML as a fake .pdf.
    """
    if "text/html" not in (content_type or "").lower():
        return False
    snippet = head[:4096].decode("utf-8", errors="replace")
    return looks_like_login_page(snippet) or is_login_redirect(snippet)


async def download_file(
    chat_id: str, url: str, dest_path: Path, *, _relogin_attempt: int = 0
) -> dict | None:
    """Download a Moodle file to ``dest_path`` with validation.

    Never persists a login page as a file: if the response is HTML *and* looks
    like the login form, it re-logs-in once and retries; HTML that is genuine
    content is saved as ``.html`` instead of the requested binary extension.
    Returns rich metadata (incl. ``source_url`` / ``final_url``) or ``None``.
    """
    s = get_settings()
    raw = await get_cookies_for_httpx(chat_id)
    cookies = _httpx_cookies(raw)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": _UA}

    try:
        async with httpx.AsyncClient(cookies=cookies, headers=headers,
                                     follow_redirects=True, timeout=60) as client:
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                content_disp = resp.headers.get("content-disposition", "")
                final_url = str(resp.url)

                sha = hashlib.sha256()
                total = 0
                first = True
                is_html_content = "text/html" in content_type.lower()

                # Resolve filename from Content-Disposition → URL → dest fallback.
                filename = dest_path.name
                if "filename=" in content_disp:
                    import re
                    m = re.search(r'filename="?([^";]+)"?', content_disp)
                    if m:
                        filename = m.group(1).strip()
                        dest_path = dest_path.parent / filename
                if is_html_content and not dest_path.suffix == ".html":
                    dest_path = dest_path.with_suffix(".html")
                    filename = dest_path.name

                with dest_path.open("wb") as f:
                    async for chunk in resp.aiter_bytes(65_536):
                        if first:
                            first = False
                            if _is_login_html_bytes(content_type, chunk):
                                f.close()
                                dest_path.unlink(missing_ok=True)
                                logger.info(
                                    "hebat_download_got_login url=%s final=%s", url, final_url
                                )
                                if _relogin_attempt < s.HEBAT_SESSION_MAX_RELOGIN and await relogin_hebat(chat_id):
                                    return await download_file(
                                        chat_id, url, dest_path.with_suffix(""),
                                        _relogin_attempt=_relogin_attempt + 1,
                                    )
                                logger.error("hebat_download_failed_login url=%s", url)
                                return None
                        f.write(chunk)
                        sha.update(chunk)
                        total += len(chunk)

        if total == 0:
            logger.warning("hebat_download_empty url=%s", url)
            dest_path.unlink(missing_ok=True)
            return None

        from datetime import datetime, timezone

        return {
            "filename": filename,
            "local_path": str(dest_path),
            "source_url": url,
            "final_url": final_url,
            "mime_type": content_type.split(";")[0].strip(),
            "size_bytes": total,
            "sha256": sha.hexdigest(),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("hebat_download_failed url=%s err=%s", url, e)
        return None
