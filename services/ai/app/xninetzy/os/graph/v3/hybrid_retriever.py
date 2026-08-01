"""Hybrid retrieval for GraphRAG V3 → a structured GraphContextPack.

Three retrieval legs, fused with Reciprocal Rank Fusion (RRF):
  1. SQLite FTS5 over node title+content (lexical).
  2. FAISS semantic search over node embeddings (dense).
  3. Neo4j neighborhood expansion from the fused seeds (structural).

RRF score for a node = Σ 1/(rrf_k + rank_in_leg). It needs no score
normalization across legs and is robust when a leg is empty (e.g. Neo4j down).
Structural expansion is a SEED, not evidence — expanded neighbors enter at a
discounted weight and never outrank a directly-retrieved node.

The result is a typed ``GraphContextPack`` (nodes + edges + provenance). A
markdown rendering is provided for the chat surface, but callers should prefer
the structured fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.graph.v3 import faiss_store, neo4j_store, sqlite_store


@dataclass
class GraphContextNode:
    key: str
    node_type: str
    title: str
    content: str | None
    score: float
    via: list[str] = field(default_factory=list)  # which legs surfaced it
    hops: int = 0  # 0 = directly retrieved, >0 = structural expansion


@dataclass
class GraphContextEdge:
    source_key: str
    target_key: str
    edge_type: str
    weight: float


@dataclass
class GraphContextPack:
    query: str
    nodes: list[GraphContextNode]
    edges: list[GraphContextEdge]

    def is_empty(self) -> bool:
        return not self.nodes

    def to_markdown(self) -> str:
        if not self.nodes:
            return "Belum ada konteks graph yang relevan."
        title_by_key = {n.key: n.title for n in self.nodes}
        lines = [f"*Graph context: {self.query}*"]
        for n in self.nodes:
            tag = "" if n.hops == 0 else f" _(+{n.hops} hop)_"
            lines.append(f"• [{n.node_type}] {n.title}{tag}")
        if self.edges:
            lines.append("")
            lines.append("*Relasi:*")
            for e in self.edges[:12]:
                s = title_by_key.get(e.source_key, e.source_key[:8])
                t = title_by_key.get(e.target_key, e.target_key[:8])
                lines.append(f"  - {s} —{e.edge_type}→ {t}")
        return "\n".join(lines)


def _rrf_accumulate(
    scores: dict[str, float], via: dict[str, set], ranked_keys: list[str],
    *, leg: str, rrf_k: int,
) -> None:
    for rank, key in enumerate(ranked_keys):
        scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
        via.setdefault(key, set()).add(leg)


def retrieve(query: str, *, top_k: int | None = None, expand_depth: int = 1) -> GraphContextPack:
    settings = get_settings()
    if not settings.GRAPHRAG_V3_ENABLED:
        return GraphContextPack(query=query, nodes=[], edges=[])

    rrf_k = settings.GRAPH_RRF_K
    limit = top_k or settings.GRAPH_RETRIEVAL_TOP_K
    over = max(limit * 3, 12)  # retrieve wide, fuse, then trim

    scores: dict[str, float] = {}
    via: dict[str, set] = {}

    # Leg 1 — lexical FTS
    fts_rows = sqlite_store.fts_search_nodes(query, limit=over)
    _rrf_accumulate(scores, via, [r["canonical_key"] for r in fts_rows],
                    leg="fts", rrf_k=rrf_k)

    # Leg 2 — semantic FAISS. Enforce the same cosine floor the knowledge
    # retriever uses (RAG_MIN_RELEVANCE): an off-domain query returns
    # low-similarity rows that RRF would otherwise happily seed graph context
    # from. Below the floor is noise, not evidence.
    min_relevance = settings.RAG_MIN_RELEVANCE
    raw_semantic = faiss_store.search(query, limit=over)
    semantic_active = bool(raw_semantic)  # dense index populated for this corpus
    faiss_rows = [
        r for r in raw_semantic if float(r.get("score") or 0.0) >= min_relevance
    ]
    backed_keys = {r["key"] for r in faiss_rows}
    _rrf_accumulate(scores, via, [r["key"] for r in faiss_rows],
                    leg="semantic", rrf_k=rrf_k)

    # When the dense index knows this corpus, a seed must have semantic backing
    # above the floor. Drop FTS-only seeds — a lexical match on a common word
    # across an unrelated topic is cross-document pollution, not relevance.
    if semantic_active:
        for key in list(scores):
            if key not in backed_keys:
                scores.pop(key, None)
                via.pop(key, None)

    if not scores:
        return GraphContextPack(query=query, nodes=[], edges=[])

    # Fuse and take the direct seeds.
    seeds = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    seed_keys = [k for k, _ in seeds]
    hops_by_key: dict[str, int] = {k: 0 for k in seed_keys}

    # Leg 3 — structural expansion (seeds only; discounted, never outranks).
    if expand_depth > 0:
        neighbors = neo4j_store.neighborhood(seed_keys, depth=expand_depth, limit=over)
        min_seed_score = seeds[-1][1] if seeds else 0.0
        for nb in neighbors:
            key = nb["key"]
            if key in hops_by_key:
                continue
            hops = int(nb.get("hops", 1) or 1)
            # Discount below the weakest direct seed so structure is a hint only.
            scores[key] = min_seed_score * (0.5 ** hops)
            via.setdefault(key, set()).add("structural")
            hops_by_key[key] = hops

    # Hydrate node bodies from canonical SQLite.
    all_keys = list(hops_by_key.keys())
    node_map = sqlite_store.get_nodes(all_keys)
    nodes: list[GraphContextNode] = []
    for key in all_keys:
        row = node_map.get(key)
        if row is None:
            continue
        nodes.append(
            GraphContextNode(
                key=key,
                node_type=row["node_type"],
                title=row["title"],
                content=row.get("content"),
                score=scores.get(key, 0.0),
                via=sorted(via.get(key, set())),
                hops=hops_by_key.get(key, 0),
            )
        )
    nodes.sort(key=lambda n: (n.hops, -n.score))

    # Edges strictly among the returned nodes (from canonical SQLite, so this
    # works even when Neo4j is down).
    present = {n.key for n in nodes}
    edges: list[GraphContextEdge] = []
    for e in sqlite_store.edges_for_keys(list(present)):
        if e["source_key"] in present and e["target_key"] in present:
            edges.append(
                GraphContextEdge(
                    source_key=e["source_key"],
                    target_key=e["target_key"],
                    edge_type=e["edge_type"],
                    weight=float(e["weight"]),
                )
            )

    return GraphContextPack(query=query, nodes=nodes, edges=edges)
