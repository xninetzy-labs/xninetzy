from __future__ import annotations

from xninetzy.context.evaluation.audit import (
    EVAL_VERDICT_CRITICAL,
    EVAL_VERDICT_FAIL,
    EVAL_VERDICT_PASS,
    EVAL_VERDICT_WARN,
    AuditFindings,
    AuditVerdict,
    evaluate_audit_trail,
)
from xninetzy.context.evaluation.benchmark import (
    BenchmarkMetric,
    compare_to_benchmark,
    get_engine,
    run_benchmark,
)
from xninetzy.context.evaluation.signal_gen import (
    IGNORE,
    extract_signals,
)


def setup_function(_fn):
    get_engine().clear()


def _verdict(label: str, score: float) -> AuditVerdict:
    return AuditVerdict(
        label=label,
        score=score,
        findings=AuditFindings(passed=(), warnings=(), failed=(), critical=()),
    )


def test_evaluate_audit_trail_passes_when_all_pass():
    report = evaluate_audit_trail(
        verdicts=(_verdict(EVAL_VERDICT_PASS, 0.9), _verdict(EVAL_VERDICT_PASS, 0.8))
    )
    assert report.overall.label == EVAL_VERDICT_PASS


def test_evaluate_audit_trail_critical_overrides_fail():
    report = evaluate_audit_trail(
        verdicts=(_verdict(EVAL_VERDICT_FAIL, 0.4), _verdict(EVAL_VERDICT_CRITICAL, 0.1))
    )
    assert report.overall.label == EVAL_VERDICT_CRITICAL


def test_evaluate_audit_trail_fail_when_no_pass():
    report = evaluate_audit_trail(
        verdicts=(_verdict(EVAL_VERDICT_FAIL, 0.3), _verdict(EVAL_VERDICT_WARN, 0.5))
    )
    assert report.overall.label == EVAL_VERDICT_FAIL


def test_evaluate_audit_trail_warn_only():
    report = evaluate_audit_trail(
        verdicts=(_verdict(EVAL_VERDICT_WARN, 0.6),)
    )
    assert report.overall.label == EVAL_VERDICT_WARN


def test_evaluate_audit_trail_empty():
    report = evaluate_audit_trail(verdicts=())
    assert report.overall.label == EVAL_VERDICT_WARN


def test_run_benchmark_stores_result():
    result = run_benchmark(
        name="t1",
        metrics=(
            BenchmarkMetric(name="accuracy", baseline=0.8, candidate=0.85),
        ),
    )
    assert result.overall_improved is True


def test_run_benchmark_not_improved_when_regression():
    result = run_benchmark(
        name="t2",
        metrics=(
            BenchmarkMetric(name="accuracy", baseline=0.8, candidate=0.7),
        ),
    )
    assert result.overall_improved is False


def test_compare_benchmark_no_baseline():
    get_engine().clear()
    cmp = compare_to_benchmark(
        name="missing",
        candidate_metrics=(
            BenchmarkMetric(name="accuracy", baseline=0.0, candidate=0.5),
        ),
    )
    assert cmp.improvements == ()
    assert "no baseline" in "; ".join(cmp.notes)


def test_compare_benchmark_improvements_and_regressions():
    get_engine().clear()
    run_benchmark(
        name="bench-x",
        metrics=(
            BenchmarkMetric(name="acc", baseline=0.5, candidate=0.5),
            BenchmarkMetric(
                name="lat",
                baseline=80.0,
                candidate=80.0,
                higher_is_better=False,
            ),
        ),
    )
    cmp = compare_to_benchmark(
        name="bench-x",
        candidate_metrics=(
            BenchmarkMetric(name="acc", baseline=0.5, candidate=0.7),
            BenchmarkMetric(
                name="lat",
                baseline=80.0,
                candidate=100.0,
                higher_is_better=False,
            ),
        ),
    )
    assert "acc" in cmp.improvements
    assert "lat" in cmp.regressions


def test_extract_signals_learn_high_confidence():
    batch = extract_signals(
        findings=(
            {"source": "ctx", "summary": "x", "confidence": 0.9},
        ),
    )
    assert batch.learn_count == 1
    assert batch.monitor_count == 0


def test_extract_signals_monitor_mid_confidence():
    batch = extract_signals(
        findings=(
            {"source": "ctx", "summary": "x", "confidence": 0.5},
        ),
    )
    assert batch.learn_count == 0
    assert batch.monitor_count == 1


def test_extract_signals_ignore_low_confidence():
    batch = extract_signals(
        findings=(
            {"source": "ctx", "summary": "x", "confidence": 0.1},
        ),
    )
    assert batch.ignore_count == 1
    assert batch.signals[0].action == IGNORE


def test_extract_signals_mixed():
    batch = extract_signals(
        findings=(
            {"source": "a", "summary": "x", "confidence": 0.9},
            {"source": "b", "summary": "y", "confidence": 0.5},
            {"source": "c", "summary": "z", "confidence": 0.1},
        ),
    )
    assert batch.learn_count == 1
    assert batch.monitor_count == 1
    assert batch.ignore_count == 1
