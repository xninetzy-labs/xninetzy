from app.xninetzy.skills.prompting import build_relevant_skill_context
from app.xninetzy.skills.registry import (
    SkillValidationError,
    get_skill,
    install_skill,
    list_skill_resources,
    list_skills,
    rank_skills,
    read_skill_resource,
    skill_catalog_health,
)


def test_skill_research_registered():
    assert get_skill("research")
    assert "research" in [skill.name for skill in list_skills()]


def test_skill_suggestion_covers_machine_learning_topics():
    matches = rank_skills("Saya ingin belajar clustering machine learning", limit=3)

    assert matches
    assert matches[0].skill.name == "it-learning"
    assert "clustering" in matches[0].matched_terms


def test_skill_metadata_exposes_trust_and_resource_inventory():
    skill = get_skill("playwright")
    assert skill is not None
    assert skill.trust_level == "trusted-builtin"
    assert "references/cli.md" in skill.resource_paths
    assert skill.line_count > 0


def test_skill_progressive_disclosure_keeps_body_out_of_auto_context():
    context = build_relevant_skill_context("tolong gunakan playwright untuk portal")
    assert "RELEVANT XNINETZY SKILL METADATA" in context
    assert "skill_get(name)" in context
    assert "# Playwright" not in context


def test_skill_resources_are_bounded_and_path_confined():
    resources = list_skill_resources("playwright")
    assert "references/cli.md" in resources
    content = read_skill_resource("playwright", "references/cli.md")
    assert content


def test_skill_catalog_health_reports_all_builtin_skills():
    health = skill_catalog_health()
    assert health["valid_count"] >= 20
    assert health["invalid_count"] == 0


def test_skill_install_supports_bounded_text_resources(tmp_path):
    markdown = """---
name: temporary-skill
description: A bounded test skill for resource installation.
---

Use the reference only after inspecting the request.
"""
    skill, action = install_skill(
        markdown,
        resources={"references/workflow.md": "step one\n"},
        destination=tmp_path,
    )
    assert action == "installed"
    assert "references/workflow.md" in skill.resource_paths
    assert (tmp_path / "temporary-skill" / "references/workflow.md").read_text() == "step one\n"


def test_skill_resource_install_rejects_parent_traversal(tmp_path):
    markdown = """---
name: temporary-skill
description: A bounded test skill for resource validation.
---

Use the reference only after inspecting the request.
"""
    try:
        install_skill(
            markdown,
            resources={"../secret.txt": "nope"},
            destination=tmp_path,
        )
    except SkillValidationError:
        return
    raise AssertionError("parent traversal resource should be rejected")
