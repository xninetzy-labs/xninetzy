from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.context.process_engineering.execution import (
    ExecutionPlan,
    is_flowable_enabled,
    plan_execution,
)
from xninetzy.context.process_engineering.mining import (
    DiscoveryReport,
    discover_process,
    is_native_mining_enabled,
    parse_event_log_csv,
)
from xninetzy.context.process_engineering.providers import (
    PROVIDER_BPMN_JS,
    PROVIDER_BIZAGI_COMPAT,
    PROVIDER_CAMUNDA_COMPAT,
    PROVIDER_FLOWABLE,
    PROVIDER_NATIVE,
    PROVIDER_PM4PY,
    PROVIDER_SIMPY,
    ProviderDecision,
    is_provider_enabled,
    list_enabled_providers,
    list_providers_by_capability,
    select_provider,
)
from xninetzy.context.process_engineering.simulation import (
    SIM_OUTCOME_OK,
    ActivityProfile,
    ArrivalPattern,
    ResourcePool,
    SimulationResult,
    SimulationSpec,
    simulate,
)


@tool
def process_list_providers() -> list[dict]:
    """List enabled process_engineering providers with license profile.

    Returns:
        List of provider profiles (provider_id, capability, license, runtime).
    """
    return [p.to_dict() for p in list_enabled_providers()]


@tool
def process_select_provider(capability: str, preferred: str | None = None) -> dict:
    """Select a provider for a given process capability.

    Args:
        capability: capability name (process_modeling|process_mining|
            process_execution|process_simulation|process_validation|
            process_interop)
        preferred: optional provider_id hint

    Returns:
        Decision dict with chosen provider, candidates, and license warnings.
    """
    decision: ProviderDecision = select_provider(capability, preferred=preferred)
    return decision.to_dict()


@tool
def process_is_provider_enabled(provider_id: str) -> bool:
    """Check whether a provider is enabled under current env config.

    Args:
        provider_id: provider identifier
            (native_xninetzy|bpmn_js|pm4py|flowable|simpy|bizagi_compatible|camunda_compatible)

    Returns:
        True if the provider is available, False otherwise.
    """
    if provider_id == PROVIDER_NATIVE:
        return True
    if provider_id == PROVIDER_BPMN_JS:
        return True
    if provider_id == PROVIDER_SIMPY:
        return True
    if provider_id == PROVIDER_BIZAGI_COMPAT:
        return True
    if provider_id == PROVIDER_CAMUNDA_COMPAT:
        return True
    if provider_id == PROVIDER_PM4PY:
        return is_provider_enabled(
            next(
                p for p in (
                    __import__(
                        "xninetzy.context.process_engineering.providers",
                        fromlist=["PROVIDER_TABLE"],
                    ).PROVIDER_TABLE[p]
                    for p in (PROVIDER_PM4PY,)
                )
            )
        )
    if provider_id == PROVIDER_FLOWABLE:
        return is_flowable_enabled()
    return False


@tool
def process_discover_from_event_log(csv_text: str) -> dict:
    """Run native process discovery on a CSV event log.

    Args:
        csv_text: CSV text with columns case_id, activity, timestamp,
            optional resource

    Returns:
        Discovery report with case count, variants, activity frequency.
    """
    rows = parse_event_log_csv(csv_text)
    report: DiscoveryReport = discover_process(rows)
    return report.to_dict()


@tool
def process_is_native_mining_enabled() -> bool:
    """Check whether native event-log mining is enabled (opt-in env)."""
    return is_native_mining_enabled()


@tool
def process_simulate(
    case_count: int,
    interarrival_minutes: float,
    nodes_json: str,
    seed: int = 0,
) -> dict:
    """Run discrete-event process simulation.

    Args:
        case_count: number of cases to simulate
        interarrival_minutes: minutes between case arrivals
        nodes_json: JSON list of {node_id, duration_minutes, required_resource}
        seed: RNG seed for deterministic replay
    """
    import json as _json

    raw = _json.loads(nodes_json)
    activities: list[ActivityProfile] = []
    resource_names: set[str] = set()
    for item in raw:
        node_id = str(item["node_id"])
        duration = float(item["duration_minutes"])
        required = item.get("required_resource")
        activities.append(
            ActivityProfile(
                node_id=node_id,
                duration_minutes=duration,
                required_resource=required,
            )
        )
        if required:
            resource_names.add(str(required))
    resources = tuple(
        ResourcePool(name=name, capacity=1) for name in sorted(resource_names)
    )
    spec = SimulationSpec(
        arrival=ArrivalPattern(
            name="default",
            interarrival_minutes=interarrival_minutes,
            count=int(case_count),
        ),
        resources=resources,
        activities=tuple(activities),
        seed=int(seed),
    )
    nodes_seq = [a.node_id for a in activities]
    model = _build_sim_model(nodes_seq)
    result: SimulationResult = simulate(spec, model)
    return result.to_dict()


def _build_sim_model(node_ids: list[str]):
    from xninetzy.context.process_engineering.model import (
        NODE_KIND_END,
        NODE_KIND_START,
        NODE_KIND_TASK,
        NodeDef,
        ProcessEdge,
        ProcessModel,
        ProcessNode,
    )

    nodes = []
    for index, nid in enumerate(node_ids):
        kind = (
            NODE_KIND_START
            if index == 0
            else NODE_KIND_END
            if index == len(node_ids) - 1
            else NODE_KIND_TASK
        )
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
        id="sim-model",
        title="sim",
        description="",
        nodes=tuple(nodes),
        lanes=(),
    )


@tool
def process_plan_execution(
    deployment_key: str,
    business_key: str,
    process_definition_key: str,
    bpmn_xml_length: int,
    variables_json: str | None = None,
    tenant_id: str | None = None,
) -> dict:
    """Plan a Flowable execution. Dry-run when env var unset.

    Args:
        deployment_key: Flowable deployment key
        business_key: case/business identifier
        process_definition_key: process definition key
        bpmn_xml_length: length of BPMN XML (length-only, not the XML itself)
        variables_json: JSON object of process variables
        tenant_id: optional Flowable tenant id

    Returns:
        Execution plan with dry_run flag.
    """
    import json as _json

    variables = _json.loads(variables_json) if variables_json else {}
    if not isinstance(variables, dict):
        variables = {"value": variables}
    plan: ExecutionPlan = plan_execution(
        deployment_key=deployment_key,
        bpmn_xml="x" * int(bpmn_xml_length),
        business_key=business_key,
        process_definition_key=process_definition_key,
        variables=variables,
        tenant_id=tenant_id,
    )
    return plan.to_dict()


@tool
def process_is_flowable_enabled() -> bool:
    """Check whether Flowable REST adapter is enabled via env var."""
    return is_flowable_enabled()


@tool
def process_capability_providers(capability: str) -> list[dict]:
    """Return enabled providers for a capability.

    Args:
        capability: capability name

    Returns:
        List of provider profiles.
    """
    return [p.to_dict() for p in list_providers_by_capability(capability)]


__all__ = [
    "SIM_OUTCOME_OK",
    "process_capability_providers",
    "process_discover_from_event_log",
    "process_is_flowable_enabled",
    "process_is_native_mining_enabled",
    "process_is_provider_enabled",
    "process_list_providers",
    "process_plan_execution",
    "process_select_provider",
    "process_simulate",
]
