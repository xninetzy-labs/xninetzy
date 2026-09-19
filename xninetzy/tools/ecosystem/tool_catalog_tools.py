from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.tools.manifest import manifest_for


@tool
def tool_catalog(feature_pack: str = "", risk: str = "", limit: int = 250) -> list[dict]:
    """List shared Xninetzy tool metadata for routing and operator inspection."""
    from xninetzy.tools.registry import get_all_tools

    bounded_limit = max(1, min(limit, 500))
    normalized_pack = feature_pack.strip().lower()
    normalized_risk = risk.strip().lower()
    results: list[dict] = []
    for current in get_all_tools():
        manifest = manifest_for(current.name)
        if normalized_pack and manifest.feature_pack.value != normalized_pack:
            continue
        if normalized_risk and manifest.risk.value != normalized_risk:
            continue
        item = manifest.as_dict()
        item["description"] = (current.description or "").split("\n", 1)[0]
        results.append(item)
        if len(results) >= bounded_limit:
            break
    return results


@tool
def tool_rank(query: str, feature_pack: str = "", risk: str = "", limit: int = 25) -> list[dict]:
    """Rank tools for a query using the same keyword+bandit scorer as harness_router."""
    from xninetzy.tools.ecosystem.harness_router_tools import _score_tools
    from xninetzy.tools.registry import get_all_tools

    bounded_limit = max(1, min(limit, 200))
    normalized_pack = feature_pack.strip().lower()
    normalized_risk = risk.strip().lower()
    pool: list[str] = []
    manifests: dict[str, dict] = {}
    for current in get_all_tools():
        manifest = manifest_for(current.name)
        if normalized_pack and manifest.feature_pack.value != normalized_pack:
            continue
        if normalized_risk and manifest.risk.value != normalized_risk:
            continue
        pool.append(current.name)
        manifests[current.name] = manifest.as_dict()
    scored = _score_tools(query, pool, {})
    scored = scored[:bounded_limit]
    out: list[dict] = []
    for item in scored:
        row = dict(manifests.get(item["tool_name"], {}))
        row["tool_name"] = item["tool_name"]
        row["score"] = item["score"]
        if "bandit_score" in item:
            row["bandit_score"] = item["bandit_score"]
        out.append(row)
    return out
