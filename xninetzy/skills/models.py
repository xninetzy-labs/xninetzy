from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    name: str
    description: str
    path: str
    source: str
    content_hash: str
    metadata: dict[str, str] = Field(default_factory=dict)
    line_count: int = 0
    resource_paths: list[str] = Field(default_factory=list)
    trust_level: str = "owner"
    quality_warnings: list[str] = Field(default_factory=list)

    @property
    def summary(self) -> str:
        return self.description


class SkillMatch(BaseModel):
    skill: SkillDefinition
    score: int
    matched_terms: list[str]
    confidence: float = 0.0
    selection_reasons: list[str] = Field(default_factory=list)
