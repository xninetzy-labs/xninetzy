"""Deterministic Moodle HTML cleaning.

The agent must never be handed raw Moodle HTML (huge, noisy, hallucination-prone).
These helpers strip chrome and reduce a page to readable text *before* any LLM
step. Pure functions over HTML strings — fully unit-testable offline.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

# Structural chrome that repeats on every Moodle page and adds no content value.
_STRIP_TAGS = ("script", "style", "noscript", "svg", "template", "iframe")
_STRIP_SELECTORS = (
    "nav",
    "footer",
    "header.navbar",
    ".navbar",
    "#nav-drawer",
    ".drawer",
    "[data-region='drawer']",
    ".block_settings",
    ".secondary-navigation",
    "#page-footer",
    ".footer-content",
    ".activity-navigation",
    ".skiplinks",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "lxml")


def clean_moodle_html(html: str) -> str:
    """Return a trimmed HTML string with scripts/nav/footer/drawers removed.

    Content that matters for course/assignment understanding is preserved:
    headings, activity titles, links (with hrefs), tables, dates, instructions.
    """
    soup = _soup(html)

    for tag in soup(list(_STRIP_TAGS)):
        tag.decompose()

    for selector in _STRIP_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    body = soup.body or soup
    return str(body)


def html_to_readable_text(html: str) -> str:
    """Flatten cleaned HTML to readable plain text, keeping link targets inline.

    Links render as ``text (url)`` so downstream extractors and the LLM can still
    see where a "Download" button points without parsing markup.
    """
    soup = _soup(clean_moodle_html(html))

    # Inline the href next to anchor text so it survives get_text().
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        label = a.get_text(strip=True)
        if href and href not in label:
            a.replace_with(f"{label} ({href})" if label else href)

    text = soup.get_text(separator="\n")
    # Collapse runs of blank lines / trailing whitespace.
    lines = [ln.strip() for ln in text.splitlines()]
    cleaned: list[str] = []
    blank = False
    for ln in lines:
        if not ln:
            if not blank:
                cleaned.append("")
            blank = True
        else:
            cleaned.append(ln)
            blank = False
    return "\n".join(cleaned).strip()
