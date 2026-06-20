"""Deterministic resource / folder / page extraction.

Resources expose direct file links; folders list multiple child files; pages are
readable HTML. Pure over HTML — unit-tested offline.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from app.xninetzy.os.academic.hebat.html_cleaner import html_to_readable_text
from app.xninetzy.os.academic.hebat.link_extractor import extract_file_links
from app.xninetzy.os.academic.hebat.models import DownloadLink


def extract_resource_detail_from_html(html: str, base_url: str, *, source: str = "resource") -> dict:
    """Title + description + file links (+ readable text for `page` activities)."""
    soup = BeautifulSoup(html or "", "lxml")

    title_el = soup.select_one("h1") or soup.select_one(".page-header-headings h1")
    title = title_el.get_text(strip=True) if title_el else None

    desc_el = (
        soup.find(id="intro")
        or soup.find(class_="resourceworkaround")
        or soup.find(class_="box generalbox")
    )
    description = desc_el.get_text(" ", strip=True) if desc_el else None

    files = [
        DownloadLink(url=f["url"], filename=f.get("filename"), title=f.get("title"), source=source)
        for f in extract_file_links(html, base_url)
    ]

    return {
        "title": title,
        "description": description,
        "files": [l.model_dump() for l in files],
        "file_count": len(files),
        "readable_text": html_to_readable_text(html),
    }
