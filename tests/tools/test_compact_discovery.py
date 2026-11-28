from __future__ import annotations

import pytest

from xninetzy.skills.models import SkillDefinition
from xninetzy.skills import tools as skills
from xninetzy.tools.ecosystem import tool_catalog_tools as catalog


def test_compact_catalog_preserves_execution_policy_and_paging():
    full = catalog.tool_catalog.invoke({"risk": "read", "limit": 500})
    first = catalog.tool_catalog.invoke({"risk": "read", "limit": 2, "compact": True})
    second = catalog.tool_catalog.invoke({"risk": "read", "limit": 2, "offset": 2, "compact": True})
    assert [row["name"] for row in first + second] == [row["name"] for row in full[:4]]
    assert all(set(row) == {"name", "description", "risk", "requires_approval", "requires_idempotency"} for row in first)
    for row, original in zip(first, full, strict=False):
        for key in row:
            assert row[key] == original[key]


def test_compact_catalog_filter_cannot_relax_final_policy():
    rows = catalog.tool_catalog.invoke({"query": "hebat_remove_submission", "compact": True})
    assert len(rows) == 1
    assert rows[0]["risk"] == "final"
    assert rows[0]["requires_approval"] is True
    assert rows[0]["requires_idempotency"] is True
    assert catalog.tool_catalog.invoke({"query": "no-such-fixture-tool", "compact": True}) == []


def test_legacy_catalog_still_contains_the_full_manifest():
    row = catalog.tool_catalog.invoke({"limit": 1})[0]
    assert {"name", "version", "feature_pack", "policy_known", "stability"} <= set(row)


def test_compact_skill_list_is_filtered_bounded_and_explicitly_untrusted(monkeypatch):
    items = [SkillDefinition(name=f"fixture-{n}", description="Context assembly", path="", source="user",
                            content_hash="", trust_level="owner-installed", quality_warnings=["Review resource"])
             for n in range(4)]
    monkeypatch.setattr(skills, "list_skills", lambda: items)
    result = skills.skill_list.invoke({"query": "context", "limit": 1, "offset": 1, "compact": True})
    assert "fixture-1" in result and "fixture-0" not in result and "fixture-2" not in result
    assert "owner-installed" in result and "warnings=1" in result
    assert "skill_get" in result


@pytest.mark.parametrize("limit", [-1, 0, 1])
def test_catalog_limit_remains_bounded(limit):
    assert len(catalog.tool_catalog.invoke({"limit": limit, "compact": True})) == 1
