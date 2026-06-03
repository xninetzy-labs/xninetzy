"""Deterministic link extraction from Moodle HTML.

Separates the two link kinds that matter:
  * activity links (`/mod/<type>/view.php?id=<cmid>`) — navigation targets
  * file links (`/pluginfile.php/...`, `forcedownload=1`, direct `.pdf`/`.docx`…)
    — actual downloadable bytes

Pure functions over HTML strings; no network, fully unit-testable.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from app.tools.hebat.models import ActivityType

_MOD_RE = re.compile(r"/mod/([a-z]+)/view\.php\?id=(\d+)", re.I)

_FILE_EXTS = (
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".zip", ".rar", ".txt", ".csv", ".md", ".odt", ".ods", ".odp",
)

_TYPE_MAP = {
    "resource": ActivityType.RESOURCE,
    "folder": ActivityType.FOLDER,
    "assign": ActivityType.ASSIGN,
    "forum": ActivityType.FORUM,
    "quiz": ActivityType.QUIZ,
    "page": ActivityType.PAGE,
    "url": ActivityType.URL,
}


def classify_mod_type(mod_name: str) -> ActivityType:
    return _TYPE_MAP.get(mod_name.lower(), ActivityType.UNKNOWN)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "lxml")


def looks_like_file_url(url: str) -> bool:
    """True if a URL is (probably) a direct downloadable file, not a page."""
    if not url:
        return False
    lowered = url.lower()
    if "/pluginfile.php/" in lowered:
        return True
    qs = parse_qs(urlparse(lowered).query)
    if qs.get("forcedownload", ["0"])[0] in ("1", "true") or "download=1" in lowered:
        return True
    path = urlparse(lowered).path
    return any(path.endswith(ext) for ext in _FILE_EXTS)


def extract_mod_links(html: str, base_url: str) -> list[dict]:
    """All Moodle activity links, deduped by cmid, with type + title."""
    soup = _soup(html)
    seen: set[str] = set()
    out: list[dict] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = _MOD_RE.search(href)
        if not m:
            continue
        mod_name, cmid = m.group(1), m.group(2)
        if cmid in seen:
            continue
        seen.add(cmid)
        out.append({
            "cmid": cmid,
            "type": classify_mod_type(mod_name),
            "title": a.get_text(strip=True) or None,
            "activity_url": urljoin(base_url, href),
        })
    return out


def extract_file_links(html: str, base_url: str) -> list[dict]:
    """All direct file/download links on a page, deduped by absolute URL."""
    soup = _soup(html)
    seen: set[str] = set()
    out: list[dict] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not looks_like_file_url(href):
            continue
        absolute = urljoin(base_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        label = a.get_text(strip=True) or None
        filename = _filename_from_url(absolute)
        out.append({
            "url": absolute,
            "filename": filename,
            "title": label,
        })
    return out


def _filename_from_url(url: str) -> str | None:
    from urllib.parse import unquote

    path = urlparse(url).path
    name = unquote(path.rsplit("/", 1)[-1]) if "/" in path else None
    return name or None
