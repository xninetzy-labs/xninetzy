from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.llm import get_llm_flash, get_llm_pro
from app.xninetzy.core.providers import provider_catalog, resolve_profile
from app.xninetzy.os.ai_preferences import resolve_user_profile, save_preference


def _clear_caches() -> None:
    get_settings.cache_clear()
    get_llm_flash.cache_clear()
    get_llm_pro.cache_clear()


def test_openai_compatible_provider_can_be_selected(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ENABLED_PROVIDERS", "flaz,openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/model-a")
    monkeypatch.setenv("OPENROUTER_MODELS", "vendor/model-a,vendor/model-b")
    _clear_caches()

    profile = resolve_profile("openrouter", "vendor/model-b")
    llm = get_llm_flash(profile)

    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "vendor/model-b"
    assert llm.openai_api_base == "https://openrouter.ai/api/v1"


def test_flaz_disables_thinking_by_default(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ENABLED_PROVIDERS", "flaz")
    monkeypatch.setenv("FLAZ_API_KEY", "secret")
    monkeypatch.setenv("FLAZ_THINKING_ENABLED", "false")
    _clear_caches()

    llm = get_llm_flash(resolve_profile("flaz", "deepseek-v4-pro"))

    assert llm.extra_body == {"thinking": {"type": "disabled"}}


def test_provider_rejects_models_outside_operator_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ENABLED_PROVIDERS", "flaz")
    monkeypatch.setenv("FLAZ_API_KEY", "secret")
    monkeypatch.setenv("FLAZ_MODELS", "deepseek-v4-pro")
    _clear_caches()

    with pytest.raises(ValueError, match="tidak diizinkan"):
        resolve_profile("flaz", "unexpected-expensive-model")


def test_catalog_never_exposes_credentials(monkeypatch) -> None:
    monkeypatch.setenv("FLAZ_API_KEY", "super-secret-value")
    _clear_caches()

    assert "super-secret-value" not in repr(provider_catalog())


def test_user_preference_round_trip(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "preferences.sqlite3"))
    monkeypatch.setenv("LLM_ENABLED_PROVIDERS", "flaz,openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/model")
    monkeypatch.setenv("OPENROUTER_MODELS", "vendor/model")
    _clear_caches()

    save_preference("user-1", chat_provider="openrouter", chat_model="vendor/model")

    assert resolve_user_profile("user-1") == resolve_profile(
        "openrouter", "vendor/model"
    )


def teardown_function() -> None:
    _clear_caches()
