from __future__ import annotations

from app.xninetzy.os.research.academic_search import academic_search
from app.xninetzy.os.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput


class AcademicSearchAction(ResearchAction):
    name = "academic_search"

    def enabled(self, config: dict) -> bool:
        return bool(config.get("include_academic"))

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        query = input.query or input.topic
        limit = int(input.config.get("limit") or 3)
        sources = await academic_search(query, limit=limit)
        return ResearchActionOutput(type="academic_search", data={"sources": sources})
