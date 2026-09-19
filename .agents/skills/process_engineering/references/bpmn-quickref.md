# BPMN 2.0 Quick Reference

Xninetzy's process_engineering MVP supports a strict subset of BPMN 2.0,
sufficient for round-trip with most diagramming tools (Bizagi Modeler,
Camunda Modeler, bpmn.io). Supported elements:

| BPMN tag            | NodeKind       |
| ------------------- | -------------- |
| `startEvent`        | `start`        |
| `endEvent`          | `end`          |
| `task`              | `task`         |
| `userTask`          | `task`         |
| `serviceTask`       | `task`         |
| `exclusiveGateway`  | `gateway`      |
| `parallelGateway`   | `gateway`      |
| `subProcess`        | `subprocess`   |

Edges use `<sequenceFlow>` with `sourceRef` and `targetRef`. Lanes use
`<laneSet>` / `<lane>` / `<flowNodeRef>`. The parser is namespace-aware
(default namespace `http://www.omg.org/spec/BPMN/20100524/MODEL`).

Anything outside this subset is ignored during parse and silently dropped
during render. This is intentional: the goal is **canonical fidelity**, not
full BPMN coverage.