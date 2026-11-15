from __future__ import annotations


from langchain_core.tools import tool

from xninetzy.context.registry.taxonomy import (
    SEMANTIC_DOMAINS,
    SYSTEM_CAPABILITIES,
    build_cross_walk,
    intent_domain_to_canonical,
    legacy_group_to_canonical,
    resolve_alias,
)
from xninetzy.tools.tool_results import to_tool_result


@tool
def routing_taxonomy_inspect(query: str = "") -> str:
    """Inspect the canonical routing taxonomy and resolve aliases.

    Args:
        query: Optional legacy name to resolve (alias, tool group,
            or skill prefix). Empty returns the full cross-walk.

    Returns:
        JSON: `{canonical_name}` if query resolves, otherwise the
        full `{semantic_domains, system_capabilities, domains,
        empty_legacy_groups}` cross-walk.
    """
    if query:
        canonical = resolve_alias(query) or legacy_group_to_canonical(query) or intent_domain_to_canonical(query)
        if canonical:
            return to_tool_result(
                f"Resolved '{query}' -> '{canonical}'.",
                items=[{"query": query, "canonical": canonical}],
                meta={"resolver": "routing_taxonomy_inspect"},
            )
        return to_tool_result(
            f"No canonical match for '{query}'.",
            items=[],
            meta={"resolver": "routing_taxonomy_inspect", "result": "unresolved"},
            ok=False,
        )
    cross_walk = build_cross_walk()
    from datetime import UTC, datetime

    cross_walk["generated_at"] = datetime.now(UTC).isoformat()
    return to_tool_result(
        f"Routing taxonomy: {len(SEMANTIC_DOMAINS)} domains, "
        f"{len(SYSTEM_CAPABILITIES)} system capabilities.",
        items=[cross_walk],
        meta={"resolver": "routing_taxonomy_inspect"},
    )


def _self_test() -> int:
    cases = [
        ("it_learning", "learning"),
        ("xninetzy-obsidian", "integrations.obsidian"),
        ("xninetzy-uacc", "academic.uacc"),
        ("career", "career"),
        ("dream", "career"),
        ("security", "security"),
        ("os_kernel", "knowledge"),
    ]
    failures = 0
    for raw, expected in cases:
        got = resolve_alias(raw)
        if got != expected:
            failures += 1
            print(f"FAIL: resolve_alias({raw!r}) -> {got!r} expected {expected!r}")
    groups_with_members = (
        "it_learning",
        "academic",
        "career",
        "research",
        "media",
        "security",
        "repo",
    )
    for g in groups_with_members:
        got = legacy_group_to_canonical(g)
        if got is None:
            failures += 1
            print(f"FAIL: legacy_group_to_canonical({g!r}) -> None")
    if failures > 0:
        return 1
    print("PASS: taxonomy_resolve_aliases")
    return 0


routing_taxonomy_tools_list = [routing_taxonomy_inspect]


if __name__ == "__main__":
    import sys

    sys.exit(_self_test())
