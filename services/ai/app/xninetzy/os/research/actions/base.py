from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ResearchActionInput(BaseModel):
    session_id: int
    topic: str
    query: str | None = None
    mode: str = "balanced"
    config: dict[str, Any] = Field(default_factory=dict)


class ResearchActionOutput(BaseModel):
    type: str
    data: dict[str, Any] = Field(default_factory=dict)


class ResearchAction(ABC):
    name: str

    @abstractmethod
    def enabled(self, config: dict) -> bool:
        ...

    @abstractmethod
    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        ...
