from __future__ import annotations

from xninetzy.context.registry.taxonomy import (
    SEMANTIC_DOMAINS,
    SYSTEM_CAPABILITIES,
    build_cross_walk,
    intent_domain_to_canonical,
    legacy_group_to_canonical,
    resolve_alias,
)


def test_canonical_names_unique_and_count() -> None:
    assert len(SEMANTIC_DOMAINS) == 16
    assert len(SYSTEM_CAPABILITIES) >= 10
    assert len(set(SEMANTIC_DOMAINS)) == len(SEMANTIC_DOMAINS)
    assert len(set(SYSTEM_CAPABILITIES)) == len(SYSTEM_CAPABILITIES)
    assert not (set(SEMANTIC_DOMAINS) & set(SYSTEM_CAPABILITIES))


def test_resolve_alias_for_known_aliases() -> None:
    cases = [
        ("it_learning", "learning"),
        ("xninetzy-obsidian", "integrations.obsidian"),
        ("xninetzy-uacc", "academic.uacc"),
        ("xninetzy-hebat", "academic.hebat"),
        ("career", "career"),
        ("dream", "career"),
        ("os_kernel", "knowledge"),
        ("unified_search", "knowledge"),
        ("repo", "software"),
        ("notes", "integrations.obsidian"),
    ]
    for raw, expected in cases:
        assert resolve_alias(raw) == expected, f"resolve_alias({raw!r}) -> {resolve_alias(raw)!r}"


def test_resolve_alias_for_unknown_returns_none() -> None:
    assert resolve_alias("definitely_not_a_domain_xyz") is None
    assert resolve_alias("") is None


def test_legacy_group_to_canonical_round_trip() -> None:
    from xninetzy.tools.registry import get_tool_groups

    groups = get_tool_groups()
    for grp in groups:
        canonical = legacy_group_to_canonical(grp)
        assert canonical is not None, f"group {grp!r} unmapped"
        assert canonical in SEMANTIC_DOMAINS or canonical in SYSTEM_CAPABILITIES or "." in canonical


def test_performance_group_routes_to_existing_software_domain() -> None:
    assert legacy_group_to_canonical("performance") == "software"


def test_intent_domain_to_canonical_handles_internal_keys() -> None:
    for src, expected in [
        ("research", "research"),
        ("engineering", "software"),
        ("vision", "browser"),
    ]:
        assert intent_domain_to_canonical(src) == expected


def test_cross_walk_covers_all_legacy_groups() -> None:
    from xninetzy.tools.registry import get_tool_groups

    cross = build_cross_walk()
    assert set(cross["semantic_domains"]) == set(SEMANTIC_DOMAINS)
    assert set(cross["system_capabilities"]) == set(SYSTEM_CAPABILITIES)
    total = sum(len(v) for v in cross["domains"].values())
    total += sum(len(v) for v in cross["system"].values())
    total += sum(len(v) for v in cross["integrations"].values())
    assert not cross["unmapped_legacy_groups"]
    assert total + len(cross["empty_legacy_groups"]) == len(get_tool_groups())
