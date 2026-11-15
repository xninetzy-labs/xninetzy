from __future__ import annotations

from unittest.mock import patch

from xninetzy.context.routing.embeddings_warmup import warm_faiss_index
from xninetzy.context.routing.warmup import warm_once, warmup_routing_stack


def test_warmup_routing_stack_returns_summary() -> None:
    summary = warmup_routing_stack(queries=("submit HEBAT", "find papers"))
    assert "version" in summary
    assert "faiss_loaded" in summary
    assert "n_warmup_queries" in summary
    assert summary["n_warmup_queries"] == 2


def test_warm_once_is_idempotent() -> None:
    a = warm_once(queries=("warm a",))
    b = warm_once(queries=("warm a",))
    assert a.get("already_warm") is True or b.get("already_warm") is True
    assert b["already_warm"] is True


def test_warm_faiss_index_handles_unavailable() -> None:
    from xninetzy.context.routing import embeddings_warmup

    embeddings_warmup._warm_cache["warmed"] = False
    with patch.object(embeddings_warmup, "_load_or_create_index", side_effect=Exception("nope")):
        ok, latency = warm_faiss_index(queries=("submit HEBAT",))
    assert ok is False
    assert latency >= 0.0
