from __future__ import annotations

from app.xninetzy.os.knowledge.vector_store import semantic_search


def quick_search(query: str, limit: int = 5) -> list[dict]:
    """Return knowledge sources (not chunks) matching query."""
    chunks = semantic_search(query, limit=limit)
    seen: dict[int, dict] = {}
    for c in chunks:
        sid = c.get("source_id", 0)
        if sid not in seen:
            seen[sid] = {"source_id": sid, "title": c.get("title", "?"),
                         "source_type": c.get("source_type", "?"), "score": c.get("score", 0)}
    return list(seen.values())


def build_rag_context(query: str, top_k: int | None = None) -> str:
    """Build a RAG context string from top matching chunks."""
    from app.xninetzy.core.config import get_settings
    k = top_k or get_settings().RAG_TOP_K
    chunks = semantic_search(query, limit=k)
    if not chunks:
        return ""

    parts: list[str] = ["[Konteks dari knowledge base:]\n"]
    for i, c in enumerate(chunks, 1):
        title = c.get("title", "?")
        text = c.get("text", "")[:600]
        score = c.get("score", 0)
        parts.append(f"[{i}] Sumber: {title} (relevance: {score:.2f})\n{text}\n")

    return "\n".join(parts)
