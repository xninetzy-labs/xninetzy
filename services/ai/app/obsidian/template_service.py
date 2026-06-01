from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


class TemplateService:
    def daily_note(self, date_text: str | None = None) -> tuple[str, str]:
        now = _now()
        day = date_text or now.strftime("%Y-%m-%d")
        return (
            f"Daily/{day}.md",
            f"""---
type: daily
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
        slug = _slug(topic)
        return (
            f"Learning/{slug}.md",
            f"""---
type: learning
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
            f"Projects/{folder}/README.md",
            f"""---
type: project
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
            f"Tasks/{_slug(task_name)}.md",
            f"""---
type: task
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
