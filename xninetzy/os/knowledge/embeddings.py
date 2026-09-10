from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

_model = None
_PROVIDER: str | None = None


def _configure_cpu_threads(s) -> None:
    """Cap the torch intra-op thread pool for a personal single-owner CPU load.

    Idempotent and best-effort — a missing torch (numpy TF-IDF fallback path)
    is not an error here.
    """
    try:
        import torch

        torch.set_num_threads(s.cpu_threads())
    except Exception:  # pragma: no cover - torch optional / already configured
        pass


def _load_model():
    global _model, _PROVIDER
    if _model is not None:
        return _model

    s = get_settings()
    if s.EMBEDDING_PROVIDER == "sentence_transformers":
        try:
            _configure_cpu_threads(s)
            from sentence_transformers import SentenceTransformer
            # CPU-only runtime: pin the model to CPU explicitly so it never
            # tries to move tensors onto CUDA even if a GPU build slipped in.
            _model = SentenceTransformer(s.EMBEDDING_MODEL, device="cpu")
            _PROVIDER = "sentence_transformers"
            logger.info(
                "Embeddings: using sentence_transformers (%s) on CPU",
                s.EMBEDDING_MODEL,
            )
            return _model
        except ImportError:
            logger.warning("sentence_transformers not installed — falling back to numpy TF-IDF")
        except Exception as e:
            logger.warning("Failed to load sentence_transformers: %s — falling back", e)

    _PROVIDER = "numpy_tfidf"
    logger.info("Embeddings: using numpy TF-IDF fallback")
    return None


def embed_texts(texts: list[str]) -> "list[list[float]]":
    """Embed a list of strings. Returns list of float vectors."""
    model = _load_model()

    if model is not None and _PROVIDER == "sentence_transformers":
        s = get_settings()
        vecs = model.encode(
            texts,
            batch_size=s.EMBEDDING_BATCH_SIZE,
            device="cpu",
            normalize_embeddings=s.EMBEDDING_NORMALIZE,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vecs]

    # Numpy TF-IDF fallback
    return _tfidf_embed(texts)


def embed_query(query: str) -> "list[float]":
    return embed_texts([query])[0]


# ─── TF-IDF fallback ────────────────────────────────────────────────────────

_vocab: dict[str, int] = {}
_idf: "list[float] | None" = None


def _tfidf_embed(texts: list[str], dim: int = 256) -> list[list[float]]:
    """Simple normalized bag-of-words with fixed vocabulary. Deterministic."""
    import numpy as np
    import hashlib

    def text_to_vec(t: str) -> list[float]:
        words = t.lower().split()
        vec = np.zeros(dim, dtype=np.float32)
        for w in words:
            idx = int(hashlib.md5(w.encode()).hexdigest(), 16) % dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    return [text_to_vec(t) for t in texts]


def embedding_dim() -> int:
    model = _load_model()
    if model is not None and _PROVIDER == "sentence_transformers":
        return model.get_sentence_embedding_dimension()
    return 256


def runtime_info() -> dict:
    """Non-secret embedding runtime facts for the health endpoint.

    Never loads the heavy model just to report — only reflects torch + config.
    """
    s = get_settings()
    info: dict = {
        "provider": _PROVIDER or s.EMBEDDING_PROVIDER,
        "model": s.EMBEDDING_MODEL,
        "device": s.EMBEDDING_DEVICE,
        "backend": s.EMBEDDING_BACKEND,
        "normalize": s.EMBEDDING_NORMALIZE,
        "batch_size": s.EMBEDDING_BATCH_SIZE,
    }
    try:
        import torch

        info["torch_version"] = torch.__version__
        info["torch_cuda_version"] = torch.version.cuda
        info["cuda_available"] = torch.cuda.is_available()
        info["threads"] = torch.get_num_threads()
    except Exception:  # pragma: no cover - torch optional
        info["torch_version"] = None
        info["torch_cuda_version"] = None
        info["cuda_available"] = False
    return info
