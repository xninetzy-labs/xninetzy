from __future__ import annotations

from xninetzy.context.routing.shadow import (
    SHADOW_DEFAULT_SAMPLE_RATE,
    SHADOW_VERSION,
    ShadowDecision,
    ShadowStore,
    compare_summary,
    run_shadow_once,
)


def test_run_shadow_once_returns_decision() -> None:
    d = run_shadow_once("submit to HEBAT")
    assert isinstance(d, ShadowDecision)
    assert d.run_id
    assert d.timestamp


def test_shadow_persists_to_store(tmp_path) -> None:
    store = ShadowStore(storage_dir=tmp_path)
    d = run_shadow_once("find research papers", store=store)
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1
    assert d.run_id in files[0].read_text(encoding="utf-8")


def test_compare_summary_handles_empty() -> None:
    summary = compare_summary([])
    assert summary == {"n": 0}


def test_compare_summary_computes_agreement() -> None:
    decisions = [
        ShadowDecision(
            run_id="a",
            query="x",
            timestamp="2026-09-28T00:00:00+00:00",
            legacy_top1="tool_a",
            legacy_topk=("tool_a", "tool_b"),
            new_top1="tool_a",
            new_topk=("tool_a", "tool_b"),
            agreement_top1=True,
            agreement_topk=2,
            domain_overlap=(),
            latency_legacy_ms=1.0,
            latency_new_ms=10.0,
            sampling_rate=0.1,
        ),
        ShadowDecision(
            run_id="b",
            query="y",
            timestamp="2026-09-28T00:00:01+00:00",
            legacy_top1="tool_c",
            legacy_topk=("tool_c",),
            new_top1="tool_a",
            new_topk=("tool_a", "tool_b"),
            agreement_top1=False,
            agreement_topk=0,
            domain_overlap=(),
            latency_legacy_ms=1.5,
            latency_new_ms=12.0,
            sampling_rate=0.1,
        ),
    ]
    summary = compare_summary(decisions)
    assert summary["n"] == 2
    assert summary["agreement_top1"] == 0.5
    assert summary["avg_topk_overlap"] == 1.0


def test_shadow_defaults() -> None:
    assert SHADOW_VERSION == "1.0.0"
    assert SHADOW_DEFAULT_SAMPLE_RATE >= 0.0
