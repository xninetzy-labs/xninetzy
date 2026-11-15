"""Optional CPU FAISS projection with atomic, bounded two-slot snapshots.

Legacy graph.index/graph_map.json files are preserved, never silently rebuilt.
New writes publish a complete checked slot through one atomic pointer. SQLite
is canonical; an unavailable/corrupt projection yields no semantic evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging
from xninetzy.os.knowledge import embeddings
from xninetzy.os.knowledge.embeddings import embed_query, embed_texts, embedding_dim

logger = logging.getLogger(__name__)
_graph_index = None
_graph_id_map: list[str] = []
_graph_hashes: list[str] = []
_graph_signature: dict | None = None
_cache_token = None
_lock = threading.RLock()


class GraphVectorError(RuntimeError):
    """Safe operational code, without provider messages or private text."""


def _root() -> Path:
    path = Path(get_settings().GRAPH_VECTOR_DATA_DIR).expanduser().absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise GraphVectorError("graph_vector_symlink")
    return path.resolve()


def _index_path() -> Path:
    return _root() / "graph.index"


def _map_path() -> Path:
    return _root() / "graph_map.json"


def _signature() -> dict:
    settings = get_settings()
    dimension = embedding_dim()
    actual = embeddings._PROVIDER
    if actual != settings.EMBEDDING_PROVIDER:
        raise GraphVectorError("graph_vector_embedding_provider_unavailable")
    return {"provider": actual, "model": settings.EMBEDDING_MODEL if actual == "sentence_transformers" else "hash-bow-v1",
            "dimension": dimension, "normalize": bool(settings.EMBEDDING_NORMALIZE)}


def _read_json(path: Path, maximum: int = 65536):
    if path.is_symlink():
        raise GraphVectorError("graph_vector_symlink")
    with path.open("rb") as handle:
        raw = handle.read(maximum + 1)
    if len(raw) > maximum:
        raise GraphVectorError("graph_vector_metadata_limit")
    return json.loads(raw)


def _pointer(root: Path) -> dict | None:
    path = root / "graph.current.json"
    if not path.exists() and not path.is_symlink():
        return None
    value = _read_json(path)
    if (not isinstance(value, dict) or type(value.get("version")) is not int or value["version"] != 1 or value.get("slot") not in {"a", "b"}
            or not isinstance(value.get("generation"), str) or not isinstance(value.get("embedding"), dict)
            or type(value.get("count")) is not int or value["count"] < 0):
        raise GraphVectorError("graph_vector_manifest_invalid")
    files = value.get("files")
    if not isinstance(files, dict) or set(files) != {"index", "map"}:
        raise GraphVectorError("graph_vector_manifest_invalid")
    for metadata in files.values():
        if (not isinstance(metadata, dict) or not isinstance(metadata.get("sha256"), str)
                or len(metadata["sha256"]) != 64 or type(metadata.get("size")) is not int or metadata["size"] < 0):
            raise GraphVectorError("graph_vector_manifest_invalid")
    return value


def _slot(root: Path, slot: str, kind: str) -> Path:
    return root / (f"graph.{slot}.index" if kind == "index" else f"graph.{slot}.map.json")


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clear_cache() -> None:
    global _graph_index, _graph_id_map, _graph_hashes, _graph_signature, _cache_token
    _graph_index, _graph_id_map, _graph_hashes, _graph_signature, _cache_token = None, [], [], None, None


def _load_or_create_index():
    global _graph_index, _graph_id_map, _graph_hashes, _graph_signature, _cache_token
    try:
        import faiss
    except ImportError:
        return None
    root = _root()
    pointer = _pointer(root)
    if pointer is None:
        _clear_cache()
        if any(p.exists() or p.is_symlink() for p in (_index_path(), _map_path())):
            raise GraphVectorError("graph_vector_legacy_requires_reviewed_rebuild")
        return None
    signature = _signature()
    if pointer["embedding"] != signature:
        raise GraphVectorError("graph_vector_embedding_mismatch")
    paths = {kind: _slot(root, pointer["slot"], kind) for kind in ("index", "map")}
    for path in paths.values():
        if path.is_symlink() or not path.is_file():
            raise GraphVectorError("graph_vector_snapshot_missing")
    token = (str(root), pointer["generation"], *(item for p in paths.values() for item in (p.stat().st_mtime_ns, p.stat().st_size)))
    if _graph_index is not None and token == _cache_token:
        return _graph_index
    for kind, path in paths.items():
        if path.stat().st_size != pointer["files"][kind]["size"] or _hash(path) != pointer["files"][kind]["sha256"]:
            raise GraphVectorError("graph_vector_checksum_mismatch")
    rows = _read_json(paths["map"], maximum=64 * 1024 * 1024)
    if not isinstance(rows, list) or len(rows) != pointer["count"] or any(
        not isinstance(row, dict) or not isinstance(row.get("key"), str) or not isinstance(row.get("text_hash"), str)
        for row in rows
    ):
        raise GraphVectorError("graph_vector_map_invalid")
    index = faiss.read_index(str(paths["index"]))
    if not isinstance(index, faiss.IndexFlatIP) or index.d != signature["dimension"] or index.ntotal != len(rows):
        raise GraphVectorError("graph_vector_index_mismatch")
    if _pointer(root) != pointer:
        raise GraphVectorError("graph_vector_generation_changed")
    _graph_index, _graph_id_map = index, [row["key"] for row in rows]
    _graph_hashes, _graph_signature, _cache_token = [row["text_hash"] for row in rows], signature, token
    return index


def _sync_directory(root: Path) -> None:
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_json(path: Path, value) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _writer():
    with _lock:
        try:
            import fcntl
        except ImportError:
            raise GraphVectorError("graph_vector_requires_posix_lock") from None
        root = _root()
        root.mkdir(parents=True, mode=0o700, exist_ok=True)
        fd = os.open(root / ".graph-vector.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield root
        finally:
            os.close(fd)


def _publish(index, keys: list[str], hashes: list[str], signature: dict, *, rebuild: bool = False) -> None:
    import faiss
    root = _root()
    previous = None
    try:
        previous = _pointer(root)
    except Exception:
        if not rebuild:
            raise
        original = root / "graph.current.json"
        if original.is_symlink():
            raise GraphVectorError("graph_vector_symlink")
        if original.exists():
            backup = root / f"graph.current.invalid-{uuid4().hex}.json"
            fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle, original.open("rb") as source:
                shutil.copyfileobj(source, handle)
                handle.flush()
                os.fsync(handle.fileno())
    slot = "b" if previous and previous["slot"] == "a" else "a"
    target = _slot(root, slot, "index")
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        if target.is_symlink() or _slot(root, slot, "map").is_symlink():
            raise GraphVectorError("graph_vector_symlink")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        faiss.write_index(index, str(temporary))
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        _atomic_json(_slot(root, slot, "map"), [{"key": key, "text_hash": digest} for key, digest in zip(keys, hashes, strict=True)])
        metadata = {"version": 1, "slot": slot, "generation": uuid4().hex, "embedding": signature, "count": len(keys), "files": {}}
        for kind in ("index", "map"):
            path = _slot(root, slot, kind)
            metadata["files"][kind] = {"size": path.stat().st_size, "sha256": _hash(path)}
        _atomic_json(root / "graph.current.json", metadata)
    finally:
        temporary.unlink(missing_ok=True)
    _clear_cache()
    _load_or_create_index()


def _save_index() -> None:
    if _graph_index is not None and _graph_signature is not None:
        _publish(_graph_index, _graph_id_map, _graph_hashes, _graph_signature)


def _node_text(title: str, content: str | None) -> str:
    body = (content or "").strip()
    return f"{title}\n{body}".strip() if body else title


def node_text_hash(title: str, content: str | None) -> str:
    return hashlib.sha256(_node_text(title, content).encode()).hexdigest()


def _vectors(values, count: int, dimension: int):
    import numpy as np
    array = np.asarray(values, dtype=np.float32)
    if array.shape != (count, dimension) or not np.isfinite(array).all():
        raise GraphVectorError("graph_vector_embedding_invalid")
    return array


def upsert_node_vector(key: str, title: str, content: str | None) -> int | None:
    try:
        import faiss
    except ImportError:
        return None
    try:
        with _writer():
            index = _load_or_create_index()
            signature = _signature()
            text = _node_text(title, content)
            digest = node_text_hash(title, content)
            latest = {k: row for row, k in enumerate(_graph_id_map)}
            if key in latest and _graph_hashes[latest[key]] == digest:
                return latest[key]
            vectors = _vectors(embed_texts([text]), 1, signature["dimension"])
            candidate = faiss.clone_index(index) if index is not None else faiss.IndexFlatIP(signature["dimension"])
            row = candidate.ntotal
            candidate.add(vectors)
            _publish(candidate, [*_graph_id_map, key], [*_graph_hashes, digest], signature)
            return row
    except GraphVectorError:
        raise
    except Exception as error:
        raise GraphVectorError(f"graph_vector_write_failed:{type(error).__name__}") from None


def search(query: str, limit: int = 10) -> list[dict]:
    if limit <= 0:
        return []
    try:
        with _lock:
            index = _load_or_create_index()
            if index is None or index.ntotal == 0:
                return []
            vectors = _vectors([embed_query(query)], 1, index.d)
            latest = {key: row for row, key in enumerate(_graph_id_map)}
            count = min(index.ntotal, max(limit * 2, 16))
            while True:
                scores, indices = index.search(vectors, count)
                results = [{"key": _graph_id_map[row], "score": float(score), "text_hash": _graph_hashes[row]} for score, row in zip(scores[0], indices[0])
                           if row >= 0 and latest[_graph_id_map[row]] == row]
                if len(results) >= limit or count == index.ntotal:
                    return results[:limit]
                count = min(index.ntotal, count * 2)
    except Exception as error:
        logger.warning("Graph semantic retrieval unavailable (%s)", str(error) if isinstance(error, GraphVectorError) else type(error).__name__)
        return []


def rebuild_index() -> int:
    """Explicit operator-controlled rebuild; never called as read/error recovery."""
    try:
        import faiss
    except ImportError:
        return 0
    from xninetzy.os.graph.v3 import sqlite_store
    try:
        with _writer():
            nodes = sqlite_store.iter_active_nodes()
            signature = _signature()
            texts = [_node_text(node["title"], node.get("content")) for node in nodes]
            index = faiss.IndexFlatIP(signature["dimension"])
            if texts:
                index.add(_vectors(embed_texts(texts), len(texts), signature["dimension"]))
            _publish(index, [node["canonical_key"] for node in nodes], [hashlib.sha256(text.encode()).hexdigest() for text in texts], signature, rebuild=True)
            for row, node in enumerate(nodes):
                sqlite_store.set_faiss_row(node["canonical_key"], row, version=node["version"], content_hash=node["content_hash"])
            return len(nodes)
    except GraphVectorError:
        raise
    except Exception as error:
        raise GraphVectorError(f"graph_vector_rebuild_failed:{type(error).__name__}") from None
