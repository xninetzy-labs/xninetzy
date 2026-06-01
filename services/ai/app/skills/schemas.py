from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillRoute(BaseModel):
    needs_skill: bool = False
    skill_name: str | None = None
    skill_action: str | None = None
    skill_args: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    reason: str = ""


class SkillRunRequest(BaseModel):
    chat_id: str = "debug"
    sender_id: str | None = None
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
