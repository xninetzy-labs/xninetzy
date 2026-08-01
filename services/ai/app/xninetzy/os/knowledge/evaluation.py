from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.xninetzy.os.knowledge.retrieval import EvidenceBundle, retrieve_evidence


@dataclass(frozen=True, slots=True)
class RetrievalEvalCase:
    query: str
    expected_source_ids: frozenset[int] = frozenset()
    expected_terms: frozenset[str] = frozenset()


def _case(value: RetrievalEvalCase | dict) -> RetrievalEvalCase:
    if isinstance(value, RetrievalEvalCase):
        return value
    return RetrievalEvalCase(
        query=str(value["query"]),
        expected_source_ids=frozenset(int(item) for item in value.get("expected_source_ids", [])),
        expected_terms=frozenset(str(item).casefold() for item in value.get("expected_terms", [])),
    )


def evaluate_retrieval(
    cases: list[RetrievalEvalCase | dict],
    *,
    limit: int = 5,
    retriever: Callable[[str, int], EvidenceBundle] = retrieve_evidence,
) -> dict:
    normalized = [_case(item) for item in cases]
    rows: list[dict] = []
    for item in normalized:
        bundle = retriever(item.query, limit)
        source_ids = {e.source_id for e in bundle.evidence}
        text = " ".join(e.text.casefold() for e in bundle.evidence)
        source_hit = bool(source_ids & item.expected_source_ids) if item.expected_source_ids else True
        term_hit = all(term in text for term in item.expected_terms)
        citation_ids = [e.citation for e in bundle.evidence]
        citations_valid = citation_ids == [f"K{index}" for index in range(1, len(citation_ids) + 1)]
        rows.append(
            {
                "query": item.query,
                "status": bundle.status,
                "confidence": bundle.confidence,
                "source_hit": source_hit,
                "term_hit": term_hit,
                "citations_valid": citations_valid,
                "evidence_count": len(bundle.evidence),
            }
        )
    total = len(rows)
    passed = sum(row["source_hit"] and row["term_hit"] and row["citations_valid"] for row in rows)
    sufficient = sum(row["status"] == "sufficient" for row in rows)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "recall_at_k": passed / total if total else 0.0,
        "sufficient_rate": sufficient / total if total else 0.0,
        "cases": rows,
    }
