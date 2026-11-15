from __future__ import annotations

import time
from typing import Any

from xninetzy.context.routing.laya import invoke_laya
from xninetzy.context.routing.state import RouterLayerDecision, StateSnapshot, build_state_snapshot
from xninetzy.context.registry.taxonomy import SEMANTIC_DOMAINS


MAX_OPTIONS_BY_LAYER: dict[str, int] = {
    "L2_domain": 20,
    "L3_skill": 25,
    "L4_task": 20,
    "L5_tool": 25,
}


def _bounded_menu(menu: list[dict[str, Any]], layer: str) -> list[dict[str, Any]]:
    cap = MAX_OPTIONS_BY_LAYER.get(layer, 20)
    if len(menu) <= cap:
        return menu
    return list(menu[:cap])


def _make_decision(
    *,
    layer: str,
    query: str,
    selected: list[str],
    confidence: dict[str, float],
    reason_codes: list[str],
    latency_ms: float,
    abstained: bool,
    metadata: dict[str, Any],
    laya_decision=None,
    shortlist_size: int = 0,
) -> RouterLayerDecision:
    return RouterLayerDecision(
        layer=layer,
        query=query,
        selected=tuple(selected),
        confidence=confidence,
        reason_codes=tuple(reason_codes),
        abstained=abstained,
        latency_ms=latency_ms,
        laya_decision=laya_decision,
        shortlist_size=shortlist_size,
        metadata=metadata,
    )


def route_domain(query: str, *, state: StateSnapshot | None = None, top_n: int = 3) -> RouterLayerDecision:
    t0 = time.perf_counter()
    menu = [{"name": d, "description": ""} for d in SEMANTIC_DOMAINS]
    bounded = _bounded_menu(menu, "L2_domain")
    decision = invoke_laya(layer="L2_domain", query=query, menu=bounded)
    latency = (time.perf_counter() - t0) * 1000.0
    selected = list(decision.selected)[:top_n] if not decision.abstained else []
    return _make_decision(
        layer="L2_domain",
        query=query,
        selected=selected,
        confidence=decision.calibrated_probabilities or decision.raw_probabilities,
        reason_codes=list(decision.reason_codes) + ["l2_domain"],
        latency_ms=latency,
        abstained=decision.abstained or not selected,
        metadata={"menu_size": len(bounded), "raw": decision.metadata.get("raw")},
        laya_decision=decision,
        shortlist_size=len(bounded),
    )


def route_task(query: str, *, domain_set: tuple[str, ...] = (), state: StateSnapshot | None = None) -> RouterLayerDecision:
    t0 = time.perf_counter()
    menu = [
        {"name": f, "verb": f, "description": ""}
        for f in (
            "find",
            "summarize",
            "create",
            "render",
            "execute",
            "review",
            "audit",
            "submit",
            "track",
            "compare",
            "analyze",
            "search",
        )
    ]
    decision = invoke_laya(layer="L4_task", query=query, menu=menu)
    latency = (time.perf_counter() - t0) * 1000.0
    if decision.metadata:
        raw = decision.metadata.get("raw") or {}
        task = raw.get("task") if isinstance(raw, dict) else None
    else:
        task = None
    selected = [task] if isinstance(task, str) and task else list(decision.selected)[:1]
    return _make_decision(
        layer="L4_task",
        query=query,
        selected=selected or ["execute"],
        confidence=decision.calibrated_probabilities or decision.raw_probabilities,
        reason_codes=list(decision.reason_codes) + ["l4_task"],
        latency_ms=latency,
        abstained=decision.abstained and not selected,
        metadata={"domain_set": list(domain_set)},
        laya_decision=decision,
        shortlist_size=len(menu),
    )


def route_capability(query: str, *, skill_set: tuple[str, ...] = (), domain_set: tuple[str, ...] = ()) -> RouterLayerDecision:
    capabilities = (
        "search",
        "retrieve",
        "compare",
        "extract",
        "analyze",
        "generate",
        "edit",
        "capture",
        "render",
        "publish",
        "validate",
        "monitor",
        "schedule",
        "authenticate",
        "inspect",
    )
    t0 = time.perf_counter()
    menu = [{"name": c} for c in capabilities]
    decision = invoke_laya(layer="L4_task", query=query, menu=menu)
    latency = (time.perf_counter() - t0) * 1000.0
    selected = list(decision.selected)[:3]
    return _make_decision(
        layer="L5_capability",
        query=query,
        selected=selected,
        confidence=decision.calibrated_probabilities or decision.raw_probabilities,
        reason_codes=list(decision.reason_codes) + ["l5_capability"],
        latency_ms=latency,
        abstained=decision.abstained and not selected,
        metadata={"skill_set_size": len(skill_set), "domain_set_size": len(domain_set)},
        laya_decision=decision,
        shortlist_size=len(menu),
    )


def route_skill(query: str, *, domain_set: tuple[str, ...] = (), candidate_skills: tuple[str, ...] = ()) -> RouterLayerDecision:
    from xninetzy.skills.registry import discover_skills

    all_skills = candidate_skills or tuple(sorted(discover_skills().keys()))
    t0 = time.perf_counter()
    menu = [{"name": s} for s in all_skills]
    bounded = _bounded_menu(menu, "L3_skill")
    decision = invoke_laya(layer="L3_skill", query=query, menu=bounded)
    latency = (time.perf_counter() - t0) * 1000.0
    selected = list(decision.selected)[:3] if not decision.abstained else []
    return _make_decision(
        layer="L3_skill",
        query=query,
        selected=selected,
        confidence=decision.calibrated_probabilities or decision.raw_probabilities,
        reason_codes=list(decision.reason_codes) + ["l3_skill"],
        latency_ms=latency,
        abstained=decision.abstained or not selected,
        metadata={"candidate_pool": len(bounded)},
        laya_decision=decision,
        shortlist_size=len(bounded),
    )


def route_tool(
    query: str,
    *,
    capability_set: tuple[str, ...] = (),
    candidate_tools: tuple[str, ...] = (),
    top_k: int = 20,
) -> RouterLayerDecision:
    pool = list(candidate_tools) if candidate_tools else []
    bounded = pool[: top_k]
    t0 = time.perf_counter()
    menu = [{"name": t} for t in bounded]
    decision = invoke_laya(layer="L5_tool", query=query, menu=menu)
    latency = (time.perf_counter() - t0) * 1000.0
    selected: list[str] = []
    for item in decision.metadata.get("raw", {}).get("ranking", []) if isinstance(decision.metadata.get("raw"), dict) else []:
        if isinstance(item, dict):
            n = item.get("name")
            if isinstance(n, str):
                selected.append(n)
    if not selected:
        selected = list(decision.selected)[:top_k]
    return _make_decision(
        layer="L5_tool",
        query=query,
        selected=selected[:top_k],
        confidence=decision.calibrated_probabilities or decision.raw_probabilities,
        reason_codes=list(decision.reason_codes) + ["l5_tool"],
        latency_ms=latency,
        abstained=decision.abstained and not selected,
        metadata={"capability_count": len(capability_set), "candidate_pool": len(bounded)},
        laya_decision=decision,
        shortlist_size=len(bounded),
    )


def build_state_snapshot_for(chat_id: str = "", owner: str = "") -> StateSnapshot:
    return build_state_snapshot(chat_id=chat_id, owner_hash=owner)
