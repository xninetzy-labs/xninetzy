from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from xninetzy.context.routing.abstention import decide_abstention
from xninetzy.context.routing.calibration import apply_calibration
from xninetzy.context.routing.calibration import CalibrationRegistry
from xninetzy.context.routing.lazy_schema import materialize_schemas
from xninetzy.context.routing.policy import evaluate_routing_policy
from xninetzy.context.routing.routers import (
    route_capability,
    route_domain,
    route_skill,
    route_task,
    route_tool,
)
from xninetzy.context.routing.state import StateSnapshot, build_state_snapshot
from xninetzy.tools.registry import get_tool_names

PIPELINE_VERSION = "1.0.0"
_TOKEN_RE = re.compile(r"[a-z_]+")


@dataclass(frozen=True, slots=True)
class NormalizedRequest:
    request_id: str
    text: str
    language: str = "en"
    language_mode: str = "natural"
    entities: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    desired_output: str = ""


def normalize_request(query: str, *, request_id: str | None = None) -> NormalizedRequest:
    rid = request_id or f"r-{abs(hash(query)) % 10**9}"
    text = (query or "").strip()[:4000]
    lowered = text.lower()
    entities = tuple(sorted(set(_TOKEN_RE.findall(lowered))))[:32]
    has_negation = any(t in lowered for t in ("not ", "don't ", "without ", "only "))
    return NormalizedRequest(
        request_id=rid,
        text=text,
        language="en" if any(c in "abcdefghijklmnopqrstuvwxyz" for c in lowered) else "id",
        language_mode="natural",
        entities=entities,
        constraints=("has_negation",) if has_negation else (),
        desired_output="tool-call",
    )


@dataclass(frozen=True, slots=True)
class PipelineOutcome:
    request_id: str
    normalized: NormalizedRequest
    domain_decision: Any
    skill_decision: Any
    task_decision: Any
    capability_decision: Any
    tool_decision: Any
    policy: Any
    schema_bundle: Any | None
    selected_tool: str
    ablated: bool
    reason_codes: tuple[str, ...] = ()
    timestamp: str = ""
    total_latency_ms: float = 0.0


def run_pipeline(
    query: str,
    *,
    request_id: str | None = None,
    state: StateSnapshot | None = None,
    approval_id: int | None = None,
    idempotency_key: str | None = None,
    calibration_dir: str = "data/routing_calibration",
    persist: bool = True,
) -> PipelineOutcome:
    t0 = time.perf_counter()
    normalized = normalize_request(query, request_id=request_id)
    if state is None:
        state = build_state_snapshot()
    domain_decision = route_domain(normalized.text, state=state)
    skill_decision = route_skill(
        normalized.text,
        domain_set=tuple(domain_decision.selected) if not domain_decision.abstained else (),
    )
    task_decision = route_task(normalized.text)
    capability_decision = route_capability(normalized.text)
    candidates_pool = tuple(t for t in get_tool_names() if not t.startswith("_"))[:200]
    tool_decision = route_tool(
        normalized.text,
        capability_set=tuple(capability_decision.selected) if not capability_decision.abstained else (),
        candidate_tools=candidates_pool,
    )

    cal_registry = CalibrationRegistry(storage_dir=calibration_dir)
    cal_record = cal_registry.lookup("L5_tool", "general") or cal_registry.lookup("L5_tool", "research")
    if cal_record is not None:
        calibrated = apply_calibration(tool_decision.confidence, cal_record.coefficients)
    else:
        calibrated = dict(tool_decision.confidence)

    abstention = decide_abstention(
        confidence=calibrated,
        top_k=5,
        historical_abstention_rate=0.10,
        min_abstention_rate=0.05,
        max_abstention_rate=0.25,
    )
    if abstention.should_abstain and abstention.selected:
        tool_decision = type(tool_decision)(
            layer=tool_decision.layer,
            query=tool_decision.query,
            selected=abstention.selected,
            confidence=tool_decision.confidence,
            reason_codes=tuple(list(tool_decision.reason_codes) + list(abstention.reason_codes)),
            abstained=False,
            latency_ms=tool_decision.latency_ms,
            laya_decision=tool_decision.laya_decision,
            shortlist_size=tool_decision.shortlist_size,
            metadata={**tool_decision.metadata, "abstention": abstention.reason_codes},
        )
    elif abstention.should_abstain:
        tool_decision = type(tool_decision)(
            layer=tool_decision.layer,
            query=tool_decision.query,
            selected=(),
            confidence=tool_decision.confidence,
            reason_codes=tuple(list(tool_decision.reason_codes) + list(abstention.reason_codes)),
            abstained=True,
            latency_ms=tool_decision.latency_ms,
            laya_decision=tool_decision.laya_decision,
            shortlist_size=tool_decision.shortlist_size,
            metadata={**tool_decision.metadata, "abstention": abstention.reason_codes},
        )

    final_tool = (
        tool_decision.selected[0]
        if tool_decision.selected
        else (candidates_pool[0] if candidates_pool else "knowledge_search")
    )
    policy_result = evaluate_routing_policy(
        final_tool,
        approval_id=approval_id,
        idempotency_key=idempotency_key,
    )
    schema_bundle = materialize_schemas(
        final_tool,
        alternates=tuple(tool_decision.selected[1:6]),
    )

    latency = (time.perf_counter() - t0) * 1000.0
    ablated = policy_result.decision.outcome in ("block", "require_approval") and not approval_id
    now = datetime.now(UTC).isoformat()
    outcome = PipelineOutcome(
        request_id=normalized.request_id,
        normalized=normalized,
        domain_decision=domain_decision,
        skill_decision=skill_decision,
        task_decision=task_decision,
        capability_decision=capability_decision,
        tool_decision=tool_decision,
        policy=policy_result,
        schema_bundle=schema_bundle,
        selected_tool=final_tool,
        ablated=ablated,
        reason_codes=(
            "pipeline_run_ok",
            f"policy_{policy_result.decision.outcome}",
            f"tool_routing_{'ok' if not tool_decision.abstained else 'abstain'}",
        ) + tuple(
            f"abstention_{code}" for code in abstention.reason_codes
        ),
        timestamp=now,
        total_latency_ms=latency,
    )
    if persist:
        _persist(outcome)
    return outcome


def _persist(outcome: PipelineOutcome) -> None:
    try:
        root = Path("data/routing_runs")
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{outcome.request_id}.json"
        path.write_text(
            json.dumps(_serialize(outcome), ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


def _serialize(outcome: PipelineOutcome) -> dict[str, Any]:
    payload = {
        "version": PIPELINE_VERSION,
        "request_id": outcome.request_id,
        "timestamp": outcome.timestamp,
        "selected_tool": outcome.selected_tool,
        "ablated": outcome.ablated,
        "total_latency_ms": round(outcome.total_latency_ms, 3),
        "reason_codes": list(outcome.reason_codes),
        "normalized": asdict(outcome.normalized),
        "policy_outcome": outcome.policy.decision.outcome if outcome.policy else None,
        "policy_reason": outcome.policy.decision.reason if outcome.policy else None,
        "tool_selected": list(outcome.tool_decision.selected[:5]),
        "tool_shortlist_size": outcome.tool_decision.shortlist_size,
        "schema_total_bytes": outcome.schema_bundle.total_bytes if outcome.schema_bundle else 0,
        "domain_selected": list(outcome.domain_decision.selected[:3]),
    }
    return payload


def load_pipeline_outcome(request_id: str) -> dict[str, Any] | None:
    path = Path("data/routing_runs") / f"{request_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
