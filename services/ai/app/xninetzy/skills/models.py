from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    name: str
    description: str
    path: str
    source: str
    content_hash: str
    metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def summary(self) -> str:
        return self.description


class SkillMatch(BaseModel):
    skill: SkillDefinition
    score: int
    matched_terms: list[str]
