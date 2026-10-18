# BPMN 2.0 Quick Reference

Xninetzy's process_engineering supports a defined subset of BPMN 2.0 and produces files that import into Bizagi Modeler, Camunda Modeler and bpmn.io.

## Supported elements

| BPMN tag                                                                   | NodeKind     | Kept on round trip |
| -------------------------------------------------------------------------- | ------------ | ------------------ |
| `startEvent`                                                               | `start`      | yes                |
| `endEvent`                                                                 | `end`        | yes                |
| `task`, `userTask`, `serviceTask`, `manualTask`, `scriptTask`              | `task`       | exact tag kept     |
| `businessRuleTask`, `sendTask`, `receiveTask`, `callActivity`              | `task`       | exact tag kept     |
| `intermediateCatchEvent`, `intermediateThrowEvent`                         | `task`       | exact tag kept     |
| `exclusiveGateway`, `parallelGateway`, `inclusiveGateway`                  | `gateway`    | exact tag kept     |
| `eventBasedGateway`, `complexGateway`                                      | `gateway`    | exact tag kept     |
| `subProcess`                                                               | `subprocess` | yes (collapsed)    |

Edges are `sequenceFlow` (`name` is the branch condition; the `default` flow of a gateway is kept). Lanes are `laneSet` / `lane` with `flowNodeRef` whose **text content** is the node id. A `collaboration` with one `participant` (the pool) is always written.

## What is written for Bizagi

- `targetNamespace` on `definitions` (required by BPMN 2.0)
- valid, unique NCName ids (invalid ids such as `1 end` become `id_1_end`)
- `incoming` / `outgoing` on every flow node
- a full diagram section: one `BPMNShape` per pool, lane and node, one `BPMNEdge` with waypoints per flow, computed by a layered auto-layout

A file without the diagram section (`BPMNDiagram`) shows up empty in Bizagi Modeler. That is the most common reason a generated `.bpmn` "cannot be opened".

## What is not carried over

Boundary events, text annotations, groups, associations, data objects and data stores are not part of the model. They are never dropped silently: `process_bpmn_import`, `process_bpmn_validate` and `process_bpmn_convert` list them in `skipped_elements` / `dropped_elements`. Flows that touch a skipped element are listed in `dangling_flows`. Only the first `process` of a multi-pool file is read; the others are listed in `extra_processes`.

## Tools

| tool | risk | purpose |
| ---- | ---- | ------- |
| `process_bpmn_generate` | draft | spec (nodes, flows, lanes) to an interchange-ready `.bpmn` |
| `process_bpmn_validate` | read | interchange check of a file or XML text |
| `process_bpmn_import` | read | file to an editable spec, with skipped content reported |
| `process_bpmn_convert` | draft | existing `.bpmn` without layout to a new importable file (source untouched) |

The tools run a structural interchange check and report `verified_in_bizagi: false`: opening the file in Bizagi Modeler is a manual step (File > Import > BPMN 2.0 XML).
