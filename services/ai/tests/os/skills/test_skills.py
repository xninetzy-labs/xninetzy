from app.xninetzy.skills.registry import get_skill, list_skills, rank_skills


def test_skill_research_registered():
    assert get_skill("research")
    assert "research" in [skill.name for skill in list_skills()]


def test_skill_suggestion_covers_machine_learning_topics():
    matches = rank_skills("Saya ingin belajar clustering machine learning", limit=3)

    assert matches
    assert matches[0].skill.name == "it-learning"
    assert "clustering" in matches[0].matched_terms
