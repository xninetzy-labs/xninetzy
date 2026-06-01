from __future__ import annotations

from app.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput
from app.research.web_search import web_search


class WebSearchAction(ResearchAction):
    name = "web_search"

    def enabled(self, config: dict) -> bool:
        return True

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        limit = int(input.config.get("limit") or 3)
        results = await web_search(input.query or input.topic, limit=limit)
        for result in results:
            result.setdefault("source_type", "web")
        return ResearchActionOutput(type="web_search", data={"sources": results})
