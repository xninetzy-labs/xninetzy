from __future__ import annotations

from app.xninetzy.os.knowledge.vector_store import semantic_search


def quick_search(query: str, limit: int = 5) -> list[dict]:
    """Return knowledge sources (not chunks) matching query."""
    chunks = semantic_search(query, limit=limit)
    seen: dict[int, dict] = {}
    for c in chunks:
        sid = c.get("source_id", 0)
        if sid not in seen:
            seen[sid] = {
                "source_id": sid,
                "title": c.get("title", "?"),
                "source_type": c.get("source_type", "?"),
                "score": c.get("score", 0),
            }
    return list(seen.values())


def build_rag_context(query: str, top_k: int | None = None) -> str:
    """Backward-compatible evidence context; never returns unlabelled raw chunks."""
    from app.xninetzy.os.knowledge.retrieval import (
        render_evidence_bundle,
        retrieve_evidence,
    )

    bundle = retrieve_evidence(query, limit=top_k)
    return render_evidence_bundle(bundle) if bundle.evidence else ""
