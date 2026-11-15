---
name: architecture-analysis
description: 'Static architecture analysis of a repository: module, dependency and layer maps, cycles, dependency-direction violations, god modules, hotspots, drift and change impact. Use for codebase overviews, architecture health checks and before large refactors.'
metadata:
  author: xninetzy
  owner: misbahul45
  version: 2.0.0
  scope: domain
  priority: P1
  domain: xninetzy.domains.architecture
  lifecycle: discover -> inventory -> graph -> classify -> infer -> assert -> measure -> detect -> correlate -> impact -> report
  keywords: api architectural automatically backed boundary builds call changes churn circular dependencies description detection detects driven evidence expansion fan high inconsistencies introduction leakage manual metrics misplaced models new out overview ownership pending prescribing produces public questions refactor repositories responsibilities review risk signals skill smells symbol unstable without
---

# architecture-analysis

Static architectural intelligence layer for Xninetzy: model the repository as a measurable system, not a collection of files.

Core principle: architecture claims require structural evidence. Never say "this module is too coupled", "the architecture is messy", "there are too many layers" or "this should be a service" without measurable or source-backed evidence.

# 0. Skill Contract

- Required tools: `repo_architecture`, `repo_dependency`, `repo_search`, `repo_symbol`.
- Optional tools: `repo_risk`, `repo_diff`, `repo_test`, `lightning_record_action`, `learning_attach_resource`. The v2 spec also names `repo_ownership`, `repo_history` and `memory_architecture_store`; they are not registered, so skip them.
- Triggers: architecture overview; whether module X may import Y; planned large refactor or framework migration; new module; package or service boundary change; suspected drift; risky modules; where coupling concentrates; why a change touches many parts; dependency-direction health; module ownership change.
- Prerequisites: repository reachable and parseable; import/dependency graph resolvable; symbols resolvable where supported.
- Non-goals: automatic refactoring, module deletion, package moves or architecture-policy mutation; speculative claims without graph or source evidence.
- Related skills: `repo-context-packaging` when repository structure is incomplete; `security-threat-model` when the review crosses trust boundaries; `security-review` when a finding depends on secure-coding details.

# 1. Purpose

The analysis must answer:

What are the modules?

How do they depend on each other?

What are the architectural layers?

What dependency direction is intended?

Where are the boundaries?

Which dependencies violate those boundaries?

Where are cycles?

Which modules are architectural hotspots?

Which modules are unstable or central?

Where is architecture drifting from its apparent design?

What changes are likely to have broad impact?

Which findings are measured facts versus heuristics?

# 2. Core Pipeline

REPOSITORY
    ↓
MODULE INVENTORY
    ↓
FILE / SYMBOL INVENTORY
    ↓
IMPORT GRAPH
    ↓
DEPENDENCY GRAPH
    ↓
CALL GRAPH
    ↓
LAYER INFERENCE
    ↓
OWNERSHIP INFERENCE
    ↓
BOUNDARY MODEL
    ↓
METRIC CALCULATION
    ↓
CYCLE DETECTION
    ↓
ARCHITECTURE SMELLS
    ↓
ARCHITECTURE DRIFT
    ↓
CHANGE IMPACT
    ↓
REPORT

# 3. Evidence Model

Every architecture claim must be classified.

OBSERVED
MEASURED
INFERRED
HEURISTIC
UNKNOWN

OBSERVED

Direct source evidence.

Example:

src/domain/user.ts imports src/infrastructure/postgres.ts

MEASURED

Graph-derived metric.

Example:

fan_in = 17
fan_out = 11

INFERRED

Derived architectural classification.

Example:

src/domain/*
=> likely domain layer

HEURISTIC

Pattern-based judgment.

Example:

module may be a god module

UNKNOWN

Insufficient evidence.

Never silently convert UNKNOWN to OBSERVED.

# 52. Completion Contract

An architecture analysis is complete only when:

[ ] repository inventory built
[ ] modules identified
[ ] dependencies resolved
[ ] import graph built
[ ] call graph built where supported
[ ] layers inferred or declared
[ ] boundaries modeled
[ ] fan-in/fan-out calculated
[ ] cycles detected
[ ] hotspots calculated
[ ] architecture smells emitted
[ ] evidence attached
[ ] architecture drift checked
[ ] change impact checked where applicable
[ ] limitations recorded
[ ] graphs generated
[ ] report generated

# 53. Required Outputs

Module Inventory

module
path
layer
owner
fan_in
fan_out
churn

Cycle Report

cycle_id
full_path
edge_count
affected_modules
evidence

Hotspot Report

module
fan_in
fan_out
churn
centrality
cycle_membership
score

Boundary Report

source
target
source_layer
target_layer
rule
evidence
severity

Smell Report

smell_id
category
severity
confidence
evidence
impact
suggested_fix_owner

# 55. Decision Rules

IF architecture contract exists
    -> use it as policy baseline

IF architecture contract does not exist
    -> report inferred architecture

IF dependency edge is unresolved
    -> mark UNKNOWN

IF cycle exists
    -> show full cycle

IF boundary violation exists
    -> cite exact edge

IF hotspot is reported
    -> include metrics

IF historical data exists
    -> include churn

IF diff exists
    -> perform impact analysis

IF evidence is insufficient
    -> do not emit definitive architectural claim

# 57. Anti-Patterns

Never:

"too many layers"

without counting them.

Never:

"too coupled"

without coupling measurements.

Never:

"god module"

from LOC alone.

Never:

"cycle is harmless because tests pass"

Tests do not eliminate architectural cycles.

Never:

"add an interface"

without naming:

consumer
producer
boundary
dependency

Never:

"rewrite the architecture"

without first establishing the current architecture and change impact.

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/04-12-repository-inventory.md` — §4–12: Repository Inventory, Module Identity, Import Graph, Dependency Graph, Call Graph, Dependency Direction, Layer Inference, Declared Architecture, Boundary Model
- `references/13-24-boundary-violations.md` — §13–24: Boundary Violations, Public API Detection, Private Surface Leakage, Fan-In / Fan-Out, Coupling Metrics, Cohesion Signals, Cycle Detection, Strongly Connected Components, Architecture Hotspots, Change Frequency, Hotspot Ranking, God Module Detection
- `references/25-36-responsibility-smell.md` — §25–36: Responsibility Smell, Utility Explosion, Stable-Core Violations, Dependency Inversion Signals, Framework Leakage, Database Leakage, Cross-Feature Coupling, Shared Module Analysis, Architecture Drift, Architecture Drift Over Time, Change Impact Analysis, Refactor Blast Radius
- `references/37-47-new-module-review.md` — §37–47: New Module Review, Architecture Review for Large Refactors, Architecture Smell Taxonomy, Smell Severity, Finding Schema, Evidence Requirement, Refactoring Boundary, Suggested-Fix Format, Graph Output, Architecture Map, Ownership Analysis
- `references/48-51-test-architecture.md` — §48–51: Test Architecture, Generated Code, Dynamic Resolution, Architecture Confidence
- `references/54-standard-report-structure.md` — §54: Standard Report Structure
- `references/56-example.md` — §56: Example
- `references/58-60-routing.md` — §58–60: Routing, Reference Loading, Final Principle
