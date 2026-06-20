from __future__ import annotations

from app.xninetzy.os.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput


class PlanResearchAction(ResearchAction):
    name = "plan"

    def enabled(self, config: dict) -> bool:
        return True

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        return ResearchActionOutput(
            type="plan",
            data={
                "topic": input.topic,
                "scope": input.config.get("scope") or "learning-os-research",
                "mode": input.mode,
                "goal": f"Menghasilkan brief riset terstruktur tentang {input.topic}",
            },
        )
