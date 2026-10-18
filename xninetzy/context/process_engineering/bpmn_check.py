from __future__ import annotations

import re
from dataclasses import dataclass

from lxml import etree

from xninetzy.context.process_engineering.bpmn_io import BPMN_NS, DI_NS, DOCTYPE_PATTERN, FLOW_NODE_TAGS

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
_NCNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
_SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)
_CONTAINER_TAGS = frozenset({"participant", "lane"})


@dataclass(frozen=True, slots=True)
class InterchangeIssue:
    code: str
    message: str
    location: str | None = None
    severity: str = SEVERITY_ERROR


def _local(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def _ns(tag: object) -> str:
    return tag[1:].split("}", 1)[0] if isinstance(tag, str) and tag.startswith("{") else ""


def _issue(code: str, message: str, location: str | None = None, severity: str = SEVERITY_ERROR) -> InterchangeIssue:
    return InterchangeIssue(code=code, message=message, location=location, severity=severity)


def _overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def check_interchange(xml_text: str) -> list[InterchangeIssue]:
    if DOCTYPE_PATTERN.search(xml_text):
        return [_issue("xml:doctype", "DOCTYPE/ENTITY tidak diizinkan di dokumen BPMN")]
    try:
        root = etree.fromstring(xml_text.encode("utf-8"), _SAFE_PARSER)
    except etree.XMLSyntaxError as exc:
        return [_issue("xml:not-well-formed", f"XML tidak well-formed: {exc}")]
    issues: list[InterchangeIssue] = []
    if _local(root.tag) != "definitions" or _ns(root.tag) != BPMN_NS:
        return [_issue("xml:not-bpmn", f"root harus <definitions> di namespace {BPMN_NS}")]
    if not root.get("targetNamespace"):
        issues.append(_issue("xml:missing-target-namespace", "definitions tidak punya targetNamespace (wajib di BPMN 2.0; importer menolak)", "definitions"))

    seen: dict[str, int] = {}
    for element in root.iter():
        raw = element.get("id") if isinstance(element.tag, str) else None
        if raw is None:
            continue
        seen[raw] = seen.get(raw, 0) + 1
        if not _NCNAME.match(raw):
            issues.append(_issue("xml:invalid-id", f"id '{raw}' bukan NCName valid (tidak boleh diawali angka atau berisi spasi/simbol)", raw))
    for raw, count in seen.items():
        if count > 1:
            issues.append(_issue("xml:duplicate-id", f"id '{raw}' dipakai {count} kali", raw))

    processes = [e for e in root.iter() if _local(e.tag) == "process" and _ns(e.tag) == BPMN_NS]
    process_ids = {p.get("id") for p in processes}
    for participant in (e for e in root.iter() if _local(e.tag) == "participant"):
        ref = participant.get("processRef")
        if ref and ref not in process_ids:
            issues.append(_issue("structural:missing-process", f"participant '{participant.get('id')}' merujuk process '{ref}' yang tidak ada", participant.get("id")))

    flow_nodes: dict[str, etree._Element] = {}
    flows: dict[str, etree._Element] = {}
    lane_of: dict[str, list[str]] = {}
    for process in processes:
        for child in process:
            local = _local(child.tag)
            if local in FLOW_NODE_TAGS and child.get("id"):
                flow_nodes[child.get("id")] = child
            elif local == "sequenceFlow" and child.get("id"):
                flows[child.get("id")] = child
        for lane in process.iter():
            if _local(lane.tag) != "lane":
                continue
            for ref in (c for c in lane if _local(c.tag) == "flowNodeRef"):
                target = "".join(ref.itertext()).strip()
                if not target and ref.get("id"):
                    issues.append(_issue("xml:flownoderef-attribute", "flowNodeRef harus berisi teks id node, bukan atribut id", lane.get("id")))
                    target = ref.get("id")
                if target and target not in flow_nodes:
                    issues.append(_issue("structural:missing-node", f"lane '{lane.get('id')}' merujuk node '{target}' yang tidak ada", lane.get("id")))
                if target:
                    lane_of.setdefault(target, []).append(lane.get("id", ""))
    for node_id, lanes in lane_of.items():
        if len(lanes) > 1:
            issues.append(_issue("structural:multiple-lanes", f"node '{node_id}' ada di beberapa lane: {', '.join(lanes)}", node_id, SEVERITY_WARNING))

    incoming: dict[str, int] = {n: 0 for n in flow_nodes}
    outgoing: dict[str, int] = {n: 0 for n in flow_nodes}
    for flow_id, flow in flows.items():
        source, target = flow.get("sourceRef"), flow.get("targetRef")
        if source not in flow_nodes or target not in flow_nodes:
            issues.append(_issue("structural:dangling-flow", f"sequenceFlow '{flow_id}' menghubungkan '{source}' -> '{target}' yang tidak ada", flow_id))
            continue
        outgoing[source] += 1
        incoming[target] += 1
    for node_id, node in flow_nodes.items():
        tag = _local(node.tag)
        if tag != "startEvent" and incoming[node_id] == 0:
            issues.append(_issue("structural:no-incoming", f"node '{node_id}' tidak punya flow masuk", node_id, SEVERITY_WARNING))
        if tag != "endEvent" and outgoing[node_id] == 0:
            issues.append(_issue("structural:no-outgoing", f"node '{node_id}' tidak punya flow keluar", node_id, SEVERITY_WARNING))
    tags = {_local(n.tag) for n in flow_nodes.values()}
    if flow_nodes and "startEvent" not in tags:
        issues.append(_issue("structural:no-start", "proses tidak punya startEvent", severity=SEVERITY_WARNING))
    if flow_nodes and "endEvent" not in tags:
        issues.append(_issue("structural:no-end", "proses tidak punya endEvent", severity=SEVERITY_WARNING))
    for node_id, node in flow_nodes.items():
        for tag in ("incoming", "outgoing"):
            for ref in (c for c in node if _local(c.tag) == tag):
                if "".join(ref.itertext()).strip() not in flows:
                    issues.append(_issue("structural:dangling-reference", f"<{tag}> pada '{node_id}' merujuk flow yang tidak ada", node_id, SEVERITY_WARNING))

    diagrams = [e for e in root.iter() if _local(e.tag) == "BPMNDiagram" and _ns(e.tag) == DI_NS]
    if not diagrams:
        issues.append(_issue("diagram:missing-di", "tidak ada BPMNDiagram: Bizagi Modeler dan bpmn.io tidak dapat menampilkan proses tanpa informasi grafis", "definitions"))
        return issues
    shaped: dict[str, tuple[float, float, float, float]] = {}
    edged: set[str] = set()
    for element in root.iter():
        local = _local(element.tag)
        if _ns(element.tag) != DI_NS or local not in {"BPMNShape", "BPMNEdge"}:
            continue
        ref = element.get("bpmnElement")
        if not ref or ref not in seen:
            issues.append(_issue("diagram:dangling-element", f"{local} merujuk elemen '{ref}' yang tidak ada", element.get("id")))
            continue
        if local == "BPMNShape":
            bounds = next((c for c in element if _local(c.tag) == "Bounds"), None)
            try:
                box = tuple(float(bounds.get(k)) for k in ("x", "y", "width", "height")) if bounds is not None else None
            except (TypeError, ValueError):
                box = None
            if box is None or box[2] <= 0 or box[3] <= 0:
                issues.append(_issue("diagram:bad-bounds", f"BPMNShape '{ref}' tidak punya Bounds valid (width/height > 0)", ref))
                continue
            shaped[ref] = box
        else:
            points = [c for c in element if _local(c.tag) == "waypoint"]
            if len(points) < 2 or any(p.get("x") is None or p.get("y") is None for p in points):
                issues.append(_issue("diagram:bad-waypoints", f"BPMNEdge '{ref}' butuh minimal dua waypoint dengan x dan y", ref))
                continue
            edged.add(ref)
    for node_id in flow_nodes:
        if node_id not in shaped:
            issues.append(_issue("diagram:missing-shape", f"node '{node_id}' tidak punya BPMNShape; akan hilang di Bizagi", node_id))
    for flow_id in flows:
        if flow_id not in edged:
            issues.append(_issue("diagram:missing-edge", f"sequenceFlow '{flow_id}' tidak punya BPMNEdge; garis tidak tergambar", flow_id))
    for participant in (e for e in root.iter() if _local(e.tag) == "participant"):
        if participant.get("id") not in shaped:
            issues.append(_issue("diagram:missing-pool-shape", f"participant '{participant.get('id')}' tidak punya BPMNShape", participant.get("id"), SEVERITY_WARNING))
    drawn = [(n, shaped[n]) for n in flow_nodes if n in shaped and _local(flow_nodes[n].tag) not in _CONTAINER_TAGS]
    for index, (name_a, box_a) in enumerate(drawn):
        for name_b, box_b in drawn[index + 1:]:
            if _overlaps(box_a, box_b):
                issues.append(_issue("diagram:overlap", f"shape '{name_a}' dan '{name_b}' saling menimpa", name_a, SEVERITY_WARNING))
    return issues


def errors_only(issues: list[InterchangeIssue]) -> list[InterchangeIssue]:
    return [issue for issue in issues if issue.severity == SEVERITY_ERROR]
