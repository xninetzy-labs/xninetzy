from __future__ import annotations

from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.providers import LLMProfile, provider_catalog, resolve_profile


@lru_cache(maxsize=32)
def get_llm_flash(profile: LLMProfile | None = None) -> BaseChatModel:
    """Fast LLM for orchestrator routing and direct responses."""
    return _build_llm(profile)


@lru_cache(maxsize=32)
def get_llm_pro(profile: LLMProfile | None = None) -> BaseChatModel:
    """LLM for the ReAct agent and complex multi-step reasoning."""
    return _build_llm(profile)


def _build_llm(profile: LLMProfile | None = None) -> BaseChatModel:
    s = get_settings()
    try:
        selected = resolve_profile(
            profile.provider if profile else None,
            profile.model if profile else None,
            s,
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    info = provider_catalog(s)[selected.provider]

    if info.kind == "anthropic":
        return ChatAnthropic(
            api_key=s.ANTHROPIC_API_KEY,
            model=selected.model,
            timeout=s.LLM_TIMEOUT_SECONDS,
            max_retries=s.LLM_MAX_RETRIES,
            temperature=0,
        )

    api_keys = {
        "flaz": s.FLAZ_API_KEY,
        "openai": s.OPENAI_API_KEY,
        "openrouter": s.OPENROUTER_API_KEY,
        "ollama": "ollama",
        "generic": s.GENERIC_OPENAI_API_KEY or "not-required",
    }
    return ChatOpenAI(
        api_key=api_keys[selected.provider],
        base_url=info.base_url,
        model=selected.model,
        timeout=s.LLM_TIMEOUT_SECONDS,
        max_retries=s.LLM_MAX_RETRIES,
        temperature=0,
    )


def _build_flaz_llm() -> BaseChatModel:
    """Backward-compatible helper for integrations that imported this symbol."""
    return _build_llm(resolve_profile("flaz"))
