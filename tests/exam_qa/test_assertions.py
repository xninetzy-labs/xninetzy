from __future__ import annotations

from xninetzy.context.exam_qa.assertions import (
    ASSERTION_FAIL,
    ASSERTION_PASS,
    ASSERTION_SKIP,
    AssertionResult,
    RetryCounter,
    aggregate_assertions,
    assert_contains,
    assert_equals,
    assert_persisted,
    assert_regex,
    assert_state,
    make_idempotency_key,
)


def test_assert_equals_pass():
    result = assert_equals("title", "ok", "ok")
    assert result.outcome == ASSERTION_PASS
    assert result.target == "title"


def test_assert_equals_fail():
    result = assert_equals("title", "ok", "error")
    assert result.outcome == ASSERTION_FAIL
    assert result.reason is not None


def test_assert_contains_pass():
    result = assert_contains("body", "exam", "the exam started")
    assert result.outcome == ASSERTION_PASS


def test_assert_contains_fail():
    result = assert_contains("body", "exam", "nothing here")
    assert result.outcome == ASSERTION_FAIL


def test_assert_regex_pass():
    result = assert_regex("answer", r"^\d+$", "42")
    assert result.outcome == ASSERTION_PASS


def test_assert_regex_fail():
    result = assert_regex("answer", r"^\d+$", "abc")
    assert result.outcome == ASSERTION_FAIL


def test_assert_regex_invalid_pattern_returns_fail():
    result = assert_regex("answer", r"[", "abc")
    assert result.outcome == ASSERTION_FAIL
    assert "regex" in (result.reason or "")


def test_assert_state_uses_equals_logic():
    result = assert_state("exam", "in_progress", "in_progress")
    assert result.outcome == ASSERTION_PASS
    result_fail = assert_state("exam", "in_progress", "submitted")
    assert result_fail.outcome == ASSERTION_FAIL


def test_assert_persisted_pass():
    result = assert_persisted(
        "q1",
        saved_now=True,
        reentry_observed="answer-A",
        original="answer-A",
    )
    assert result.outcome == ASSERTION_PASS


def test_assert_persisted_save_missing():
    result = assert_persisted(
        "q1",
        saved_now=False,
        reentry_observed=None,
        original="answer-A",
    )
    assert result.outcome == ASSERTION_FAIL


def test_assert_persisted_reentry_skipped():
    result = assert_persisted(
        "q1",
        saved_now=True,
        reentry_observed=None,
        original="answer-A",
    )
    assert result.outcome == ASSERTION_SKIP


def test_assert_persisted_mismatch():
    result = assert_persisted(
        "q1",
        saved_now=True,
        reentry_observed="answer-B",
        original="answer-A",
    )
    assert result.outcome == ASSERTION_FAIL


def test_aggregate_assertions_counts():
    results = (
        AssertionResult(ASSERTION_PASS, "a", ASSERTION_PASS, "ok"),
        AssertionResult(ASSERTION_FAIL, "b", ASSERTION_FAIL, "no"),
        AssertionResult(ASSERTION_SKIP, "c", ASSERTION_SKIP, ""),
    )
    agg = aggregate_assertions(results)
    assert agg["total"] == 3
    assert agg["passed"] == 1
    assert agg["failed"] == 1
    assert agg["skipped"] == 1
    assert agg["all_passed"] is False


def test_aggregate_assertions_empty_is_not_all_passed():
    agg = aggregate_assertions(())
    assert agg["total"] == 0
    assert agg["all_passed"] is False


def test_aggregate_assertions_only_passes():
    results = (
        AssertionResult(ASSERTION_PASS, "a", ASSERTION_PASS, "ok"),
        AssertionResult(ASSERTION_PASS, "b", ASSERTION_PASS, "ok"),
    )
    agg = aggregate_assertions(results)
    assert agg["all_passed"] is True


def test_make_idempotency_key_deterministic():
    a = make_idempotency_key("run-1", "step-3", "exam-qa")
    b = make_idempotency_key("run-1", "step-3", "exam-qa")
    assert a == b
    assert a.startswith("examqa-")


def test_make_idempotency_key_differs_for_different_parts():
    a = make_idempotency_key("run-1")
    b = make_idempotency_key("run-2")
    assert a != b


def test_retry_counter_starts_at_zero():
    counter = RetryCounter(target="login")
    assert counter.attempts == 0
    assert counter.should_retry() is True


def test_retry_counter_increments_on_record():
    counter = RetryCounter(target="login")
    counter = counter.record(error="timeout")
    assert counter.attempts == 1
    assert counter.last_error == "timeout"


def test_retry_counter_respects_max():
    counter = RetryCounter(target="login", max_attempts=2)
    counter = counter.record()
    counter = counter.record()
    assert counter.should_retry() is False


def test_retry_counter_to_dict():
    counter = RetryCounter(target="submit", max_attempts=3)
    counter = counter.record(error="x")
    data = counter.to_dict()
    for key in ("target", "max_attempts", "attempts", "last_error", "should_retry"):
        assert key in data
