from app.xninetzy.ecosystem.command_router import parse_command


def test_research_command_allowed_parse():
    tool, kwargs = parse_command("/research LangGraph untuk pemula")
    assert tool == "research_light"
    assert kwargs["topic"] == "LangGraph untuk pemula"


def test_deep_research_quality_parse():
    tool, kwargs = parse_command("/deep-research quality Graph RAG")
    assert tool == "deep_research_topic"
    assert kwargs == {"mode": "quality", "topic": "Graph RAG"}
