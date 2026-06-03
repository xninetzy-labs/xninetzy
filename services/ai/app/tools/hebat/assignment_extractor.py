"""Deterministic assignment-page extraction.

Builds on the existing ``parse_assignment_page`` and adds classified download
links (instruction attachments vs submission files vs feedback files) plus a
clean readable-text blob for the LLM. Pure over HTML — unit-tested offline.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from app.tools.hebat.html_cleaner import html_to_readable_text
from app.tools.hebat.link_extractor import extract_file_links
from app.tools.hebat.models import DownloadLink
from app.tools.hebat.parsers import parse_assignment_page

_SUBMISSION_RE = re.compile(r"assignsubmission|submissionstatustable|submission", re.I)
_FEEDBACK_RE = re.compile(r"feedback", re.I)


def _classify_region(node) -> str:
    """Best-effort source label for a link based on its surrounding region."""
    for parent in node.parents:
        classes = " ".join(parent.get("class", [])) if hasattr(parent, "get") else ""
        ident = parent.get("id", "") if hasattr(parent, "get") else ""
        blob = f"{classes} {ident}"
        if _FEEDBACK_RE.search(blob):
            return "assign_feedback"
        if _SUBMISSION_RE.search(blob):
            return "assign_submission"
    return "assign_intro"


def extract_assignment_detail_from_html(html: str, base_url: str) -> dict:
    """Structured assignment detail + classified download links + clean text."""
    base = parse_assignment_page(html)
    soup = BeautifulSoup(html or "", "lxml")

    # Classify every file link by the region it sits in.
    attachments: list[DownloadLink] = []
    submission_files: list[DownloadLink] = []
    feedback_files: list[DownloadLink] = []
    seen: set[str] = set()

    for f in extract_file_links(html, base_url):
        url = f["url"]
        if url in seen:
            continue
        seen.add(url)
        # Find the anchor again to inspect its region.
        anchor = soup.find("a", href=lambda h: h and (h in url or url.endswith(h)))
        source = _classify_region(anchor) if anchor else "assign_intro"
        link = DownloadLink(url=url, filename=f.get("filename"), title=f.get("title"), source=source)
        if source == "assign_feedback":
            feedback_files.append(link)
        elif source == "assign_submission":
            submission_files.append(link)
        else:
            attachments.append(link)

    return {
        "title": base.get("title"),
        "instruction_text": base.get("instruction"),
        "due_date_text": base.get("due_at"),
        "opened_at": base.get("opened_at"),
        "time_remaining_text": base.get("time_remaining"),
        "submission_status": base.get("submission_status"),
        "grading_status": base.get("grading_status"),
        "last_modified": base.get("last_modified"),
        "can_submit": base.get("can_submit"),
        "attachments": [l.model_dump() for l in attachments],
        "submission_files": [l.model_dump() for l in submission_files],
        "feedback_files": [l.model_dump() for l in feedback_files],
        "raw_clean_text": html_to_readable_text(html),
    }
