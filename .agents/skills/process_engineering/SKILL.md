---
name: "process_engineering"
description: "Modeling, validating, and exchanging process diagrams for business, operations, BPMN, swimlane, approval workflows, and governance pipelines. Use for drafting processes from text, validating structural soundness (start/end/lane/edge integrity), rendering BPMN 2.0 XML, and storing reusable process artifacts in the Xninetzy catalog. Applies when the owner asks to model a workflow, review a BPMN file, normalize a process diagram, or migrate hand-written flowcharts into the canonical process_engineering model."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "0.1.0"
  lifecycle: "intake -> model -> validate -> render -> store -> review"
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