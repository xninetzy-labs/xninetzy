from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class LoopStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DROPPED = "dropped"


class SkillStatus(str, Enum):
    UNKNOWN = "unknown"
    EXPOSED = "exposed"
    PRACTICING = "practicing"
    APPLIED = "applied"
    STRONG = "strong"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class PersonalProject:
    project_id: str
    title: str
    objective: str
    goal_id: int | None
    status: ProjectStatus
    next_action: str
    created_at: str
    updated_at: str
    last_activity: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "objective": self.objective,
            "goal_id": self.goal_id,
            "status": self.status.value,
            "next_action": self.next_action,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_activity": self.last_activity,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class OpenLoop:
    loop_id: str
    title: str
    description: str
    status: LoopStatus
    age_days: int
    importance: str
    owner_scope: str
    project_id: str | None
    next_action: str
    created_at: str
    resolved_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "age_days": self.age_days,
            "importance": self.importance,
            "owner_scope": self.owner_scope,
            "project_id": self.project_id,
            "next_action": self.next_action,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


@dataclass(frozen=True, slots=True)
class SkillState:
    skill_id: str
    name: str
    status: SkillStatus
    evidence_count: int
    last_practiced: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "status": self.status.value,
            "evidence_count": self.evidence_count,
            "last_practiced": self.last_practiced,
        }


@dataclass(frozen=True, slots=True)
class ReviewRun:
    review_id: str
    period: str
    generated_at: str
    active_projects: tuple[str, ...]
    open_loops: tuple[str, ...]
    stalled_projects: tuple[str, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "period": self.period,
            "generated_at": self.generated_at,
            "active_projects": list(self.active_projects),
            "open_loops": list(self.open_loops),
            "stalled_projects": list(self.stalled_projects),
            "recommendations": list(self.recommendations),
        }


def new_project_id() -> str:
    return f"proj-{uuid.uuid4().hex[:12]}"


def new_loop_id() -> str:
    return f"loop-{uuid.uuid4().hex[:12]}"


def new_skill_id() -> str:
    return f"skill-{uuid.uuid4().hex[:12]}"


def new_review_id() -> str:
    return f"rev-{uuid.uuid4().hex[:12]}"


def _now() -> str:
    return _utcnow()
