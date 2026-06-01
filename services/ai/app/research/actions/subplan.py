from __future__ import annotations

from app.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput
from app.research.subplanner import generate_research_subplans


class SubPlanResearchAction(ResearchAction):
    name = "subplan"

    def enabled(self, config: dict) -> bool:
        return True

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        subplans = await generate_research_subplans(
            input.topic,
            input.config.get("scope"),
            input.mode,
        )
        return ResearchActionOutput(
            type="subplan",
            data={"subplans": [sp.model_dump() for sp in subplans]},
        )
