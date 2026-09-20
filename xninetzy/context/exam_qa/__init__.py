from __future__ import annotations

from xninetzy.context.exam_qa.fixture import (
    ExamFixture,
    build_fixture,
)
from xninetzy.context.exam_qa.scenario import (
    ExamScenario,
    build_scenario,
)
from xninetzy.context.exam_qa.state_machine import (
    ExamRunState,
    RunPhase,
    transition_run,
)
from xninetzy.context.exam_qa.provider import (
    PROVIDER_LOCAL,
    PROVIDER_MOCK,
    ExamProvider,
    resolve_provider,
)
from xninetzy.context.exam_qa.selector import (
    QuestionSelector,
    select_questions,
)

PACKAGE_MARKER: str = "xninetzy.context.exam_qa"

__all__ = [
    "ExamFixture",
    "ExamProvider",
    "ExamRunState",
    "ExamScenario",
    "PACKAGE_MARKER",
    "PROVIDER_LOCAL",
    "PROVIDER_MOCK",
    "QuestionSelector",
    "RunPhase",
    "build_fixture",
    "build_scenario",
    "resolve_provider",
    "select_questions",
    "transition_run",
]