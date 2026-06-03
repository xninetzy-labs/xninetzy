"""Extract course list and deep course outline from full Moodle HTML.

Deterministic, heuristic-based parsing (no LLM). Tolerant of Moodle theme
variations by trying several selectors and falling back to flat link scraping
so a layout change degrades gracefully instead of returning nothing.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from app.tools.hebat.link_extractor import classify_mod_type
from app.tools.hebat.models import CourseOutline, OutlineActivity, OutlineSection

_COURSE_RE = re.compile(r"/course/view\.php\?id=(\d+)")
_MOD_RE = re.compile(r"/mod/([a-z]+)/view\.php\?id=(\d+)", re.I)
_DUE_RE = re.compile(r"(due|tenggat|deadline|batas)\b", re.I)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "lxml")


# ─── course list ─────────────────────────────────────────────────────────────

def extract_courses_from_html(html: str, base_url: str) -> list[dict]:
    """All courses linked on a dashboard / my-courses / course-index page."""
    soup = _soup(html)
    courses: dict[str, dict] = {}
    for a in soup.find_all("a", href=True):
        m = _COURSE_RE.search(a["href"])
        if not m:
            continue
        course_id = m.group(1)
        title = a.get_text(strip=True)
        if not title:
            # Card layouts sometimes put the name on a sibling/aria-label.
            title = (a.get("aria-label") or a.get("title") or "").strip()
        if not title:
            continue
        existing = courses.get(course_id)
        if existing and len(existing["fullname"]) >= len(title):
            continue
        courses[course_id] = {
            "moodle_course_id": course_id,
            "fullname": title,
            "shortname": None,
            "course_url": urljoin(base_url, a["href"]),
            "category": _nearest_category(a),
        }
    return list(courses.values())


def _nearest_category(anchor: Tag) -> str | None:
    for parent in anchor.parents:
        if not isinstance(parent, Tag):
            continue
        cat = parent.find(class_=re.compile(r"category|coursecat", re.I))
        if cat and cat is not anchor:
            text = cat.get_text(strip=True)
            if text:
                return text
    return None


# ─── course outline ──────────────────────────────────────────────────────────

def extract_course_outline_from_html(html: str, base_url: str, course_id: str) -> CourseOutline:
    """Structured sections → activities for one course page."""
    soup = _soup(html)
    title = _course_title(soup)

    section_nodes = (
        soup.select("li.section")
        or soup.select(".course-content .section")
        or soup.select("[data-for='section']")
    )

    sections: list[OutlineSection] = []
    seen_cmids: set[str] = set()

    for node in section_nodes:
        section = _parse_section(node, base_url, seen_cmids)
        if section.activities or section.summary:
            sections.append(section)

    # Fallback: no recognisable sections — scrape every mod link flatly.
    if not any(s.activities for s in sections):
        flat = _flat_activities(soup, base_url, seen_cmids)
        if flat:
            sections = [OutlineSection(title="General", activities=flat)]

    return CourseOutline(course_id=course_id, title=title, sections=sections)


def _course_title(soup: BeautifulSoup) -> str | None:
    for sel in ("h1", ".page-header-headings h1", "header h1", "title"):
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            if text:
                return text
    return None


def _parse_section(node: Tag, base_url: str, seen_cmids: set[str]) -> OutlineSection:
    title_el = node.find(class_=re.compile(r"sectionname", re.I)) or node.find(
        ["h3", "h4"]
    )
    title = title_el.get_text(strip=True) if title_el else "Section"

    summary_el = node.find(class_=re.compile(r"\bsummary\b", re.I))
    summary = summary_el.get_text(" ", strip=True) if summary_el else None

    activities = _activities_in(node, base_url, seen_cmids, title)
    return OutlineSection(title=title or "Section", summary=summary or None, activities=activities)


def _activities_in(
    node: Tag, base_url: str, seen_cmids: set[str], section_title: str
) -> list[OutlineActivity]:
    activity_nodes = (
        node.select("li.activity")
        or node.select(".activity-item")
        or node.select("[data-for='cmitem']")
    )
    out: list[OutlineActivity] = []
    for an in activity_nodes:
        act = _parse_activity(an, base_url, section_title)
        if act and act.cmid and act.cmid not in seen_cmids:
            seen_cmids.add(act.cmid)
            out.append(act)
    return out


def _parse_activity(node: Tag, base_url: str, section_title: str) -> OutlineActivity | None:
    link = None
    for a in node.find_all("a", href=True):
        if _MOD_RE.search(a["href"]):
            link = a
            break
    if not link:
        return None

    m = _MOD_RE.search(link["href"])
    mod_name, cmid = m.group(1), m.group(2)

    name_el = node.find(class_=re.compile(r"instancename", re.I))
    title = name_el.get_text(strip=True) if name_el else link.get_text(strip=True)
    # Moodle appends an accessibility " Assignment"/" File" suffix to instancename.
    accesshide = name_el.find(class_=re.compile(r"accesshide", re.I)) if name_el else None
    if accesshide:
        suffix = accesshide.get_text(strip=True)
        if suffix and title.endswith(suffix):
            title = title[: -len(suffix)].strip()

    visible = node.get_text(" ", strip=True) or None
    avail_el = node.find(class_=re.compile(r"availabilityinfo", re.I))
    availability = avail_el.get_text(" ", strip=True) if avail_el else None
    due = _due_text(visible)

    return OutlineActivity(
        cmid=cmid,
        type=classify_mod_type(mod_name),
        title=title or f"{mod_name} {cmid}",
        activity_url=urljoin(base_url, link["href"]),
        section_title=section_title,
        visible_text=visible,
        due_date_text=due,
        availability_text=availability,
    )


def _flat_activities(soup: BeautifulSoup, base_url: str, seen_cmids: set[str]) -> list[OutlineActivity]:
    out: list[OutlineActivity] = []
    for a in soup.find_all("a", href=True):
        m = _MOD_RE.search(a["href"])
        if not m:
            continue
        cmid = m.group(2)
        if cmid in seen_cmids:
            continue
        seen_cmids.add(cmid)
        out.append(OutlineActivity(
            cmid=cmid,
            type=classify_mod_type(m.group(1)),
            title=a.get_text(strip=True) or f"{m.group(1)} {cmid}",
            activity_url=urljoin(base_url, a["href"]),
            section_title="General",
        ))
    return out


def _due_text(text: str | None) -> str | None:
    if not text or not _DUE_RE.search(text):
        return None
    for sentence in re.split(r"[.\n]", text):
        if _DUE_RE.search(sentence):
            return sentence.strip() or None
    return None
