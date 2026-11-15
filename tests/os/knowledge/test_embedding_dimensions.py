from __future__ import annotations

from types import SimpleNamespace

import pytest

from xninetzy.os.knowledge import embeddings


def test_embedding_dimension_prefers_current_api_without_deprecated_call(monkeypatch):
    def old_api():
        raise AssertionError("deprecated dimension method must not run")

    model = SimpleNamespace(get_embedding_dimension=lambda: 384,
                            get_sentence_embedding_dimension=old_api)
    monkeypatch.setattr(embeddings, "_load_model", lambda: model)
    monkeypatch.setattr(embeddings, "_PROVIDER", "sentence_transformers")
    assert embeddings.embedding_dim() == 384


def test_embedding_dimension_preserves_older_supported_model_api(monkeypatch):
    model = SimpleNamespace(get_sentence_embedding_dimension=lambda: 768)
    monkeypatch.setattr(embeddings, "_load_model", lambda: model)
    monkeypatch.setattr(embeddings, "_PROVIDER", "sentence_transformers")
    assert embeddings.embedding_dim() == 768


@pytest.mark.parametrize("dimension", [None, 0, -1, True, 3.5])
def test_unknown_or_invalid_model_dimension_fails_before_index_creation(monkeypatch, dimension):
    model = SimpleNamespace(get_embedding_dimension=lambda: dimension,
                            get_sentence_embedding_dimension=lambda: dimension)
    monkeypatch.setattr(embeddings, "_load_model", lambda: model)
    monkeypatch.setattr(embeddings, "_PROVIDER", "sentence_transformers")
    with pytest.raises(ValueError, match="positive integer"):
        embeddings.embedding_dim()


def test_fallback_dimension_does_not_claim_semantic_model(monkeypatch):
    monkeypatch.setattr(embeddings, "_load_model", lambda: None)
    monkeypatch.setattr(embeddings, "_PROVIDER", "numpy_tfidf")
    assert embeddings.embedding_dim() == 256


@pytest.fixture
def fake_model_runtime(monkeypatch):
    import sys
    from xninetzy.core.config import get_settings
    created = []

    def model(name, **kwargs):
        created.append(name)
        return SimpleNamespace(name=name, get_embedding_dimension=lambda: 384)

    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=model))
    monkeypatch.setattr(embeddings, "_configure_cpu_threads", lambda settings: None)
    monkeypatch.setattr(embeddings, "_model", None)
    monkeypatch.setattr(embeddings, "_PROVIDER", None)
    monkeypatch.setattr(embeddings, "_MODEL_CONFIG", None, raising=False)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "sentence_transformers")
    monkeypatch.setenv("EMBEDDING_MODEL", "fixture-a")
    get_settings.cache_clear()
    yield created
    get_settings.cache_clear()


def test_model_config_change_does_not_relabel_a_cached_old_model(monkeypatch, fake_model_runtime):
    from xninetzy.core.config import get_settings
    assert embeddings._load_model().name == "fixture-a"
    monkeypatch.setenv("EMBEDDING_MODEL", "fixture-b")
    get_settings.cache_clear()
    assert embeddings._load_model().name == "fixture-b"
    assert fake_model_runtime == ["fixture-a", "fixture-b"]


def test_explicit_provider_change_releases_the_old_model(monkeypatch, fake_model_runtime):
    from xninetzy.core.config import get_settings
    embeddings._load_model()
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    get_settings.cache_clear()
    assert embeddings._load_model() is None
    assert embeddings._PROVIDER == "numpy_tfidf"


def test_model_load_failure_does_not_log_private_provider_text(monkeypatch, fake_model_runtime, caplog):
    import sys

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic-private-model-credential")

    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=fail))
    assert embeddings._load_model() is None
    assert "synthetic-private-model-credential" not in caplog.text
