from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from xninetzy.tools.manifest import manifest_for
from xninetzy.tools.registry import get_all_tools, get_tool_groups


TAG_BY_GROUP = {
    "core": "core",
    "os_kernel": "os",
    "policy": "policy",
    "ai_runtime": "ai",
    "it_learning": "learning",
    "knowledge": "knowledge",
    "unified_search": "search",
    "pixelrag": "visual",
    "web_intelligence": "web",
    "repo": "repo",
    "research": "research",
    "graph": "graph",
    "skills": "skills",
    "notes": "obsidian",
    "academic": "academic",
    "lightning": "rl",
    "life": "life",
    "reminders": "reminders",
    "media": "media",
    "documentation": "docs",
}


def _annotations_for(risk: str, requires_approval: bool) -> dict[str, Any]:
    hints: dict[str, Any] = {
        "readOnlyHint": risk == "read",
        "destructiveHint": risk in {"write", "final"},
        "idempotentHint": risk != "final",
        "openWorldHint": False,
    }
    if requires_approval:
        hints["title"] = "requires approval"
    return hints


def meta_for(name: str) -> dict[str, Any]:
    manifest = manifest_for(name)
    groups = get_tool_groups()
    tags: list[str] = []
    if name.startswith(("hebat_", "portal_", "qa_", "uacc_")):
        tags.append(TAG_BY_GROUP["academic"])
    for group, members in groups.items():
        if name in members:
            tag = TAG_BY_GROUP.get(group)
            if tag and tag not in tags:
                tags.append(tag)
    if not tags:
        for prefix, tag in (
            ("memory_", "memory"),
            ("lightning_", "rl"),
            ("graph_", "graph"),
            ("workflow_", "workflow"),
            ("workflow_internal_", "workflow"),
            ("web_", "web"),
            ("obsidian_", "obsidian"),
            ("research_", "research"),
            ("knowledge_", "knowledge"),
            ("deep_research_", "research"),
            ("youTube_", "research"),
            ("youtube_", "research"),
            ("document_", "knowledge"),
            ("unified_", "search"),
            ("hebat_", "academic"),
            ("portal_", "academic"),
            ("qa_", "academic"),
            ("uacc_", "academic"),
            ("task_", "life"),
            ("habit_", "life"),
            ("workout_", "life"),
            ("money_", "life"),
            ("daily_", "life"),
            ("goal_", "life"),
            ("life_", "life"),
            ("reminder_", "reminders"),
            ("ai_provider_", "ai"),
            ("coding_agent_", "ai"),
            ("rule_", "rules"),
            ("rules_", "rules"),
            ("style_", "style"),
            ("learning_", "learning"),
            ("hitl_", "hitl"),
            ("action_", "policy"),
            ("os_", "os"),
            ("idea_", "planning"),
            ("generate_", "planning"),
            ("draft_", "planning"),
            ("task_breakdown", "planning"),
            ("skill_discovery", "planning"),
            ("admin_", "admin"),
            ("skill_", "skills"),
            ("helper_", "helper"),
            ("pixelrag_", "visual"),
            ("web_", "web"),
            ("repo_", "repo"),
            ("adr_", "docs"),
            ("implementation_record", "docs"),
            ("security_finding_record", "docs"),
            ("learning_record", "docs"),
            ("calculate", "core"),
            ("datetime", "core"),
            ("tool_catalog", "meta"),
            ("calculate_percentage", "core"),
        ):
            if name.startswith(prefix):
                if tag not in tags:
                    tags.append(tag)
                break
    annotations = _annotations_for(manifest.risk.value, manifest.requires_approval)
    return {
        "tags": tags,
        "annotations": annotations,
        "feature_pack": manifest.feature_pack.value,
        "risk": manifest.risk.value,
        "stability": manifest.stability.value,
        "requires_approval": manifest.requires_approval,
        "requires_idempotency": manifest.requires_idempotency,
        "requires_evidence": manifest.requires_evidence,
        "version": "2.2.0",
    }


def catalog_metadata() -> dict[str, dict[str, Any]]:
    """Return metadata for every registered tool, keyed by tool name."""
    return {tool.name: meta_for(tool.name) for tool in get_all_tools()}


def write_catalog_json(path: str | Path) -> Path:
    """Dump full tool catalog metadata to a JSON file for client-side filtering."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(catalog_metadata(), indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return target
