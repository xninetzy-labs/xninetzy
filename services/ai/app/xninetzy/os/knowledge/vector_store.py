from __future__ import annotations

import json
from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect, init_db
from app.xninetzy.os.knowledge.embeddings import embed_query, embed_texts, embedding_dim

logger = logging.getLogger(__name__)

_faiss_index = None
_faiss_id_map: list[int] = []  # faiss_row → chunk.id in SQLite


def _index_path() -> Path:
    p = Path(get_settings().VECTOR_DATA_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p / "faiss.index"


def _map_path() -> Path:
    return _index_path().parent / "faiss_map.json"


def _load_or_create_index():
    global _faiss_index, _faiss_id_map
    if _faiss_index is not None:
        return _faiss_index

    try:
        import faiss
    except ImportError:
        logger.warning("faiss not available — knowledge search will use FTS5 only")
        return None

    idx_path = _index_path()
    map_path = _map_path()

    if idx_path.exists() and map_path.exists():
        try:
            _faiss_index = faiss.read_index(str(idx_path))
            _faiss_id_map = json.loads(map_path.read_text())
            if not isinstance(_faiss_id_map, list) or _faiss_index.ntotal != len(
                _faiss_id_map
            ):
                logger.warning(
                    "FAISS invariant failed (vectors=%d, map=%d) — rebuilding",
                    _faiss_index.ntotal,
                    len(_faiss_id_map) if isinstance(_faiss_id_map, list) else -1,
                )
                rebuild_index()
                return _faiss_index
            logger.info("FAISS index loaded: %d vectors", _faiss_index.ntotal)
            return _faiss_index
        except Exception as e:
            logger.warning("Failed to load FAISS index: %s — creating new", e)

    dim = embedding_dim()
    _faiss_index = faiss.IndexFlatIP(
        dim
    )  # Inner product (cosine for normalized vectors)
    _faiss_id_map = []
    logger.info("Created new FAISS index, dim=%d", dim)
    return _faiss_index


def _save_index() -> None:
    global _faiss_index, _faiss_id_map
    if _faiss_index is None:
        return
    try:
        import faiss

        faiss.write_index(_faiss_index, str(_index_path()))
        _map_path().write_text(json.dumps(_faiss_id_map))
    except Exception as e:
        logger.warning("Failed to save FAISS index: %s", e)


def add_chunks_to_index(source_id: int, chunks: list[str]) -> list[int]:
    """Embed chunks, store in SQLite + FAISS. Returns list of chunk IDs."""
    init_db()
    if not chunks:
        return []

    idx = _load_or_create_index()
    embeddings = embed_texts(chunks)
    chunk_ids: list[int] = []
    now = __import__("datetime").datetime.now().isoformat()
    first_faiss_row = idx.ntotal if idx is not None else None

    with connect() as conn:
        for i, text in enumerate(chunks):
            token_count = len(text.split())
            faiss_row = first_faiss_row + i if first_faiss_row is not None else None

            cur = conn.execute(
                """
                INSERT INTO knowledge_chunks
                  (source_id, chunk_index, text, token_count, faiss_id, metadata_json, created_at)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    source_id,
                    i,
                    text,
                    token_count,
                    faiss_row,
                    json.dumps({"source_id": source_id}),
                    now,
                ),
            )
            chunk_id = cur.lastrowid
            chunk_ids.append(chunk_id)

            # Update FTS
            conn.execute(
                "INSERT INTO knowledge_fts(chunk_id, text) VALUES (?,?)",
                (chunk_id, text),
            )

    # Batch add to FAISS
    if idx is not None:
        try:
            import numpy as np

            vecs = np.array(embeddings, dtype=np.float32)
            idx.add(vecs)
            _faiss_id_map.extend(chunk_ids)
            _save_index()
        except Exception as e:
            logger.warning("FAISS add/save failed: %s — rebuilding index", e)
            rebuild_index()

    return chunk_ids


def semantic_search(query: str, limit: int = 5) -> list[dict]:
    """Hybrid FAISS + FTS5 search fused with reciprocal-rank scoring."""
    idx = _load_or_create_index()
    candidate_limit = max(limit * 3, limit)
    if idx is not None and idx.ntotal > 0:
        semantic_results = _faiss_search(query, candidate_limit)
    else:
        semantic_results = []
    keyword_results = _fts_search(query, candidate_limit)
    return _rrf_fuse_results(semantic_results, keyword_results, limit)


def _result_key(result: dict) -> tuple[object, str]:
    chunk_id = result.get("id")
    if chunk_id is not None:
        return ("chunk", str(chunk_id))
    normalized = " ".join(str(result.get("text") or "").split()).casefold()
    return (result.get("source_id"), normalized)


def _rrf_fuse_results(
    semantic_results: list[dict], keyword_results: list[dict], limit: int
) -> list[dict]:
    if not semantic_results:
        return _deduplicate_results(keyword_results, limit)
    if not keyword_results:
        return _deduplicate_results(semantic_results, limit)

    fused: dict[tuple[object, str], dict] = {}
    scores: dict[tuple[object, str], float] = {}
    channels: dict[tuple[object, str], set[str]] = {}
    for channel, results in (
        ("semantic", semantic_results),
        ("keyword", keyword_results),
    ):
        for rank, result in enumerate(results, 1):
            key = _result_key(result)
            fused.setdefault(key, dict(result))
            scores[key] = scores.get(key, 0.0) + 1.0 / (60 + rank)
            channels.setdefault(key, set()).add(channel)

    ordered = sorted(fused, key=lambda key: scores[key], reverse=True)
    output: list[dict] = []
    for key in ordered[:limit]:
        output.append(
            {
                **fused[key],
                "score": scores[key],
                "retrieval_channels": sorted(channels[key]),
            }
        )
    return output


def _deduplicate_results(results: list[dict], limit: int) -> list[dict]:
    unique: list[dict] = []
    seen: set[tuple[object, str]] = set()
    for result in results:
        normalized = " ".join(str(result.get("text") or "").split()).casefold()
        key = (result.get("source_id"), normalized)
        if key in seen:
            continue
        seen.add(key)
        unique.append(result)
        if len(unique) >= limit:
            break
    return unique


def _faiss_search(query: str, limit: int) -> list[dict]:
    global _faiss_id_map
    try:
        import numpy as np

        idx = _load_or_create_index()
        if idx is None or idx.ntotal == 0:
            return _fts_search(query, limit)

        qvec = np.array([embed_query(query)], dtype=np.float32)
        scores, indices = idx.search(qvec, min(limit, idx.ntotal))

        results = []
        init_db()
        with connect() as conn:
            for score, faiss_row in zip(scores[0], indices[0]):
                if faiss_row < 0 or faiss_row >= len(_faiss_id_map):
                    continue
                chunk_id = _faiss_id_map[faiss_row]
                row = conn.execute(
                    """
                    SELECT kc.*, ks.title, ks.source_type, ks.uri
                    FROM knowledge_chunks kc
                    JOIN knowledge_sources ks ON ks.id = kc.source_id
                    WHERE kc.id=?
                    """,
                    (chunk_id,),
                ).fetchone()
                if row:
                    results.append({**dict(row), "score": float(score)})
        return results
    except Exception as e:
        logger.warning("FAISS search error: %s — falling back to FTS5", e)
        return _fts_search(query, limit)


def _fts_search(query: str, limit: int) -> list[dict]:
    init_db()
    try:
        with connect() as conn:
            rows = conn.execute(
                """
                SELECT kc.*, ks.title, ks.source_type, ks.uri, bm25(knowledge_fts) as score
                FROM knowledge_fts
                JOIN knowledge_chunks kc ON kc.id = knowledge_fts.chunk_id
                JOIN knowledge_sources ks ON ks.id = kc.source_id
                WHERE knowledge_fts MATCH ?
                ORDER BY score LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning("FTS5 search error: %s", e)
        return []


def rebuild_index() -> int:
    """Rebuild FAISS index from all stored chunks."""
    global _faiss_index, _faiss_id_map
    init_db()
    try:
        import faiss
        import numpy as np
    except ImportError:
        return 0

    with connect() as conn:
        chunks = conn.execute(
            "SELECT id, text FROM knowledge_chunks ORDER BY id"
        ).fetchall()

    if not chunks:
        dim = embedding_dim()
        _faiss_index = faiss.IndexFlatIP(dim)
        _faiss_id_map = []
        _save_index()
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    chunk_ids = [c["id"] for c in chunks]

    dim = embedding_dim()
    _faiss_index = faiss.IndexFlatIP(dim)
    vecs = np.array(embeddings, dtype=np.float32)
    _faiss_index.add(vecs)
    _faiss_id_map = chunk_ids

    _save_index()
    # Update faiss_id in SQLite
    with connect() as conn:
        for faiss_row, chunk_id in enumerate(chunk_ids):
            conn.execute(
                "UPDATE knowledge_chunks SET faiss_id=? WHERE id=?",
                (faiss_row, chunk_id),
            )

    logger.info("FAISS index rebuilt: %d vectors", _faiss_index.ntotal)
    return _faiss_index.ntotal
