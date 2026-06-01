from __future__ import annotations

from typing import Any

from app.skills.router import route_skill


async def skill_router_node(state: dict[str, Any]) -> dict[str, Any]:
    route = route_skill(str(state.get("normalized_text") or state.get("raw_message") or ""))
    state.update(route.model_dump())
    return state
