from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class SkillInput(BaseModel):
    chat_id: str
    sender_id: str | None = None
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillOutput(BaseModel):
    success: bool
    skill_name: str
    result: dict[str, Any] = Field(default_factory=dict)
    user_facing_text: str | None = None
    memory_updates: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class Skill(Protocol):
    name: str
    description: str
    category: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    safety_policy: str
    memory_behavior: str

    async def run(self, payload: SkillInput) -> SkillOutput:
        ...
