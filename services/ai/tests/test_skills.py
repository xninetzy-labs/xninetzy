from app.skills.registry import get_skill, list_skills


def test_skill_research_registered():
    assert get_skill("research")
    assert "research" in [skill.name for skill in list_skills()]
