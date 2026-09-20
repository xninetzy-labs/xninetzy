from __future__ import annotations

from xninetzy.context.process_engineering.model import (
    NODE_KIND_END,
    NODE_KIND_START,
    NODE_KIND_TASK,
    NodeDef,
    ProcessEdge,
    ProcessModel,
    ProcessNode,
)
from xninetzy.context.process_engineering.simulation import (
    SIM_OUTCOME_INFEASIBLE,
    SIM_OUTCOME_OK,
    ActivityProfile,
    ArrivalPattern,
    ResourcePool,
    SimulationSpec,
    simulate,
)


def _linear_model(node_ids: list[str]) -> ProcessModel:
    nodes: list[ProcessNode] = []
    for index, nid in enumerate(node_ids):
        if index == 0:
            kind = NODE_KIND_START
        elif index == len(node_ids) - 1:
            kind = NODE_KIND_END
        else:
            kind = NODE_KIND_TASK
        outgoing: tuple[ProcessEdge, ...] = ()
        if index < len(node_ids) - 1:
            outgoing = (ProcessEdge(source_id=nid, target_id=node_ids[index + 1]),)
        nodes.append(
            ProcessNode(
                definition=NodeDef(id=nid, kind=kind, name=nid),
                outgoing=outgoing,
            )
        )
    return ProcessModel(
        id="m1",
        title="m1",
        description="",
        nodes=tuple(nodes),
        lanes=(),
    )


def test_simulate_basic_completion():
    model = _linear_model(["start", "task1", "end"])
    spec = SimulationSpec(
        arrival=ArrivalPattern(name="a", interarrival_minutes=5.0, count=3),
        resources=(ResourcePool(name="agent", capacity=1),),
        activities=(
            ActivityProfile(node_id="start", duration_minutes=0.0, required_resource=None),
            ActivityProfile(node_id="task1", duration_minutes=2.0, required_resource="agent"),
            ActivityProfile(node_id="end", duration_minutes=0.0, required_resource=None),
        ),
        seed=42,
    )
    result = simulate(spec, model)
    assert result.outcome == SIM_OUTCOME_OK
    assert result.cases_completed == 3
    assert result.bottleneck_node == "task1"
    assert result.makespan_minutes >= 2.0


def test_simulate_empty_arrival_returns_infeasible():
    model = _linear_model(["start", "end"])
    spec = SimulationSpec(
        arrival=ArrivalPattern(name="a", interarrival_minutes=1.0, count=0),
        resources=(),
        activities=(
            ActivityProfile(node_id="start", duration_minutes=1.0),
            ActivityProfile(node_id="end", duration_minutes=1.0),
        ),
    )
    result = simulate(spec, model)
    assert result.outcome == SIM_OUTCOME_INFEASIBLE


def test_simulate_missing_activity_returns_infeasible():
    model = _linear_model(["start", "task1", "end"])
    spec = SimulationSpec(
        arrival=ArrivalPattern(name="a", interarrival_minutes=1.0, count=1),
        resources=(),
        activities=(
            ActivityProfile(node_id="start", duration_minutes=1.0),
        ),
    )
    result = simulate(spec, model)
    assert result.outcome == SIM_OUTCOME_INFEASIBLE


def test_simulate_single_node_returns_infeasible():
    model = ProcessModel(
        id="m2",
        title="m2",
        description="",
        nodes=(
            ProcessNode(
                definition=NodeDef(id="start", kind=NODE_KIND_START, name="s"),
                outgoing=(),
            ),
        ),
        lanes=(),
    )
    spec = SimulationSpec(
        arrival=ArrivalPattern(name="a", interarrival_minutes=1.0, count=1),
        resources=(),
        activities=(ActivityProfile(node_id="start", duration_minutes=1.0),),
    )
    result = simulate(spec, model)
    assert result.outcome == SIM_OUTCOME_INFEASIBLE


def test_simulate_unknown_resource_returns_infeasible():
    model = _linear_model(["start", "task1", "end"])
    spec = SimulationSpec(
        arrival=ArrivalPattern(name="a", interarrival_minutes=1.0, count=1),
        resources=(ResourcePool(name="agent", capacity=1),),
        activities=(
            ActivityProfile(node_id="start", duration_minutes=1.0),
            ActivityProfile(node_id="task1", duration_minutes=1.0, required_resource="ghost"),
            ActivityProfile(node_id="end", duration_minutes=1.0),
        ),
    )
    result = simulate(spec, model)
    assert result.outcome == SIM_OUTCOME_INFEASIBLE


def test_simulate_deterministic_seed():
    model = _linear_model(["start", "task1", "end"])
    activities = (
        ActivityProfile(node_id="start", duration_minutes=0.0),
        ActivityProfile(node_id="task1", duration_minutes=2.0, required_resource="agent"),
        ActivityProfile(node_id="end", duration_minutes=0.0),
    )
    resources = (ResourcePool(name="agent", capacity=1),)
    arrival = ArrivalPattern(name="a", interarrival_minutes=1.0, count=4)
    spec_a = SimulationSpec(
        arrival=arrival, resources=resources, activities=activities, seed=7
    )
    spec_b = SimulationSpec(
        arrival=arrival, resources=resources, activities=activities, seed=7
    )
    result_a = simulate(spec_a, model)
    result_b = simulate(spec_b, model)
    assert result_a.makespan_minutes == result_b.makespan_minutes
    assert result_a.cases_completed == result_b.cases_completed


def test_simulate_collects_wait_when_capacity_one():
    model = _linear_model(["start", "task1", "end"])
    spec = SimulationSpec(
        arrival=ArrivalPattern(name="a", interarrival_minutes=1.0, count=3),
        resources=(ResourcePool(name="agent", capacity=1),),
        activities=(
            ActivityProfile(node_id="start", duration_minutes=0.0),
            ActivityProfile(node_id="task1", duration_minutes=5.0, required_resource="agent"),
            ActivityProfile(node_id="end", duration_minutes=0.0),
        ),
        seed=1,
    )
    result = simulate(spec, model)
    assert result.outcome == SIM_OUTCOME_OK
    task1_stat = next(s for s in result.activity_stats if s.node_id == "task1")
    assert task1_stat.max_wait_minutes > 0.0


def test_simulate_no_start_node_returns_infeasible():
    model = ProcessModel(
        id="m3",
        title="m3",
        description="",
        nodes=(
            ProcessNode(
                definition=NodeDef(id="task1", kind=NODE_KIND_TASK, name="t"),
                outgoing=(),
            ),
        ),
        lanes=(),
    )
    spec = SimulationSpec(
        arrival=ArrivalPattern(name="a", interarrival_minutes=1.0, count=1),
        resources=(),
        activities=(ActivityProfile(node_id="task1", duration_minutes=1.0),),
    )
    result = simulate(spec, model)
    assert result.outcome == SIM_OUTCOME_INFEASIBLE
