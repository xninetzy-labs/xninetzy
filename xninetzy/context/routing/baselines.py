from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from xninetzy.context.routing.dataset import bucket_domains
from xninetzy.tools.registry import get_tool_names


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    request_id: str
    baseline: str
    selected: tuple[str, ...]
    candidate_pool_size: int
    latency_ms: float
    reason_codes: tuple[str, ...] = ()
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    request_id: str
    query: str
    expected_tools: tuple[str, ...]
    expected_domains: tuple[str, ...]
    split: str = "test"
    difficulty: str = "easy"


class RouterLike(Protocol):
    baseline_id: str

    def route(self, query: str, *, top_k: int = 10, candidate_tools: list[str] | None = None) -> RoutingDecision: ...


def _case_from_dataset_row(row: dict[str, Any]) -> BenchmarkCase:
    expected = row.get("expected", {})
    return BenchmarkCase(
        request_id=str(row.get("id", "")),
        query=str(row.get("input", {}).get("text", "")),
        expected_tools=tuple(expected.get("tools", []) or []),
        expected_domains=tuple(expected.get("domains", []) or []),
        split=str(row.get("split", "test")),
        difficulty=str(row.get("difficulty", "easy")),
    )


def load_benchmark_cases(*, split: str = "test", limit: int | None = None, data_root: str = "data/routing_dataset") -> list[BenchmarkCase]:
    from pathlib import Path

    p = Path(data_root) / f"{split}.jsonl"
    if not p.exists():
        return []
    cases: list[BenchmarkCase] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        import json

        cases.append(_case_from_dataset_row(json.loads(line)))
    if limit is not None:
        cases = cases[:limit]
    return cases


_TOKEN_RE = re.compile(r"[a-z_]+")


def _score_alias(query: str, tool_name: str) -> float:
    normalized = query.lower()
    tokens = _TOKEN_RE.findall(normalized)
    name_norm = tool_name.lower().replace("_", " ").replace("-", " ")
    name_tokens = tool_name.lower().replace("_", " ").replace("-", " ").split()
    score = 0.0
    for tk in tokens:
        if tk in name_tokens or tk in name_norm:
            score += 0.4
        elif len(tk) >= 5 and any(tk in t for t in name_tokens):
            score += 0.2
    return score


def top1_acc(cases: list[BenchmarkCase], *, router: RouterLike, top_k: int = 5) -> dict[str, Any]:
    n = 0
    top1_hits = 0
    topk_hits = 0
    domains_ok = 0
    latencies: list[float] = []
    for case in cases:
        n += 1
        decision = router.route(case.query, top_k=top_k)
        latencies.append(decision.latency_ms)
        sel = set(decision.selected[:top_k])
        exp = set(case.expected_tools)
        if exp:
            if decision.selected and decision.selected[0] in exp:
                top1_hits += 1
            if sel & exp:
                topk_hits += 1
        if case.expected_domains and bucket_domains(decision.selected[:top_k]) == list(case.expected_domains):
            domains_ok += 1
    return {
        "baseline": router.baseline_id,
        "n": n,
        "top1": top1_hits / n if n else 0.0,
        "topk": topk_hits / n if n else 0.0,
        "domain_match": domains_ok / n if n else 0.0,
        "latency_p50_ms": sorted(latencies)[len(latencies) // 2] if latencies else 0.0,
        "latency_p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0,
    }


def _timer(fn: Callable[[], RoutingDecision]) -> tuple[RoutingDecision, float]:
    t0 = time.perf_counter()
    decision = fn()
    return decision, (time.perf_counter() - t0) * 1000.0


class RulesBaseline:
    baseline_id = "B-rules"

    def __init__(self, intent_registry_getter=None) -> None:
        self.intent_registry_getter = intent_registry_getter

    def route(self, query: str, *, top_k: int = 10, candidate_tools: list[str] | None = None) -> RoutingDecision:
        pool = list(candidate_tools) if candidate_tools else list(get_tool_names())
        if self.intent_registry_getter is not None:
            registry = self.intent_registry_getter()
        else:
            registry = {}
        keyword_to_domain: dict[str, str] = {}
        for keyword, (domain, _members) in registry.items():
            keyword_to_domain[keyword] = domain
        scored: list[tuple[float, str]] = []
        for tool_name in pool:
            score = _score_alias(query, tool_name)
            for kw, dom in keyword_to_domain.items():
                if kw in query.lower() and dom in tool_name:
                    score += 0.3
            if score > 0.0:
                scored.append((score, tool_name))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [name for _, name in scored[:top_k]]
        decision, latency = _timer(lambda: RoutingDecision(
            request_id=f"B-{abs(hash(query)) % 10**9}",
            baseline=self.baseline_id,
            selected=tuple(selected),
            candidate_pool_size=len(pool),
            latency_ms=0.0,
            reason_codes=("rules_keywords",),
            confidence=min(1.0, (scored[0][0] if scored else 0.0) / 2.0),
        ))
        return RoutingDecision(
            request_id=decision.request_id,
            baseline=decision.baseline,
            selected=decision.selected,
            candidate_pool_size=decision.candidate_pool_size,
            latency_ms=latency,
            reason_codes=decision.reason_codes,
            confidence=decision.confidence,
            metadata=decision.metadata,
        )


class EmbeddingsBaseline:
    baseline_id = "C-embeddings"

    def route(self, query: str, *, top_k: int = 10, candidate_tools: list[str] | None = None) -> RoutingDecision:
        try:
            import numpy as np
            from xninetzy.os.knowledge.embeddings import embed_query, embed_texts
        except Exception:
            decision, latency = _timer(lambda: RoutingDecision(
                request_id=f"C-{abs(hash(query)) % 10**9}",
                baseline=self.baseline_id,
                selected=tuple(),
                candidate_pool_size=len(candidate_tools or get_tool_names()),
                latency_ms=0.0,
                reason_codes=("embeddings_unavailable",),
                confidence=0.0,
            ))
            return decision
        pool = list(candidate_tools) if candidate_tools else list(get_tool_names())
        docs = [name.replace("_", " ") for name in pool]
        try:
            target = embed_query(query)
            matrix = np.array(embed_texts(docs[:200]))
            sims = matrix @ np.array(target)
            ranked_idx = sims.argsort()[::-1][:top_k]
            selected = [pool[int(i)] for i in ranked_idx if 0 <= int(i) < len(pool)]
            confidence = float(sims[ranked_idx[0]]) if len(ranked_idx) > 0 else 0.0
        except Exception:
            decision, latency = _timer(lambda: RoutingDecision(
                request_id=f"C-{abs(hash(query)) % 10**9}",
                baseline=self.baseline_id,
                selected=tuple(),
                candidate_pool_size=len(pool),
                latency_ms=0.0,
                reason_codes=("embeddings_failed",),
                confidence=0.0,
            ))
            return decision
        decision, latency = _timer(lambda: RoutingDecision(
            request_id=f"C-{abs(hash(query)) % 10**9}",
            baseline=self.baseline_id,
            selected=tuple(selected),
            candidate_pool_size=len(pool),
            latency_ms=0.0,
            reason_codes=("embedding_top_k",),
            confidence=confidence,
        ))
        return RoutingDecision(
            request_id=decision.request_id,
            baseline=decision.baseline,
            selected=decision.selected,
            candidate_pool_size=decision.candidate_pool_size,
            latency_ms=latency,
            reason_codes=decision.reason_codes,
            confidence=decision.confidence,
            metadata=decision.metadata,
        )


class CombinedBaseline:
    baseline_id = "D-rules+embeddings"

    def __init__(self) -> None:
        self.rules = RulesBaseline()
        self.embed = EmbeddingsBaseline()

    def route(self, query: str, *, top_k: int = 10, candidate_tools: list[str] | None = None) -> RoutingDecision:
        a = self.rules.route(query, top_k=top_k * 2, candidate_tools=candidate_tools)
        b = self.embed.route(query, top_k=top_k * 2, candidate_tools=candidate_tools)
        combined_scores: dict[str, float] = {}
        for i, t in enumerate(a.selected):
            combined_scores[t] = combined_scores.get(t, 0.0) + 1.0 - i * 0.01
        for i, t in enumerate(b.selected):
            combined_scores[t] = combined_scores.get(t, 0.0) + (b.confidence if b.confidence else 0.5) - i * 0.005
        ordered = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [n for n, _ in ordered[:top_k]]
        a_meta = {t: (1.0 - i * 0.01) for i, t in enumerate(a.selected)}
        b_meta = {t: (b.confidence or 0.0) for i, t in enumerate(b.selected)}
        decision, latency = _timer(lambda: RoutingDecision(
            request_id=f"D-{abs(hash(query)) % 10**9}",
            baseline=self.baseline_id,
            selected=tuple(selected),
            candidate_pool_size=a.candidate_pool_size,
            latency_ms=0.0,
            reason_codes=("rules_combined", "embeddings_combined"),
            confidence=min(1.0, sum(a_meta.values()) * 0.5 + sum(b_meta.values()) * 0.5),
        ))
        return RoutingDecision(
            request_id=decision.request_id,
            baseline=decision.baseline,
            selected=decision.selected,
            candidate_pool_size=decision.candidate_pool_size,
            latency_ms=max(a.latency_ms, b.latency_ms) + 0.5,
            reason_codes=decision.reason_codes,
            confidence=decision.confidence,
            metadata=decision.metadata,
        )


def get_baseline(identifier: str, intent_registry_getter=None) -> RouterLike:
    if identifier in ("B", "B-rules", "rules"):
        return RulesBaseline(intent_registry_getter=intent_registry_getter)
    if identifier in ("C", "C-embeddings", "embeddings"):
        return EmbeddingsBaseline()
    if identifier in ("D", "D-rules+embeddings", "rules+embeddings"):
        return CombinedBaseline()
    raise NotImplementedError(f"Baseline {identifier} not implemented in Phase 5; populated by Phase 6+")
