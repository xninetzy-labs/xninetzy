from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from xninetzy.context.reasoning.critic import (
    CRITIC_SEVERITY_BLOCKER,
    CRITIC_VERDICT_FAIL,
    CRITIC_VERDICT_PASS,
    CRITIC_VERDICT_WARN,
    CriticVerdict,
    critique_outcome,
)
from xninetzy.context.reasoning.depth import (
    REASONING_DEPTH_COMPLEX,
    REASONING_DEPTH_HIGH_RISK,
    REASONING_DEPTH_ROUTINE,
    REASONING_DEPTH_TRIVIAL,
    ReasoningDepth,
    classify_request_depth,
    get_depth,
)
from xninetzy.context.reasoning.stop import (
    STOP_CONTINUE,
    STOP_HALT,
    STOP_REPLAN,
    StopDecision,
    should_stop,
)


_STRATEGY_STATE: dict[str, dict[str, Any]] = {}


def _coerce_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    if isinstance(value, str):
        if not value:
            return ()
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (list, tuple)):
                return tuple(str(v) for v in parsed)
        except (ValueError, TypeError):
            pass
        return tuple(part.strip() for part in value.split(",") if part.strip())
    return (str(value),)


@tool
def reasoning_classify_depth(
    side_effect: str | None,
    trust_tier: int | None = None,
    irreversible: bool | None = None,
    high_value: bool | None = None,
    multi_domain: bool | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    """Classify reasoning depth for a request.

    Args:
        side_effect: side_effect class name (read_only, idempotent_write,
            non_idempotent_write, external, irreversible)
        trust_tier: numeric trust tier (0=local, 1=known_external,
            2=third_party, 3=unverified, 4=blocked)
        irreversible: explicit override flag
        high_value: high-value/financial/security flag
        multi_domain: spans multiple domains flag
        hint: explicit depth hint (trivial|routine|complex|high_risk)

    Returns:
        Depth descriptor with name, rank, budgets, and required flags.
    """
    depth: ReasoningDepth = classify_request_depth(
        side_effect=side_effect,
        trust_tier=trust_tier,
        irreversible=irreversible,
        high_value=high_value,
        multi_domain=multi_domain,
        hint=hint,
    )
    return depth.to_dict()


@tool
def reasoning_get_depth(name: str) -> dict[str, Any]:
    """Return a depth descriptor by name.

    Args:
        name: depth name (trivial|routine|complex|high_risk)

    Returns:
        Depth descriptor with name, rank, budgets, required flags.
    """
    return get_depth(name).to_dict()


@tool
def reasoning_list_depths() -> list[dict[str, Any]]:
    """Return all registered reasoning depth descriptors.

    Returns:
        List of depth descriptors.
    """
    return [get_depth(name).to_dict() for name in (
        REASONING_DEPTH_TRIVIAL,
        REASONING_DEPTH_ROUTINE,
        REASONING_DEPTH_COMPLEX,
        REASONING_DEPTH_HIGH_RISK,
    )]


@tool
def reasoning_critique(
    expected: str | None,
    actual: str | None,
    claims: str | tuple[str, ...] | list[str] | None = None,
    evidence_ids: str | tuple[str, ...] | list[str] | None = None,
    missing_evidence_codes: str | tuple[str, ...] | list[str] | None = None,
    contradictions: str | tuple[str, ...] | list[str] | None = None,
    notes: str | tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """Run a critic pass on a reasoning outcome.

    Args:
        expected: expected outcome string
        actual: actual outcome string
        claims: comma-separated string or tuple/list of claims to inspect
        evidence_ids: comma-separated string or tuple/list of evidence ids
        missing_evidence_codes: comma-separated string or tuple/list of
            required evidence codes that were missing
        contradictions: comma-separated string or tuple/list of contradictions
        notes: comma-separated string or tuple/list of notes

    Returns:
        Verdict with defects and checked claims.
    """
    verdict: CriticVerdict = critique_outcome(
        expected=expected,
        actual=actual,
        claims=_coerce_str_tuple(claims),
        evidence_ids=_coerce_str_tuple(evidence_ids),
        missing_evidence_codes=_coerce_str_tuple(missing_evidence_codes),
        contradictions=_coerce_str_tuple(contradictions),
        notes=_coerce_str_tuple(notes),
    )
    return verdict.to_dict()


@tool
def reasoning_should_stop(
    iteration: int,
    history_json: str | None = None,
    success_criteria_met: bool = False,
    critical_uncertainty: float = 0.0,
    min_iterations: int = 1,
    max_iterations: int = 8,
    anti_loop_window: int = 4,
    force_replan: bool = False,
) -> dict[str, Any]:
    """Decide whether to continue, halt, or replan a reasoning loop.

    Args:
        iteration: current iteration number (0-based)
        history_json: JSON-encoded list of {hypothesis,tool,outcome} dicts
        success_criteria_met: whether success criteria are satisfied
        critical_uncertainty: 0..1, how unresolved critical uncertainty is
        min_iterations: minimum iterations before halting on success
        max_iterations: iteration ceiling
        anti_loop_window: window size for anti-loop detection
        force_replan: explicit replan override

    Returns:
        Stop decision with reason and anti-loop signal if any.
    """
    history: tuple[dict[str, Any], ...] = ()
    if history_json:
        try:
            parsed = json.loads(history_json)
            if isinstance(parsed, list):
                history = tuple(
                    {str(k): v for k, v in step.items()}
                    for step in parsed
                    if isinstance(step, dict)
                )
        except (ValueError, TypeError):
            history = ()
    decision: StopDecision = should_stop(
        iteration=iteration,
        steps=history,
        success_criteria_met=success_criteria_met,
        critical_uncertainty=critical_uncertainty,
        min_iterations=min_iterations,
        max_iterations=max_iterations,
        anti_loop_window=anti_loop_window,
        force_replan=force_replan,
    )
    return decision.to_dict()


@tool
def reasoning_record_history(
    context_key: str,
    request_id: str,
    hypothesis: str,
    tool: str,
    outcome: str,
) -> dict[str, Any]:
    """Append a step to the in-memory reasoning history for a context.

    Args:
        context_key: context/session key
        request_id: request id
        hypothesis: hypothesis text or identifier
        tool: tool/provider used
        outcome: observed outcome

    Returns:
        Updated history length.
    """
    state = _STRATEGY_STATE.setdefault(
        context_key,
        {"history": [], "request_id": request_id, "depth": None},
    )
    state["request_id"] = request_id
    state["history"].append(
        {"hypothesis": hypothesis, "tool": tool, "outcome": outcome}
    )
    return {
        "context_key": context_key,
        "request_id": request_id,
        "history_len": len(state["history"]),
    }


@tool
def reasoning_set_strategy(
    context_key: str,
    depth: str,
    min_iterations: int = 1,
    max_iterations: int = 8,
    anti_loop_window: int = 4,
) -> dict[str, Any]:
    """Set the reasoning strategy for a context.

    Args:
        context_key: context/session key
        depth: depth name (trivial|routine|complex|high_risk)
        min_iterations: minimum iterations before halt on success
        max_iterations: iteration ceiling
        anti_loop_window: anti-loop fingerprint window

    Returns:
        Strategy descriptor.
    """
    depth_obj = get_depth(depth)
    _STRATEGY_STATE[context_key] = {
        "depth": depth_obj.name,
        "min_iterations": int(min_iterations),
        "max_iterations": int(max_iterations),
        "anti_loop_window": int(anti_loop_window),
        "history": _STRATEGY_STATE.get(context_key, {}).get("history", []),
    }
    return {
        "context_key": context_key,
        "depth": depth_obj.name,
        "min_iterations": int(min_iterations),
        "max_iterations": int(max_iterations),
        "anti_loop_window": int(anti_loop_window),
    }


@tool
def reasoning_get_strategy(context_key: str) -> dict[str, Any]:
    """Get the current reasoning strategy for a context.

    Args:
        context_key: context/session key

    Returns:
        Strategy descriptor or empty dict if unset.
    """
    state = _STRATEGY_STATE.get(context_key)
    if state is None:
        return {"context_key": context_key, "depth": None}
    return {
        "context_key": context_key,
        "depth": state.get("depth"),
        "min_iterations": state.get("min_iterations"),
        "max_iterations": state.get("max_iterations"),
        "anti_loop_window": state.get("anti_loop_window"),
        "history_len": len(state.get("history", [])),
    }


@tool
def reasoning_clear_strategy(context_key: str) -> dict[str, Any]:
    """Clear the reasoning strategy for a context.

    Args:
        context_key: context/session key

    Returns:
        Confirmation dict.
    """
    _STRATEGY_STATE.pop(context_key, None)
    return {"context_key": context_key, "cleared": True}


@tool
def reasoning_trace(
    context_key: str,
    last_n: int = 10,
) -> dict[str, Any]:
    """Return the recent reasoning history for a context.

    Args:
        context_key: context/session key
        last_n: maximum number of steps to return

    Returns:
        History list and summary counters.
    """
    state = _STRATEGY_STATE.get(context_key, {})
    history = list(state.get("history", []))
    recent = history[-max(0, int(last_n)):]
    tools: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    for step in history:
        tool_name = str(step.get("tool", ""))
        outcome = str(step.get("outcome", ""))
        tools[tool_name] = tools.get(tool_name, 0) + 1
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    return {
        "context_key": context_key,
        "depth": state.get("depth"),
        "history": recent,
        "total_steps": len(history),
        "tool_counts": tools,
        "outcome_counts": outcomes,
    }


__all__ = [
    "CRITIC_SEVERITY_BLOCKER",
    "CRITIC_VERDICT_FAIL",
    "CRITIC_VERDICT_PASS",
    "CRITIC_VERDICT_WARN",
    "REASONING_DEPTH_COMPLEX",
    "REASONING_DEPTH_HIGH_RISK",
    "REASONING_DEPTH_ROUTINE",
    "REASONING_DEPTH_TRIVIAL",
    "STOP_CONTINUE",
    "STOP_HALT",
    "STOP_REPLAN",
    "reasoning_classify_depth",
    "reasoning_clear_strategy",
    "reasoning_critique",
    "reasoning_get_depth",
    "reasoning_get_strategy",
    "reasoning_list_depths",
    "reasoning_record_history",
    "reasoning_set_strategy",
    "reasoning_should_stop",
    "reasoning_trace",
]
