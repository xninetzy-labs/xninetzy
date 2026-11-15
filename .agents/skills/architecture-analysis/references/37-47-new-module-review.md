# architecture-analysis — §37–47

Contents: 37. New Module Review; 38. Architecture Review for Large Refactors; 39. Architecture Smell Taxonomy; 40. Smell Severity; 41. Finding Schema; 42. Evidence Requirement; 43. Refactoring Boundary; 44. Suggested-Fix Format; 45. Graph Output; 46. Architecture Map; 47. Ownership Analysis

## 37. New Module Review

When a new module is added:

new module
   ↓
imports
   ↓
exports
   ↓
consumers
   ↓
layer
   ↓
boundary

Check:

correct layer
dependency direction
unnecessary imports
public surface
feature coupling
shared dependency creation
cycle creation

Report before and after graph deltas.

## 38. Architecture Review for Large Refactors

Required sequence:

BASELINE
   ↓
CURRENT GRAPH
   ↓
CHANGE SET
   ↓
IMPACT GRAPH
   ↓
EXPECTED TARGET ARCHITECTURE
   ↓
DELTA

The skill must first establish the current architecture.

Do not design a target architecture from assumptions alone.

## 39. Architecture Smell Taxonomy

Use stable identifiers:

ARCH-CYCLE
ARCH-LAYER-001
ARCH-DIR-001
ARCH-HOTSPOT
ARCH-GOD-MODULE
ARCH-FRAMEWORK-LEAK
ARCH-DB-LEAK
ARCH-SHARED-DUMP
ARCH-CROSS-FEATURE
ARCH-PUBLIC-API-DRIFT
ARCH-PRIVATE-LEAK
ARCH-STABLE-CORE-DRIFT
ARCH-DOC-DRIFT
ARCH-OWNERSHIP-DRIFT

## 40. Smell Severity

Use:

INFO
LOW
MEDIUM
HIGH

Severity should consider:

scope
fan-out
blast radius
cycle participation
layer violation
change frequency
centrality
public API impact

Do not assign severity solely based on smell category.

## 41. Finding Schema

smell:
  id:
  category:
  severity:
  confidence:

location:
  module:
  file:
  line:
  symbol:

evidence:
  graph_edges:
  metrics:
  source_excerpt:
  history:

architecture:
  inferred_layer:
  expected_layer:
  boundary:
  declared_rule:

impact:
  direct_dependents:
  transitive_dependents:
  public_api:
  blast_radius:

recommendation:
  category:
  consumer:
  producer:
  boundary:
  rationale:

status:
  open
  accepted
  resolved
  false_positive
  unknown

## 42. Evidence Requirement

Every smell must contain at least one of:

exact import/dependency edge
graph metric
cycle path
history metric
public API mapping
diff evidence
source symbol evidence
declared architecture rule

Never emit:

"This architecture feels tightly coupled."

without measurable evidence.

## 43. Refactoring Boundary

The skill may produce:

refactor candidates
boundary candidates
dependency inversion candidates
module extraction candidates
ownership questions

But it must not automatically perform the refactor.

The operator owns:

prioritization
architecture choice
tradeoff selection
migration strategy

## 44. Suggested-Fix Format

Instead of:

add an interface

produce:

Consumer:
  src/application/order-service.ts

Producer:
  src/infrastructure/postgres-order-repository.ts

Current coupling:
  consumer directly imports concrete repository

Observed dependency:
  order-service.ts:17

Potential direction:
  application -> abstraction
  infrastructure -> abstraction implementation

The architecture skill reports the structural opportunity.

It does not silently rewrite the repository.

## 45. Graph Output

Required:

module graph
dependency graph
layered graph
cycle graph
hotspot graph

Preferred formats:

DOT
Mermaid
JSON

Example:

graph TD
    UI --> Application
    Application --> Domain
    Infrastructure --> Domain
    Application --> Infrastructure

Graphs should identify:

nodes
edges
layers
cycles
hotspots
boundary violations

## 46. Architecture Map

Required summary:

Repository
├── applications
├── services
├── packages
│   ├── domain
│   ├── application
│   ├── infrastructure
│   └── shared
└── tests

Every node should expose:

module count
dependency count
fan-in
fan-out
layer
owner
churn

where available.

## 47. Ownership Analysis

If ownership metadata is available:

module
  ->
owner/team

Analyze:

single-owner core
multi-owner module
unowned module
cross-team dependency

Potential smell:

highly central module
+
many teams
+
high churn

Classify as:

OWNERSHIP_HOTSPOT

not as a team-performance judgment.
