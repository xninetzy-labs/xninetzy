---
name: "process_engineering:review-process"
description: "Audit an existing process artifact for structural integrity, lane coverage, edge reachability, and BPMN round-trip fidelity. Produces a ValidationReport with issues grouped by severity."
metadata:
  scope: "task"
  owner: "xninetzy"
  language: "en"
  version: "0.1.0"
  lifecycle: "load -> validate -> report"
---

# Task: Review a Process

## Inputs

- `artifact_id` (or BPMN file path)

## Procedure

1. Load artifact via `os.process_engineering.bpmn_xml.load_artifact`.
2. Run `validate_against_diagram` for structural checks.
3. Run `validate_against_xml` if BPMN payload is provided.
4. Group issues by code (`structural` / `diagram` / `xml`).
5. Emit `ValidationReport.passed` flag; do **not** mutate the artifact.

## Outputs

- `ValidationReport` with `issues` tuple and `passed` boolean
- Optional list of recommended fixes (new lane / new edge / rename)