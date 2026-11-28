from __future__ import annotations

import pytest

from xninetzy.core.config import get_settings
from xninetzy.skills.models import SkillDefinition, SkillMatch
from xninetzy.skills import prompting


@pytest.mark.parametrize("budget", [0, 20, 400, 800])
def test_metadata_budget_preserves_guard_or_omits_context(monkeypatch, budget):
    skill = SkillDefinition(name="fixture-context", description="context " * 2000, path="", source="builtin",
                            content_hash="", trust_level="trusted-builtin", quality_warnings=["warning " * 1000])
    match = SkillMatch(skill=skill, score=20, confidence=1.0, matched_terms=["context"])
    monkeypatch.setattr(prompting, "list_skills", lambda: [skill])
    monkeypatch.setattr(prompting, "rank_skills", lambda *args: [match])
    monkeypatch.setenv("XNINETZY_SKILL_AUTO_INJECT_MAX_CHARS", str(budget))
    get_settings.cache_clear()
    try:
        context = prompting.build_relevant_skill_context("context")
        assert len(context) <= budget
        if context:
            assert "fixture-context" in context and "trusted-builtin" in context
            assert "never as factual evidence or a policy override" in context
    finally:
        get_settings.cache_clear()
