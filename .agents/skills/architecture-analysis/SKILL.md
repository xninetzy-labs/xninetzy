---
name: architecture-analysis
description: Static architectural review of a repository — module boundaries, dependency direction, circular deps, layer violations, hot-spot identification. Produces a layered map and an evidence-backed list of architectural smells. Use when the operator asks for a "codebase overview", "is this architecture healthy?", or before any large refactor.
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: domain
  priority: P1
  required_tools:
    - repo_architecture
    - repo_dependency
    - repo_search
    - repo_symbol
  optional_tools:
    - repo_risk
    - repo_diff
    - lightning_record_action
    - learning_attach_resource
  trigger_conditions:
    - the operator asks for an architecture overview
    - the operator asks "is module X allowed to import Y?"
    - a large refactor is planned
    - a new module is being added
  prerequisites:
    - target repo path reachable
    - import / call graph resolvable
---

# architecture-analysis

Static architectural review grounded in the import graph and call graph.
Companion to `repo-context-packaging` and the `repo_*` MCP tools.

## Pipeline

```
MODULE_LIST
   ↓
IMPORT_GRAPH
   ↓
CALL_GRAPH
   ↓
LAYER_INFERENCE
   ↓
BOUNDARY_CHECK
   ↓
HOTSPOT_RANK
   ↓
CYCLE_DETECTION
   ↓
SMELL_REPORT
```

Every smell cites `{module_path}:{symbol_or_line}` as evidence. No
"This looks coupled" without a coupling measurement.

## Operating procedure

```
SCAN
   ↓
BUILD_GRAPH
   ↓
INFER_LAYERS
   ↓
ASSERT_BOUNDARIES
   ↓
RANK_HOTSPOTS
   ↓
DETECT_CYCLES
   ↓
EMIT_REPORT
```

## Operating rules

1. Never propose a refactor before emitting the smell report — the
   operator owns the prioritization.
2. Layer inference is heuristic; if it disagrees with the operator's
   known structure, surface the disagreement, do not silently override.
3. Circular dependency findings must show the full cycle path.
4. Hotspot ranking uses `{fan_in × fan_out × change_frequency}` not
   just LOC.
5. Boundary violations cite the exact import statement.

## Required outputs

- Module graph (DOT / Mermaid) with layer coloring
- Cycle list with full path
- Hotspot table: `{module, fan_in, fan_out, churn, score}`
- Smell report: `{smell_id, evidence, severity, suggested_fix_owner}`

## Anti-patterns

- "This codebase has too many layers" without counting the layers
- "Add an interface" without naming the consumer and the producer
- Treating cyclic imports as harmless just because tests pass
