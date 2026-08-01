from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.notes.folder_policy import canonical_path


class TemplateService:
    def daily_note(self, date_text: str | None = None) -> tuple[str, str]:
        now = _now()
        day = date_text or now.strftime("%Y-%m-%d")
        return (
            canonical_path('daily', date_value=day, title="daily"),
            f"""---
schema_version: 1
type: daily
title: "Daily Note - {day}"
canonical_path: {canonical_path('daily', date_value=day, title="daily")}
date: {day}
created: {now.isoformat()}
tags: [daily, xninetzy]
---

# Daily Note - {day}

## Fokus Hari Ini
- 

## Task
- [ ] 

## Catatan Belajar
- 

## Ide
- 

## Ringkasan Hari Ini
""",
        )

    def learning_note(self, topic: str, summary: str = "", explanation: str = "") -> tuple[str, str]:
        now = _now()
        return (
            canonical_path('learning_note', title=topic),
            f"""---
schema_version: 1
type: learning_note
title: "{topic}"
canonical_path: {canonical_path('learning_note', title=topic)}
topic: "{topic}"
created: {now.isoformat()}
tags: [learning]
---

# {topic}

## Ringkasan
{summary}

## Penjelasan
{explanation}

## Contoh

## Catatan Penting

## Latihan

## Related
""",
        )

    def project_note(self, project_name: str, goal: str = "", scope: str = "", architecture: str = "") -> tuple[str, str]:
        now = _now()
        folder = _slug(project_name)
        return (
            canonical_path('project', title=project_name, project=folder),
            f"""---
schema_version: 1
type: project
title: "{project_name}"
canonical_path: {canonical_path('project', title=project_name, project=folder)}
project: "{project_name}"
status: active
created: {now.isoformat()}
tags: [project]
---

# {project_name}

## Tujuan
{goal}

## Scope
{scope}

## Arsitektur / Konsep
{architecture}

## Task Breakdown
- [ ] 

## Timeline
| Minggu | Fokus | Output |
|---|---|---|

## Keputusan Teknis
- 

## Risiko
- 

## Related Notes
""",
        )

    def task_note(self, task_name: str, goal: str = "", priority: str = "medium", deadline: str | None = None) -> tuple[str, str]:
        now = _now()
        return (
            canonical_path('task', title=task_name),
            f"""---
schema_version: 1
type: task
title: "{task_name}"
canonical_path: {canonical_path('task', title=task_name)}
status: active
created: {now.isoformat()}
tags: [task]
---

# {task_name}

## Goal
{goal}

## Breakdown
- [ ] 

## Priority
{priority}

## Deadline
{deadline or "-"}

## Progress
- 

## Next Action
- 
""",
        )


def _now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    return "-".join(part for part in slug.split("-") if part) or "untitled"
