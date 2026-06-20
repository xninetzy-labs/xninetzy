import importlib

from app.xninetzy.skills.registry import get_skill, list_skills


def test_it_learning_skill_package_importable():
    assert importlib.import_module("app.xninetzy.skills.it_learning")


def test_it_learning_skill_tools_importable():
    mod = importlib.import_module("app.xninetzy.skills.it_learning.tools")
    assert hasattr(mod, "learning_create_roadmap")


def test_it_learning_skill_registered():
    skill = get_skill("it_learning")
    assert skill is not None
    assert skill.name == "it_learning"
    assert "it_learning" in [s.name for s in list_skills()]


def test_learning_alias_still_works():
    # Legacy `learning` must not break.
    assert get_skill("learning") is not None


def test_friendly_aliases_resolve_to_it_learning():
    for alias in ("it", "programming", "coding"):
        skill = get_skill(alias)
        assert skill is not None and skill.name == "it_learning"
