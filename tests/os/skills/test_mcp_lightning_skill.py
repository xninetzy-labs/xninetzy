from app.xninetzy.skills.registry import get_skill, rank_skills


def test_mcp_lightning_skill_is_discoverable_and_valid():
    skill = get_skill("xninetzy-mcp-lightning")

    assert skill is not None
    assert skill.metadata["version"] == "1.0"
    assert "Lightning" in skill.description


def test_mcp_lightning_skill_routes_optimization_requests():
    matches = rank_skills(
        "optimasi MCP RL contextual bandit provider dan deep research evidence",
        limit=3,
    )
    assert matches
    assert matches[0].skill.name == "xninetzy-mcp-lightning"

