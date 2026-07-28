from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.llm import get_llm_flash, get_llm_pro


def _clear_llm_caches() -> None:
    get_settings.cache_clear()
    get_llm_flash.cache_clear()
    get_llm_pro.cache_clear()


def test_flaz_llm_uses_openai_compatible_configuration(monkeypatch) -> None:
    monkeypatch.setenv("FLAZ_API_KEY", "test-secret")
    monkeypatch.setenv("FLAZ_BASE_URL", "https://ai.flaz.id/v1/")
    monkeypatch.setenv("FLAZ_MODEL", "deepseek-v4-pro")
    _clear_llm_caches()

    llm = get_llm_flash()

    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "deepseek-v4-pro"
    assert llm.openai_api_base == "https://ai.flaz.id/v1"
    assert llm.openai_api_key.get_secret_value() == "test-secret"


def test_flaz_llm_rejects_missing_api_key(monkeypatch) -> None:
    monkeypatch.setenv("FLAZ_API_KEY", "")
    _clear_llm_caches()

    with pytest.raises(RuntimeError, match="FLAZ_API_KEY"):
        get_llm_pro()


def teardown_function() -> None:
    _clear_llm_caches()
