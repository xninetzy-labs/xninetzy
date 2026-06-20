"""Resolve Moodle activity URLs to actual downloadable file links.

Moodle activity links (``/mod/resource/view.php?id=``) are *pages*, not files —
they either embed a ``/pluginfile.php/...`` link or 303-redirect straight to one.
This module turns an activity URL into concrete :class:`DownloadLink` candidates.

The HTML→candidates step is deterministic and unit-tested offline; the network
step reuses the session-healed ``_get`` / no-follow redirect probe.
"""

from __future__ import annotations

from urllib.parse import urljoin

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.academic.hebat.link_extractor import extract_file_links, looks_like_file_url
from app.xninetzy.os.academic.hebat.models import DownloadLink

logger = logging.getLogger(__name__)


def extract_download_candidates(
    html: str, base_url: str, *, source: str = "unknown"
) -> list[DownloadLink]:
    """All direct file links found in a page, tagged with a ``source`` label."""
    out: list[DownloadLink] = []
    for f in extract_file_links(html, base_url):
        out.append(DownloadLink(
            url=f["url"],
            filename=f.get("filename"),
            title=f.get("title"),
            source=source,
        ))
    return out


async def _resource_redirect_target(chat_id: str, url: str) -> DownloadLink | None:
    """Probe a resource URL with redirects disabled.

    Moodle's ``/mod/resource/view.php`` for a single file 303-redirects directly
    to ``/pluginfile.php/...``; capture that Location as a download link without
    chasing it (and without tripping the login-redirect healer for real files).
    """
    import httpx

    from app.xninetzy.os.academic.hebat.browser_session import get_cookies_for_httpx
    from app.xninetzy.os.academic.hebat.parsers import is_login_redirect

    raw = await get_cookies_for_httpx(chat_id)
    cookies = {c["name"]: c["value"] for c in raw if "name" in c and "value" in c}
    if not cookies:
        return None
    try:
        async with httpx.AsyncClient(
            cookies=cookies, follow_redirects=False, timeout=30,
            headers={"User-Agent": "Xninetzy-AI-Bot/1.0"},
        ) as client:
            resp = await client.get(url)
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("location", "")
            if location and not is_login_redirect(location) and looks_like_file_url(location):
                absolute = urljoin(url, location)
                return DownloadLink(url=absolute, source="resource",
                                    filename=absolute.rsplit("/", 1)[-1] or None)
    except Exception as exc:  # pragma: no cover - network edge
        logger.debug("resource redirect probe failed for %s: %s", url, exc)
    return None


async def resolve_download_links(chat_id: str, activity_url: str) -> list[DownloadLink]:
    """Network entry point: turn an activity URL into download candidates.

    1. Probe for a direct resource→pluginfile redirect.
    2. Otherwise fetch the (session-healed) HTML and scrape file links.
    """
    from app.xninetzy.os.academic.hebat.moodle_client import _get

    candidates: list[DownloadLink] = []
    seen: set[str] = set()

    redirect_link = await _resource_redirect_target(chat_id, activity_url)
    if redirect_link:
        candidates.append(redirect_link)
        seen.add(redirect_link.url)

    html = await _get(chat_id, activity_url)
    if html:
        source = _source_for(activity_url)
        for link in extract_download_candidates(html, get_settings().HEBAT_BASE_URL, source=source):
            if link.url not in seen:
                seen.add(link.url)
                candidates.append(link)

    logger.info("hebat_download_candidates url=%s found=%d", activity_url, len(candidates))
    return candidates


def _source_for(activity_url: str) -> str:
    lowered = activity_url.lower()
    if "/mod/assign/" in lowered:
        return "assign_intro"
    if "/mod/folder/" in lowered:
        return "folder"
    if "/mod/page/" in lowered:
        return "page"
    if "/mod/resource/" in lowered:
        return "resource"
    return "unknown"
