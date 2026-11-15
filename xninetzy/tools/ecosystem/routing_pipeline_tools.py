from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.context.routing.benchmark import (
    BENCHMARK_VERSION,
    BenchmarkCase,
    evaluate_scorecard,
    write_report,
)
from xninetzy.context.routing.baselines import CombinedBaseline, RulesBaseline
from xninetzy.context.routing.pipeline import (
    PIPELINE_VERSION,
    load_pipeline_outcome,
    normalize_request,
    run_pipeline,
)
from xninetzy.context.routing.warmup import warm_once
from xninetzy.tools.tool_results import to_tool_result


@tool
def routing_route_request(
    query: str,
    request_id: str = "",
    approval_id: int | None = None,
    idempotency_key: str = "",
    persist: bool = True,
) -> str:
    """Run the universal routing pipeline end-to-end.

    Args:
        query: Free-text request.
        request_id: Optional idempotent request ID.
        approval_id: HITL approval token for FINAL actions; required
            only when the pipeline selects a FINAL tool.
        idempotency_key: Optional opaque key for write/final actions.
        persist: Write the routing snapshot to data/routing_runs/.

    Returns:
        JSON: {request_id, selected_tool, policy_outcome, ablation,
        domain_selected, tool_selected, schema_total_bytes,
        reason_codes, total_latency_ms}.
    """
    outcome = run_pipeline(
        query,
        request_id=request_id or None,
        approval_id=approval_id,
        idempotency_key=idempotency_key or None,
        persist=persist,
    )
    payload: dict[str, Any] = {
        "version": PIPELINE_VERSION,
        "request_id": outcome.request_id,
        "timestamp": outcome.timestamp,
        "selected_tool": outcome.selected_tool,
        "ablated": outcome.ablated,
        "total_latency_ms": round(outcome.total_latency_ms, 3),
        "reason_codes": list(outcome.reason_codes),
        "domain_selected": list(outcome.domain_decision.selected[:3]),
        "tool_selected": list(outcome.tool_decision.selected[:5]),
        "schema_total_bytes": outcome.schema_bundle.total_bytes if outcome.schema_bundle else 0,
        "policy_outcome": outcome.policy.decision.outcome,
        "policy_reason": outcome.policy.decision.reason,
    }
    return to_tool_result(
        f"Routed '{query[:48]}' → {outcome.selected_tool} (policy={outcome.policy.decision.outcome}).",
        items=[payload],
        meta={"version": PIPELINE_VERSION, "request_id": outcome.request_id},
    )


@tool
def routing_replay(request_id: str) -> str:
    """Replay a previously persisted routing decision.

    Args:
        request_id: The request_id returned by routing_route_request.

    Returns:
        JSON: the persisted snapshot, or an error message.
    """
    snapshot = load_pipeline_outcome(request_id)
    if snapshot is None:
        return to_tool_result(
            f"No routing snapshot for request_id={request_id}.",
            items=[],
            meta={"hint": "ensure persist=True when running the pipeline"},
            ok=False,
        )
    return to_tool_result(
        f"Routing snapshot for {request_id} loaded.",
        items=[snapshot],
        meta={"version": PIPELINE_VERSION, "request_id": request_id},
    )


@tool
def routing_inspect(query: str) -> str:
    """Read-only inspection: normalize request and report the candidate layer outputs WITHOUT executing the tool.

    Args:
        query: Free-text request.

    Returns:
        JSON: {normalized, domain_options, skill_options,
        task_options, capability_options, tool_shortlist, calibration_used}.
    """
    n = normalize_request(query)
    return to_tool_result(
        "Routing inspect (no execution).",
        items=[
            {
                "version": PIPELINE_VERSION,
                "normalized": {
                    "request_id": n.request_id,
                    "text": n.text,
                    "language": n.language,
                    "entities": list(n.entities)[:16],
                    "constraints": list(n.constraints),
                    "desired_output": n.desired_output,
                },
            }
        ],
    )


@tool
def routing_warmup() -> str:
    """Pre-warm the FAISS index + calibration registry so the first
    pipeline run after process start is fast (eliminates the 14s
    cold-load spike observed in Phase 16 baseline runs).

    Returns:
        JSON: {version, faiss_loaded, faiss_warm_latency_ms,
        n_calibration_records, n_warmup_queries, total_warmup_ms,
        already_warm}.
    """
    summary = warm_once()
    return to_tool_result(
        f"Routing warmup: faiss_loaded={summary['faiss_loaded']}, "
        f"warm_latency={summary['faiss_warm_latency_ms']:.1f}ms.",
        items=[summary],
        meta={"version": summary["version"], "owner_action": "optional_one_shot_at_startup"},
    )


routing_pipeline_tools_list = [
    routing_route_request,
    routing_replay,
    routing_inspect,
    routing_warmup,
]


@tool
def routing_benchmark_run(
    split: str = "adversarial_curated",
    baseline: str = "D-rules+embeddings",
    output_dir: str = "data/routing_benchmarks",
    limit: int = 200,
) -> str:
    """Run the routing benchmark on a dataset split and write a report.

    Args:
        split: dataset split to evaluate. Accepts 'adversarial_curated',
            'test', 'val', 'train'. Default: 'adversarial_curated'.
        baseline: 'B-rules' or 'D-rules+embeddings'.
        output_dir: where to write the report JSON + Markdown.
        limit: max cases to evaluate.

    Returns:
        JSON: {baseline, layer, n, top1, topk, domain_match, paths}.
    """
    path = Path("data/routing_dataset") / f"{split}.jsonl"
    if not path.exists():
        return to_tool_result(
            f"dataset split not found: {path}",
            items=[],
            meta={"hint": "run scripts/extract_routing_registry or build dataset first"},
            ok=False,
        )

    import json as _json

    cases: list[BenchmarkCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = _json.loads(line)
        cases.append(
            BenchmarkCase(
                request_id=str(row.get("id", "")),
                query=str(row.get("input", {}).get("text", "")),
                expected_tools=tuple(row.get("expected", {}).get("tools", []) or []),
                expected_domains=tuple(row.get("expected", {}).get("domains", []) or []),
                split=str(row.get("split", split)),
            )
        )
        if len(cases) >= limit:
            break

    if baseline == "B-rules":
        router = RulesBaseline()

        def route_fn(q: str) -> tuple[str, ...]:
            return tuple(router.route(q).selected[:10])

    elif baseline == "D-rules+embeddings":
        router = CombinedBaseline()

        def route_fn(q: str) -> tuple[str, ...]:
            return tuple(router.route(q).selected[:10])

    else:
        return to_tool_result(
            f"unknown baseline: {baseline}",
            items=[],
            meta={"hint": "B-rules or D-rules+embeddings"},
            ok=False,
        )

    scorecard = evaluate_scorecard(
        cases=cases, router=route_fn, baseline_id=baseline, layer="L6"
    )
    paths = write_report(
        type("R", (), {
            "scorecards": (scorecard,),
            "confusion": {},
            "option_cardinality": {},
            "baselines_run": (baseline,),
        })(),
        output_dir=output_dir,
    )
    payload = {
        "version": BENCHMARK_VERSION,
        "baseline": scorecard.baseline,
        "layer": scorecard.layer,
        "n": scorecard.n,
        "top1": round(scorecard.top1, 4),
        "topk": round(scorecard.topk, 4),
        "domain_match": round(scorecard.domain_match, 4),
        "abstention_rate": round(scorecard.abstention_rate, 4),
        "p50_ms": round(scorecard.latency_p50_ms, 2),
        "p95_ms": round(scorecard.latency_p95_ms, 2),
        "max_ms": round(scorecard.latency_max_ms, 2),
        "paths": paths,
    }
    return to_tool_result(
        f"Benchmark complete on '{split}': n={scorecard.n} top1={scorecard.top1:.3f}",
        items=[payload],
        meta={"baseline": baseline, "split": split},
    )


routing_pipeline_tools_list = [
    routing_route_request,
    routing_replay,
    routing_inspect,
    routing_warmup,
    routing_benchmark_run,
]
