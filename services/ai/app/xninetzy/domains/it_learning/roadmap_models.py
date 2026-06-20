from __future__ import annotations

from pydantic import BaseModel


class RoadmapDraft(BaseModel):
    topic: str
    duration_days: int = 14
    target: str
    milestones: list[str]
    first_day_tasks: list[str]
