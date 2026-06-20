from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

_model = None
_PROVIDER: str | None = None


def _load_model():
    global _model, _PROVIDER
    if _model is not None:
        return _model

    s = get_settings()
    if s.EMBEDDING_PROVIDER == "sentence_transformers":
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(s.EMBEDDING_MODEL)
            _PROVIDER = "sentence_transformers"
            logger.info("Embeddings: using sentence_transformers (%s)", s.EMBEDDING_MODEL)
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
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
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
