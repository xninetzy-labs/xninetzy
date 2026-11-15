"""Canonical text must validate semantic candidates before they affect fusion."""
from __future__ import annotations

import hashlib

import pytest

from xninetzy.core.config import get_settings
from xninetzy.os.graph.v3 import hybrid_retriever as retriever


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv("GRAPHRAG_V3_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_stale_vector_cannot_suppress_fresh_lexical_evidence(monkeypatch):
    node = {"canonical_key": "current", "node_type": "topic", "title": "current title", "content": "updated evidence"}
    monkeypatch.setattr(retriever.sqlite_store, "fts_search_nodes", lambda *a, **kw: [node])
    monkeypatch.setattr(retriever.sqlite_store, "get_nodes", lambda keys: {"current": node})
    monkeypatch.setattr(retriever.sqlite_store, "edges_for_keys", lambda keys: [])
    monkeypatch.setattr(retriever.faiss_store, "search", lambda *a, **kw: [
        {"key": "current", "score": 0.01, "text_hash": hashlib.sha256(b"old title").hexdigest()},
    ])
    pack = retriever.retrieve("updated", expand_depth=0)
    assert [n.key for n in pack.nodes] == ["current"]
    assert pack.nodes[0].via == ["fts"]


@pytest.mark.parametrize("stale", [True, False])
def test_semantic_seed_requires_current_canonical_text(monkeypatch, stale):
    node = {"canonical_key": "current", "node_type": "topic", "title": "stable", "content": "evidence"}
    digest = hashlib.sha256(b"stable\nevidence").hexdigest()
    monkeypatch.setattr(retriever.sqlite_store, "fts_search_nodes", lambda *a, **kw: [])
    monkeypatch.setattr(retriever.sqlite_store, "get_nodes", lambda keys: {"current": node})
    monkeypatch.setattr(retriever.sqlite_store, "edges_for_keys", lambda keys: [])
    monkeypatch.setattr(retriever.faiss_store, "search", lambda *a, **kw: [
        {"key": "current", "score": 0.99, "text_hash": "outdated" if stale else digest},
    ])
    pack = retriever.retrieve("meaning", expand_depth=0)
    assert [n.key for n in pack.nodes] == ([] if stale else ["current"])
