from __future__ import annotations

from xninetzy.context.process_engineering.bpmn_io import (
    parse_bpmn_text,
    render_bpmn_text,
)
from xninetzy.context.process_engineering.model import (
    validate_process_model,
)


BPMN_XML = """<?xml version='1.0' encoding='UTF-8'?>
<definitions xmlns:bpmn='http://www.omg.org/spec/BPMN/20100524/MODEL'>
  <process id='proc' name='Demo'>
    <startEvent id='start' name='Start'/>
    <task id='a' name='Step A'/>
    <endEvent id='end' name='End'/>
    <sequenceFlow id='f1' sourceRef='start' targetRef='a'/>
    <sequenceFlow id='f2' sourceRef='a' targetRef='end'/>
  </process>
</definitions>
"""


def test_parse_bpmn_basic():
    model = parse_bpmn_text(BPMN_XML)
    assert model.id == "proc"
    assert {n.definition.id for n in model.nodes} == {"start", "a", "end"}
    assert validate_process_model(model) == []


def test_render_bpmn_roundtrip():
    model = parse_bpmn_text(BPMN_XML)
    text = render_bpmn_text(model)
    again = parse_bpmn_text(text)
    assert {n.definition.id for n in again.nodes} == {
        n.definition.id for n in model.nodes
    }
    assert validate_process_model(again) == []