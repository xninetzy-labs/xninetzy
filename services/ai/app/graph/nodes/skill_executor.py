from __future__ import annotations

from typing import Any

from app.skills.base import SkillInput
from app.skills.executor import execute_skill


async def skill_executor_node(state: dict[str, Any]) -> dict[str, Any]:
    if not state.get("needs_skill") or not state.get("skill_name"):
        return state

    output = await execute_skill(
        str(state["skill_name"]),
        SkillInput(
            chat_id=str(state.get("chat_id") or "unknown"),
            sender_id=state.get("sender_id"),
            message=str(state.get("normalized_text") or state.get("raw_message") or ""),
            metadata=state.get("skill_args") or {},
        ),
        action=state.get("skill_action"),
    )
    state["skill_result"] = output.model_dump()
    state.setdefault("skill_results", []).append(output.model_dump())
    return state
