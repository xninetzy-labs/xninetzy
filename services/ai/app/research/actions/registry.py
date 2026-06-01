from __future__ import annotations

from app.research.actions.base import ResearchAction


class ResearchActionRegistry:
    _actions: dict[str, ResearchAction] = {}

    @classmethod
    def register(cls, action: ResearchAction):
        cls._actions[action.name] = action

    @classmethod
    def get(cls, name: str) -> ResearchAction | None:
        return cls._actions.get(name)

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._actions.keys())


def register_default_actions() -> None:
    from app.research.actions.done import DoneResearchAction
    from app.research.actions.plan import PlanResearchAction
    from app.research.actions.search.academic import AcademicSearchAction
    from app.research.actions.search.uploads import UploadsSearchAction
    from app.research.actions.search.web import WebSearchAction
    from app.research.actions.search.youtube import YoutubeSearchAction
    from app.research.actions.subplan import SubPlanResearchAction

    for action in [
        PlanResearchAction(),
        SubPlanResearchAction(),
        WebSearchAction(),
        YoutubeSearchAction(),
        AcademicSearchAction(),
        UploadsSearchAction(),
        DoneResearchAction(),
    ]:
        ResearchActionRegistry.register(action)


register_default_actions()
