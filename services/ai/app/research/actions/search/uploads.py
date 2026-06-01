from __future__ import annotations

from app.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput


class UploadsSearchAction(ResearchAction):
    name = "uploads_search"

    def enabled(self, config: dict) -> bool:
        return bool(config.get("include_uploads"))

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        return ResearchActionOutput(type="uploads_search", data={"sources": []})
