from __future__ import annotations

from app.xninetzy.os.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput


class DoneResearchAction(ResearchAction):
    name = "done"

    def enabled(self, config: dict) -> bool:
        return True

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        return ResearchActionOutput(type="done", data={"status": "done", "topic": input.topic})
