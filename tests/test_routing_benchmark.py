from __future__ import annotations

from pathlib import Path

from xninetzy.context.routing.benchmark import (
    BenchmarkCase,
    BenchmarkReport,
    Scorecard,
    _percentile,
    compute_confusion,
    evaluate_option_cardinality,
    evaluate_scorecard,
    write_report,
)


def test_percentile_handles_empty() -> None:
    assert _percentile([], 0.5) == 0.0
    assert _percentile([42.0], 0.5) == 42.0


def test_evaluate_scorecard_returns_metrics() -> None:
    cases = [
        BenchmarkCase(
            request_id="1",
            query="submit to HEBAT",
            expected_tools=("hebat_upload_submission",),
            expected_domains=("academic",),
        ),
        BenchmarkCase(
            request_id="2",
            query="find research",
            expected_tools=("research_search_papers",),
            expected_domains=("research",),
        ),
    ]

    def router(q):
        if "submit" in q:
            return ("hebat_upload_submission", "knowledge_search")
        if "find research" in q:
            return ("research_search_papers", "research_search")
        return ("knowledge_search",)

    cases2 = list(cases) + [
        BenchmarkCase(
            request_id="3",
            query="submit HEBAT but lowercase",
            expected_tools=("never_matches_xyz",),
            expected_domains=(),
        )
    ]
    sc = evaluate_scorecard(cases=cases2, router=router, baseline_id="T", layer="L6")
    assert sc.baseline == "T"
    assert sc.layer == "L6"
    assert sc.n == 3
    assert abs(sc.top1 - (2.0 / 3.0)) < 1e-6
    assert abs(sc.topk - (2.0 / 3.0)) < 1e-6


def test_compute_confusion_records_actual_vs_expected() -> None:
    cases = [
        BenchmarkCase(request_id="1", query="q1", expected_tools=("expected_a",), expected_domains=()),
        BenchmarkCase(request_id="2", query="q2", expected_tools=("expected_a",), expected_domains=()),
    ]

    def router(q):
        return ("expected_a",) if q == "q1" else ("predicted_b",)

    matrix = compute_confusion(cases, router)
    assert matrix["expected_a"]["expected_a"] == 1
    assert matrix["expected_a"]["predicted_b"] == 1


def test_evaluate_option_cardinality_returns_keys() -> None:
    cases = [
        BenchmarkCase(request_id="1", query="x", expected_tools=("a",), expected_domains=()),
    ]

    def router(q):
        return ("a", "b", "c", "d")

    res = evaluate_option_cardinality(
        cases=cases,
        router=router,
        budgets=(3, 5),
    )
    assert "3" in res and "5" in res
    assert res["3"]["top1"] == 1.0


def test_write_report_creates_files(tmp_path) -> None:
    sc = Scorecard(
        layer="L6",
        baseline="T",
        n=5,
        top1=0.6,
        topk=0.8,
        domain_match=0.4,
        latency_p50_ms=10.0,
        latency_p95_ms=15.0,
        latency_max_ms=20.0,
        abstention_rate=0.1,
        generated_at="2026-09-28T00:00:00+00:00",
    )
    report = BenchmarkReport(
        scorecards=(sc,),
        confusion={},
        option_cardinality={"10": {"top1": 0.6, "topk": 0.8, "p50_ms": 10.0}},
        baselines_run=("T",),
    )
    paths = write_report(report, tmp_path)
    for k in ("json", "md", "latest_json", "latest_md"):
        assert Path(paths[k]).exists()
