from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from xninetzy.context.capability_graph.graph import (
    CapabilityNode,
    _nodes_from_registry,
    seed_from_registry,
)
from xninetzy.context.registry.taxonomy import (
    SEMANTIC_DOMAINS,
    SYSTEM_CAPABILITIES,
    legacy_group_to_canonical,
    resolve_alias,
)
from xninetzy.skills.registry import discover_skills

GRAPH_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class GraphEdge:
    src: str
    dst: str
    edge_type: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CapabilityGraphArtifact:
    nodes: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    provenance: dict[str, Any]


def _node_kind(canonical: str | None) -> str:
    if canonical is None:
        return "tool"
    if canonical in SEMANTIC_DOMAINS:
        return "domain"
    if canonical in SYSTEM_CAPABILITIES:
        return "system_capability"
    if canonical.startswith("integrations."):
        return "integration"
    if "." in canonical:
        return "subdomain"
    return "tool"


def _node_dict(node: CapabilityNode, *, kind: str, domain: str | None, skill: str | None) -> dict[str, Any]:
    payload = asdict(node)
    payload["kind"] = kind
    payload["domain"] = domain
    payload["skill"] = skill
    return payload


def _domain_for_tool(tool_name: str, group: str | None) -> str | None:
    if group:
        canonical = legacy_group_to_canonical(group)
        if canonical:
            if canonical.startswith("integrations."):
                return canonical.split(".", 1)[0]
            if canonical in SYSTEM_CAPABILITIES:
                return None
            return canonical
    canonical = resolve_alias(tool_name)
    if canonical is None:
        return None
    if canonical.startswith("integrations."):
        return canonical.split(".", 1)[0]
    if canonical in SYSTEM_CAPABILITIES:
        return None
    return canonical


def _skill_for_tool(tool_name: str, skill_index: dict[str, set[str]]) -> str | None:
    candidates = skill_index.get(tool_name)
    if candidates:
        return sorted(candidates)[0]
    return None


def _build_skill_tool_index() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for name, skill in discover_skills().items():
        meta = dict(skill.metadata or {})
        consumes = str(meta.get("consumes", "") or "")
        produces = str(meta.get("produces", "") or "")
        for token in {consumes, produces}:
            token = token.strip()
            if not token:
                continue
            out.setdefault(token, set()).add(name)
    return out


def _seed_edges_from_skill_metadata(nodes: list[CapabilityNode], skill_index: dict[str, set[str]]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for node in nodes:
        if node.metadata.get("kind") != "tool":
            continue
        for skill_name in sorted(skill_index.get(node.capability, set())):
            edges.append(
                GraphEdge(
                    src=f"skill:{skill_name}",
                    dst=f"tool:{node.capability}",
                    edge_type="implements",
                    weight=1.0,
                    metadata={"source": "skill_metadata"},
                )
            )
    return edges


def _seed_alternative_edges(nodes: list[CapabilityNode]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    by_group: dict[str, list[CapabilityNode]] = {}
    for n in nodes:
        if n.metadata.get("kind") != "tool":
            continue
        group = n.metadata.get("group")
        if not group:
            continue
        by_group.setdefault(group, []).append(n)
    for grp, members in by_group.items():
        tool_nodes = [m for m in members if m.tool]
        if len(tool_nodes) < 2:
            continue
        for i, a in enumerate(tool_nodes):
            for b in tool_nodes[i + 1 :]:
                edges.append(
                    GraphEdge(src=a.surface, dst=b.surface, edge_type="alternative_to", weight=0.5)
                )
                edges.append(
                    GraphEdge(src=b.surface, dst=a.surface, edge_type="alternative_to", weight=0.5)
                )
    return edges


def build_graph(*, seed_db: bool = True) -> CapabilityGraphArtifact:
    if seed_db:
        try:
            seed_from_registry()
        except Exception:
            pass
    seed_nodes = _nodes_from_registry()
    skill_index = _build_skill_tool_index()

    nodes_out: list[dict[str, Any]] = []
    nodes_out.append(
        {
            "id": "graph:universe",
            "name": "graph",
            "kind": "system_capability",
            "domain": None,
            "skill": None,
            "capability": "graph",
            "surface": "graph:root",
            "tool": None,
            "aliases": ("graph", "graph-rag"),
            "metadata": {"kind": "system_capability", "synthetic": True},
        }
    )
    for d in SEMANTIC_DOMAINS:
        nodes_out.append(
            {
                "id": f"domain:{d}",
                "name": d,
                "kind": "domain",
                "domain": d,
                "skill": None,
                "capability": d,
                "surface": f"domain:{d}",
                "tool": None,
                "aliases": (d,),
                "metadata": {"kind": "domain"},
            }
        )
    for s in SYSTEM_CAPABILITIES:
        nodes_out.append(
            {
                "id": f"system:{s}",
                "name": s,
                "kind": "system_capability",
                "domain": None,
                "skill": None,
                "capability": s,
                "surface": f"system:{s}",
                "tool": None,
                "aliases": (s,),
                "metadata": {"kind": "system_capability"},
            }
        )
    for sk in discover_skills():
        nodes_out.append(
            {
                "id": f"skill:{sk}",
                "name": sk,
                "kind": "skill",
                "domain": None,
                "skill": sk,
                "capability": sk,
                "surface": f"skill:{sk}",
                "tool": None,
                "aliases": (sk, sk.replace("-", " "), sk.replace("-", "_")),
                "metadata": {"kind": "skill", "source": "skills_directory"},
            }
        )

    for n in seed_nodes:
        grp = n.metadata.get("group") if isinstance(n.metadata, dict) else None
        domain = _domain_for_tool(n.capability, grp)
        skill = _skill_for_tool(n.capability, skill_index)
        d = _node_dict(n, kind="tool", domain=domain, skill=skill)
        d["id"] = f"tool:{n.capability}"
        nodes_out.append(d)

    edges: list[GraphEdge] = []
    edges.append(
        GraphEdge(src="graph:universe", dst="graph:universe", edge_type="contains", metadata={"synthetic": True})
    )
    for n in seed_nodes:
        if not n.metadata.get("group"):
            edges.append(
                GraphEdge(src="graph:universe", dst=f"tool:{n.capability}", edge_type="contains", weight=0.1)
            )
            continue
        domain = _domain_for_tool(n.capability, n.metadata.get("group"))
        if domain:
            src_id = f"domain:{domain}" if domain in SEMANTIC_DOMAINS else None
            if src_id:
                edges.append(
                    GraphEdge(src=src_id, dst=f"tool:{n.capability}", edge_type="contains", weight=1.0)
                )
        else:
            canonical = legacy_group_to_canonical(n.metadata.get("group") or "")
            if canonical and canonical in SYSTEM_CAPABILITIES:
                edges.append(
                    GraphEdge(
                        src=f"system:{canonical}",
                        dst=f"tool:{n.capability}",
                        edge_type="contains",
                        weight=1.0,
                    )
                )
            else:
                edges.append(
                    GraphEdge(
                        src="graph:universe",
                        dst=f"tool:{n.capability}",
                        edge_type="contains",
                        weight=0.1,
                    )
                )
    for d in SEMANTIC_DOMAINS:
        edges.append(
            GraphEdge(src="graph:universe", dst=f"domain:{d}", edge_type="contains", weight=1.0)
        )
    for s in SYSTEM_CAPABILITIES:
        edges.append(
            GraphEdge(src="graph:universe", dst=f"system:{s}", edge_type="contains", weight=1.0)
        )
    for sk in discover_skills():
        edges.append(
            GraphEdge(src="graph:universe", dst=f"skill:{sk}", edge_type="contains", weight=1.0)
        )
    edges.extend(_seed_edges_from_skill_metadata(seed_nodes, skill_index))
    edges.extend(_seed_alternative_edges(seed_nodes))

    counts: dict[str, int] = {}
    for n in nodes_out:
        k = str(n.get("kind", "unknown"))
        counts[k] = counts.get(k, 0) + 1
    edge_counts: dict[str, int] = {}
    for e in edges:
        edge_counts[e.edge_type] = edge_counts.get(e.edge_type, 0) + 1

    summary = {
        "node_count": len(nodes_out),
        "edge_count": len(edges),
        "nodes_by_kind": counts,
        "edges_by_type": edge_counts,
    }
    provenance = {
        "version": GRAPH_VERSION,
        "registry_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": [
            "xninetzy.tools.registry.get_tool_groups",
            "xninetzy.skills.registry.discover_skills",
            "xninetzy.context.registry.taxonomy",
        ],
    }
    artifact = CapabilityGraphArtifact(
        nodes=tuple(nodes_out),
        edges=tuple(
            {
                "src": e.src,
                "dst": e.dst,
                "edge_type": e.edge_type,
                "weight": e.weight,
                "metadata": e.metadata,
            }
            for e in edges
        ),
        summary=summary,
        provenance=provenance,
    )
    return artifact


def to_json(artifact: CapabilityGraphArtifact) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": artifact.provenance["version"],
        "registry_version": artifact.provenance["registry_version"],
        "generated_at": artifact.provenance["generated_at"],
        "summary": artifact.summary,
        "provenance": artifact.provenance,
        "nodes": list(artifact.nodes),
        "edges": list(artifact.edges),
    }


def to_dot(artifact: CapabilityGraphArtifact) -> str:
    lines: list[str] = ["digraph routing_graph {", "  rankdir=LR;", "  node [shape=box, style=rounded];"]
    kind_shape = {
        "domain": "ellipse",
        "skill": "box",
        "tool": "note",
        "system_capability": "diamond",
        "integration": "parallelogram",
    }
    for n in artifact.nodes:
        shape = kind_shape.get(str(n.get("kind", "tool")), "box")
        nid = str(n.get("id", ""))
        label = str(n.get("name", ""))
        lines.append(f'  "{nid}" [label="{label}" shape={shape}];')
    for e in artifact.edges:
        lines.append(f'  "{e["src"]}" -> "{e["dst"]}" [label="{e["edge_type"]}"];')
    lines.append("}")
    return "\n".join(lines)


def to_markdown(artifact: CapabilityGraphArtifact) -> str:
    lines: list[str] = []
    lines.append("# Routing capability graph")
    lines.append("")
    lines.append(f"Version: `{artifact.provenance['version']}`  ")
    lines.append(f"Generated at: `{artifact.provenance['generated_at']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Nodes:** {artifact.summary['node_count']}")
    lines.append(f"- **Edges:** {artifact.summary['edge_count']}")
    lines.append("")
    lines.append("### Nodes by kind")
    lines.append("")
    lines.append("| kind | count |")
    lines.append("| --- | --- |")
    for k, v in sorted(artifact.summary["nodes_by_kind"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### Edges by type")
    lines.append("")
    lines.append("| edge_type | count |")
    lines.append("| --- | --- |")
    for k, v in sorted(artifact.summary["edges_by_type"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    return "\n".join(lines)


def write_graph_artifacts(output_root: str | Path = "data/registry") -> dict[str, str]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    artifact = build_graph()
    json_path = root / "routing_graph.json"
    json_path.write_text(json.dumps(to_json(artifact), ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    dot_path = root / "routing_graph.dot"
    dot_path.write_text(to_dot(artifact), encoding="utf-8")
    md_path = root / "routing_graph.md"
    md_path.write_text(to_markdown(artifact), encoding="utf-8")
    coverage_md = root / "routing_coverage.md"
    orphan_count = compute_orphan_count(artifact)
    coverage_md.write_text(_render_coverage(artifact, orphan_count), encoding="utf-8")
    return {
        "json": str(json_path),
        "dot": str(dot_path),
        "md": str(md_path),
        "coverage": str(coverage_md),
    }


def compute_orphan_count(artifact: CapabilityGraphArtifact) -> dict[str, int]:
    nodes = artifact.nodes
    edges = artifact.edges
    in_count: dict[str, int] = {}
    out_count: dict[str, int] = {}
    for e in edges:
        out_count[e["src"]] = out_count.get(e["src"], 0) + 1
        in_count[e["dst"]] = in_count.get(e["dst"], 0) + 1
    by_kind_orphan: dict[str, int] = {}
    for n in nodes:
        nid = str(n.get("id", ""))
        if in_count.get(nid, 0) == 0 and out_count.get(nid, 0) == 0:
            k = str(n.get("kind", "unknown"))
            by_kind_orphan[k] = by_kind_orphan.get(k, 0) + 1
    return by_kind_orphan


def _render_coverage(artifact: CapabilityGraphArtifact, orphans: dict[str, int]) -> str:
    lines = [
        "# Routing coverage",
        "",
        f"Generated: `{artifact.provenance['generated_at']}`",
        "",
        "## Layer rollup",
        "",
        "| layer | present |",
        "| --- | --- |",
        f"| domain | {len(SEMANTIC_DOMAINS)} |",
        f"| system_capability | {len(SYSTEM_CAPABILITIES)} |",
        f"| tool | {artifact.summary['nodes_by_kind'].get('tool', 0)} |",
        f"| skill | {artifact.summary['nodes_by_kind'].get('skill', 0)} |",
        "",
        "## Orphans (no edges)",
        "",
        "| kind | count |",
        "| --- | --- |",
    ]
    for k in sorted(orphans):
        lines.append(f"| {k} | {orphans[k]} |")
    if not orphans:
        lines.append("| (none) | 0 |")
    return "\n".join(lines)
