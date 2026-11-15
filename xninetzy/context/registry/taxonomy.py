from __future__ import annotations

from typing import Any

SEMANTIC_DOMAINS: tuple[str, ...] = (
    "learning",
    "academic",
    "research",
    "knowledge",
    "career",
    "software",
    "data",
    "security",
    "browser",
    "files",
    "os",
    "automation",
    "communication",
    "media",
    "productivity",
    "integrations",
)

SYSTEM_CAPABILITIES: tuple[str, ...] = (
    "routing",
    "policy",
    "state",
    "memory",
    "telemetry",
    "tasks",
    "artifacts",
    "cache",
    "improvement",
    "lightning",
    "harness",
    "retrieval",
    "graph",
    "evaluation",
    "scheduling",
    "verification",
)

_ALIAS_TO_CANONICAL: dict[str, str] = {
    "xninetzy_core": "learning",
    "xninetzy-it-learning": "learning",
    "xninetzy_it_learning": "learning",
    "it-learning": "learning",
    "it_learning": "learning",
    "it learning": "learning",
    "learning": "learning",
    "coding": "software",
    "programming": "software",
    "xninetzy_obsidian": "integrations.obsidian",
    "obsidian": "integrations.obsidian",
    "os_kernel": "knowledge",
    "unified_search": "knowledge",
    "web_intelligence": "browser",
    "graph": "knowledge",
    "management": "os",
    "life": "os",
    "reminders": "os",
    "academic": "academic",
    "career": "career",
    "research": "research",
    "knowledge": "knowledge",
    "security": "security",
    "media": "media",
    "repo": "software",
    "notes": "integrations.obsidian",
    "career_acquisition": "career",
    "dream": "career",
    "harness": "automation",
    "dashboard": "data",
    "datasets": "data",
    "nvd": "security",
    "documents": "files",
    "video": "media",
    "pptx": "media",
}

_LEGACY_GROUP_TO_CANONICAL: dict[str, str] = {
    "performance": "software",
    "it_learning": "learning",
    "academic": "academic",
    "research": "research",
    "notes": "integrations.obsidian",
    "obsidian_ops": "integrations.obsidian",
    "academic_acquisition": "academic",
    "academic_operations": "academic",
    "dream": "career",
    "documents": "files",
    "media": "media",
    "lightning": "lightning",
    "life": "os",
    "reminders": "os",
    "repo": "software",
    "datasets": "data",
    "document": "files",
    "vision": "browser",
    "career": "career",
    "security": "security",
    "web": "browser",
    "doc": "files",
    "learning": "learning",
    "memory_lifecycle": "memory",
    "core": "routing",
    "policy": "policy",
    "os_kernel": "knowledge",
    "unified_search": "knowledge",
    "graph": "knowledge",
    "evaluator": "evaluation",
    "improvement": "improvement",
    "analytics": "data",
    "reasoning": "evaluation",
    "evaluation": "evaluation",
    "memory": "memory",
    "rules": "policy",
    "style": "policy",
    "planning": "automation",
    "process_engineering": "automation",
    "process": "automation",
    "harness": "automation",
    "skill_routing": "routing",
    "helper": "routing",
    "tool_results": "routing",
    "tool_meta": "routing",
    "ai_runtime": "routing",
    "internal": "routing",
    "skill": "routing",
    "tools_internal": "routing",
    "skill_management": "routing",
    "skills_runtime": "routing",
    "cache": "cache",
    "metrics": "telemetry",
    "telemetry": "telemetry",
    "observability": "telemetry",
    "state": "state",
    "tasks": "tasks",
}

_INTENT_REGISTRY_DOMAIN_TO_CANONICAL: dict[str, str] = {
    "research": "research",
    "engineering": "software",
    "knowledge": "knowledge",
    "life": "os",
    "harness": "automation",
    "improvement": "improvement",
    "observability": "telemetry",
    "vision": "browser",
    "security": "security",
}

_SKILL_NAME_PREFIX_TO_CANONICAL: tuple[tuple[str, str], ...] = (
    ("xninetzy-hebat", "academic.hebat"),
    ("hebat-academic", "academic.hebat"),
    ("hebat", "academic.hebat"),
    ("xninetzy-cyber", "academic.cyber-campus"),
    ("cyber-campus", "academic.cyber-campus"),
    ("xninetzy-uacc", "academic.uacc"),
    ("xninetzy-research", "research"),
    ("xninetzy-deep-research", "research"),
    ("xninetzy-obsidian", "integrations.obsidian"),
    ("obsidian-knowledge", "integrations.obsidian"),
    ("xninetzy-os", "os"),
    ("xninetzy-memory", "memory"),
    ("xninetzy-assignment", "academic"),
    ("xninetzy-learning", "learning"),
    ("xninetzy-it-learning", "learning"),
    ("it-learning", "learning"),
    ("xninetzy-career", "career"),
    ("xninetzy-academic", "academic"),
    ("xninetzy-knowledge", "knowledge"),
    ("xninetzy-research-memory", "research"),
    ("xninetzy-krs", "academic.krs"),
    ("xninetzy_uacc", "academic.uacc"),
    ("xninetzy_cyber", "academic.cyber-campus"),
    ("xninetzy_hebat", "academic.hebat"),
    ("xninetzy_research", "research"),
    ("xninetzy_research_memory", "research"),
    ("xninetzy_assignment", "academic"),
    ("xninetzy_learning", "learning"),
    ("xninetzy_career", "career"),
    ("xninetzy_knowledge", "knowledge"),
    ("xninetzy_obsidian", "integrations.obsidian"),
    ("it_learning", "learning"),
    ("research", "research"),
    ("academic", "academic"),
    ("career", "career"),
    ("security", "security"),
    ("media", "media"),
    ("obsidian", "integrations.obsidian"),
    ("cyber-campus", "academic.cyber-campus"),
    ("uacc", "academic.uacc"),
    ("krs", "academic.krs"),
)


def resolve_alias(name: str) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    if key in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[key]
    if key in SEMANTIC_DOMAINS or key in SYSTEM_CAPABILITIES:
        return key
    for prefix, canonical in _SKILL_NAME_PREFIX_TO_CANONICAL:
        if key == prefix or key.startswith(prefix + "-"):
            return canonical
    return None


def legacy_group_to_canonical(group_name: str) -> str | None:
    if not group_name:
        return None
    key = group_name.strip().lower()
    if key in _LEGACY_GROUP_TO_CANONICAL:
        return _LEGACY_GROUP_TO_CANONICAL[key]
    if key in SEMANTIC_DOMAINS or key in SYSTEM_CAPABILITIES:
        return key
    candidates = [
        ("routing", key in {"core", "tools", "tools_internal", "skill", "tools_ecosystem", "ai_runtime", "helper", "skill_routing", "helper_tools", "skills"}),
        ("automation", key in {"harness", "process", "planning", "process_engineering"}),
        ("evaluation", key in {"evaluation", "metrics", "benchmark", "patterns"}),
        ("memory", key in {"memory", "memory_lifecycle"}),
        ("telemetry", key in {"telemetry", "observability"}),
        ("tasks", key in {"tasks"}),
        ("state", key in {"state"}),
        ("policy", key in {"policy", "rules", "style", "permissions"}),
        ("cache", key in {"cache", "retrieval"}),
        ("graph", key in {"graph", "graph_rag", "graph_v3"}),
        ("research", key in {"research", "web_evidence", "web_search", "research_tools", "research_v2", "research_storm", "storm"}),
        ("data", key in {"data", "analytics", "datasets"}),
        ("academic", key in {"academic", "documents", "doc"}),
        ("career", key in {"career", "career_ecosystem"}),
        ("media", key in {"media", "documents", "document"}),
        ("integrations", key in {"pixelrag", "web_intelligence"}),
        ("files", key in {"documentation", "docs"}),
    ]
    for canonical, cond in candidates:
        if cond:
            return canonical
    return None


def intent_domain_to_canonical(domain: str) -> str | None:
    if not domain:
        return None
    key = domain.strip().lower()
    if key in _INTENT_REGISTRY_DOMAIN_TO_CANONICAL:
        return _INTENT_REGISTRY_DOMAIN_TO_CANONICAL[key]
    return resolve_alias(key)


def build_cross_walk() -> dict[str, Any]:
    from xninetzy.tools.registry import get_tool_groups

    groups = get_tool_groups()
    legacy_groups_with_tools = sorted(name for name, members in groups.items() if members)
    legacy_groups_empty = sorted(name for name, members in groups.items() if not members)

    domain_distribution: dict[str, list[str]] = {d: [] for d in SEMANTIC_DOMAINS}
    system_distribution: dict[str, list[str]] = {s: [] for s in SYSTEM_CAPABILITIES}
    integration_distribution: dict[str, list[str]] = {}
    unmapped: list[str] = []

    for grp in legacy_groups_with_tools:
        canonical = legacy_group_to_canonical(grp)
        if canonical is None:
            unmapped.append(grp)
            continue
        if canonical in domain_distribution:
            domain_distribution[canonical].append(grp)
        elif canonical in system_distribution:
            system_distribution[canonical].append(grp)
        else:
            bucket, _, sub = canonical.partition(".")
            if canonical.startswith("integrations.") and sub:
                integration_distribution.setdefault(sub, []).append(grp)
            else:
                unmapped.append(grp)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": "1.0.0",
        "registry_version": "1.0.0",
        "generated_at": None,
        "semantic_domains": list(SEMANTIC_DOMAINS),
        "system_capabilities": list(SYSTEM_CAPABILITIES),
        "domains": domain_distribution,
        "system": system_distribution,
        "integrations": integration_distribution,
        "empty_legacy_groups": legacy_groups_empty,
        "unmapped_legacy_groups": unmapped,
    }
