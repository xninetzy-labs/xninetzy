from __future__ import annotations

from pydantic import BaseModel


class SkillDefinition(BaseModel):
    name: str
    summary: str
    path: str
    tools: list[str]
