from __future__ import annotations

from xninetzy.os.research.actions.base import ResearchAction


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
    from xninetzy.os.research.actions.done import DoneResearchAction
    from xninetzy.os.research.actions.plan import PlanResearchAction
    from xninetzy.os.research.actions.search.academic import AcademicSearchAction
    from xninetzy.os.research.actions.search.uploads import UploadsSearchAction
    from xninetzy.os.research.actions.search.web import WebSearchAction
    from xninetzy.os.research.actions.search.youtube import YoutubeSearchAction
    from xninetzy.os.research.actions.subplan import SubPlanResearchAction

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
