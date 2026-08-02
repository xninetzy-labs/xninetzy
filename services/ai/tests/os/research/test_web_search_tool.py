from __future__ import annotations

import pytest

from app.xninetzy.os.research import web_search as web_search_service
from app.xninetzy.tools.ecosystem import research_tools


@pytest.mark.asyncio
async def test_web_search_tool_reaches_free_fallback(monkeypatch):
    async def fake_search(query: str, limit: int):
        return [{"title": "Free source", "url": "https://example.org", "snippet": "grounded"}]

    monkeypatch.setattr(web_search_service, "web_search", fake_search)

    result = await research_tools.web_search.ainvoke({"query": "learning"})

    assert "Free source" in result
    assert "example.org" in result
