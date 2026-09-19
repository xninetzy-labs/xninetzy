from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, ParseError

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

BPMN_KIND_TAGS: dict[str, str] = {
    "startEvent": NODE_KIND_START,
    "endEvent": NODE_KIND_END,
    "task": NODE_KIND_TASK,
    "userTask": NODE_KIND_TASK,
    "serviceTask": NODE_KIND_TASK,
    "exclusiveGateway": NODE_KIND_GATEWAY,
    "parallelGateway": NODE_KIND_GATEWAY,
    "subProcess": NODE_KIND_SUBPROCESS,
}


def _q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def _local(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def parse_bpmn_text(xml_text: str) -> ProcessModel:
    if not xml_text.strip():
        raise ValueError("empty BPMN payload")
    try:
        root = ET.fromstring(xml_text)
    except ParseError as exc:
        raise ValueError(f"invalid BPMN XML: {exc}") from exc
    process_el = root.find(_q(BPMN_NS, "process"))
    if process_el is None:
        raise ValueError("BPMN payload missing <process> element")
    model_id = process_el.attrib.get("id", "process-1")
    title = process_el.attrib.get("name", model_id)
    description = process_el.attrib.get("", "")
    nodes: list[ProcessNode] = []
    outgoing_index: dict[str, list[ProcessEdge]] = {}
    incoming_targets: set[str] = set()
    incoming_by_target: dict[str, list[str]] = {}
    for child in process_el:
        local = _local(child.tag)
        if local not in BPMN_KIND_TAGS:
            continue
        node_id = child.attrib.get("id")
        if not node_id:
            continue
        node_name = child.attrib.get("name", node_id)
        nodes.append(
            ProcessNode(
                definition=NodeDef(
                    id=node_id,
                    kind=BPMN_KIND_TAGS[local],
                    name=node_name,
                )
            )
        )
        outgoing_index[node_id] = []
    for child in process_el:
        local = _local(child.tag)
        if local != "sequenceFlow":
            continue
        src = child.attrib.get("sourceRef")
        tgt = child.attrib.get("targetRef")
        if not src or not tgt:
            continue
        if src not in outgoing_index or tgt not in {n.definition.id for n in nodes}:
            continue
        outgoing_index[src].append(
            ProcessEdge(
                source_id=src,
                target_id=tgt,
                condition=child.attrib.get("name"),
                label=child.attrib.get(""),
            )
        )
        incoming_targets.add(tgt)
        incoming_by_target.setdefault(tgt, []).append(src)
    final_nodes: list[ProcessNode] = []
    for node in nodes:
        final_nodes.append(
            ProcessNode(
                definition=node.definition,
                outgoing=tuple(outgoing_index.get(node.definition.id, [])),
            )
        )
    lanes: list[ProcessLane] = []
    lane_set = process_el.find(_q(BPMN_NS, "laneSet"))
    if lane_set is not None:
        for lane_el in lane_set.findall(_q(BPMN_NS, "lane")):
            lane_id = lane_el.attrib.get("id")
            lane_name = lane_el.attrib.get("name", lane_id or "lane")
            if not lane_id:
                continue
            lane_node_ids = tuple(
                ref.attrib.get("id")
                for ref in lane_el.findall(_q(BPMN_NS, "flowNodeRef"))
                if ref.attrib.get("id")
            )
            lanes.append(
                ProcessLane(
                    definition=LaneDef(
                        id=lane_id,
                        name=lane_name,
                    ),
                    node_ids=lane_node_ids,
                )
            )
    metadata = {
        "incoming_by_target": incoming_by_target,
        "node_count": len(final_nodes),
        "edge_count": sum(len(n.outgoing) for n in final_nodes),
    }
    return ProcessModel(
        id=model_id,
        title=title,
        description=description,
        nodes=tuple(final_nodes),
        lanes=tuple(lanes),
        metadata=metadata,
    )


def render_bpmn_text(model: ProcessModel) -> str:
    definitions = Element(_q(BPMN_NS, "definitions"))
    for prefix, uri in (
        ("bpmn", BPMN_NS),
        ("bpmndi", DI_NS),
    ):
        definitions.attrib[f"xmlns:{prefix}"] = uri
    process_el = Element(_q(BPMN_NS, "process"))
    process_el.attrib["id"] = model.id
    process_el.attrib["name"] = model.title
    for node in model.nodes:
        kind = node.definition.kind
        tag_name = _bpmn_tag_for(kind)
        node_el = Element(_q(BPMN_NS, tag_name))
        node_el.attrib["id"] = node.definition.id
        node_el.attrib["name"] = node.definition.name
        process_el.append(node_el)
    for node in model.nodes:
        for edge in node.outgoing:
            flow = Element(_q(BPMN_NS, "sequenceFlow"))
            flow.attrib["id"] = f"{edge.source_id}__{edge.target_id}"
            flow.attrib["sourceRef"] = edge.source_id
            flow.attrib["targetRef"] = edge.target_id
            if edge.condition:
                flow.attrib["name"] = edge.condition
            process_el.append(flow)
    if model.lanes:
        lane_set = Element(_q(BPMN_NS, "laneSet"))
        lane_set.attrib["id"] = f"{model.id}-lanes"
        for lane in model.lanes:
            lane_el = Element(_q(BPMN_NS, "lane"))
            lane_el.attrib["id"] = lane.definition.id
            lane_el.attrib["name"] = lane.definition.name
            for node_id in lane.node_ids:
                ref = Element(_q(BPMN_NS, "flowNodeRef"))
                ref.attrib["id"] = node_id
                lane_el.append(ref)
            lane_set.append(lane_el)
        process_el.append(lane_set)
    definitions.append(process_el)
    ET.indent(definitions, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        definitions, encoding="unicode"
    )


def _bpmn_tag_for(kind: str) -> str:
    for tag, mapped in BPMN_KIND_TAGS.items():
        if mapped == kind:
            return tag
    return "task"