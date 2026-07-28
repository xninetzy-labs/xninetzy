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
