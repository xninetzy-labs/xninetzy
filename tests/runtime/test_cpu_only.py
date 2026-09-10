"""CPU-only runtime guarantees.

These assert the invariant the whole migration exists to protect: PyTorch is a
CPU build, no GPU distributions are installed, and the runtime guard agrees.

The heavy real-model embedding check is marked ``integration`` (it may download
~90 MB) so the default unit run stays fast and offline; the guard/package
checks below need no model.
"""

from __future__ import annotations

import importlib.metadata

import pytest

import torch

from app.xninetzy.runtime.cpu_guard import validate_cpu_only_runtime


def _installed() -> set[str]:
    names: set[str] = set()
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            names.add(name.strip().casefold())
    return names


def test_torch_is_cpu_only() -> None:
    assert torch.version.cuda is None
    assert torch.cuda.is_available() is False


def test_forbidden_gpu_packages_are_absent() -> None:
    installed = _installed()

    for pkg in (
        "triton",
        "faiss-gpu",
        "onnxruntime-gpu",
        "bitsandbytes",
        "flash-attn",
        "xformers",
    ):
        assert pkg not in installed, f"{pkg} must not be installed in a CPU-only runtime"

    nvidia = sorted(p for p in installed if p.startswith("nvidia-"))
    assert nvidia == [], f"unexpected nvidia packages: {nvidia}"


def test_faiss_cpu_is_installed() -> None:
    installed = _installed()
    assert "faiss-cpu" in installed
    assert "faiss-gpu" not in installed


def test_cpu_runtime_guard() -> None:
    result = validate_cpu_only_runtime()

    assert result["device"] == "cpu"
    assert result["embedding_device"] == "cpu"
    assert result["torch_cuda_available"] is False
    assert result["torch_cuda_version"] is None
    assert result["forbidden_packages"] == []


def test_embeddings_runtime_info_reports_cpu() -> None:
    from app.xninetzy.os.knowledge import embeddings

    info = embeddings.runtime_info()
    assert info["device"] == "cpu"
    assert info["cuda_available"] is False
    assert info["torch_cuda_version"] is None


@pytest.mark.integration
def test_embed_texts_runs_on_cpu() -> None:
    from app.xninetzy.os.knowledge.embeddings import embed_texts

    vecs = embed_texts(
        [
            "GraphRAG uses graph structure.",
            "FAISS performs semantic retrieval.",
        ]
    )
    assert len(vecs) == 2
    assert all(isinstance(v, list) and v for v in vecs)
    # every embedding is the same fixed dimension
    assert len({len(v) for v in vecs}) == 1
