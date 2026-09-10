from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.policy.action_policy import evaluate_action


@tool
def action_policy_evaluate(action: str, payload: dict | None = None) -> dict:
    """Evaluasi mode auto, approval, atau manual untuk sebuah aksi OS."""
    decision = evaluate_action(action, payload)
    return {
        "action": decision.action,
        "risk": decision.risk.value,
        "mode": decision.mode.value,
        "allowed": decision.allowed,
        "requires_approval": decision.requires_approval,
        "reason": decision.reason,
        "action_hash": decision.action_hash,
    }


POLICY_TOOLS = [action_policy_evaluate]
