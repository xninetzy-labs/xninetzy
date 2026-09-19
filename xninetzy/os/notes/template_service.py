from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import yaml

from xninetzy.core.config import get_settings
from xninetzy.os.notes.folder_policy import canonical_path, slugify

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_VALID_PRIORITY = {"low", "medium", "high", "critical"}
_VALID_STATUS = {"active", "paused", "done", "archived"}


def _render_frontmatter(data: dict[str, object]) -> str:
    try:
        serialized = yaml.safe_dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
    except yaml.YAMLError:
        serialized = yaml.safe_dump(
            {"_render_error": "yaml_dump_failed"},
            default_flow_style=False, allow_unicode=True, sort_keys=False,
        )
    return "---\n" + serialized.rstrip("\n") + "\n---\n\n"


class TemplateService:
    def daily_note(self, date_text: str | None = None) -> tuple[str, str]:
        now = _now()
        if date_text and not _DATE_RE.match(date_text):
            raise ValueError(f"date_text must be YYYY-MM-DD, got: {date_text!r}")
        day = date_text or now.strftime("%Y-%m-%d")
        canonical = canonical_path("daily", date_value=day, title="daily")
        frontmatter = _render_frontmatter({
            "schema_version": 1,
            "type": "daily",
            "title": f"Daily Note - {day}",
            "canonical_path": canonical,
            "date": day,
            "created": now.isoformat(),
            "tags": ["daily", "xninetzy"],
        })
        body = (
            f"# Daily Note - {day}\n\n"
            "## Fokus Hari Ini\n- \n\n"
            "## Task\n- [ ] \n\n"
            "## Catatan Belajar\n- \n\n"
            "## Ide\n- \n\n"
            "## Ringkasan Hari Ini\n"
        )
        return canonical, frontmatter + body

    def learning_note(self, topic: str, summary: str = "", explanation: str = "") -> tuple[str, str]:
        now = _now()
        canonical = canonical_path("learning_note", title=topic)
        frontmatter = _render_frontmatter({
            "schema_version": 1,
            "type": "learning_note",
            "title": topic,
            "canonical_path": canonical,
            "topic": topic,
            "created": now.isoformat(),
            "tags": ["learning"],
        })
        body = (
            f"# {topic}\n\n"
            "## Ringkasan\n{summary}\n\n"
            "## Penjelasan\n{explanation}\n\n"
            "## Contoh\n\n"
            "## Catatan Penting\n\n"
            "## Latihan\n\n"
            "## Related\n"
        )
        return canonical, frontmatter + body

    def project_note(self, project_name: str, goal: str = "", scope: str = "", architecture: str = "") -> tuple[str, str]:
        now = _now()
        folder = slugify(project_name)
        canonical = canonical_path("project", title=project_name, project=folder)
        frontmatter = _render_frontmatter({
            "schema_version": 1,
            "type": "project",
            "title": project_name,
            "canonical_path": canonical,
            "project": project_name,
            "status": "active",
            "created": now.isoformat(),
            "tags": ["project"],
        })
        body = (
            f"# {project_name}\n\n"
            "## Tujuan\n{goal}\n\n"
            "## Scope\n{scope}\n\n"
            "## Arsitektur / Konsep\n{architecture}\n\n"
            "## Task Breakdown\n- [ ] \n\n"
            "## Timeline\n| Minggu | Fokus | Output |\n|---|---|---|\n\n"
            "## Keputusan Teknis\n- \n\n"
            "## Risiko\n- \n\n"
            "## Related Notes\n"
        )
        return canonical, frontmatter + body

    def task_note(
        self,
        task_name: str,
        goal: str = "",
        priority: str = "medium",
        deadline: str | None = None,
        status: str = "active",
    ) -> tuple[str, str]:
        if priority not in _VALID_PRIORITY:
            raise ValueError(
                f"priority tidak valid: {priority!r}; expected one of {sorted(_VALID_PRIORITY)}"
            )
        if status not in _VALID_STATUS:
            raise ValueError(
                f"status tidak valid: {status!r}; expected one of {sorted(_VALID_STATUS)}"
            )
        if deadline and not _DATE_RE.match(deadline):
            raise ValueError(f"deadline must be YYYY-MM-DD, got: {deadline!r}")
        now = _now()
        canonical = canonical_path("task", title=task_name)
        frontmatter = _render_frontmatter({
            "schema_version": 1,
            "type": "task",
            "title": task_name,
            "canonical_path": canonical,
            "status": status,
            "priority": priority,
            "deadline": deadline,
            "created": now.isoformat(),
            "tags": ["task"],
        })
        body = (
            f"# {task_name}\n\n"
            "## Goal\n{goal}\n\n"
            "## Breakdown\n- [ ] \n\n"
            f"## Priority\n{priority}\n\n"
            f"## Deadline\n{deadline or '-'}\n\n"
            "## Progress\n- \n\n"
            "## Next Action\n- \n"
        )
        return canonical, frontmatter + body


def _now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
