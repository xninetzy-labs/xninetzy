from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.xninetzy.core.config import get_settings


@lru_cache
def get_llm_flash() -> ChatOpenAI:
    """Fast LLM for orchestrator routing and direct responses."""
    s = get_settings()
    return ChatOpenAI(
        model=s.DEEPSEEK_MODEL,
        api_key=s.DEEPSEEK_API_KEY,
        base_url=s.DEEPSEEK_BASE_URL,
        temperature=0.1,
    )


@lru_cache
def get_llm_pro() -> ChatOpenAI:
    """Pro LLM for ReAct agent requiring complex multi-step reasoning."""
    s = get_settings()
    return ChatOpenAI(
        model=s.DEEPSEEK_PRO_MODEL,
        api_key=s.DEEPSEEK_API_KEY,
        base_url=s.DEEPSEEK_BASE_URL,
        temperature=0.3,
    )
