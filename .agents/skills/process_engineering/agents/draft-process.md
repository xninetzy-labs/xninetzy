---
name: "process_engineering:draft-process"
description: "Translate a free-form process description into a canonical ProcessModel and persist it as a draft artifact. Produces a validated BPMN-compatible model with at least one start node, one end node, swimlane assignments, and edge list."
metadata:
  scope: "task"
  owner: "xninetzy"
  language: "en"
  version: "0.1.0"
  lifecycle: "intake -> model -> validate -> store"
---

# Task: Draft a Process

## Inputs

- Owner prompt describing the process in natural language
- Optional existing BPMN XML to import

## Procedure

1. Identify the trigger (start event), terminal states (end events), and
   decisions (gateways).
2. Identify lanes (roles / teams) and assign nodes to lanes.
3. Build a `ProcessModel` using the dataclasses from
   `xninetzy.context.process_engineering.model`.
4. Validate with `validate_process_model`; fix structural issues
   (missing start/end, broken edges).
5. Persist via `os.process_engineering.serializers.serialize_artifact` and
   insert into `process_artifacts` table.

## Outputs

- `ProcessArtifact` with `status="draft"`
- Validation report (passed=True)
- BPMN XML projection (`render_bpmn_text`)