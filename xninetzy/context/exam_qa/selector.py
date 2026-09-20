from __future__ import annotations

import hashlib
from dataclasses import dataclass

from xninetzy.context.exam_qa.fixture import ExamFixture, ExamQuestion


SELECTOR_SEQUENTIAL: str = "sequential"
SELECTOR_RANDOMIZED: str = "randomized"

VALID_SELECTORS: frozenset[str] = frozenset(
    {SELECTOR_SEQUENTIAL, SELECTOR_RANDOMIZED}
)


@dataclass(frozen=True, slots=True)
class QuestionSelector:
    strategy: str
    seed: str
    limit: int | None = None

    def identifier(self) -> str:
        digest = hashlib.sha256(
            f"{self.strategy}:{self.seed}:{self.limit}".encode("utf-8")
        ).hexdigest()[:12]
        return f"{self.strategy}-{digest}"


def _deterministic_index(seed: str, total: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % max(total, 1)


def select_questions(
    fixture: ExamFixture,
    selector: QuestionSelector,
) -> tuple[ExamQuestion, ...]:
    if selector.strategy not in VALID_SELECTORS:
        raise ValueError(f"invalid strategy {selector.strategy!r}")
    if not fixture.questions:
        return ()
    if selector.strategy == SELECTOR_SEQUENTIAL:
        chosen = fixture.questions
    else:
        start = _deterministic_index(selector.seed, len(fixture.questions))
        chosen = fixture.questions[start:] + fixture.questions[:start]
    if selector.limit is not None and selector.limit >= 0:
        chosen = chosen[: selector.limit]
    return chosen