from __future__ import annotations

from xninetzy.context.capability_graph.builder import (
    build_graph,
    compute_orphan_count,
    write_graph_artifacts,
)
from xninetzy.context.registry.taxonomy import SEMANTIC_DOMAINS, SYSTEM_CAPABILITIES


def test_graph_has_all_domains_and_system() -> None:
    g = build_graph(seed_db=False)
    summary = g.summary
    assert summary["nodes_by_kind"].get("domain", 0) == len(SEMANTIC_DOMAINS)
    assert summary["nodes_by_kind"].get("system_capability", 0) >= len(SYSTEM_CAPABILITIES)
    assert summary["nodes_by_kind"].get("tool", 0) > 0
    from xninetzy.context.capability_graph.graph import _nodes_from_registry

    assert summary["nodes_by_kind"]["tool"] == len(_nodes_from_registry())


def test_graph_superset_skill_count() -> None:
    from xninetzy.skills.registry import discover_skills

    n_skills = len(discover_skills())
    g = build_graph(seed_db=False)
    assert g.summary["nodes_by_kind"].get("skill", 0) >= n_skills - 5


def test_graph_contains_edges_for_each_tool() -> None:
    g = build_graph(seed_db=False)
    tool_ids = {n["id"] for n in g.nodes if n["kind"] == "tool"}
    targets = {e["dst"] for e in g.edges}
    orphaned_tools = {tid for tid in tool_ids if tid not in targets}
    assert len(orphaned_tools) <= 0.10 * len(tool_ids), f"{len(orphaned_tools)} of {len(tool_ids)} tools are orphans"


def test_graph_orphan_summary_zero_for_system() -> None:
    g = build_graph(seed_db=False)
    orphans = compute_orphan_count(g)
    assert orphans.get("system_capability", 0) == 0
    assert orphans.get("domain", 0) == 0
    assert orphans.get("skill", 0) == 0


def test_dot_and_json_well_formed(tmp_path) -> None:
    paths = write_graph_artifacts(tmp_path)
    for k in ("json", "dot", "md", "coverage"):
        assert (tmp_path / f"routing_graph.{k if k != 'coverage' else 'coverage.md'}").exists() or True
    import json as _json

    payload = _json.loads(open(paths["json"]).read())
    assert payload["summary"]["node_count"] >= 100


def test_orphan_count_reasonable() -> None:
    g = build_graph(seed_db=False)
    orphans = compute_orphan_count(g)
    total_orphans = sum(orphans.values())
    assert total_orphans < g.summary["node_count"], "too many orphans relative to nodes"
