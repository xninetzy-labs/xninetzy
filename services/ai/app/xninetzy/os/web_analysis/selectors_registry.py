from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from app.xninetzy.os.web_analysis.models import ModuleRecord


SELECTOR_CANDIDATES = (
    "nav",
    "table",
    "table.generaltable",
    "form",
    "main",
    "[role='main']",
    "[role='navigation']",
    "[data-region]",
    ".course-content",
    ".dashboard-card",
    ".assignment-info",
)

MODULE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("krs_availability", ("krs", "registrasi", "mata-kuliah")),
    ("schedule", ("jadwal", "schedule", "timetable")),
    ("grades", ("nilai", "grade", "rapor", "transkrip")),
    ("assignments", ("assign", "tugas", "assignment")),
    ("announcements", ("pengumuman", "announcement", "forum")),
    ("courses", ("course", "matakuliah", "mata-kuliah")),
    ("login", ("login", "signin", "masuk")),
)

_SAFE_FIELD_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.:\[\]-]{0,79}$")


def _module_name(path: str, field_names: list[str]) -> str:
    sample = path.lower()
    for name, patterns in MODULE_PATTERNS:
        if any(pattern in sample for pattern in patterns):
            return name
    if "password" in field_names:
        return "login"
    return "page_structure"


def extract_module_structure(url: str, html: str) -> ModuleRecord:
    """Extract structure only; visible page values are intentionally not retained."""
    soup = BeautifulSoup(html, "html.parser")
    selectors: list[str] = []
    for selector in SELECTOR_CANDIDATES:
        try:
            if soup.select_one(selector):
                selectors.append(selector)
        except Exception:
            continue

    field_names = sorted(
        {
            str(element.get("name"))
            for element in soup.select("input[name], select[name], textarea[name]")
            if element.get("name") and _SAFE_FIELD_NAME.fullmatch(str(element.get("name")))
        }
    )
    path = urlsplit(url).path or "/"
    module_name = _module_name(path, field_names)
    has_form = soup.select_one("form") is not None
    if module_name == "krs_availability":
        classification = "monitor_only"
    elif has_form:
        classification = "contains_action"
    else:
        classification = "read_only"

    tag_signature = {
        tag: len(soup.find_all(tag))
        for tag in ("nav", "main", "section", "table", "form", "article")
    }
    hash_input = {
        "module": module_name,
        "path": path,
        "selectors": selectors,
        "field_names": field_names,
        "tags": tag_signature,
    }
    structure_hash = hashlib.sha256(
        json.dumps(hash_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ModuleRecord(
        name=module_name,
        path=path,
        classification=classification,
        selectors=selectors,
        field_names=field_names,
        structure_hash=structure_hash,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )
