"""FAISS semantic index for GraphRAG V3 nodes — a rebuildable projection.

Mirrors the knowledge ``vector_store`` (IndexFlatIP + JSON row→id map, cosine
via normalized embeddings) but keeps its own files under
``GRAPH_VECTOR_DATA_DIR`` so the graph and knowledge indexes never collide.

The map stores ``faiss_row → node canonical_key`` (a string). Re-embedding a
changed node appends a fresh vector and repoints the node's ``faiss_row``; the
old row is left as a harmless stale duplicate that resolves to the same (now
updated) node and is compacted away on the next ``rebuild_index``. Retrieval
dedups by key, so duplicates never surface twice.

Only node IDs + the embedding live here — no raw content, per the V3 contract.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.knowledge.embeddings import embed_query, embed_texts, embedding_dim

logger = logging.getLogger(__name__)

_graph_index = None
_graph_id_map: list[str] = []  # faiss_row → node canonical_key


def _index_path() -> Path:
    p = Path(get_settings().GRAPH_VECTOR_DATA_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p / "graph.index"


def _map_path() -> Path:
    return _index_path().parent / "graph_map.json"


def _load_or_create_index():
    global _graph_index, _graph_id_map
    if _graph_index is not None:
        return _graph_index

    try:
        import faiss
    except ImportError:
        logger.warning("faiss not available — graph semantic search disabled")
        return None

    idx_path = _index_path()
    map_path = _map_path()

    if idx_path.exists() and map_path.exists():
        try:
            _graph_index = faiss.read_index(str(idx_path))
            _graph_id_map = json.loads(map_path.read_text())
            if not isinstance(_graph_id_map, list) or _graph_index.ntotal != len(
                _graph_id_map
            ):
                logger.warning(
                    "Graph FAISS invariant failed (vectors=%d, map=%d) — rebuilding",
                    _graph_index.ntotal,
                    len(_graph_id_map) if isinstance(_graph_id_map, list) else -1,
                )
                rebuild_index()
                return _graph_index
            logger.info("Graph FAISS index loaded: %d vectors", _graph_index.ntotal)
            return _graph_index
        except Exception as e:
            logger.warning("Failed to load graph FAISS index: %s — creating new", e)

    dim = embedding_dim()
    _graph_index = faiss.IndexFlatIP(dim)
    _graph_id_map = []
    logger.info("Created new graph FAISS index, dim=%d", dim)
    return _graph_index


def _save_index() -> None:
    global _graph_index, _graph_id_map
    if _graph_index is None:
        return
    try:
        import faiss

        faiss.write_index(_graph_index, str(_index_path()))
        _map_path().write_text(json.dumps(_graph_id_map))
    except Exception as e:
        logger.warning("Failed to save graph FAISS index: %s", e)


def _node_text(title: str, content: str | None) -> str:
    body = (content or "").strip()
    return f"{title}\n{body}".strip() if body else title


def upsert_node_vector(key: str, title: str, content: str | None) -> int | None:
    """Embed a node and append it. Returns the new faiss_row, or None if FAISS
    is unavailable. Idempotency lives in the caller (content_hash gating); this
    always appends when called."""
    idx = _load_or_create_index()
    if idx is None:
        return None
    try:
        import numpy as np

        vec = embed_texts([_node_text(title, content)])
        row = idx.ntotal
        idx.add(np.array(vec, dtype=np.float32))
        _graph_id_map.append(key)
        _save_index()
        return row
    except Exception as e:
        logger.warning("Graph FAISS upsert failed: %s — rebuilding", e)
        rebuild_index()
        # After rebuild the node's row is recomputed; look it up.
        try:
            return _graph_id_map.index(key)
        except ValueError:
            return None


def search(query: str, limit: int = 10) -> list[dict]:
    """Semantic leg of hybrid retrieval. Returns [{key, score}] best-first,
    deduped by key (keeping the highest score)."""
    idx = _load_or_create_index()
    if idx is None or idx.ntotal == 0:
        return []
    try:
        import numpy as np

        qvec = np.array([embed_query(query)], dtype=np.float32)
        scores, indices = idx.search(qvec, min(limit * 2, idx.ntotal))
        best: dict[str, float] = {}
        for score, row in zip(scores[0], indices[0]):
            if row < 0 or row >= len(_graph_id_map):
                continue
            key = _graph_id_map[row]
            if key not in best or float(score) > best[key]:
                best[key] = float(score)
        ranked = sorted(best.items(), key=lambda kv: kv[1], reverse=True)
        return [{"key": k, "score": s} for k, s in ranked[:limit]]
    except Exception as e:
        logger.warning("Graph FAISS search error: %s", e)
        return []


def rebuild_index() -> int:
    """Rebuild the whole graph index from active canonical nodes and repoint
    every node's ``faiss_row``. Safe to call anytime; used by HITL rebuild."""
    global _graph_index, _graph_id_map
    # Imported lazily to avoid a circular import at module load.
    from app.xninetzy.os.graph.v3 import sqlite_store

    try:
        import faiss
        import numpy as np
    except ImportError:
        return 0

    nodes = sqlite_store.iter_active_nodes()
    dim = embedding_dim()
    _graph_index = faiss.IndexFlatIP(dim)
    _graph_id_map = []

    if not nodes:
        _save_index()
        return 0

    texts = [_node_text(n["title"], n.get("content")) for n in nodes]
    keys = [n["canonical_key"] for n in nodes]
    vecs = np.array(embed_texts(texts), dtype=np.float32)
    _graph_index.add(vecs)
    _graph_id_map = keys
    _save_index()

    for row, key in enumerate(keys):
        sqlite_store.set_faiss_row(key, row)

    logger.info("Graph FAISS index rebuilt: %d vectors", _graph_index.ntotal)
    return _graph_index.ntotal
