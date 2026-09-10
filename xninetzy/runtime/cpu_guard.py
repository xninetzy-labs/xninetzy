"""CPU-only runtime guard.

Xninetzy runs all AI inference on CPU exclusively. This module verifies that
invariant at startup and refuses to boot a GPU-tainted build: it checks the
configured device, scans installed distributions for forbidden GPU packages
(triton, nvidia-*, faiss-gpu, …), and confirms the installed PyTorch is a CPU
wheel (``torch.version.cuda is None`` and CUDA unavailable).

The guard is intentionally strict — a CUDA wheel that slipped back into the
lock would balloon the image and quietly pull the whole CUDA stack, so we fail
loud rather than degrade. It never imports the embedding model, so it is cheap.
"""

from __future__ import annotations

import importlib.metadata
import os

FORBIDDEN_DISTRIBUTION_PREFIXES = ("nvidia-",)

FORBIDDEN_DISTRIBUTIONS = {
    "triton",
    "faiss-gpu",
    "onnxruntime-gpu",
    "bitsandbytes",
    "flash-attn",
    "xformers",
}


def installed_distributions() -> set[str]:
    """Case-folded set of installed distribution names."""
    names: set[str] = set()
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            names.add(name.strip().casefold())
    return names


def _forbidden_present(installed: set[str]) -> list[str]:
    return sorted(
        name
        for name in installed
        if name in FORBIDDEN_DISTRIBUTIONS
        or any(name.startswith(prefix) for prefix in FORBIDDEN_DISTRIBUTION_PREFIXES)
    )


def validate_cpu_only_runtime() -> dict[str, object]:
    """Assert the process is a pure CPU runtime. Raises RuntimeError otherwise.

    Returns a non-secret dict of runtime facts on success (used for logging and
    the health endpoint).
    """
    configured_device = os.getenv("XNINETZY_DEVICE", "cpu").strip().casefold()
    embedding_device = os.getenv("EMBEDDING_DEVICE", "cpu").strip().casefold()

    if configured_device != "cpu":
        raise RuntimeError(f"XNINETZY_DEVICE must be cpu (got {configured_device!r}).")
    if embedding_device != "cpu":
        raise RuntimeError(f"EMBEDDING_DEVICE must be cpu (got {embedding_device!r}).")

    installed = installed_distributions()
    forbidden = _forbidden_present(installed)
    if forbidden:
        raise RuntimeError(
            "GPU dependencies detected in CPU-only runtime: " + ", ".join(forbidden)
        )

    import torch

    if torch.version.cuda is not None:
        raise RuntimeError(
            f"CUDA-enabled PyTorch build detected: torch.version.cuda={torch.version.cuda}"
        )
    if torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is available although Xninetzy is configured as CPU-only."
        )

    return {
        "device": "cpu",
        "embedding_device": "cpu",
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_available": torch.cuda.is_available(),
        "torch_threads": torch.get_num_threads(),
        "forbidden_packages": forbidden,
    }
