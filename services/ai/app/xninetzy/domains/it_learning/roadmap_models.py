from __future__ import annotations

from pydantic import BaseModel, Field


class RoadmapSource(BaseModel):
    source_id: int
    title: str
    source_type: str = "unknown"


class RoadmapPhase(BaseModel):
    start_day: int
    end_day: int
    focus: str
    outcome: str


class RoadmapDraft(BaseModel):
    topic: str
    duration_days: int = 14
    level: str = "beginner"
    target: str
    milestones: list[str]
    first_day_tasks: list[str]
    strategy: str = ""
    phases: list[RoadmapPhase] = Field(default_factory=list)
    source_refs: list[RoadmapSource] = Field(default_factory=list)
