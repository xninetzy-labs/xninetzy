from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from xninetzy.context.process_engineering.model import (
    NODE_KIND_END,
    NODE_KIND_START,
    ProcessModel,
)


SIM_OUTCOME_OK: str = "ok"
SIM_OUTCOME_INFEASIBLE: str = "infeasible"


@dataclass(frozen=True, slots=True)
class ResourcePool:
    name: str
    capacity: int

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "capacity": self.capacity}


@dataclass(frozen=True, slots=True)
class ArrivalPattern:
    name: str
    interarrival_minutes: float
    count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "interarrival_minutes": self.interarrival_minutes,
            "count": self.count,
        }


@dataclass(frozen=True, slots=True)
class ActivityProfile:
    node_id: str
    duration_minutes: float
    required_resource: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "duration_minutes": self.duration_minutes,
            "required_resource": self.required_resource,
        }


@dataclass(frozen=True, slots=True)
class SimulationSpec:
    arrival: ArrivalPattern
    resources: tuple[ResourcePool, ...]
    activities: tuple[ActivityProfile, ...]
    seed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "arrival": self.arrival.to_dict(),
            "resources": [r.to_dict() for r in self.resources],
            "activities": [a.to_dict() for a in self.activities],
            "seed": self.seed,
        }


@dataclass(frozen=True, slots=True)
class ActivityStat:
    node_id: str
    started: int
    completed: int
    total_busy_minutes: float
    max_wait_minutes: float
    avg_wait_minutes: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "started": self.started,
            "completed": self.completed,
            "total_busy_minutes": round(self.total_busy_minutes, 4),
            "max_wait_minutes": round(self.max_wait_minutes, 4),
            "avg_wait_minutes": round(self.avg_wait_minutes, 4),
        }


@dataclass(frozen=True, slots=True)
class SimulationResult:
    outcome: str
    cases_completed: int
    makespan_minutes: float
    activity_stats: tuple[ActivityStat, ...]
    bottleneck_node: str | None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "cases_completed": self.cases_completed,
            "makespan_minutes": round(self.makespan_minutes, 4),
            "activity_stats": [s.to_dict() for s in self.activity_stats],
            "bottleneck_node": self.bottleneck_node,
            "notes": list(self.notes),
        }


def _linear_congruential(seed: int) -> "callable":
    state = [seed & 0xFFFFFFFF]

    def next_u01() -> float:
        state[0] = (state[0] * 1664525 + 1013904223) & 0xFFFFFFFF
        return state[0] / 0xFFFFFFFF

    return next_u01


def _node_sequence(model: ProcessModel) -> tuple[str, ...]:
    sequence: list[str] = []
    seen: set[str] = set()
    start_candidates = [
        node.definition.id
        for node in model.nodes
        if node.definition.kind == NODE_KIND_START
    ]
    if not start_candidates:
        return tuple(sequence)
    current: str | None = start_candidates[0]
    guard = 0
    node_index = {n.definition.id: n for n in model.nodes}
    while current is not None and guard < 1024:
        if current in seen:
            break
        seen.add(current)
        sequence.append(current)
        node = node_index.get(current)
        if node is None:
            break
        if node.definition.kind == NODE_KIND_END:
            break
        outgoing = [
            edge.target_id
            for edge in node.outgoing
        ]
        current = outgoing[0] if outgoing else None
        guard += 1
    return tuple(sequence)


def simulate(spec: SimulationSpec, model: ProcessModel) -> SimulationResult:
    if spec.arrival.count <= 0:
        return SimulationResult(
            outcome=SIM_OUTCOME_INFEASIBLE,
            cases_completed=0,
            makespan_minutes=0.0,
            activity_stats=(),
            bottleneck_node=None,
            notes=("arrival.count must be > 0",),
        )
    sequence = _node_sequence(model)
    if not sequence:
        return SimulationResult(
            outcome=SIM_OUTCOME_INFEASIBLE,
            cases_completed=0,
            makespan_minutes=0.0,
            activity_stats=(),
            bottleneck_node=None,
            notes=("model.start_node_id missing or no nodes",),
        )
    activity_map: dict[str, ActivityProfile] = {
        a.node_id: a for a in spec.activities
    }
    resource_map: dict[str, ResourcePool] = {
        r.name: r for r in spec.resources
    }
    if any(
        seq_id not in activity_map for seq_id in sequence
    ):
        missing = [seq_id for seq_id in sequence if seq_id not in activity_map]
        return SimulationResult(
            outcome=SIM_OUTCOME_INFEASIBLE,
            cases_completed=0,
            makespan_minutes=0.0,
            activity_stats=(),
            bottleneck_node=None,
            notes=(f"missing activity profile for nodes: {missing}",),
        )
    if len(sequence) < 2:
        return SimulationResult(
            outcome=SIM_OUTCOME_INFEASIBLE,
            cases_completed=0,
            makespan_minutes=0.0,
            activity_stats=(),
            bottleneck_node=None,
            notes=("model needs at least one start and one end node",),
        )
    rng = _linear_congruential(spec.seed or 1)
    resource_free_at: dict[str, float] = {
        r.name: 0.0 for r in spec.resources
    }
    activity_busy: dict[str, float] = defaultdict(float)
    activity_started: dict[str, int] = defaultdict(int)
    activity_completed: dict[str, int] = defaultdict(int)
    activity_waits: dict[str, list[float]] = defaultdict(list)
    now: float = 0.0
    case_completion_times: list[float] = []
    event_queue: list[tuple[float, int, str, int]] = []
    for case_index in range(spec.arrival.count):
        arrival_time = case_index * spec.arrival.interarrival_minutes
        heapq.heappush(event_queue, (arrival_time, 0, sequence[0], case_index))
    while event_queue:
        current_time, step_index, node_id, case_index = heapq.heappop(event_queue)
        now = max(now, current_time)
        if step_index >= len(sequence):
            case_completion_times.append(now)
            continue
        if node_id != sequence[step_index]:
            heapq.heappush(
                event_queue,
                (now, step_index, sequence[step_index], case_index),
            )
            continue
        profile = activity_map[node_id]
        wait = 0.0
        if profile.required_resource is not None:
            if profile.required_resource not in resource_map:
                return SimulationResult(
                    outcome=SIM_OUTCOME_INFEASIBLE,
                    cases_completed=len(case_completion_times),
                    makespan_minutes=now,
                    activity_stats=(),
                    bottleneck_node=None,
                    notes=(
                        f"unknown resource: {profile.required_resource}",
                    ),
                )
            ready_at = resource_free_at[profile.required_resource]
            if ready_at > now:
                wait = ready_at - now
                now = ready_at
            jitter = (rng() - 0.5) * 0.1 * profile.duration_minutes
            finish_at = now + profile.duration_minutes + jitter
            resource_free_at[profile.required_resource] = finish_at
        else:
            jitter = (rng() - 0.5) * 0.1 * profile.duration_minutes
            finish_at = now + profile.duration_minutes + jitter
        activity_started[node_id] += 1
        activity_busy[node_id] += profile.duration_minutes
        activity_waits[node_id].append(wait)
        activity_completed[node_id] += 1
        if step_index + 1 < len(sequence):
            heapq.heappush(
                event_queue,
                (finish_at, step_index + 1, sequence[step_index + 1], case_index),
            )
        else:
            heapq.heappush(event_queue, (finish_at, step_index + 1, "", case_index))
    stats_list: list[ActivityStat] = []
    for node_id in sequence:
        waits = activity_waits.get(node_id, [])
        total_waits = sum(waits)
        avg_wait = (total_waits / len(waits)) if waits else 0.0
        max_wait = max(waits) if waits else 0.0
        stats_list.append(
            ActivityStat(
                node_id=node_id,
                started=activity_started[node_id],
                completed=activity_completed[node_id],
                total_busy_minutes=activity_busy[node_id],
                max_wait_minutes=max_wait,
                avg_wait_minutes=avg_wait,
            )
        )
    bottleneck: str | None = None
    bottleneck_score: float = -1.0
    for stat in stats_list:
        score = stat.max_wait_minutes + stat.total_busy_minutes
        if score > bottleneck_score:
            bottleneck_score = score
            bottleneck = stat.node_id
    makespan = max(case_completion_times) if case_completion_times else 0.0
    return SimulationResult(
        outcome=SIM_OUTCOME_OK,
        cases_completed=len(case_completion_times),
        makespan_minutes=makespan,
        activity_stats=tuple(stats_list),
        bottleneck_node=bottleneck,
    )


def make_simple_spec(
    *,
    case_count: int,
    interarrival_minutes: float,
    duration_minutes: float,
    resource_name: str = "agent",
    resource_capacity: int = 1,
    seed: int = 0,
) -> SimulationSpec:
    return SimulationSpec(
        arrival=ArrivalPattern(
            name="default",
            interarrival_minutes=interarrival_minutes,
            count=case_count,
        ),
        resources=(ResourcePool(name=resource_name, capacity=resource_capacity),),
        activities=(),
        seed=seed,
    )
