from __future__ import annotations

import re

from lxml import etree

from xninetzy.context.process_engineering.layout import (
    EVENT_TAGS,
    GATEWAY_TAGS,
    Box,
    LayoutInput,
    compute_layout,
)
from xninetzy.context.process_engineering.model import (
    LaneDef,
    NodeDef,
    NODE_KIND_END,
    NODE_KIND_GATEWAY,
    NODE_KIND_START,
    NODE_KIND_SUBPROCESS,
    NODE_KIND_TASK,
    ProcessEdge,
    ProcessLane,
    ProcessModel,
    ProcessNode,
)

BPMN_NS: str = "http://www.omg.org/spec/BPMN/20100524/MODEL"
DI_NS: str = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS: str = "http://www.omg.org/spec/DD/20100524/DC"
DD_DI_NS: str = "http://www.omg.org/spec/DD/20100524/DI"
XSI_NS: str = "http://www.w3.org/2001/XMLSchema-instance"
EXPORTER: str = "Xninetzy"
EXPORTER_VERSION: str = "1.0"

BPMN_KIND_TAGS: dict[str, str] = {
    "startEvent": NODE_KIND_START,
    "endEvent": NODE_KIND_END,
    "task": NODE_KIND_TASK,
    "userTask": NODE_KIND_TASK,
    "serviceTask": NODE_KIND_TASK,
    "manualTask": NODE_KIND_TASK,
    "scriptTask": NODE_KIND_TASK,
    "businessRuleTask": NODE_KIND_TASK,
    "sendTask": NODE_KIND_TASK,
    "receiveTask": NODE_KIND_TASK,
    "callActivity": NODE_KIND_TASK,
    "intermediateCatchEvent": NODE_KIND_TASK,
    "intermediateThrowEvent": NODE_KIND_TASK,
    "exclusiveGateway": NODE_KIND_GATEWAY,
    "parallelGateway": NODE_KIND_GATEWAY,
    "inclusiveGateway": NODE_KIND_GATEWAY,
    "eventBasedGateway": NODE_KIND_GATEWAY,
    "complexGateway": NODE_KIND_GATEWAY,
    "subProcess": NODE_KIND_SUBPROCESS,
}
DEFAULT_TAG_FOR_KIND: dict[str, str] = {
    NODE_KIND_START: "startEvent",
    NODE_KIND_END: "endEvent",
    NODE_KIND_TASK: "task",
    NODE_KIND_GATEWAY: "exclusiveGateway",
    NODE_KIND_SUBPROCESS: "subProcess",
}
FLOW_NODE_TAGS = frozenset(BPMN_KIND_TAGS) | {"boundaryEvent", "adHocSubProcess", "transaction", "choreographyTask", "subChoreography"}
IGNORED_ARTIFACT_TAGS = frozenset({"textAnnotation", "group", "association", "dataObject", "dataObjectReference", "dataStoreReference"})
DEFAULT_FLOW_LABEL = "default"

_SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)
_NCNAME_INVALID = re.compile(r"[^A-Za-z0-9_.\-]")
DOCTYPE_PATTERN = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.IGNORECASE)
_LABEL_CHAR_WIDTH = 7


def _local(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def _bpmn(tag: str) -> str:
    return f"{{{BPMN_NS}}}{tag}"


def ncname(raw: str) -> str:
    cleaned = _NCNAME_INVALID.sub("_", str(raw or "").strip()) or "id"
    return cleaned if (cleaned[0].isalpha() or cleaned[0] == "_") else f"id_{cleaned}"


class _Ids:
    def __init__(self) -> None:
        self._used: set[str] = set()
        self._mapping: dict[tuple[str, str], str] = {}

    def reserve(self, raw: str, space: str = "node") -> str:
        key = (space, raw)
        if key in self._mapping:
            return self._mapping[key]
        candidate = ncname(raw)
        unique, index = candidate, 2
        while unique in self._used:
            unique, index = f"{candidate}_{index}", index + 1
        self._used.add(unique)
        self._mapping[key] = unique
        return unique

    def fresh(self, base: str) -> str:
        candidate = ncname(base)
        unique, index = candidate, 2
        while unique in self._used:
            unique, index = f"{candidate}_{index}", index + 1
        self._used.add(unique)
        return unique


def _first_text(element: etree._Element, tag: str) -> str:
    for child in element:
        if _local(child.tag) == tag:
            return "".join(child.itertext()).strip()
    return ""


def parse_bpmn_text(xml_text: str) -> ProcessModel:
    if not xml_text.strip():
        raise ValueError("empty BPMN payload")
    if DOCTYPE_PATTERN.search(xml_text):
        raise ValueError("invalid BPMN XML: DOCTYPE/ENTITY tidak diizinkan")
    try:
        root = etree.fromstring(xml_text.encode("utf-8"), _SAFE_PARSER)
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"invalid BPMN XML: {exc}") from exc
    processes = [el for el in root.iter() if _local(el.tag) == "process"]
    if not processes:
        raise ValueError("BPMN payload missing <process> element")
    process_el = processes[0]
    participant_names = {
        el.attrib.get("processRef", ""): el.attrib.get("name", "")
        for el in root.iter()
        if _local(el.tag) == "participant"
    }
    model_id = process_el.attrib.get("id", "process-1")
    title = process_el.attrib.get("name") or participant_names.get(model_id) or model_id
    description = _first_text(process_el, "documentation")

    skipped: list[str] = []
    raw_nodes: list[tuple[str, str, str, str]] = []
    known_ids: set[str] = set()
    for child in process_el:
        local = _local(child.tag)
        if local not in FLOW_NODE_TAGS and local not in IGNORED_ARTIFACT_TAGS:
            continue
        node_id = child.attrib.get("id")
        if not node_id:
            continue
        if local not in BPMN_KIND_TAGS:
            skipped.append(f"{local}:{node_id}")
            continue
        raw_nodes.append((node_id, local, child.attrib.get("name", node_id), child.attrib.get("default", "")))
        known_ids.add(node_id)
    default_flows = {default for _id, _tag, _name, default in raw_nodes if default}

    lane_membership: dict[str, str] = {}
    lanes: list[ProcessLane] = []
    for lane_set in (c for c in process_el if _local(c.tag) == "laneSet"):
        for lane_el in (c for c in lane_set if _local(c.tag) == "lane"):
            lane_id = lane_el.attrib.get("id")
            if not lane_id:
                continue
            members: list[str] = []
            for ref in (c for c in lane_el if _local(c.tag) == "flowNodeRef"):
                target = "".join(ref.itertext()).strip() or ref.attrib.get("id", "")
                if target:
                    members.append(target)
                    lane_membership.setdefault(target, lane_id)
            lanes.append(
                ProcessLane(
                    definition=LaneDef(id=lane_id, name=lane_el.attrib.get("name", lane_id)),
                    node_ids=tuple(members),
                )
            )

    outgoing: dict[str, list[ProcessEdge]] = {node_id: [] for node_id, *_ in raw_nodes}
    incoming_by_target: dict[str, list[str]] = {}
    dangling: list[str] = []
    for child in process_el:
        if _local(child.tag) != "sequenceFlow":
            continue
        src = child.attrib.get("sourceRef")
        tgt = child.attrib.get("targetRef")
        if not src or not tgt:
            continue
        if src not in known_ids or tgt not in known_ids:
            dangling.append(child.attrib.get("id", f"{src}->{tgt}"))
            continue
        condition = child.attrib.get("name") or _first_text(child, "conditionExpression") or None
        label = DEFAULT_FLOW_LABEL if child.attrib.get("id") in default_flows else None
        outgoing[src].append(ProcessEdge(source_id=src, target_id=tgt, condition=condition, label=label))
        incoming_by_target.setdefault(tgt, []).append(src)

    nodes: list[ProcessNode] = []
    for node_id, local, name, _default in raw_nodes:
        kind = BPMN_KIND_TAGS[local]
        metadata: dict[str, str] = {}
        if local != DEFAULT_TAG_FOR_KIND[kind]:
            metadata["bpmn_type"] = local
        nodes.append(
            ProcessNode(
                definition=NodeDef(id=node_id, kind=kind, name=name, lane_id=lane_membership.get(node_id), metadata=metadata),
                outgoing=tuple(outgoing[node_id]),
            )
        )

    metadata_out: dict[str, object] = {
        "incoming_by_target": incoming_by_target,
        "node_count": len(nodes),
        "edge_count": sum(len(n.outgoing) for n in nodes),
    }
    if skipped:
        metadata_out["skipped_elements"] = skipped
    if dangling:
        metadata_out["dangling_flows"] = dangling
    if len(processes) > 1:
        metadata_out["extra_processes"] = [p.attrib.get("id", "") for p in processes[1:]]
    return ProcessModel(
        id=model_id,
        title=title,
        description=description,
        nodes=tuple(nodes),
        lanes=tuple(lanes),
        metadata=metadata_out,
    )


def _bpmn_tag_for(kind: str, node: NodeDef | None = None) -> str:
    if node is not None:
        requested = str(node.metadata.get("bpmn_type") or "")
        if requested and BPMN_KIND_TAGS.get(requested) == kind:
            return requested
    return DEFAULT_TAG_FOR_KIND.get(kind, "task")


def _sub(parent: etree._Element, ns: str, tag: str, attrs: dict[str, object] | None = None, text: str | None = None) -> etree._Element:
    element = etree.SubElement(parent, f"{{{ns}}}{tag}", {k: str(v) for k, v in (attrs or {}).items() if v is not None})
    if text is not None:
        element.text = text
    return element


def _bounds(parent: etree._Element, box: Box) -> None:
    _sub(parent, DC_NS, "Bounds", {"x": box.x, "y": box.y, "width": box.width, "height": box.height})


def _label_box(box: Box, name: str) -> Box:
    width = max(40, min(120, len(name) * _LABEL_CHAR_WIDTH))
    return Box(box.center_x - width // 2, box.bottom + 4, width, 14)


def render_bpmn_text(model: ProcessModel) -> str:
    ids = _Ids()
    process_id = ids.reserve(model.id)
    collaboration_id = ids.fresh(f"Collaboration_{model.id}")
    participant_id = ids.fresh(f"Participant_{model.id}")
    node_ids = {node.definition.id: ids.reserve(node.definition.id) for node in model.nodes}
    tags = {node.definition.id: _bpmn_tag_for(node.definition.kind, node.definition) for node in model.nodes}

    lane_of_raw: dict[str, str] = {}
    lane_ids: dict[str, str] = {}
    for lane in model.lanes:
        lane_ids[lane.definition.id] = ids.reserve(lane.definition.id, "lane")
    for lane in model.lanes:
        for member in lane.node_ids:
            if member in node_ids:
                lane_of_raw.setdefault(member, lane.definition.id)
    for node in model.nodes:
        if node.definition.lane_id in lane_ids:
            lane_of_raw.setdefault(node.definition.id, node.definition.lane_id)

    lane_defs: list[tuple[str, str]] = [(lane.definition.id, lane.definition.name) for lane in model.lanes]
    unassigned = [n.definition.id for n in model.nodes if n.definition.id not in lane_of_raw]
    if lane_defs and unassigned:
        fallback = "unassigned"
        while fallback in lane_ids:
            fallback += "_"
        lane_ids[fallback] = ids.fresh("Lane_unassigned")
        lane_defs.append((fallback, "Unassigned"))
        for member in unassigned:
            lane_of_raw[member] = fallback

    flows: list[tuple[str, str, str, str | None]] = []
    default_of: dict[str, str] = {}
    for node in model.nodes:
        for edge in node.outgoing:
            if edge.source_id in node_ids and edge.target_id in node_ids:
                flow_id = ids.fresh(f"Flow_{node_ids[edge.source_id]}_{node_ids[edge.target_id]}")
                flows.append((flow_id, edge.source_id, edge.target_id, edge.condition))
                if edge.label == DEFAULT_FLOW_LABEL:
                    default_of.setdefault(edge.source_id, flow_id)

    nsmap = {"bpmn": BPMN_NS, "bpmndi": DI_NS, "dc": DC_NS, "di": DD_DI_NS, "xsi": XSI_NS}
    definitions = etree.Element(
        _bpmn("definitions"),
        {
            "id": ids.fresh(f"Definitions_{model.id}"),
            "targetNamespace": "http://bpmn.io/schema/bpmn",
            "exporter": EXPORTER,
            "exporterVersion": EXPORTER_VERSION,
        },
        nsmap=nsmap,
    )
    collaboration = _sub(definitions, BPMN_NS, "collaboration", {"id": collaboration_id})
    _sub(collaboration, BPMN_NS, "participant", {"id": participant_id, "name": model.title, "processRef": process_id})
    process = _sub(definitions, BPMN_NS, "process", {"id": process_id, "name": model.title, "isExecutable": "false"})
    if model.description:
        _sub(process, BPMN_NS, "documentation", text=model.description)

    if lane_defs:
        lane_set = _sub(process, BPMN_NS, "laneSet", {"id": ids.fresh(f"LaneSet_{model.id}")})
        for raw_lane, name in lane_defs:
            lane_el = _sub(lane_set, BPMN_NS, "lane", {"id": lane_ids[raw_lane], "name": name})
            for node in model.nodes:
                if lane_of_raw.get(node.definition.id) == raw_lane:
                    _sub(lane_el, BPMN_NS, "flowNodeRef", text=node_ids[node.definition.id])

    incoming_of: dict[str, list[str]] = {}
    outgoing_of: dict[str, list[str]] = {}
    for flow_id, source, target, _condition in flows:
        outgoing_of.setdefault(source, []).append(flow_id)
        incoming_of.setdefault(target, []).append(flow_id)
    for node in model.nodes:
        raw = node.definition.id
        attrs: dict[str, object] = {"id": node_ids[raw], "name": node.definition.name}
        if raw in default_of and tags[raw] not in EVENT_TAGS:
            attrs["default"] = default_of[raw]
        element = _sub(process, BPMN_NS, tags[raw], attrs)
        for flow_id in incoming_of.get(raw, []):
            _sub(element, BPMN_NS, "incoming", text=flow_id)
        for flow_id in outgoing_of.get(raw, []):
            _sub(element, BPMN_NS, "outgoing", text=flow_id)
    for flow_id, source, target, condition in flows:
        attrs = {"id": flow_id, "sourceRef": node_ids[source], "targetRef": node_ids[target]}
        if condition:
            attrs["name"] = condition
        _sub(process, BPMN_NS, "sequenceFlow", attrs)

    layout = compute_layout(
        LayoutInput(
            node_ids=[node_ids[n.definition.id] for n in model.nodes],
            tags={node_ids[raw]: tag for raw, tag in tags.items()},
            flows=[(fid, node_ids[s], node_ids[t]) for fid, s, t, _c in flows],
            lane_of={node_ids[raw]: lane_ids[lane] for raw, lane in lane_of_raw.items()},
            lane_order=[lane_ids[raw] for raw, _name in lane_defs],
        )
    )

    diagram = _sub(definitions, DI_NS, "BPMNDiagram", {"id": ids.fresh(f"BPMNDiagram_{model.id}")})
    plane = _sub(diagram, DI_NS, "BPMNPlane", {"id": ids.fresh(f"BPMNPlane_{model.id}"), "bpmnElement": collaboration_id})
    pool_shape = _sub(plane, DI_NS, "BPMNShape", {"id": ids.fresh(f"{participant_id}_di"), "bpmnElement": participant_id, "isHorizontal": "true"})
    _bounds(pool_shape, layout.pool)
    if lane_defs:
        for raw_lane, name in lane_defs:
            lane_shape = _sub(plane, DI_NS, "BPMNShape", {"id": ids.fresh(f"{lane_ids[raw_lane]}_di"), "bpmnElement": lane_ids[raw_lane], "isHorizontal": "true"})
            _bounds(lane_shape, layout.lanes[lane_ids[raw_lane]])
    for node in model.nodes:
        raw = node.definition.id
        safe = node_ids[raw]
        box = layout.nodes[safe]
        attrs = {"id": ids.fresh(f"{safe}_di"), "bpmnElement": safe}
        if tags[raw] in {"exclusiveGateway", "eventBasedGateway", "complexGateway"}:
            attrs["isMarkerVisible"] = "true"
        if tags[raw] == "subProcess":
            attrs["isExpanded"] = "false"
        shape = _sub(plane, DI_NS, "BPMNShape", attrs)
        _bounds(shape, box)
        if (tags[raw] in EVENT_TAGS or tags[raw] in GATEWAY_TAGS) and node.definition.name:
            label = _sub(shape, DI_NS, "BPMNLabel")
            _bounds(label, _label_box(box, node.definition.name))
    for flow_id, _source, _target, condition in flows:
        edge = _sub(plane, DI_NS, "BPMNEdge", {"id": ids.fresh(f"{flow_id}_di"), "bpmnElement": flow_id})
        points = layout.edges[flow_id]
        for x, y in points:
            _sub(edge, DD_DI_NS, "waypoint", {"x": x, "y": y})
        if condition:
            label = _sub(edge, DI_NS, "BPMNLabel")
            middle = points[len(points) // 2]
            width = max(30, min(120, len(condition) * _LABEL_CHAR_WIDTH))
            _bounds(label, Box(middle[0] - width // 2, middle[1] - 18, width, 14))

    return etree.tostring(definitions, xml_declaration=True, encoding="UTF-8", pretty_print=True).decode("utf-8")
