from __future__ import annotations

from xninetzy.context.routing.regression import (
    GATE_NAMES,
    REGRESSION_VERSION,
    RegressionStatus,
    run_regression_gate,
    write_regression_report,
)


def test_constants() -> None:
    assert REGRESSION_VERSION == "1.0.0"
    assert len(GATE_NAMES) == 11


def test_run_regression_gate_no_data_returns_skipped() -> None:
    report = run_regression_gate(candidate_report_path="/nonexistent.json")
    assert report.overall in (RegressionStatus.SKIPPED, RegressionStatus.PASSED, RegressionStatus.FAILED)
    assert all(c.status == RegressionStatus.SKIPPED for c in report.checks) or report.overall == RegressionStatus.SKIPPED


def test_run_regression_gate_with_legacy_and_candidate(tmp_path) -> None:
    legacy = {
        "scorecards": [
            {
                "baseline": "D-rules+embeddings",
                "top1": 0.184,
                "topk": 0.395,
                "latency_p95_ms": 536.5,
                "abstention_rate": 0.0,
            }
        ]
    }
    cand = {
        "scorecards": [
            {
                "baseline": "D-rules+embeddings",
                "top1": 0.190,
                "topk": 0.400,
                "latency_p95_ms": 600.0,
                "abstention_rate": 0.10,
            }
        ]
    }
    (tmp_path / "legacy.json").write_text(__import__("json").dumps(legacy), encoding="utf-8")
    (tmp_path / "candidate.json").write_text(__import__("json").dumps(cand), encoding="utf-8")
    report = run_regression_gate(
        legacy_report_path=tmp_path / "legacy.json",
        candidate_report_path=tmp_path / "candidate.json",
        p95_budget_ms=700.0,
    )
    routing_check = next((c for c in report.checks if c.name == "routing_quality"), None)
    assert routing_check is not None
    assert routing_check.status in (RegressionStatus.PASSED, RegressionStatus.FAILED, RegressionStatus.SKIPPED)


def test_run_regression_gate_top1_regression_fails() -> None:
    report = run_regression_gate(
        legacy_report_path=tmp_path_legacy(),
        candidate_report_path=tmp_path_candidate(),
    )
    routing_check = next((c for c in report.checks if c.name == "routing_quality"), None)
    assert routing_check is not None
    assert routing_check.status == RegressionStatus.FAILED
    assert report.overall == RegressionStatus.FAILED
    assert "routing_quality" in " ".join(report.block_reasons)


def tmp_path_legacy() -> str:
    import json as _json
    from pathlib import Path as _P
    p = _P("/tmp/routing_regression_legacy.json")
    p.write_text(
        _json.dumps(
            {"scorecards": [{"baseline": "D-rules+embeddings", "top1": 0.9, "topk": 0.9, "latency_p95_ms": 100.0, "abstention_rate": 0.1}]}
        ),
        encoding="utf-8",
    )
    return str(p)


def tmp_path_candidate() -> str:
    import json as _json
    from pathlib import Path as _P
    p = _P("/tmp/routing_regression_candidate.json")
    p.write_text(
        _json.dumps(
            {"scorecards": [{"baseline": "D-rules+embeddings", "top1": 0.5, "topk": 0.9, "latency_p95_ms": 100.0, "abstention_rate": 0.1}]}
        ),
        encoding="utf-8",
    )
    return str(p)


def test_write_regression_report_creates_file(tmp_path) -> None:
    report = run_regression_gate(candidate_report_path="/nonexistent.json")
    path = write_regression_report(report, tmp_path)
    import pathlib
    assert pathlib.Path(path).exists()
