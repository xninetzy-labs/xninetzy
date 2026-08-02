from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.tools.manifest import manifest_for


@tool
def tool_catalog(feature_pack: str = "", risk: str = "", limit: int = 250) -> list[dict]:
    """List shared Xninetzy tool metadata for routing and operator inspection."""
    from app.xninetzy.tools.registry import get_all_tools

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
