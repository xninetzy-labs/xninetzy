from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import get_settings
from app.core.logging import logging
from app.tools.hebat.browser_session import get_cookies_for_httpx, get_page_html
from app.tools.hebat.parsers import (
    is_logged_out,
    parse_assignment_page,
    parse_course_activities,
    parse_courses,
)

logger = logging.getLogger(__name__)


def _httpx_cookies(raw_cookies: list[dict]) -> dict[str, str]:
    return {c["name"]: c["value"] for c in raw_cookies if "name" in c and "value" in c}


async def _get(chat_id: str, url: str) -> str | None:
    """HTTP GET with stored Moodle session cookies."""
    s = get_settings()
    raw = await get_cookies_for_httpx(chat_id)
    cookies = _httpx_cookies(raw)
    if not cookies:
        # Fall back to Playwright fetch (slower but reliable)
        return await get_page_html(chat_id, url)

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Xninetzy-AI-Bot/1.0"}
    try:
        async with httpx.AsyncClient(cookies=cookies, headers=headers,
                                     follow_redirects=True, timeout=30) as client:
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.warning("HTTP GET failed for %s: %s — retrying via Playwright", url, e)
        return await get_page_html(chat_id, url)


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


async def download_file(chat_id: str, url: str, dest_path: Path) -> dict | None:
    """Download a file from Moodle to dest_path. Returns metadata dict or None."""
    s = get_settings()
    raw = await get_cookies_for_httpx(chat_id)
    cookies = _httpx_cookies(raw)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Xninetzy-AI-Bot/1.0"}

    try:
        async with httpx.AsyncClient(cookies=cookies, headers=headers,
                                     follow_redirects=True, timeout=60) as client:
            await asyncio.sleep(s.HEBAT_RATE_LIMIT_SECONDS)
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                content_disp = resp.headers.get("content-disposition", "")

                # Resolve filename
                filename = dest_path.name
                if "filename=" in content_disp:
                    import re
                    m = re.search(r'filename="?([^";]+)"?', content_disp)
                    if m:
                        filename = m.group(1).strip()
                        dest_path = dest_path.parent / filename

                sha = hashlib.sha256()
                total = 0
                with dest_path.open("wb") as f:
                    async for chunk in resp.aiter_bytes(65_536):
                        f.write(chunk)
                        sha.update(chunk)
                        total += len(chunk)

        return {
            "filename": filename,
            "local_path": str(dest_path),
            "mime_type": content_type.split(";")[0].strip(),
            "size_bytes": total,
            "sha256": sha.hexdigest(),
        }
    except Exception as e:
        logger.error("Download failed for %s: %s", url, e)
        return None
