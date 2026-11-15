---
name: process-engineering
description: 'Models, validates and exchanges process diagrams (BPMN 2.0, swimlanes, approval workflows): drafts from text, checks structural soundness, renders BPMN XML and stores reusable artifacts. Use to model a workflow or review a BPMN file.'
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: 0.1.0
  lifecycle: intake -> model -> validate -> render -> store -> review
  keywords: applies asks business canonical catalog diagram drafting edge end engineering exchanging flowcharts for governance hand integrity into lane migrate modeling normalize operations owner pipelines processes rendering start storing swimlane validating when written xninetzy
---

# Process Engineering

This skill produces **canonical, validated, exchangeable process models**. The
single source of truth is the `ProcessModel` dataclass in
`xninetzy/context/process_engineering/model.py`. Every other representation
(text, BPMN XML, swimlane diagram) is a projection of that model.

The core loop:

**Intake → Model → Validate → Render → Store → Review**

The system should answer:

- What nodes exist and what is their kind (task/start/end/gateway/subprocess)?
- Which lane owns each node, and which role is accountable?
- Which edges are valid, which conditions branch, and which nodes are unreachable?
- Can the artifact be rendered to BPMN 2.0 XML and round-tripped?

## When to use

Use this skill whenever the owner asks to:

- Draft a new operational or approval workflow
- Review an existing process diagram for completeness
- Convert a free-form description into a structured BPMN-compatible model
- Diff two process artifacts or detect regressions

Do **not** use this skill for running processes, triggering actions, or
executing tasks — those belong to workflow orchestration tools.
## BPMN files for Bizagi Modeler

Use the registered tools instead of writing BPMN XML by hand:

1. `process_bpmn_generate(title, nodes, flows, lanes)` writes a `.bpmn` with pool, lanes and a computed diagram layout.
2. `process_bpmn_validate(bpmn_path)` lists what an importer would reject (missing `targetNamespace`, missing diagram, invalid ids, dangling references).
3. `process_bpmn_import(bpmn_path)` turns an existing file into an editable spec and reports elements outside the supported subset.
4. `process_bpmn_convert(bpmn_path)` makes an old file importable (adds layout, fixes ids) without touching the source.

Report the result honestly: the tools check structure only. Say that opening the file in Bizagi Modeler is an unverified manual step, and list every entry of `skipped_elements` or `dropped_elements` under limitations.
