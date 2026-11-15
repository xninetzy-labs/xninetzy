from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from xninetzy.context.routing.dataset import bucket_domains

BENCHMARK_VERSION = "1.0.0"
DEFAULT_OPTION_BUDGETS: tuple[int, ...] = (3, 5, 8, 10, 12, 15, 20, 25, 30, 50)


@dataclass(frozen=True, slots=True)
class Scorecard:
    layer: str
    baseline: str
    n: int
    top1: float
    topk: float
    domain_match: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_max_ms: float
    abstention_rate: float
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": BENCHMARK_VERSION,
            "layer": self.layer,
            "baseline": self.baseline,
            "n": self.n,
            "top1": round(self.top1, 4),
            "topk": round(self.topk, 4),
            "domain_match": round(self.domain_match, 4),
            "latency_p50_ms": round(self.latency_p50_ms, 3),
            "latency_p95_ms": round(self.latency_p95_ms, 3),
            "latency_max_ms": round(self.latency_max_ms, 3),
            "abstention_rate": round(self.abstention_rate, 4),
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    scorecards: tuple[Scorecard, ...]
    confusion: dict[str, dict[str, int]]
    option_cardinality: dict[str, dict[str, float]]
    baselines_run: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": BENCHMARK_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "baselines_run": list(self.baselines_run),
            "scorecards": [s.to_dict() for s in self.scorecards],
            "confusion": self.confusion,
            "option_cardinality": self.option_cardinality,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    request_id: str
    query: str
    expected_tools: tuple[str, ...]
    expected_domains: tuple[str, ...]
    split: str = "test"


def _topk_overlap(predicted: tuple[str, ...], expected: tuple[str, ...], k: int) -> bool:
    if not expected:
        return False
    return any(p in expected for p in predicted[:k])


def _domain_match(predicted_tools: tuple[str, ...], expected_domains: tuple[str, ...]) -> bool:
    if not expected_domains:
        return False
    return bucket_domains(list(predicted_tools)) == list(expected_domains)


def evaluate_scorecard(
    *,
    cases: list[BenchmarkCase],
    router: Callable[[str], tuple[str, ...]],
    baseline_id: str,
    layer: str,
) -> Scorecard:
    if not cases:
        return Scorecard(
            layer=layer,
            baseline=baseline_id,
            n=0,
            top1=0.0,
            topk=0.0,
            domain_match=0.0,
            latency_p50_ms=0.0,
            latency_p95_ms=0.0,
            latency_max_ms=0.0,
            abstention_rate=0.0,
        )
    top1_hits = 0
    topk_hits = 0
    domain_hits = 0
    abstains = 0
    latencies: list[float] = []
    for c in cases:
        import time as _t

        t0 = _t.perf_counter()
        predicted = router(c.query)
        latencies.append((_t.perf_counter() - t0) * 1000.0)
        if not predicted:
            abstains += 1
            continue
        if predicted[0] in c.expected_tools:
            top1_hits += 1
        if _topk_overlap(predicted, c.expected_tools, k=5):
            topk_hits += 1
        if _domain_match(predicted, c.expected_domains):
            domain_hits += 1
    n = len(cases)
    return Scorecard(
        layer=layer,
        baseline=baseline_id,
        n=n,
        top1=top1_hits / n,
        topk=topk_hits / n,
        domain_match=domain_hits / n,
        latency_p50_ms=_percentile(latencies, 0.5),
        latency_p95_ms=_percentile(latencies, 0.95),
        latency_max_ms=max(latencies) if latencies else 0.0,
        abstention_rate=abstains / n,
        generated_at=datetime.now(UTC).isoformat(),
    )


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    sorted_values = sorted(values)
    idx = max(0, min(len(sorted_values) - 1, int(len(sorted_values) * p)))
    return float(sorted_values[idx])


def compute_confusion(cases: list[BenchmarkCase], router: Callable[[str], tuple[str, ...]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for c in cases:
        predicted = router(c.query)
        expected = c.expected_tools[0] if c.expected_tools else "<none>"
        pred = predicted[0] if predicted else "<abstain>"
        matrix.setdefault(expected, {})
        matrix[expected][pred] = matrix[expected].get(pred, 0) + 1
    return matrix


def evaluate_option_cardinality(
    *,
    cases: list[BenchmarkCase],
    router: Callable[[str], tuple[str, ...]],
    budgets: tuple[int, ...] = DEFAULT_OPTION_BUDGETS,
) -> dict[str, dict[str, float]]:
    results: dict[str, dict[str, float]] = {}
    for budget in budgets:
        s = evaluate_scorecard(
            cases=cases,
            router=lambda q, _b=budget: router(q)[:_b],
            baseline_id=f"B-budget-{budget}",
            layer=f"budget-{budget}",
        )
        results[str(budget)] = {
            "top1": s.top1,
            "topk": s.topk,
            "p50_ms": s.latency_p50_ms,
        }
    return results


def write_report(report: BenchmarkReport, output_dir: str | Path = "data/routing_benchmarks") -> dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat().replace(":", "").replace("-", "")[:15]
    paths: dict[str, str] = {}
    main_path = root / f"report-{stamp}.json"
    main_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    paths["json"] = str(main_path)
    md_path = root / f"report-{stamp}.md"
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    paths["md"] = str(md_path)
    latest_path = root / "latest.json"
    latest_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    paths["latest_json"] = str(latest_path)
    paths["latest_md"] = str(root / "latest.md")
    (root / "latest.md").write_text(_render_markdown(report), encoding="utf-8")
    return paths


def _render_markdown(report: BenchmarkReport) -> str:
    lines: list[str] = ["# Routing benchmark report", ""]
    lines.append(f"Version: `{BENCHMARK_VERSION}`  ")
    lines.append(f"Baselines run: {', '.join(report.baselines_run)}")
    lines.append("")
    lines.append("## Scorecards")
    lines.append("")
    lines.append("| layer | baseline | n | top1 | topk | domain | p50ms | p95ms | maxms | abstention |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for sc in report.scorecards:
        lines.append(
            f"| {sc.layer} | {sc.baseline} | {sc.n} | {sc.top1:.3f} | {sc.topk:.3f} | "
            f"{sc.domain_match:.3f} | {sc.latency_p50_ms:.1f} | {sc.latency_p95_ms:.1f} | "
            f"{sc.latency_max_ms:.1f} | {sc.abstention_rate:.3f} |"
        )
    lines.append("")
    lines.append("## Confusion (top-1)")
    lines.append("")
    for expected, preds in sorted(report.confusion.items())[:20]:
        for pred, count in sorted(preds.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"- expected `{expected}` -> predicted `{pred}`: {count}")
    lines.append("")
    lines.append("## Option cardinality")
    lines.append("")
    lines.append("| budget | top1 | topk | p50_ms |")
    lines.append("| ---: | ---: | ---: | ---: |")
    for budget, metrics in report.option_cardinality.items():
        lines.append(f"| {budget} | {metrics['top1']:.3f} | {metrics['topk']:.3f} | {metrics['p50_ms']:.1f} |")
    return "\n".join(lines)
