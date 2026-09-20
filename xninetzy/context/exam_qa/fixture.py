from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FIXTURE_FORMAT_JSON: str = "json"
FIXTURE_FORMAT_YAML: str = "yaml"

VALID_FIXTURE_FORMATS: frozenset[str] = frozenset(
    {FIXTURE_FORMAT_JSON, FIXTURE_FORMAT_YAML}
)


@dataclass(frozen=True, slots=True)
class ExamQuestion:
    question_id: str
    prompt: str
    expected_answer: str
    choices: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExamFixture:
    fixture_id: str
    title: str
    subject: str
    questions: tuple[ExamQuestion, ...]
    format: str = FIXTURE_FORMAT_JSON
    metadata: dict[str, Any] = field(default_factory=dict)

    def question_ids(self) -> tuple[str, ...]:
        return tuple(q.question_id for q in self.questions)


def build_fixture(
    fixture_id: str,
    title: str,
    subject: str,
    questions: list[dict[str, Any]],
    *,
    format: str = FIXTURE_FORMAT_JSON,
    metadata: dict[str, Any] | None = None,
) -> ExamFixture:
    if not fixture_id:
        raise ValueError("fixture_id is required")
    if not title:
        raise ValueError("title is required")
    if format not in VALID_FIXTURE_FORMATS:
        raise ValueError(f"invalid format {format!r}")
    parsed: list[ExamQuestion] = []
    for raw in questions:
        question_id = str(raw.get("id") or raw.get("question_id") or "")
        if not question_id:
            raise ValueError("each question needs id or question_id")
        prompt = str(raw.get("prompt") or raw.get("question") or "")
        if not prompt:
            raise ValueError(f"question {question_id} missing prompt")
        expected = str(raw.get("expected_answer") or raw.get("answer") or "")
        if not expected:
            raise ValueError(f"question {question_id} missing expected_answer")
        parsed.append(
            ExamQuestion(
                question_id=question_id,
                prompt=prompt,
                expected_answer=expected,
                choices=tuple(raw.get("choices") or ()),
                tags=tuple(raw.get("tags") or ()),
                metadata=dict(raw.get("metadata") or {}),
            )
        )
    return ExamFixture(
        fixture_id=fixture_id,
        title=title,
        subject=subject,
        questions=tuple(parsed),
        format=format,
        metadata=dict(metadata or {}),
    )