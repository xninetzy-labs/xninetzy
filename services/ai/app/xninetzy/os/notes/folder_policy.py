from __future__ import annotations

import re
from datetime import date
from typing import Any


CANONICAL_FOLDERS = (
    "Home",
    "Inbox/Captures",
    "Inbox/Triage",
    "Inbox/Unsorted",
    "Daily",
    "Learning/Roadmaps",
    "Learning/Concepts",
    "Learning/Sessions",
    "Learning/Notes",
    "Learning/Reviews",
    "Learning/MOCs",
    "Projects",
    "Academic/HEBAT/Courses",
    "Academic/HEBAT/Assignments",
    "Academic/Cyber-Campus/Schedule",
    "Academic/Cyber-Campus/Grades",
    "Academic/Cyber-Campus/KRS",
    "Academic/QA",
    "Research/Briefs",
    "Research/Sources",
    "Research/Topics",
    "Research/MOCs",
    "Life/Goals",
    "Life/Tasks",
    "Life/Habits",
    "Life/Money",
    "Life/Workouts",
    "Life/Areas",
    "Life/Reviews",
    "Knowledge/Notes",
    "Knowledge/Sources",
    "Knowledge/MOCs",
    "Attachments",
    "System/MOCs",
    "System/Templates",
    "System/Help",
    "System/Logs",
    "System/Migration",
    "Archive",
)

LEGACY_PREFIXES = {
    "Daily": "daily",
    "Learning": "learning",
    "Projects": "project",
    "Tasks": "task",
    "Goals": "goal",
    "HEBAT": "hebat_material",
    "Helper": "helper",
    "Akademik": "system_log",
}


def slugify(value: str, fallback: str = "untitled") -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or fallback


def canonical_path(
    note_type: str,
    *,
    title: str = "untitled",
    date_value: str | date | None = None,
    domain: str = "personal",
    course: str = "course",
    project: str = "project",
    period: str = "",
) -> str:
    value = date_value or date.today()
    if isinstance(value, date):
        date_text = value.isoformat()
    else:
        date_text = str(value)[:10]
    year = date_text[:4]
    month = date_text[5:7]
    slug = slugify(title)

    if note_type == "daily":
        return f"Daily/{year}/{date_text}.md"
    if note_type == "learning_roadmap":
        return f"Learning/Roadmaps/{slug}/README.md"
    if note_type == "learning_concept":
        return f"Learning/Concepts/{slug}.md"
    if note_type == "learning_session":
        return f"Learning/Sessions/{year}/{month}/{slug}.md"
    if note_type == "learning_note":
        return f"Learning/Notes/{slug}.md"
    if note_type == "project":
        project_slug = slugify(project or title)
        return f"Projects/{project_slug}/README.md"
    if note_type == "goal":
        return f"Life/Goals/{slugify(domain)}/{slug}.md"
    if note_type == "task":
        return f"Life/Tasks/{slug}.md"
    if note_type == "hebat_material":
        return f"Academic/HEBAT/Courses/{slugify(course)}/Materials/{slug}.md"
    if note_type == "hebat_assignment":
        return f"Academic/HEBAT/Courses/{slugify(course)}/Assignments/{slug}.md"
    if note_type == "research_brief":
        return f"Research/Briefs/{year}/{date_text}-{slug}.md"
    if note_type == "helper":
        return f"System/Help/{slug}.md"
    if note_type == "system_log":
        return f"System/Logs/{slug}.md"
    if note_type == "life_review":
        return f"Life/Reviews/{period or date_text}/{slug}.md"
    if note_type == "inbox":
        return f"Inbox/Captures/{year}/{month}/{date_text}-{slug}.md"
    return f"Inbox/Unsorted/{slug}.md"


def note_type_from_path(path: str) -> str | None:
    normalized = path.strip("/")
    first = normalized.split("/", 1)[0]
    if first in LEGACY_PREFIXES:
        return LEGACY_PREFIXES[first]
    if normalized.startswith("Learning/Roadmaps/"):
        return "learning_roadmap"
    if normalized.startswith("Learning/Concepts/"):
        return "learning_concept"
    if normalized.startswith("Learning/Sessions/"):
        return "learning_session"
    if normalized.startswith("Learning/Notes/"):
        return "learning_note"
    if normalized.startswith("Life/Goals/"):
        return "goal"
    if normalized.startswith("Life/Tasks/"):
        return "task"
    if normalized.startswith("Academic/HEBAT/"):
        return "hebat_material"
    if normalized.startswith("Research/Briefs/"):
        return "research_brief"
    if normalized.startswith("Daily/"):
        return "daily"
    return None


def canonical_frontmatter(
    *,
    note_type: str,
    title: str,
    path: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "type": note_type,
        "title": title,
        "canonical_path": path,
        "tags": ["xninetzy", note_type.replace("_", "-")],
    }
    if metadata:
        data.update(metadata)
    return data
