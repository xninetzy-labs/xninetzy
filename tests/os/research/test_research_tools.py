import asyncio

import pytest

from app.xninetzy.tools.ecosystem.research_tools import research_light


@pytest.mark.asyncio
async def test_research_light_works_without_provider(monkeypatch):
    result = await research_light.ainvoke({"topic": "LangGraph", "limit": 3})
    assert "Research Ringan" in result
    assert "/deep-research LangGraph" in result


def test_deep_research_denied_does_not_claim_save():
    from app.xninetzy.os.research.permissions import deep_research_denied_message

    msg = deep_research_denied_message()
    assert "simpan ke Obsidian" not in msg
    assert "/research <topik>" in msg


@pytest.mark.asyncio
async def test_deep_research_timeout_preserves_partial_session(monkeypatch):
    from types import SimpleNamespace

    from app.xninetzy.os.research import deep_research

    async def slow_research(**kwargs):
        await asyncio.sleep(0.05)
        return "unexpected"

    failed = []
    monkeypatch.setattr(deep_research, "_run_deep_research", slow_research)
    monkeypatch.setattr(
        deep_research,
        "get_settings",
        lambda: SimpleNamespace(XNINETZY_DEEP_RESEARCH_TIMEOUT_SECONDS=0.01),
    )
    monkeypatch.setattr(deep_research, "list_research_sessions", lambda *_args, **_kwargs: [{"id": 7, "status": "running"}])
    monkeypatch.setattr(deep_research, "fail_session", lambda session_id, reason: failed.append((session_id, reason)))

    result = await deep_research.run_deep_research(
        topic="agentic systems",
        chat_id="owner",
        sender_id="owner",
        sender_name="Owner",
        chat_type="private",
        metadata={},
    )

    assert "timed out" in result
    assert failed == [(7, "deep_research_timeout")]
