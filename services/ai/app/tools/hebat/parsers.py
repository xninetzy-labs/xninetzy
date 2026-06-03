from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from app.tools.hebat.models import ActivityType


BASE = "https://hebat.elearning.unair.ac.id"

_TYPE_MAP = {
    "/mod/resource/": ActivityType.RESOURCE,
    "/mod/folder/": ActivityType.FOLDER,
    "/mod/assign/": ActivityType.ASSIGN,
    "/mod/forum/": ActivityType.FORUM,
    "/mod/quiz/": ActivityType.QUIZ,
    "/mod/page/": ActivityType.PAGE,
    "/mod/url/": ActivityType.URL,
}


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def parse_login_page(html: str) -> dict:
    soup = _soup(html)
    logintoken_input = soup.find("input", {"name": "logintoken"})
    google_link = soup.find("a", href=re.compile(r"/auth/oauth2/"))
    return {
        "logintoken": logintoken_input["value"] if logintoken_input else None,
        "has_username_field": bool(soup.find("input", {"name": "username"})),
        "google_oauth_url": google_link["href"] if google_link else None,
        "already_logged_in": bool(soup.find(string=re.compile("already logged in", re.I))),
    }


def parse_courses(html: str) -> list[dict]:
    soup = _soup(html)
    courses: dict[str, dict] = {}
    for a in soup.find_all("a", href=re.compile(r"/course/view\.php\?id=\d+")):
        href = a.get("href", "")
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        course_id = qs.get("id", [None])[0]
        if not course_id or course_id in courses:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        courses[course_id] = {
            "moodle_course_id": course_id,
            "fullname": title,
            "shortname": None,
            "course_url": urljoin(BASE, href),
        }
    return list(courses.values())


def parse_course_activities(html: str, course_id: str) -> list[dict]:
    soup = _soup(html)
    activities: list[dict] = []
    seen_cmids: set[str] = set()

    current_section = "General"
    for el in soup.find_all(["h3", "h4", "li", "div"]):
        # Section headings
        if el.name in ("h3", "h4"):
            text = el.get_text(strip=True)
            if text:
                current_section = text

        # Activity links
        link = el if el.name == "a" else el.find("a", href=True)
        if not link:
            continue
        href = link.get("href", "")
        if not href:
            continue

        activity_type = ActivityType.UNKNOWN
        for pattern, atype in _TYPE_MAP.items():
            if pattern in href:
                activity_type = atype
                break
        if activity_type == ActivityType.UNKNOWN:
            continue

        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        cmid = qs.get("id", [None])[0]
        if not cmid or cmid in seen_cmids:
            continue
        seen_cmids.add(cmid)

        title = (
            el.get("data-activityname")
            or link.get_text(strip=True)
            or f"Activity {cmid}"
        )
        activities.append({
            "course_id": course_id,
            "cmid": cmid,
            "type": activity_type,
            "title": title,
            "section_title": current_section,
            "activity_url": urljoin(BASE, href),
        })

    return activities


def parse_assignment_page(html: str) -> dict:
    soup = _soup(html)

    # Title
    title_el = soup.find("h1") or soup.find(class_="page-header-headings")
    title = title_el.get_text(strip=True) if title_el else ""

    # Dates from activity-dates region
    opened_at = due_at = time_remaining = None
    dates_region = soup.find(attrs={"data-region": "activity-dates"})
    if dates_region:
        for item in dates_region.find_all("div", class_=True):
            text = item.get_text(" ", strip=True)
            if re.search(r"open(ed)?", text, re.I):
                m = re.search(r"\d{1,2}\s+\w+\s+\d{4}", text)
                if m:
                    opened_at = m.group()
            if re.search(r"due|deadline", text, re.I):
                m = re.search(r"\d{1,2}\s+\w+\s+\d{4}.*", text)
                if m:
                    due_at = m.group()

    # Time remaining
    time_el = soup.find(string=re.compile(r"Time remaining", re.I))
    if time_el:
        row = time_el.find_parent("tr") if time_el else None
        if row:
            cells = row.find_all("td")
            time_remaining = cells[-1].get_text(strip=True) if cells else None

    # Instruction / intro
    intro_el = soup.find(id="intro") or soup.find(class_="box py-3 generalbox")
    instruction = intro_el.get_text("\n", strip=True) if intro_el else ""

    # Attachment links in intro
    attachments: list[dict] = []
    if intro_el:
        for a in intro_el.find_all("a", href=re.compile(r"pluginfile\.php|forcedownload=1")):
            attachments.append({
                "filename": a.get_text(strip=True),
                "url": urljoin(BASE, a["href"]),
            })

    # Submission status table
    submission_status = grading_status = last_modified = None
    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            if "submission status" in label:
                submission_status = value
            elif "grading status" in label:
                grading_status = value
            elif "last modified" in label:
                last_modified = value
            elif "time remaining" in label and not time_remaining:
                time_remaining = value

    # Add submission button / edit submission
    has_add_button = bool(soup.find("button", string=re.compile(r"Add submission", re.I)))
    has_edit_button = bool(soup.find("button", string=re.compile(r"Edit submission", re.I)))
    can_submit = has_add_button or has_edit_button

    return {
        "title": title,
        "opened_at": opened_at,
        "due_at": due_at,
        "time_remaining": time_remaining,
        "instruction": instruction,
        "attachments": attachments,
        "submission_status": submission_status,
        "grading_status": grading_status,
        "last_modified": last_modified,
        "can_submit": can_submit,
    }


def parse_edit_submission_page(html: str) -> dict:
    soup = _soup(html)
    form = soup.find("form", {"action": re.compile(r"/mod/assign/view\.php")})
    if not form:
        return {}

    def hidden(name: str) -> str:
        el = form.find("input", {"name": name, "type": "hidden"})
        return el["value"] if el else ""

    # itemid from file manager input
    fm_input = form.find("input", {"name": "files_filemanager"})
    item_id = fm_input["value"] if fm_input else ""

    # accepted types from filemanager options div or data attrs
    accepted_types: list[str] = [".pdf"]
    fm_div = soup.find(attrs={"data-filetypes": True})
    if fm_div:
        try:
            import json
            types = json.loads(fm_div["data-filetypes"])
            if isinstance(types, list):
                accepted_types = types
        except Exception:
            pass

    # maxbytes
    max_bytes = 5_242_880
    mb_el = soup.find(attrs={"data-maxbytes": True})
    if mb_el:
        try:
            max_bytes = int(mb_el["data-maxbytes"])
        except Exception:
            pass

    return {
        "form_action": urljoin(BASE, form.get("action", "/mod/assign/view.php")),
        "item_id": item_id,
        "sesskey": hidden("sesskey"),
        "assign_id": hidden("id"),
        "user_id": hidden("userid"),
        "context_id": None,
        "max_bytes": max_bytes,
        "max_files": 1,
        "accepted_types": accepted_types,
    }


def is_logged_out(html: str) -> bool:
    patterns = [
        r"you are not logged in",
        r"login to the site",
        r"loggedout",
        r"/login/index\.php",
    ]
    lower = html.lower()
    return any(re.search(p, lower) for p in patterns)


def is_login_redirect(location: str | None) -> bool:
    """True if a redirect ``Location`` (or any URL) points at Moodle's login page.

    Covers the two loop signatures we see in the wild::

        /login/index.php
        /login/index.php?loginredirect=1
    """
    if not location:
        return False
    lowered = location.lower()
    return "/login/index.php" in lowered or "loginredirect=1" in lowered


def looks_like_login_page(html: str) -> bool:
    """Strong "this is the Moodle login page" signal.

    Unlike :func:`is_logged_out` (which matches any stray ``/login/index.php``
    link and can false-positive on authenticated pages), this requires the
    actual login *form* — a ``logintoken`` input or a username+password pair.
    Used to decide whether a re-login is genuinely warranted so we never loop
    re-logging-in on a page that merely links to login.
    """
    if not html:
        return False
    lower = html.lower()
    if 'name="logintoken"' in lower or "name='logintoken'" in lower:
        return True
    has_username = 'name="username"' in lower or "name='username'" in lower
    has_password = 'name="password"' in lower or "name='password'" in lower
    return has_username and has_password
