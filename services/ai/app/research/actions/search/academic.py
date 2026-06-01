from __future__ import annotations

from app.research.actions.base import ResearchAction, ResearchActionInput, ResearchActionOutput


class AcademicSearchAction(ResearchAction):
    name = "academic_search"

    def enabled(self, config: dict) -> bool:
        return bool(config.get("include_academic"))

    async def execute(self, input: ResearchActionInput) -> ResearchActionOutput:
        query = input.query or input.topic
        return ResearchActionOutput(
            type="academic_search",
            data={
                "sources": [
                    {
                        "title": f"Academic search placeholder: {query}",
                        "url": "",
                        "snippet": "Academic provider belum dikonfigurasi; gunakan mode ini sebagai slot integrasi berikutnya.",
                        "source_type": "academic",
                    }
                ]
            },
        )
