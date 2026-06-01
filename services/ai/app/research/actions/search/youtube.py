from __future__ import annotations

from app.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput
from app.research.youtube_search import youtube_search


class YoutubeSearchAction(ResearchAction):
    name = "youtube_search"

    def enabled(self, config: dict) -> bool:
        return bool(config.get("include_youtube", True))

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        limit = int(input.config.get("limit") or 3)
        results = await youtube_search(input.query or f"{input.topic} tutorial", limit=limit)
        for result in results:
            result.setdefault("source_type", "youtube")
        return ResearchActionOutput(type="youtube_search", data={"sources": results})
