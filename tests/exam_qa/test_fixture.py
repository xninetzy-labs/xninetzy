from __future__ import annotations

import pytest

from xninetzy.context.exam_qa.fixture import (
    FIXTURE_FORMAT_YAML,
    build_fixture,
)


def test_build_fixture_happy_path():
    fixture = build_fixture(
        fixture_id="f-1",
        title="Intro",
        subject="biology",
        questions=[
            {
                "id": "q1",
                "prompt": "What is ATP?",
                "expected_answer": "energy carrier",
                "choices": ("a", "b"),
                "tags": ("cell",),
            }
        ],
        format=FIXTURE_FORMAT_YAML,
    )
    assert fixture.fixture_id == "f-1"
    assert fixture.format == FIXTURE_FORMAT_YAML
    assert fixture.questions[0].question_id == "q1"
    assert fixture.question_ids() == ("q1",)


def test_build_fixture_rejects_missing_id():
    with pytest.raises(ValueError):
        build_fixture(
            fixture_id="f",
            title="t",
            subject="s",
            questions=[{"prompt": "p", "expected_answer": "a"}],
        )


def test_build_fixture_rejects_bad_format():
    with pytest.raises(ValueError):
        build_fixture(
            fixture_id="f",
            title="t",
            subject="s",
            questions=[],
            format="xml",
        )