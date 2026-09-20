from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

ASSERTION_TYPE_EQUALS: str = "equals"
ASSERTION_TYPE_CONTAINS: str = "contains"
ASSERTION_TYPE_REGEX: str = "regex"
ASSERTION_TYPE_STATE: str = "state"
ASSERTION_TYPE_PERSISTED: str = "persisted"

VALID_ASSERTION_TYPES: frozenset[str] = frozenset(
    {
        ASSERTION_TYPE_EQUALS,
        ASSERTION_TYPE_CONTAINS,
        ASSERTION_TYPE_REGEX,
        ASSERTION_TYPE_STATE,
        ASSERTION_TYPE_PERSISTED,
    }
)

ASSERTION_PASS: str = "pass"
ASSERTION_FAIL: str = "fail"
ASSERTION_SKIP: str = "skip"


@dataclass(frozen=True, slots=True)
class AssertionResult:
    assertion_type: str
    target: str
    outcome: str
    observed: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "assertion_type": self.assertion_type,
            "target": self.target,
            "outcome": self.outcome,
            "observed": self.observed,
            "reason": self.reason,
        }


def _safe_match(pattern: str, value: str) -> tuple[bool, str | None]:
    try:
        import re
        return bool(re.search(pattern, value)), None
    except re.error as exc:
        return False, str(exc)


def assert_equals(target: str, expected: str, observed: str) -> AssertionResult:
    return AssertionResult(
        assertion_type=ASSERTION_TYPE_EQUALS,
        target=target,
        outcome=ASSERTION_PASS if observed == expected else ASSERTION_FAIL,
        observed=observed,
        reason=None if observed == expected else f"expected {expected!r}",
    )


def assert_contains(target: str, needle: str, observed: str) -> AssertionResult:
    return AssertionResult(
        assertion_type=ASSERTION_TYPE_CONTAINS,
        target=target,
        outcome=ASSERTION_PASS if needle in observed else ASSERTION_FAIL,
        observed=observed,
        reason=None if needle in observed else f"missing substring {needle!r}",
    )


def assert_regex(target: str, pattern: str, observed: str) -> AssertionResult:
    ok, err = _safe_match(pattern, observed)
    if err is not None:
        return AssertionResult(
            assertion_type=ASSERTION_TYPE_REGEX,
            target=target,
            outcome=ASSERTION_FAIL,
            observed=observed,
            reason=f"invalid regex: {err}",
        )
    return AssertionResult(
        assertion_type=ASSERTION_TYPE_REGEX,
        target=target,
        outcome=ASSERTION_PASS if ok else ASSERTION_FAIL,
        observed=observed,
        reason=None if ok else f"pattern {pattern!r} not matched",
    )


def assert_state(target: str, expected_state: str, observed_state: str) -> AssertionResult:
    return assert_equals(
        target=f"state:{target}",
        expected=expected_state,
        observed=observed_state,
    )


def assert_persisted(
    target: str,
    *,
    saved_now: bool,
    reentry_observed: str | None,
    original: str,
) -> AssertionResult:
    if not saved_now:
        return AssertionResult(
            assertion_type=ASSERTION_TYPE_PERSISTED,
            target=target,
            outcome=ASSERTION_FAIL,
            observed=original,
            reason="save indicator missing",
        )
    if reentry_observed is None:
        return AssertionResult(
            assertion_type=ASSERTION_TYPE_PERSISTED,
            target=target,
            outcome=ASSERTION_SKIP,
            observed=original,
            reason="re-entry not observed",
        )
    return AssertionResult(
        assertion_type=ASSERTION_TYPE_PERSISTED,
        target=target,
        outcome=ASSERTION_PASS if reentry_observed == original else ASSERTION_FAIL,
        observed=reentry_observed,
        reason=None if reentry_observed == original else "re-entry mismatch",
    )


def aggregate_assertions(results: tuple[AssertionResult, ...]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.outcome == ASSERTION_PASS)
    failed = sum(1 for r in results if r.outcome == ASSERTION_FAIL)
    skipped = sum(1 for r in results if r.outcome == ASSERTION_SKIP)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "all_passed": failed == 0 and passed > 0,
    }


def make_idempotency_key(*parts: str) -> str:
    joined = "|".join(parts)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return f"examqa-{digest[:24]}"


@dataclass(frozen=True, slots=True)
class RetryCounter:
    target: str
    max_attempts: int = 3
    attempts: int = 0
    last_error: str | None = None

    def record(self, *, error: str | None = None) -> "RetryCounter":
        return RetryCounter(
            target=self.target,
            max_attempts=self.max_attempts,
            attempts=self.attempts + 1,
            last_error=error,
        )

    def should_retry(self) -> bool:
        return self.attempts < self.max_attempts

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "max_attempts": self.max_attempts,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "should_retry": self.should_retry(),
        }
