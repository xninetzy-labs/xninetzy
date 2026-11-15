"""Real optional FAISS CPU tests, with explicit deterministic hash embeddings.

Run in the embeddings/all-extras development profile. These do not establish
neural-model retrieval quality, and never download a model.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import faiss
import numpy as np
import pytest

from xninetzy.core.config import get_settings
from xninetzy.os.graph.v3 import faiss_store as store
from xninetzy.os.knowledge import embeddings


@pytest.fixture(autouse=True)
def isolated_vectors(monkeypatch, tmp_path):
    monkeypatch.setenv("GRAPH_VECTOR_DATA_DIR", str(tmp_path / "vectors"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setattr(embeddings, "_model", None)
    monkeypatch.setattr(embeddings, "_PROVIDER", None)
    monkeypatch.setattr(embeddings, "_MODEL_CONFIG", None, raising=False)
    monkeypatch.setattr(store, "_graph_index", None)
    monkeypatch.setattr(store, "_graph_id_map", [])
    for name, value in (("_cache_token", None), ("_graph_hashes", []), ("_graph_signature", None)):
        monkeypatch.setattr(store, name, value, raising=False)
    get_settings.cache_clear()
    yield tmp_path / "vectors"
    get_settings.cache_clear()


def test_same_payload_replay_does_not_append_another_vector():
    first = store.upsert_node_vector("fixture-a", "alpha", "stable")
    second = store.upsert_node_vector("fixture-a", "alpha", "stable")
    assert first == second == 0
    assert store._graph_index.ntotal == 1


def test_replay_after_cache_restart_retains_the_existing_row():
    assert store.upsert_node_vector("fixture-a", "alpha", "stable") == 0
    store._graph_index = None
    store._graph_id_map = []
    assert store.upsert_node_vector("fixture-a", "alpha", "stable") == 0
    assert store._graph_index.ntotal == 1


def test_failed_save_is_not_acknowledged_and_keeps_committed_snapshot(monkeypatch):
    store.upsert_node_vector("fixture-a", "alpha", "original")

    def failure(*args, **kwargs):
        raise OSError("synthetic-private-save-error")

    monkeypatch.setattr(faiss, "write_index", failure)
    with pytest.raises(RuntimeError):
        store.upsert_node_vector("fixture-b", "beta", "new")
    assert store._graph_index.ntotal == 1
    assert [row["key"] for row in store.search("alpha")] == ["fixture-a"]


def test_corrupt_legacy_pair_is_preserved_without_automatic_rebuild(isolated_vectors, monkeypatch):
    root = isolated_vectors
    root.mkdir()
    index = faiss.IndexFlatIP(256)
    index.add(np.ones((1, 256), dtype="float32"))
    faiss.write_index(index, str(root / "graph.index"))
    (root / "graph_map.json").write_text(json.dumps(["a", "b"]))
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    rebuilds = []
    monkeypatch.setattr(store, "rebuild_index", lambda: rebuilds.append(True))
    assert store.search("alpha") == []
    assert rebuilds == []
    assert {p.name: p.read_bytes() for p in root.iterdir()} == before


def test_vector_cache_is_scoped_to_the_selected_directory(isolated_vectors, monkeypatch):
    store.upsert_node_vector("fixture-a", "alpha", "old directory")
    monkeypatch.setenv("GRAPH_VECTOR_DATA_DIR", str(isolated_vectors.parent / "other"))
    get_settings.cache_clear()
    assert store.search("alpha") == []


@pytest.mark.parametrize("vector", [[float("nan")] * 256, [1.0, 2.0]])
def test_invalid_embedding_does_not_publish_or_destroy_previous_vectors(monkeypatch, vector):
    store.upsert_node_vector("fixture-a", "alpha", "original")
    monkeypatch.setattr(store, "embed_texts", lambda texts: [vector])
    with pytest.raises(RuntimeError):
        store.upsert_node_vector("fixture-b", "beta", "invalid")
    assert store._graph_index.ntotal == 1


def test_read_of_missing_index_does_not_create_directories(isolated_vectors):
    assert store.search("unknown") == []
    assert not isolated_vectors.exists()


def test_reader_rejects_generation_changed_while_loading(monkeypatch, isolated_vectors):
    store.upsert_node_vector("fixture-a", "alpha", "committed")
    store._clear_cache()
    original = faiss.read_index

    def changed_generation(path):
        result = original(path)
        pointer = isolated_vectors / "graph.current.json"
        metadata = json.loads(pointer.read_text())
        metadata["generation"] = "another-writer-committed"
        pointer.write_text(json.dumps(metadata))
        return result

    monkeypatch.setattr(faiss, "read_index", changed_generation)
    assert store.search("alpha") == []


def test_old_embedding_cannot_outrank_the_latest_content_for_same_key():
    store.upsert_node_vector("fixture-a", "alpha", None)
    store.upsert_node_vector("fixture-a", "beta", None)
    results = store.search("alpha")
    assert results[0]["key"] == "fixture-a"
    assert results[0]["score"] < 0.01


def test_parallel_same_payload_replay_has_one_durable_row():
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda _: store.upsert_node_vector("fixture-a", "alpha", "same"), range(4)))
    assert rows == [0] * 4
    store._graph_index = None
    assert store._load_or_create_index().ntotal == 1


@pytest.mark.parametrize("stage", ["map", "pointer", "after_pointer"])
def test_publication_failure_retains_a_valid_commit_and_safe_replay(monkeypatch, isolated_vectors, stage):
    store.upsert_node_vector("fixture-a", "alpha", "original")
    replace = os.replace

    def fail(source, target):
        selected = (stage == "map" and str(target).endswith(".map.json")) or (stage != "map" and str(target).endswith("graph.current.json"))
        if selected and stage != "after_pointer":
            raise OSError("synthetic publication failure")
        replace(source, target)
        if selected:
            raise OSError("synthetic ambiguous commit")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(RuntimeError):
        store.upsert_node_vector("fixture-b", "beta", "candidate")
    monkeypatch.setattr(os, "replace", replace)
    assert store.upsert_node_vector("fixture-b", "beta", "candidate") == 1
    store._graph_index = None
    assert store._load_or_create_index().ntotal == 2
    assert json.loads((isolated_vectors / "graph.current.json").read_text())["count"] == 2


@pytest.mark.parametrize("target", ["pointer", "index", "map"])
def test_committed_corruption_is_held_without_repair_or_new_writes(isolated_vectors, target):
    store.upsert_node_vector("fixture-a", "alpha", "original")
    metadata = json.loads((isolated_vectors / "graph.current.json").read_text())
    path = isolated_vectors / ({"pointer": "graph.current.json", "index": f"graph.{metadata['slot']}.index", "map": f"graph.{metadata['slot']}.map.json"}[target])
    path.write_bytes(b"invalid synthetic snapshot")
    before = {p.name: p.read_bytes() for p in isolated_vectors.iterdir()}
    assert store.search("alpha") == []
    with pytest.raises(RuntimeError):
        store.upsert_node_vector("fixture-b", "beta", "held")
    assert {p.name: p.read_bytes() for p in isolated_vectors.iterdir()} == before


def test_changed_embedding_dimension_does_not_overwrite_snapshot(monkeypatch, isolated_vectors):
    store.upsert_node_vector("fixture-a", "alpha", "original")
    before = (isolated_vectors / "graph.current.json").read_bytes()
    monkeypatch.setattr(store, "embedding_dim", lambda: 128)
    assert store.search("alpha") == []
    with pytest.raises(RuntimeError, match="embedding_mismatch"):
        store.upsert_node_vector("fixture-a", "alpha", "new")
    assert (isolated_vectors / "graph.current.json").read_bytes() == before


def test_snapshot_storage_has_two_bounded_data_slots(isolated_vectors):
    for version in range(8):
        store.upsert_node_vector("fixture-a", "alpha", str(version))
    assert len(list(isolated_vectors.glob("graph.*.index"))) == 2
    assert len(list(isolated_vectors.glob("graph.*.map.json"))) == 2
    assert not list(isolated_vectors.glob(".*.tmp"))
    assert all(path.stat().st_mode & 0o077 == 0 for path in isolated_vectors.iterdir())


def test_snapshot_write_does_not_follow_an_inactive_slot_symlink(isolated_vectors):
    store.upsert_node_vector("fixture-a", "alpha", None)
    target = isolated_vectors.parent / "unrelated"
    target.write_text("keep")
    (isolated_vectors / "graph.b.index").symlink_to(target)
    with pytest.raises(RuntimeError, match="symlink"):
        store.upsert_node_vector("fixture-b", "beta", None)
    assert target.read_text() == "keep"


def test_concurrent_processes_and_restart_reuse_one_durable_vector(isolated_vectors):
    program = "from xninetzy.os.graph.v3.faiss_store import upsert_node_vector; print(upsert_node_vector('fixture-a','alpha','same'))"
    processes = [subprocess.Popen([sys.executable, "-c", program], cwd=isolated_vectors.parent, env=dict(os.environ), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    try:
        outputs = [process.communicate(timeout=15) for process in processes]
        assert all(process.returncode == 0 for process in processes), outputs
        assert [output[0].strip() for output in outputs] == ["0", "0"]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
    assert store._load_or_create_index().ntotal == 1
    assert store.upsert_node_vector("fixture-a", "alpha", "same") == 0
