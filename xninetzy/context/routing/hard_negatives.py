from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from xninetzy.context.routing.benchmark import BenchmarkCase
from xninetzy.context.routing.dataset import bucket_domains


HARD_NEGATIVE_VERSION = "1.0.0"
DEFAULT_CONFUSION_PAIRS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("research_knowledge", ("research",), ("knowledge",)),
    ("research_academic", ("research",), ("academic",)),
    ("learning_academic", ("learning",), ("academic",)),
    ("software_security", ("software",), ("security",)),
    ("browser_academic", ("browser",), ("academic",)),
    ("media_data", ("media",), ("data",)),
    ("knowledge_productivity", ("knowledge",), ("productivity",)),
    ("os_automation", ("os",), ("automation",)),
    ("career_academic", ("career",), ("academic",)),
)


def _tools_for_domain(domain: str, all_tools: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(t for t in all_tools if domain in bucket_domains([t]))


def generate_paraphrase_pair(seed_query: str, *, target_tools: tuple[str, ...]) -> tuple[BenchmarkCase, BenchmarkCase]:
    prefix = seed_query.strip()
    if not prefix:
        prefix = "find x"
    return (
        BenchmarkCase(
            request_id=f"hn-pos-{abs(hash(prefix)) % 10**9}",
            query=prefix,
            expected_tools=target_tools,
            expected_domains=bucket_domains(list(target_tools)),
            split="adversarial",
        ),
        BenchmarkCase(
            request_id=f"hn-neg-{abs(hash(prefix + ' neg')) % 10**9}",
            query=f"do NOT {prefix}",
            expected_tools=(),
            expected_domains=(),
            split="adversarial",
        ),
    )


def generate_negation_set(seed_query: str, *, exclude_tools: tuple[str, ...]) -> tuple[BenchmarkCase, ...]:
    return (
        BenchmarkCase(
            request_id=f"hn-incl-{abs(hash(seed_query + ' incl')) % 10**9}",
            query=f"include only {seed_query}",
            expected_tools=exclude_tools,
            expected_domains=bucket_domains(list(exclude_tools)),
            split="adversarial",
        ),
        BenchmarkCase(
            request_id=f"hn-excl-{abs(hash(seed_query + ' excl')) % 10**9}",
            query=f"exclude {seed_query}",
            expected_tools=(),
            expected_domains=(),
            split="adversarial",
        ),
        BenchmarkCase(
            request_id=f"hn-dont-{abs(hash(seed_query + ' dont')) % 10**9}",
            query=f"don't include {seed_query}",
            expected_tools=(),
            expected_domains=(),
            split="adversarial",
        ),
    )


def analyze_confusion_pairs(
    *,
    cases: list[BenchmarkCase],
    router: Any,
    pairs: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = DEFAULT_CONFUSION_PAIRS,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for label, positive_domains, negative_domains in pairs:
        rel = [c for c in cases if c.expected_domains and any(d in c.expected_domains for d in positive_domains)]
        if not rel:
            continue

        wrong = 0
        right = 0
        for c in rel:
            outcome_router = router(c.query)
            predicted_tools = _extract_tools(outcome_router)
            domains_pred = bucket_domains(list(predicted_tools))
            hit = any(d in domains_pred for d in positive_domains)
            if hit:
                right += 1
            else:
                wrong += 1
        denom = max(1, right + wrong)
        results[label] = {
            "n": right + wrong,
            "positive_hit": right,
            "missed": wrong,
            "accuracy": right / denom,
        }
    return results


def _extract_tools(outcome_or_decision: Any) -> tuple[str, ...]:
    selected = getattr(outcome_or_decision, "selected", None)
    if selected is not None:
        return tuple(selected[:5])
    if isinstance(outcome_or_decision, dict):
        return tuple(outcome_or_decision.get("selected", []))
    return ()


def write_hard_negative_report(analysis: dict[str, dict[str, Any]], output_dir: str | Path = "data/routing_benchmarks/hard_negatives") -> str:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    out_path = root / "confusion_pairs.json"
    out_path.write_text(json.dumps(analysis, ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    return str(out_path)
