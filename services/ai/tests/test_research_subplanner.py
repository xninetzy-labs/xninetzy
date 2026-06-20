import pytest

from app.xninetzy.os.research.subplanner import generate_research_subplans


@pytest.mark.asyncio
async def test_subplanner_generates_minimum_three():
    plans = await generate_research_subplans("Graph RAG untuk learning assistant", None, "speed")
    assert len(plans) >= 3
    assert plans[0].search_queries
