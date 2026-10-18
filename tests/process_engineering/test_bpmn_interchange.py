from __future__ import annotations

import os
from pathlib import Path

import pytest
from lxml import etree

from xninetzy.context.process_engineering.bpmn_check import check_interchange, errors_only
from xninetzy.context.process_engineering.bpmn_io import (
    BPMN_NS,
    DC_NS,
    DD_DI_NS,
    DI_NS,
    ncname,
    parse_bpmn_text,
    render_bpmn_text,
)
from xninetzy.context.process_engineering.layout import LayoutInput, compute_layout
from xninetzy.context.process_engineering.model import (
    LaneDef,
    NodeDef,
    ProcessEdge,
    ProcessLane,
    ProcessModel,
    ProcessNode,
    validate_process_model,
)
from xninetzy.context.process_engineering.validate import validate_against_xml
from xninetzy.tools.internal import bpmn_tools as tools

@pytest.fixture(autouse=True)
def _isolated_db():
    yield


NS = {"b": BPMN_NS, "bpmndi": DI_NS, "dc": DC_NS, "di": DD_DI_NS}

LEGACY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns0:definitions xmlns:ns0="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI">
  <ns0:process id="1proc" name="Legacy">
    <ns0:startEvent id="start" name="Start" />
    <ns0:task id="a b" name="Step" />
    <ns0:endEvent id="end" name="End" />
    <ns0:sequenceFlow id="start__a b" sourceRef="start" targetRef="a b" />
    <ns0:sequenceFlow id="f2" sourceRef="a b" targetRef="end" />
    <ns0:laneSet id="ls"><ns0:lane id="l1" name="Lane"><ns0:flowNodeRef id="start" /><ns0:flowNodeRef id="a b" /></ns0:lane></ns0:laneSet>
  </ns0:process>
</ns0:definitions>
"""

BIZAGI_STYLE = """<?xml version="1.0" encoding="utf-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="d1" targetNamespace="http://www.bizagi.com/bpmn20">
  <collaboration id="c1"><participant id="p1" name="Purchasing" processRef="pr1" /></collaboration>
  <process id="pr1">
    <documentation>Buys things</documentation>
    <laneSet id="ls1">
      <lane id="ln1" name="Buyer"><flowNodeRef>s1</flowNodeRef><flowNodeRef>t1</flowNodeRef><flowNodeRef>ev1</flowNodeRef><flowNodeRef>g1</flowNodeRef></lane>
    </laneSet>
    <startEvent id="s1" name="Need" />
    <manualTask id="t1" name="Fill form" />
    <intermediateCatchEvent id="ev1" name="Wait" />
    <inclusiveGateway id="g1" name="Any?" default="f4" />
    <boundaryEvent id="b1" attachedToRef="t1" />
    <textAnnotation id="ta1"><text>note</text></textAnnotation>
    <endEvent id="e1" name="Done" />
    <sequenceFlow id="f1" sourceRef="s1" targetRef="t1" />
    <sequenceFlow id="f2" sourceRef="t1" targetRef="ev1" />
    <sequenceFlow id="f3" sourceRef="ev1" targetRef="g1" />
    <sequenceFlow id="f4" sourceRef="g1" targetRef="e1" />
    <sequenceFlow id="f5" sourceRef="b1" targetRef="e1" />
  </process>
</definitions>
"""


def _node(node_id, kind, name, lane=None, bpmn_type=None, outgoing=()):
    metadata = {"bpmn_type": bpmn_type} if bpmn_type else {}
    return ProcessNode(definition=NodeDef(id=node_id, kind=kind, name=name, lane_id=lane, metadata=metadata), outgoing=tuple(outgoing))


def _flow(source, target, condition=None, label=None):
    return ProcessEdge(source_id=source, target_id=target, condition=condition, label=label)


def _complex_model() -> ProcessModel:
    nodes = (
        _node("start", "start", "Order received", "sales", outgoing=[_flow("start", "review")]),
        _node("review", "task", "Review order", "sales", "userTask", [_flow("review", "ok")]),
        _node("ok", "gateway", "Valid?", "sales", None, [_flow("ok", "split", "yes", "default"), _flow("ok", "fix", "no")]),
        _node("fix", "task", "Fix order", "sales", outgoing=[_flow("fix", "review")]),
        _node("split", "gateway", "Fork", "ops", "parallelGateway", [_flow("split", "pack"), _flow("split", "bill")]),
        _node("pack", "task", "Pack goods", "ops", outgoing=[_flow("pack", "join")]),
        _node("bill", "subprocess", "Billing", "finance", outgoing=[_flow("bill", "wait")]),
        _node("wait", "task", "Payment received", "finance", "intermediateCatchEvent", [_flow("wait", "join")]),
        _node("join", "gateway", "Join", "ops", "parallelGateway", [_flow("join", "1 end")]),
        _node("1 end", "end", "Done", "ops"),
    )
    lanes = (
        ProcessLane(LaneDef("sales", "Sales"), ("start", "review", "ok", "fix")),
        ProcessLane(LaneDef("ops", "Operations"), ("split", "pack", "join", "1 end")),
        ProcessLane(LaneDef("finance", "Finance"), ("bill", "wait")),
    )
    return ProcessModel("order & fulfil", 'Order <fulfilment> "E2E"', "Handles orders", nodes, lanes)


def _simple_model() -> ProcessModel:
    return ProcessModel(
        "simple", "Simple", "",
        (_node("s", "start", "Start", outgoing=[_flow("s", "t")]), _node("t", "task", "Work", outgoing=[_flow("t", "e")]), _node("e", "end", "End")),
        (),
    )


def _root(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def test_rendered_document_has_everything_bizagi_requires():
    xml = render_bpmn_text(_complex_model())
    root = _root(xml)
    assert root.get("targetNamespace")
    assert root.find("b:collaboration/b:participant", NS).get("processRef") == root.find("b:process", NS).get("id")
    assert root.find("bpmndi:BPMNDiagram/bpmndi:BPMNPlane", NS) is not None
    assert errors_only(check_interchange(xml)) == []
    for tag in ("bpmn", "bpmndi", "dc", "di"):
        assert f"xmlns:{tag}=" in xml.split(">", 2)[1]


def test_lane_membership_is_text_content_not_attribute():
    root = _root(render_bpmn_text(_complex_model()))
    refs = root.findall(".//b:lane/b:flowNodeRef", NS)
    assert refs and all((r.text or "").strip() and r.get("id") is None for r in refs)


def test_every_node_and_flow_is_drawn_and_ids_are_unique_valid_ncnames():
    xml = render_bpmn_text(_complex_model())
    root = _root(xml)
    shapes = {s.get("bpmnElement") for s in root.iterfind(".//bpmndi:BPMNShape", NS)}
    edges = {e.get("bpmnElement") for e in root.iterfind(".//bpmndi:BPMNEdge", NS)}
    process = root.find("b:process", NS)
    nodes = {e.get("id") for e in process if e.tag.split("}")[1] not in {"sequenceFlow", "laneSet", "documentation"}}
    flows = {e.get("id") for e in process.iterfind("b:sequenceFlow", NS)}
    assert nodes <= shapes and flows <= edges
    ids = [e.get("id") for e in root.iter() if e.get("id")]
    assert len(ids) == len(set(ids))
    assert all(ncname(i) == i for i in ids)


def test_node_type_gateway_kind_and_default_flow_survive_a_roundtrip():
    xml = render_bpmn_text(_complex_model())
    root = _root(xml)
    tags = {e.get("id"): e.tag.split("}")[1] for e in root.find("b:process", NS)}
    assert tags["split"] == "parallelGateway" and tags["join"] == "parallelGateway" and tags["ok"] == "exclusiveGateway"
    assert tags["review"] == "userTask" and tags["wait"] == "intermediateCatchEvent" and tags["bill"] == "subProcess"
    gateway = next(e for e in root.iter() if e.get("id") == "ok")
    default_flow = gateway.get("default")
    assert default_flow and root.find(f".//b:sequenceFlow[@id='{default_flow}']", NS).get("targetRef") == "split"
    again = parse_bpmn_text(xml)
    by_id = {n.definition.id: n for n in again.nodes}
    assert by_id["split"].definition.metadata["bpmn_type"] == "parallelGateway"
    assert by_id["ok"].definition.lane_id == "sales" and by_id["bill"].definition.lane_id == "finance"
    assert {(e.target_id, e.condition, e.label) for e in by_id["ok"].outgoing} == {("split", "yes", "default"), ("fix", "no", None)}
    assert validate_process_model(again) == []


def test_render_parse_render_is_stable():
    first = render_bpmn_text(_complex_model())
    second = render_bpmn_text(parse_bpmn_text(first))
    assert first == second


def test_hostile_and_invalid_ids_and_names_are_neutralized():
    xml = render_bpmn_text(_complex_model())
    root = _root(xml)
    assert root.find("b:process", NS).get("name") == 'Order <fulfilment> "E2E"'
    assert root.find("b:process", NS).get("id") == "order___fulfil"
    assert "id_1_end" in xml
    assert errors_only(check_interchange(xml)) == []


def test_nodes_without_lane_get_a_synthesized_lane_when_lanes_exist():
    model = ProcessModel(
        "m", "M", "",
        (_node("a", "start", "A", "l1", outgoing=[_flow("a", "b")]), _node("b", "task", "B", outgoing=[_flow("b", "c")]), _node("c", "end", "C", "l1")),
        (ProcessLane(LaneDef("l1", "Only"), ("a", "c")),),
    )
    xml = render_bpmn_text(model)
    lanes = [lane.get("name") for lane in _root(xml).iterfind(".//b:lane", NS)]
    assert lanes == ["Only", "Unassigned"]
    assert errors_only(check_interchange(xml)) == []


def test_process_without_lanes_renders_a_pool_with_diagram():
    xml = render_bpmn_text(_simple_model())
    root = _root(xml)
    assert root.find(".//b:laneSet", NS) is None
    assert errors_only(check_interchange(xml)) == []
    assert len(list(root.iterfind(".//bpmndi:BPMNShape", NS))) == 4


def test_empty_model_still_renders_a_valid_document():
    xml = render_bpmn_text(ProcessModel("empty", "Empty", "", (), ()))
    assert errors_only(check_interchange(xml)) == []


def _boxes(xml):
    root = _root(xml)
    out = {}
    for shape in root.iterfind(".//bpmndi:BPMNShape", NS):
        b = shape.find("dc:Bounds", NS)
        out[shape.get("bpmnElement")] = tuple(float(b.get(k)) for k in ("x", "y", "width", "height"))
    return out, root


def test_layout_has_no_overlaps_and_keeps_nodes_inside_their_lanes():
    xml = render_bpmn_text(_complex_model())
    boxes, root = _boxes(xml)
    lane_of = {}
    for lane in root.iterfind(".//b:lane", NS):
        for ref in lane.iterfind("b:flowNodeRef", NS):
            lane_of[ref.text.strip()] = lane.get("id")
    names = [n for n in lane_of]
    for index, a in enumerate(names):
        for b in names[index + 1:]:
            ax, ay, aw, ah = boxes[a]
            bx, by, bw, bh = boxes[b]
            assert not (ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah), (a, b)
    for node, lane in lane_of.items():
        x, y, w, h = boxes[node]
        lx, ly, lw, lh = boxes[lane]
        assert lx <= x and x + w <= lx + lw and ly <= y and y + h <= ly + lh, node
    pool = boxes[root.find("b:collaboration/b:participant", NS).get("id")]
    for lane in set(lane_of.values()):
        x, y, w, h = boxes[lane]
        assert pool[0] <= x and x + w <= pool[0] + pool[2] and pool[1] <= y and y + h <= pool[1] + pool[3]


def test_edges_are_orthogonal_and_touch_their_endpoints():
    xml = render_bpmn_text(_complex_model())
    boxes, root = _boxes(xml)
    flows = {f.get("id"): (f.get("sourceRef"), f.get("targetRef")) for f in root.iterfind(".//b:sequenceFlow", NS)}
    for edge in root.iterfind(".//bpmndi:BPMNEdge", NS):
        points = [(float(p.get("x")), float(p.get("y"))) for p in edge.iterfind("di:waypoint", NS)]
        assert len(points) >= 2
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            assert x1 == x2 or y1 == y2
        source, target = flows[edge.get("bpmnElement")]
        for (px, py), name in ((points[0], source), (points[-1], target)):
            x, y, w, h = boxes[name]
            assert x <= px <= x + w and y <= py <= y + h
            assert px in (x, x + w) or py in (y, y + h)


def test_layout_ranks_follow_flow_direction_and_loops_do_not_break_it():
    layout = compute_layout(LayoutInput(
        node_ids=["s", "a", "b", "e"],
        tags={"s": "startEvent", "a": "task", "b": "task", "e": "endEvent"},
        flows=[("f1", "s", "a"), ("f2", "a", "b"), ("f3", "b", "a"), ("f4", "b", "e"), ("f5", "e", "e")],
    ))
    assert layout.ranks["s"] < layout.ranks["a"] < layout.ranks["b"] < layout.ranks["e"]
    assert all(len(points) >= 2 for points in layout.edges.values())
    assert layout.nodes["b"].bottom < layout.pool.bottom


def test_layout_handles_disconnected_and_unknown_references():
    layout = compute_layout(LayoutInput(node_ids=["a", "b"], tags={"a": "task", "b": "task"}, flows=[("f", "a", "ghost")]))
    assert set(layout.nodes) == {"a", "b"} and layout.edges == {}


def test_parser_reads_bizagi_style_documents_and_reports_what_it_skips():
    model = parse_bpmn_text(BIZAGI_STYLE)
    assert model.title == "Purchasing" and model.description == "Buys things"
    kinds = {n.definition.id: (n.definition.kind, n.definition.metadata.get("bpmn_type")) for n in model.nodes}
    assert kinds == {"s1": ("start", None), "t1": ("task", "manualTask"), "ev1": ("task", "intermediateCatchEvent"), "g1": ("gateway", "inclusiveGateway"), "e1": ("end", None)}
    assert set(model.metadata["skipped_elements"]) == {"boundaryEvent:b1", "textAnnotation:ta1"}
    assert model.metadata["dangling_flows"] == ["f5"]
    assert next(n for n in model.nodes if n.definition.id == "g1").outgoing[0].label == "default"
    assert model.lanes[0].node_ids == ("s1", "t1", "ev1", "g1")
    assert next(n for n in model.nodes if n.definition.id == "t1").definition.lane_id == "ln1"
    assert model.metadata["edge_count"] == 4


def test_parser_reads_legacy_flownoderef_attribute_and_multiple_processes():
    model = parse_bpmn_text(LEGACY_XML)
    assert model.lanes[0].node_ids == ("start", "a b")
    two = BIZAGI_STYLE.replace("</definitions>", '<process id="pr2"><startEvent id="x" /></process></definitions>')
    assert parse_bpmn_text(two).metadata["extra_processes"] == ["pr2"]


def test_parser_rejects_bad_input_and_blocks_entity_expansion():
    with pytest.raises(ValueError):
        parse_bpmn_text("")
    with pytest.raises(ValueError):
        parse_bpmn_text("<definitions>")
    with pytest.raises(ValueError):
        parse_bpmn_text("<definitions xmlns='http://www.omg.org/spec/BPMN/20100524/MODEL'/>")
    bomb = '<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "AAAA">]><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"><process id="p" name="&a;"/></definitions>'
    with pytest.raises(ValueError, match="DOCTYPE"):
        parse_bpmn_text(bomb)
    assert check_interchange(bomb)[0].code == "xml:doctype"


def test_check_flags_exactly_what_makes_bizagi_reject_the_legacy_output():
    codes = {i.code for i in errors_only(check_interchange(LEGACY_XML))}
    assert {"xml:missing-target-namespace", "diagram:missing-di", "xml:invalid-id", "xml:flownoderef-attribute"} <= codes


def test_check_detects_broken_diagrams():
    xml = render_bpmn_text(_simple_model())
    root = _root(xml)
    shape = root.find(".//bpmndi:BPMNShape[@bpmnElement='t']", NS)
    shape.getparent().remove(shape)
    edge = root.find(".//bpmndi:BPMNEdge", NS)
    for point in edge.findall("di:waypoint", NS)[1:]:
        edge.remove(point)
    zero = root.find(".//bpmndi:BPMNShape[@bpmnElement='s']/dc:Bounds", NS)
    zero.set("width", "0")
    codes = {i.code for i in errors_only(check_interchange(etree.tostring(root).decode()))}
    assert {"diagram:missing-shape", "diagram:bad-waypoints", "diagram:bad-bounds"} <= codes


def test_check_detects_duplicate_ids_dangling_refs_and_overlaps():
    xml = render_bpmn_text(_simple_model())
    root = _root(xml)
    flow = root.find(".//b:sequenceFlow", NS)
    flow.set("targetRef", "ghost")
    task = root.find("b:process/b:task", NS)
    task.set("id", "s")
    codes = {i.code for i in check_interchange(etree.tostring(root).decode())}
    assert {"xml:duplicate-id", "structural:dangling-flow"} <= codes
    overlap = render_bpmn_text(_simple_model())
    root = _root(overlap)
    for bounds in root.iterfind(".//bpmndi:BPMNShape/dc:Bounds", NS):
        bounds.set("x", "300")
        bounds.set("y", "300")
    assert "diagram:overlap" in {i.code for i in check_interchange(etree.tostring(root).decode())}


def test_check_reports_non_bpmn_and_malformed_input():
    assert check_interchange("<a/>")[0].code == "xml:not-bpmn"
    assert check_interchange("<a")[0].code == "xml:not-well-formed"


def test_validate_against_xml_can_require_interchange():
    good = render_bpmn_text(_simple_model())
    assert validate_against_xml(good, artifact_id="a", checked_at="t", interchange=True).passed
    report = validate_against_xml(LEGACY_XML, artifact_id="a", checked_at="t", interchange=True)
    assert not report.passed and any(i.code == "diagram:missing-di" for i in report.issues)
    assert validate_against_xml(LEGACY_XML, artifact_id="a", checked_at="t").passed


@pytest.mark.skipif(not os.environ.get("XNINETZY_BPMN_XSD_DIR"), reason="set XNINETZY_BPMN_XSD_DIR to a folder with BPMN20.xsd and its imports")
@pytest.mark.parametrize("factory", [_complex_model, _simple_model])
def test_rendered_document_validates_against_the_official_bpmn_xsd(factory):
    schema = etree.XMLSchema(etree.parse(str(Path(os.environ["XNINETZY_BPMN_XSD_DIR"]) / "BPMN20.xsd")))
    document = _root(render_bpmn_text(factory()))
    assert schema.validate(document), schema.error_log


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    for name in ("OUTPUT_DIR", "UNTRACKED_OUTPUT_DIR", "GENERATED_DOCUMENTS_DIR", "RESEARCH_OUTPUT_DIR"):
        monkeypatch.setenv(name, str(tmp_path / "out"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def _call(tool, **kwargs):
    return tool.invoke(kwargs)


SPEC_NODES = [
    {"id": "start", "name": "Order received", "kind": "start", "lane": "sales"},
    {"id": "check", "name": "Check stock", "kind": "task", "type": "serviceTask", "lane": "sales"},
    {"id": "ok", "name": "In stock?", "kind": "gateway", "lane": "sales"},
    {"id": "ship", "name": "Ship", "kind": "task", "lane": "ops"},
    {"id": "end", "name": "Done", "kind": "end", "lane": "ops"},
]
SPEC_FLOWS = [
    {"source": "start", "target": "check"},
    {"source": "check", "target": "ok"},
    {"source": "ok", "target": "ship", "name": "yes", "default": True},
    {"source": "ok", "target": "check", "name": "no"},
    {"source": "ship", "target": "end"},
]
SPEC_LANES = [{"id": "sales", "name": "Sales"}, {"id": "ops", "name": "Operations"}]


def test_generate_tool_writes_an_interchange_ready_file(workspace):
    result = _call(tools.process_bpmn_generate, title="Order to ship", nodes=SPEC_NODES, flows=SPEC_FLOWS, lanes=SPEC_LANES)
    assert result["interchange"]["errors"] == 0 and result["verified_in_bizagi"] is False
    assert result["node_count"] == 5 and result["flow_count"] == 5 and result["lane_count"] == 2
    path = Path(result["path"])
    assert path.suffix == ".bpmn" and path.is_relative_to(workspace / "out")
    assert errors_only(check_interchange(path.read_text(encoding="utf-8"))) == []
    assert "Bizagi" in result["import_hint"]


def test_generate_tool_chains_nodes_when_flows_are_omitted(workspace):
    nodes = [{"id": "a", "kind": "start"}, {"id": "b", "kind": "task"}, {"id": "c", "kind": "end"}]
    result = _call(tools.process_bpmn_generate, title="Chain", nodes=nodes)
    assert result["flow_count"] == 2 and result["model_warnings"] == []


def test_generate_tool_rejects_bad_specs_without_writing(workspace):
    def bad(**over):
        params = {"title": "T", "nodes": SPEC_NODES, "flows": SPEC_FLOWS, "lanes": SPEC_LANES}
        params.update(over)
        return _call(tools.process_bpmn_generate, **params)

    assert bad(title=" ")["error"] == "invalid_spec"
    assert bad(nodes=[])["error"] == "invalid_spec"
    assert "duplikat" in bad(nodes=SPEC_NODES + [SPEC_NODES[0]])["message"]
    assert "lane" in bad(lanes=[SPEC_LANES[0]])["message"]
    assert "tidak ada" in bad(flows=[{"source": "start", "target": "ghost"}])["message"]
    assert bad(nodes=[{"id": "x", "kind": "blob"}])["error"] == "invalid_spec"
    assert bad(nodes=[{"id": "x", "type": "wizardTask"}])["error"] == "invalid_spec"
    assert "tidak cocok" in bad(nodes=[{"id": "x", "kind": "gateway", "type": "userTask"}])["message"]
    assert not list((workspace / "out").rglob("*.bpmn"))


def test_generate_tool_reports_model_warnings_but_still_writes(workspace):
    result = _call(tools.process_bpmn_generate, title="No events", nodes=[{"id": "a", "kind": "task"}, {"id": "b", "kind": "task"}])
    assert "path" in result and any("no start node" in w for w in result["model_warnings"])


def test_generate_tool_confines_output_to_allowed_roots(workspace, tmp_path):
    denied = _call(tools.process_bpmn_generate, title="T", nodes=SPEC_NODES, flows=SPEC_FLOWS, lanes=SPEC_LANES, output_path="/etc/evil.bpmn")
    assert denied["error"] == "path_denied"
    wrong = _call(tools.process_bpmn_generate, title="T", nodes=SPEC_NODES, flows=SPEC_FLOWS, lanes=SPEC_LANES, output_path=str(workspace / "out" / "x.exe"))
    assert wrong["error"] == "path_denied"
    explicit = _call(tools.process_bpmn_generate, title="T", nodes=SPEC_NODES, flows=SPEC_FLOWS, lanes=SPEC_LANES, output_path=str(workspace / "out" / "sub" / "named.bpmn"))
    assert Path(explicit["path"]).name == "named.bpmn"


def test_generate_import_generate_roundtrip_is_lossless(workspace):
    first = _call(tools.process_bpmn_generate, title="Order to ship", nodes=SPEC_NODES, flows=SPEC_FLOWS, lanes=SPEC_LANES, process_id="p1")
    imported = _call(tools.process_bpmn_import, bpmn_path=first["path"])
    assert imported["has_diagram"] is True and imported["skipped_elements"] == []
    spec = imported["spec"]
    assert {(f["source"], f["target"], f.get("name"), f.get("default", False)) for f in spec["flows"]} == {
        ("start", "check", None, False), ("check", "ok", None, False), ("ok", "ship", "yes", True), ("ok", "check", "no", False), ("ship", "end", None, False),
    }
    assert next(n for n in spec["nodes"] if n["id"] == "check")["type"] == "serviceTask"
    second = _call(tools.process_bpmn_generate, title=spec["title"], nodes=spec["nodes"], flows=spec["flows"], lanes=spec["lanes"], process_id=spec["process_id"], output_path=str(workspace / "out" / "again.bpmn"))
    assert Path(first["path"]).read_text(encoding="utf-8") == Path(second["path"]).read_text(encoding="utf-8")


def test_validate_tool_reports_legacy_files_and_accepts_generated_ones(workspace):
    legacy = workspace / "legacy.bpmn"
    legacy.write_text(LEGACY_XML, encoding="utf-8")
    report = _call(tools.process_bpmn_validate, bpmn_path=str(legacy))
    assert report["valid"] is False and report["interchange"]["errors"] >= 3
    generated = _call(tools.process_bpmn_generate, title="Ok", nodes=SPEC_NODES, flows=SPEC_FLOWS, lanes=SPEC_LANES)
    assert _call(tools.process_bpmn_validate, bpmn_path=generated["path"])["valid"] is True
    inline = _call(tools.process_bpmn_validate, xml_text=Path(generated["path"]).read_text(encoding="utf-8"))
    assert inline["valid"] is True and inline["source"] == "inline"
    assert _call(tools.process_bpmn_validate, xml_text="<nope")["parse_error"]


def test_source_tools_validate_their_input(workspace):
    assert _call(tools.process_bpmn_validate)["error"] == "invalid_input"
    assert _call(tools.process_bpmn_validate, bpmn_path="a.bpmn", xml_text="<x/>")["error"] == "invalid_input"
    assert _call(tools.process_bpmn_validate, bpmn_path=str(workspace / "missing.bpmn"))["error"] == "not_found"
    secret = workspace / "notes.txt"
    secret.write_text("x")
    assert _call(tools.process_bpmn_import, bpmn_path=str(secret))["error"] == "not_found"
    assert _call(tools.process_bpmn_import, xml_text="<nope")["error"] == "parse_error"
    huge = workspace / "huge.bpmn"
    huge.write_bytes(b"<a>" + b"x" * (tools.MAX_SOURCE_BYTES + 1))
    assert _call(tools.process_bpmn_import, bpmn_path=str(huge))["error"] == "too_large"


def test_import_tool_reports_skipped_and_dangling_content(workspace):
    result = _call(tools.process_bpmn_import, xml_text=BIZAGI_STYLE)
    assert result["has_diagram"] is False
    assert set(result["skipped_elements"]) == {"boundaryEvent:b1", "textAnnotation:ta1"}
    assert result["dangling_flows"] == ["f5"]
    assert {n["id"]: n.get("type") for n in result["spec"]["nodes"]}["g1"] == "inclusiveGateway"


def test_convert_tool_makes_legacy_files_importable_without_touching_the_source(workspace):
    legacy = workspace / "legacy.bpmn"
    legacy.write_text(LEGACY_XML, encoding="utf-8")
    result = _call(tools.process_bpmn_convert, bpmn_path=str(legacy))
    assert result["before"]["errors"] >= 3 and result["after"]["errors"] == 0
    assert legacy.read_text(encoding="utf-8") == LEGACY_XML
    converted = Path(result["path"])
    assert converted != legacy and errors_only(check_interchange(converted.read_text(encoding="utf-8"))) == []
    assert parse_bpmn_text(converted.read_text(encoding="utf-8")).lanes[0].node_ids == ("start", "a_b")


def test_convert_tool_lists_everything_it_cannot_carry_over(workspace):
    source = workspace / "bizagi.bpmn"
    source.write_text(BIZAGI_STYLE, encoding="utf-8")
    result = _call(tools.process_bpmn_convert, bpmn_path=str(source))
    assert set(result["dropped_elements"]) == {"boundaryEvent:b1", "textAnnotation:ta1"}
    assert result["dangling_flows"] == ["f5"] and result["after"]["errors"] == 0


def test_convert_tool_refuses_to_overwrite_its_source_and_bad_targets(workspace):
    source = workspace / "out" / "src.bpmn"
    source.parent.mkdir(parents=True)
    source.write_text(LEGACY_XML, encoding="utf-8")
    same = _call(tools.process_bpmn_convert, bpmn_path=str(source), output_path=str(source))
    assert same["error"] == "path_denied" and source.read_text(encoding="utf-8") == LEGACY_XML
    assert _call(tools.process_bpmn_convert, bpmn_path=str(source), output_path="/etc/x.bpmn")["error"] == "path_denied"


def test_bpmn_tools_are_registered_with_the_expected_risk_classes():
    from xninetzy.os.policy.action_policy import RiskClass, classify_risk
    from xninetzy.tools.registry import get_tool_groups, get_tool_names

    names = {t.name for t in tools.BPMN_TOOLS}
    assert names <= set(get_tool_names()) and names <= set(get_tool_groups()["process_engineering"])
    assert classify_risk("process_bpmn_validate") is RiskClass.READ and classify_risk("process_bpmn_import") is RiskClass.READ
    assert classify_risk("process_bpmn_generate") is RiskClass.DRAFT and classify_risk("process_bpmn_convert") is RiskClass.DRAFT
