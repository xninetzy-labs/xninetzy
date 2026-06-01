from __future__ import annotations

from typing import Any


async def skill_result_processor_node(state: dict[str, Any]) -> dict[str, Any]:
    result = state.get("skill_result") or {}
    if result.get("user_facing_text"):
        state["draft_response"] = result["user_facing_text"]
    return state
