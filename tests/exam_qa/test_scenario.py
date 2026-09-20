from __future__ import annotations

import pytest

from xninetzy.context.exam_qa.scenario import (
    SCENARIO_DRY_RUN,
    SCENARIO_EXAM,
    SCENARIO_PRACTICE,
    build_scenario,
)


def test_build_scenario_accepts_known_kinds():
    for kind in (SCENARIO_DRY_RUN, SCENARIO_PRACTICE, SCENARIO_EXAM):
        scenario = build_scenario(
            scenario_id="s",
            fixture_id="f",
            kind=kind,
            time_limit_minutes=30,
            pass_threshold=0.7,
            authorized=kind == SCENARIO_EXAM,
        )
        assert scenario.kind == kind


def test_build_scenario_rejects_unknown_kind():
    with pytest.raises(ValueError):
        build_scenario(
            scenario_id="s",
            fixture_id="f",
            kind="live",
            time_limit_minutes=30,
            pass_threshold=0.5,
        )


def test_build_scenario_rejects_bad_threshold():
    with pytest.raises(ValueError):
        build_scenario(
            scenario_id="s",
            fixture_id="f",
            kind=SCENARIO_PRACTICE,
            time_limit_minutes=30,
            pass_threshold=1.5,
        )