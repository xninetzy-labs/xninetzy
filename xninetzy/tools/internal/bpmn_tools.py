from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.context.process_engineering.bpmn_check import (
    SEVERITY_ERROR,
    InterchangeIssue,
    check_interchange,
    errors_only,
)
from xninetzy.context.process_engineering.bpmn_io import (
    BPMN_KIND_TAGS,
    DEFAULT_FLOW_LABEL,
    DEFAULT_TAG_FOR_KIND,
    ncname,
    parse_bpmn_text,
    render_bpmn_text,
)
from xninetzy.context.process_engineering.model import (
    NODE_KIND_END,
    VALID_NODE_KINDS,
    LaneDef,
    NodeDef,
    ProcessEdge,
    ProcessLane,
    ProcessModel,
    ProcessNode,
    validate_process_model,
)
from xninetzy.core.config import expand_path, get_settings
from xninetzy.core.paths import ArtifactPathError, resolve_artifact_output

MAX_NODES = 500
MAX_FLOWS = 2000
MAX_SOURCE_BYTES = 5_000_000
ALLOWED_SUFFIXES = frozenset({".bpmn", ".xml"})
BIZAGI_IMPORT_HINT = "Bizagi Modeler: File > Import > BPMN 2.0 XML (.bpmn)"


def _error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"error": code, "message": message, **extra}


def _issue_dict(issue: InterchangeIssue) -> dict[str, Any]:
    return {"code": issue.code, "severity": issue.severity, "message": issue.message, "location": issue.location}


def _interchange_summary(issues: list[InterchangeIssue], limit: int = 15) -> dict[str, Any]:
    errors = [i for i in issues if i.severity == SEVERITY_ERROR]
    ordered = errors + [i for i in issues if i.severity != SEVERITY_ERROR]
    return {
        "errors": len(errors),
        "warnings": len(issues) - len(errors),
        "issues": [_issue_dict(i) for i in ordered[:limit]],
    }


def _output_target(output_path: str, stem: str, suffix: str = ".bpmn") -> Path:
    base = Path(expand_path(get_settings().OUTPUT_DIR)) / "process_engineering"
    target = Path(output_path).expanduser() if output_path.strip() else base / f"{ncname(stem)}{suffix}"
    if target.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ArtifactPathError("output_path harus berekstensi .bpmn atau .xml")
    return resolve_artifact_output(target, create_parents=True)


def _read_source(bpmn_path: str, xml_text: str) -> tuple[str | None, str, dict[str, Any] | None]:
    if bool(bpmn_path.strip()) == bool(xml_text.strip()):
        return None, "", _error("invalid_input", "isi tepat satu dari bpmn_path atau xml_text")
    if xml_text.strip():
        if len(xml_text.encode("utf-8")) > MAX_SOURCE_BYTES:
            return None, "", _error("too_large", f"xml_text melebihi {MAX_SOURCE_BYTES} byte")
        return xml_text, "inline", None
    path = Path(bpmn_path).expanduser()
    if path.suffix.lower() not in ALLOWED_SUFFIXES or not path.is_file():
        return None, "", _error("not_found", "bpmn_path harus file .bpmn atau .xml yang ada", path=str(path))
    if path.stat().st_size > MAX_SOURCE_BYTES:
        return None, "", _error("too_large", f"file melebihi {MAX_SOURCE_BYTES} byte", path=str(path))
    return path.read_text(encoding="utf-8", errors="replace"), path.stem, None


def _build_model(
    process_id: str,
    title: str,
    description: str,
    nodes: list[dict[str, Any]],
    flows: list[dict[str, Any]] | None,
    lanes: list[dict[str, Any]] | None,
) -> tuple[ProcessModel | None, dict[str, Any] | None]:
    if not nodes:
        return None, _error("invalid_spec", "nodes tidak boleh kosong")
    if len(nodes) > MAX_NODES:
        return None, _error("invalid_spec", f"nodes melebihi {MAX_NODES}")
    lane_defs: dict[str, str] = {}
    for lane in lanes or []:
        lane_id = str(lane.get("id") or "").strip()
        if not lane_id or lane_id in lane_defs:
            return None, _error("invalid_spec", f"lane id kosong atau duplikat: '{lane_id}'")
        lane_defs[lane_id] = str(lane.get("name") or lane_id)

    defs: list[NodeDef] = []
    seen: set[str] = set()
    for item in nodes:
        node_id = str(item.get("id") or "").strip()
        if not node_id or node_id in seen:
            return None, _error("invalid_spec", f"node id kosong atau duplikat: '{node_id}'")
        seen.add(node_id)
        bpmn_type = str(item.get("type") or "").strip()
        kind = str(item.get("kind") or "").strip().lower()
        if bpmn_type:
            if bpmn_type not in BPMN_KIND_TAGS:
                return None, _error("invalid_spec", f"type '{bpmn_type}' tidak didukung", node=node_id, supported=sorted(BPMN_KIND_TAGS))
            derived = BPMN_KIND_TAGS[bpmn_type]
            if kind and kind != derived:
                return None, _error("invalid_spec", f"kind '{kind}' tidak cocok dengan type '{bpmn_type}' ({derived})", node=node_id)
            kind = derived
        if kind not in VALID_NODE_KINDS:
            return None, _error("invalid_spec", f"kind node '{node_id}' harus salah satu dari {sorted(VALID_NODE_KINDS)}", node=node_id)
        lane_id = str(item.get("lane") or "").strip() or None
        if lane_id is not None and lane_id not in lane_defs:
            return None, _error("invalid_spec", f"node '{node_id}' memakai lane '{lane_id}' yang tidak dideklarasikan", node=node_id)
        metadata = {"bpmn_type": bpmn_type} if bpmn_type and bpmn_type != DEFAULT_TAG_FOR_KIND[kind] else {}
        defs.append(NodeDef(id=node_id, kind=kind, name=str(item.get("name") or node_id), lane_id=lane_id, metadata=metadata))

    if flows is None:
        flows = [
            {"source": a.id, "target": b.id}
            for a, b in zip(defs, defs[1:])
            if a.kind != NODE_KIND_END
        ]
    if len(flows) > MAX_FLOWS:
        return None, _error("invalid_spec", f"flows melebihi {MAX_FLOWS}")
    edges: dict[str, list[ProcessEdge]] = {d.id: [] for d in defs}
    for flow in flows:
        source, target = str(flow.get("source") or "").strip(), str(flow.get("target") or "").strip()
        if source not in seen or target not in seen:
            return None, _error("invalid_spec", f"flow '{source}' -> '{target}' merujuk node yang tidak ada")
        name = str(flow.get("name") or "").strip() or None
        label = DEFAULT_FLOW_LABEL if flow.get("default") else None
        edges[source].append(ProcessEdge(source_id=source, target_id=target, condition=name, label=label))

    lane_members: dict[str, list[str]] = {lane_id: [] for lane_id in lane_defs}
    for d in defs:
        if d.lane_id:
            lane_members[d.lane_id].append(d.id)
    model = ProcessModel(
        id=process_id or ncname(title),
        title=title,
        description=description,
        nodes=tuple(ProcessNode(definition=d, outgoing=tuple(edges[d.id])) for d in defs),
        lanes=tuple(ProcessLane(definition=LaneDef(id=lane_id, name=name), node_ids=tuple(lane_members[lane_id])) for lane_id, name in lane_defs.items()),
    )
    return model, None


def _model_spec(model: ProcessModel) -> dict[str, Any]:
    return {
        "process_id": model.id,
        "title": model.title,
        "description": model.description,
        "nodes": [
            {
                "id": n.definition.id,
                "name": n.definition.name,
                "kind": n.definition.kind,
                **({"type": n.definition.metadata["bpmn_type"]} if n.definition.metadata.get("bpmn_type") else {}),
                **({"lane": n.definition.lane_id} if n.definition.lane_id else {}),
            }
            for n in model.nodes
        ],
        "flows": [
            {
                "source": e.source_id,
                "target": e.target_id,
                **({"name": e.condition} if e.condition else {}),
                **({"default": True} if e.label == DEFAULT_FLOW_LABEL else {}),
            }
            for n in model.nodes
            for e in n.outgoing
        ],
        "lanes": [{"id": lane.definition.id, "name": lane.definition.name} for lane in model.lanes],
    }


@tool(description=(
    "Generate a BPMN 2.0 file (.bpmn) that opens in Bizagi Modeler, Camunda Modeler and bpmn.io: includes targetNamespace, "
    "pool/lanes, incoming/outgoing and a computed diagram layout (BPMNDiagram). nodes: {id, name, kind(start|end|task|gateway|subprocess), "
    "type?(userTask|serviceTask|parallelGateway|intermediateCatchEvent|...), lane?}; flows: {source, target, name?, default?} "
    "(omitted = sequence of the nodes); lanes: {id, name}. The result reports a structural interchange check; it does not open Bizagi itself."
))
def process_bpmn_generate(
    title: str,
    nodes: list[dict[str, Any]],
    flows: list[dict[str, Any]] | None = None,
    lanes: list[dict[str, Any]] | None = None,
    process_id: str = "",
    description: str = "",
    output_path: str = "",
) -> dict[str, Any]:
    if not str(title or "").strip():
        return _error("invalid_spec", "title wajib diisi")
    model, failure = _build_model(process_id.strip(), title.strip(), description, nodes, flows, lanes)
    if failure is not None:
        return failure
    xml = render_bpmn_text(model)
    issues = check_interchange(xml)
    if errors_only(issues):
        return _error("generated_document_invalid", "dokumen hasil generate gagal cek interchange", interchange=_interchange_summary(issues))
    try:
        target = _output_target(output_path, model.id)
    except ArtifactPathError as exc:
        return _error("path_denied", str(exc))
    target.write_text(xml, encoding="utf-8")
    return {
        "path": str(target),
        "bytes": len(xml.encode("utf-8")),
        "process_id": model.id,
        "node_count": len(model.nodes),
        "flow_count": sum(len(n.outgoing) for n in model.nodes),
        "lane_count": len(model.lanes),
        "interchange": _interchange_summary(issues),
        "model_warnings": validate_process_model(model),
        "import_hint": BIZAGI_IMPORT_HINT,
        "verified_in_bizagi": False,
    }


@tool(description=(
    "Validate a BPMN 2.0 file or XML text for interchange with Bizagi Modeler: targetNamespace, valid unique ids, resolvable references, "
    "lane membership, and the diagram section (a BPMNShape per node, a BPMNEdge with waypoints per flow). Provide exactly one of bpmn_path or xml_text."
))
def process_bpmn_validate(bpmn_path: str = "", xml_text: str = "") -> dict[str, Any]:
    text, label, failure = _read_source(bpmn_path, xml_text)
    if failure is not None:
        return failure
    issues = check_interchange(text)
    summary = _interchange_summary(issues, limit=50)
    try:
        model = parse_bpmn_text(text)
    except ValueError as exc:
        return {"source": label, "valid": False, "interchange": summary, "parse_error": str(exc)}
    return {
        "source": label,
        "valid": summary["errors"] == 0,
        "interchange": summary,
        "process_id": model.id,
        "node_count": len(model.nodes),
        "flow_count": sum(len(n.outgoing) for n in model.nodes),
        "lane_count": len(model.lanes),
        "skipped_elements": list(model.metadata.get("skipped_elements", [])),
        "verified_in_bizagi": False,
    }


@tool(description=(
    "Import a BPMN 2.0 file or XML text (for example exported from Bizagi Modeler) into an editable spec accepted by process_bpmn_generate. "
    "Elements outside the supported subset (boundary events, data objects, annotations, ...) are reported in skipped_elements, never dropped silently."
))
def process_bpmn_import(bpmn_path: str = "", xml_text: str = "") -> dict[str, Any]:
    text, label, failure = _read_source(bpmn_path, xml_text)
    if failure is not None:
        return failure
    try:
        model = parse_bpmn_text(text)
    except ValueError as exc:
        return _error("parse_error", str(exc))
    return {
        "source": label,
        "spec": _model_spec(model),
        "has_diagram": not any(i.code == "diagram:missing-di" for i in check_interchange(text)),
        "skipped_elements": list(model.metadata.get("skipped_elements", [])),
        "dangling_flows": list(model.metadata.get("dangling_flows", [])),
        "extra_processes": list(model.metadata.get("extra_processes", [])),
        "model_warnings": validate_process_model(model),
    }


@tool(description=(
    "Convert an existing BPMN file that Bizagi cannot open (no diagram layout, missing targetNamespace, invalid ids, flowNodeRef as attribute) "
    "into a new interchange-ready .bpmn with a computed layout. The source file is never modified; unsupported elements that cannot be carried over are listed in dropped_elements."
))
def process_bpmn_convert(bpmn_path: str, output_path: str = "") -> dict[str, Any]:
    text, label, failure = _read_source(bpmn_path, "")
    if failure is not None:
        return failure
    before = check_interchange(text)
    try:
        model = parse_bpmn_text(text)
    except ValueError as exc:
        return _error("parse_error", str(exc))
    xml = render_bpmn_text(model)
    after = check_interchange(xml)
    if errors_only(after):
        return _error("generated_document_invalid", "hasil konversi gagal cek interchange", interchange=_interchange_summary(after))
    try:
        target = _output_target(output_path, f"{label}_converted")
    except ArtifactPathError as exc:
        return _error("path_denied", str(exc))
    if Path(bpmn_path).expanduser().resolve() == target:
        return _error("path_denied", "output_path tidak boleh sama dengan file sumber")
    target.write_text(xml, encoding="utf-8")
    return {
        "path": str(target),
        "source": str(Path(bpmn_path).expanduser()),
        "before": _interchange_summary(before),
        "after": _interchange_summary(after),
        "node_count": len(model.nodes),
        "flow_count": sum(len(n.outgoing) for n in model.nodes),
        "dropped_elements": list(model.metadata.get("skipped_elements", [])),
        "dangling_flows": list(model.metadata.get("dangling_flows", [])),
        "import_hint": BIZAGI_IMPORT_HINT,
        "verified_in_bizagi": False,
    }


BPMN_TOOLS = [
    process_bpmn_generate,
    process_bpmn_validate,
    process_bpmn_import,
    process_bpmn_convert,
]
