name: architecture-analysis



description: >
Evidence-driven static architectural analysis for repositories. Builds module,
dependency, symbol, call, ownership, layer, and boundary models; detects circular
dependencies, dependency-direction violations, layer leakage, unstable/high-churn
modules, god modules, high fan-in/fan-out, architectural hotspots, boundary drift,
public API expansion, misplaced responsibilities, and architecture inconsistencies.
Produces evidence-backed architecture maps, metrics, smells, impact analysis,
and refactor-risk signals without automatically prescribing architectural changes.
Use for codebase overview, architecture health review, module-boundary questions,
large refactors, new module introduction, architecture drift detection, and
change-impact analysis.



metadata:
author: xninetzy
owner: misbahul45
version: "2.0.0"
scope: domain
priority: P1
domain: xninetzy.domains.architecture
lifecycle: >
discover -> inventory -> graph -> classify -> infer ->
assert -> measure -> detect -> correlate -> impact -> report



required_tools:



repo_architecture

repo_dependency

repo_search

repo_symbol



optional_tools:



repo_risk

repo_diff

repo_ownership

repo_test

repo_history

lightning_record_action

learning_attach_resource

memory_architecture_store



trigger_conditions:



the operator asks for an architecture overview

the operator asks whether module X may import Y

a large refactor is planned

a new module is being added

a package or service boundary changes

architecture drift is suspected

the operator asks which modules are risky to change

the operator asks where coupling is concentrated

the operator asks why a change affects many parts of the repository

the operator asks whether dependency direction is healthy

a framework migration is planned

ownership of a module changes



prerequisites:



target repository path reachable

repository can be parsed

import/dependency graph resolvable

source symbols resolvable where supported



non_goals:



automatic refactoring

automatic deletion of modules

automatic package moves

automatic architecture-policy mutation

speculative claims without graph or source evidence



references:
repository_context:
file: ../repo-context-packaging/SKILL.md
use_when:
- repository structure is incomplete
- repository context packaging is required



security_architecture:
file: ../security-threat-model/SKILL.md
use_when:
- architecture review intersects with security trust boundaries

coding: file: ../security-review/SKILL.md use_when: - architectural finding depends on secure coding implementation details

architecture-analysis

Static architectural intelligence layer for Xninetzy.



The skill models the repository as a measurable system rather than a collection
of files.



Core principle:

Architecture claims require structural evidence.

Never emit:

"this module is too coupled"
"the architecture is messy"
"there are too many layers"
"this should be a service"


without measurable or source-backed evidence.

1. Purpose

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


2. Core Pipeline

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


3. Evidence Model

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

4. Repository Inventory

Collect:

repository
branches
workspace/package boundaries
modules
packages
apps
services
libraries
directories
files
symbols
configuration files
build files
dependency manifests
test directories
generated code


Recognize common structures:

apps/
packages/
src/
lib/
core/
domain/
application/
infrastructure/
services/
modules/
features/
components/


Do not assume directory names are architectural truth.

5. Module Identity

A module may be:

package
workspace package
application
service
directory
namespace
source file
framework module
library


The preferred module granularity is the smallest unit that provides meaningful
architectural ownership and dependency information.



For large repositories:

repository
    ↓
workspace
    ↓
package/service
    ↓
module
    ↓
symbol


6. Import Graph

Build:

A -> B


where A imports or depends on B.



Track:

dependency:
  source:
  target:
  kind:
  file:
  line:
  symbol:
  language:
  package:


Kinds:

runtime
type-only
test-only
generated
build-time
optional
dynamic
unknown


Do not mix test-only dependencies with production dependencies when evaluating
production architecture.

7. Dependency Graph

Represent:

module
  ->
module

package
  ->
package

service
  ->
service

application
  ->
library


Track both:

direct dependencies
transitive dependencies


The report must distinguish them.

8. Call Graph

Where tooling supports it, build:

caller
   ->
callee


Record:

call:
  caller_module:
  caller_symbol:
  callee_module:
  callee_symbol:
  file:
  line:
  resolution:
    static
    partial
    dynamic
    unknown


Dynamic dispatch, reflection, dependency injection, metaprogramming, and
generated code may prevent complete resolution.



Report this limitation.

9. Dependency Direction

The skill must determine whether a dependency direction exists.



Examples:

presentation
    ↓
application
    ↓
domain
    ↓
infrastructure


or:

feature
    ↓
shared


Directionality can be:

ALLOWED
SUSPICIOUS
VIOLATION
UNKNOWN


Never assume one universal architecture.

10. Layer Inference

Infer layers from multiple signals:

directory
package name
imports
framework role
symbols
dependencies
annotations
configuration


Possible layer classes:

presentation
application
domain
infrastructure
data
integration
transport
platform
shared
utility
test
generated
unknown


Example:

src/domain/*
  -> likely domain

src/api/*
  -> likely transport/presentation

src/db/*
  -> likely infrastructure/data


Inference confidence:

HIGH
MEDIUM
LOW


The operator's explicitly declared architecture overrides heuristic inference.

11. Declared Architecture

Allow an optional architecture contract:

architecture:
  layers:
    presentation:
    application:
    domain:
    infrastructure:

  allowed_dependencies:
    presentation:
      - application

    application:
      - domain

    domain:
      - domain

    infrastructure:
      - domain

  forbidden_dependencies:
    domain:
      - presentation


This becomes the architectural policy baseline.



Without an explicit contract, the engine should report:

inferred architecture


rather than:

enforced architecture


12. Boundary Model

Boundaries may exist at:

file
module
package
workspace
service
process
database
network
team
domain


Represent:

boundary:
  id:
  name:
  members:
  owner:
  allowed_dependencies:
  forbidden_dependencies:
  public_api:


13. Boundary Violations

Examples:

domain
  -> UI framework

domain
  -> database driver

presentation
  -> direct database access

feature A
  -> private internals of feature B

service A
  -> service B database package

shared utility
  -> business-specific module


Every violation must cite:

file
line
import/dependency
source module
target module


14. Public API Detection

Determine which symbols constitute module API.



Signals:

export
public
package visibility
index/barrel exports
interface
service registration
route registration
dependency injection
public constructors


Track:

public_api:
  module:
  symbol:
  exported_from:
  consumers:


Use this to identify:

unnecessary public surface
API expansion
boundary leakage
internal implementation coupling


15. Private Surface Leakage

Potential smell:

module A
  ->
private/internal implementation
of module B


Evidence:

consumer
private symbol
target file
dependency path


Classify:

DIRECT_PRIVATE_ACCESS
BARREL_LEAKAGE
UNSTABLE_INTERNAL_DEPENDENCY


16. Fan-In / Fan-Out

For each module calculate:

fan_in
fan_out


Where:

fan_in
=
number of distinct modules depending on this module

fan_out
=
number of distinct modules this module depends on


Do not count duplicate imports as multiple dependencies.

17. Coupling Metrics

Where useful calculate:

Ca = afferent coupling
Ce = efferent coupling
I  = Ce / (Ca + Ce)


Interpretation:

I ~ 0
  highly depended upon / stable direction

I ~ 1
  highly dependent / unstable direction


Do not treat coupling values as universal health scores.



Use them as structural signals.

18. Cohesion Signals

Static cohesion may be approximated using:

shared domain entities
shared symbols
internal call density
responsibility concentration
cross-feature references


Do not claim semantic cohesion from directory structure alone.



Classify:

HIGH_CONFIDENCE_SIGNAL
MODERATE_SIGNAL
WEAK_HEURISTIC


19. Cycle Detection

Detect:

A -> B -> C -> A


and larger strongly connected components.



Every cycle finding must include:

full path
edge count
source files
import lines
module owners


Example:

Cycle C-001

A
 ↓
B
 ↓
C
 ↓
A


A cycle at package level and a cycle at file level should be reported separately
when they represent different architectural issues.

20. Strongly Connected Components

Compute strongly connected components where graph support exists.



Classify:

singleton
small cycle
medium cycle
large component


Large strongly connected components are architectural hotspot candidates.



Never label them "bad" without contextual evidence.

21. Architecture Hotspots

A hotspot should not be based only on LOC.



Calculate from:

fan_in
fan_out
churn
change_frequency
dependency_centrality
cycle_membership
public_api_size
incident history where available


Example score:

hotspot =
normalized(
  fan_in
  ×
  fan_out
  ×
  change_frequency
)


Optionally enrich with:

centrality
risk
ownership dispersion


The exact scoring formula must be recorded in the report.

22. Change Frequency

If repository history is available, calculate:

commits
lines_added
lines_deleted
files_changed
distinct_contributors
time_window


Prefer:

module churn


over raw repository-wide commit count.



Example:

churn:
  commits_90d: 37
  files_changed_90d: 24
  lines_changed_90d: 811


23. Hotspot Ranking

Required table:

module
fan_in
fan_out
churn
cycle_membership
centrality
hotspot_score


The ranking is a prioritization aid, not an architectural verdict.

24. God Module Detection

Potential signals:

high fan_in
high fan_out
high LOC
many public symbols
many unrelated dependencies
many unrelated responsibilities
high change frequency


Never classify a module as a god module using LOC alone.



Evidence must include at least:

structural complexity
dependency diversity
responsibility spread


25. Responsibility Smell

Potential smell when one module references unrelated domains.



Example:

User
Billing
Notification
Analytics
Storage
Authentication


all in one module.



Report:

responsibility domains
source symbols
cross-domain references


Do not infer business responsibility solely from variable names.

26. Utility Explosion

Detect shared modules that are depended on by many unrelated domains.



Example:

common
shared
utils
helpers


Potential signals:

very high fan_in
low semantic cohesion
cross-layer dependencies
business-specific logic


Distinguish:

legitimate platform utility


from:

accidental dumping ground


using evidence.

27. Stable-Core Violations

A highly central module should ideally avoid depending heavily on volatile feature
modules.



Detect:

stable core
    ->
volatile feature


when repository history supports the classification.



Report:

core module
dependent feature
dependency edge
core churn
feature churn


28. Dependency Inversion Signals

Potential architectural issue:

high-level business module
    ->
low-level concrete implementation


Example:

domain
    ->
postgres driver


or:

application
    ->
framework-specific transport


Do not automatically recommend interfaces.



First identify:

consumer
producer
coupling
boundary


29. Framework Leakage

Detect framework-specific dependencies crossing boundaries.



Examples:

domain
  -> React

domain
  -> Express/Hono

domain
  -> ORM

application
  -> database driver


Possible classification:

FRAMEWORK_LEAK
INFRASTRUCTURE_LEAK
TRANSPORT_LEAK


Severity depends on declared architecture.

30. Database Leakage

Detect business/application modules importing:

database driver
ORM client
SQL builder
migration implementation
database-specific model


Classify:

DIRECT_DB_ACCESS
INDIRECT_DB_COUPLING
EXPECTED_DATA_LAYER
UNKNOWN


Do not assume every ORM import violates architecture.

31. Cross-Feature Coupling

For feature-oriented architectures:

feature A
   ->
feature B internal implementation


is a potential boundary smell.



Prefer dependency through:

public API
domain contract
application contract
shared stable abstraction


but only report this as a proposal signal, not as an automatic fix.

32. Shared Module Analysis

For shared, common, utils, or similar modules calculate:

consumer_count
consumer_domains
consumer_layers
internal_dependency_count
public_api_count
change_frequency


Potential classifications:

STABLE_SHARED_CORE
PLATFORM_UTILITY
CROSS_DOMAIN_DUMPING_GROUND
LAYER_LEAK_CONTAINER
UNKNOWN


33. Architecture Drift

Compare:

declared architecture
vs
observed dependency graph


Classify:

ALIGNED
DRIFT
UNKNOWN


Example:

Declared:
domain -> infrastructure forbidden

Observed:
domain/user.ts
  imports
infrastructure/postgres.ts

=> DRIFT


34. Architecture Drift Over Time

If historical data is available:

baseline architecture
       ↓
commit history
       ↓
current architecture


Detect:

new boundary violation
new cycle
new dependency direction
new shared dependency
new public API
new cross-feature edge


Classify:

NEW_DRIFT
PERSISTENT_DRIFT
RESOLVED_DRIFT
REGRESSED_DRIFT


35. Change Impact Analysis

When repo_diff is available:

changed files
   ↓
changed symbols
   ↓
dependents
   ↓
callers
   ↓
public APIs
   ↓
affected modules


Output:

impact:
  changed:
  direct_dependents:
  indirect_dependents:
  affected_public_api:
  affected_tests:
  affected_services:
  affected_boundaries:


This is especially important before large refactors.

36. Refactor Blast Radius

For a proposed change:

module X


calculate:

direct consumers
transitive consumers
callers
public API consumers
cycle neighbors
test dependencies


Classify blast radius:

LOCAL
MODERATE
WIDE
SYSTEMIC
UNKNOWN


This is a structural classification, not a prediction of failure.

37. New Module Review

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

38. Architecture Review for Large Refactors

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

39. Architecture Smell Taxonomy

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


40. Smell Severity

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

41. Finding Schema

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


42. Evidence Requirement

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

43. Refactoring Boundary

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


44. Suggested-Fix Format

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

45. Graph Output

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


46. Architecture Map

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

47. Ownership Analysis

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

48. Test Architecture

Where test metadata is available, map:

module
  ->
tests


Check:

orphaned modules
modules with no tests
cross-boundary test coupling
integration-test concentration


Architecture analysis should not infer code correctness from test presence.

49. Generated Code

Detect:

generated files
generated clients
generated ORM
generated protobuf
generated GraphQL


Do not count generated dependency edges as ordinary architectural decisions
without marking them as generated.



Example:

dependency:
  generated: true


50. Dynamic Resolution

Potentially unresolved:

reflection
runtime imports
dependency injection
dynamic module loading
plugin registries
code generation
framework conventions


Record:

resolution:
  complete
  partial
  unresolved


Architecture conclusions must account for unresolved edges.

51. Architecture Confidence

Overall confidence:

HIGH
MEDIUM
LOW


Factors:

parser coverage
graph completeness
dynamic resolution
generated code
architecture contract availability
repository history availability


Example:

confidence:
  graph: HIGH
  layer_inference: MEDIUM
  call_graph: LOW


52. Completion Contract

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


53. Required Outputs

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


54. Standard Report Structure

1. Repository Overview
2. Architecture Summary
3. Layer Model
4. Module Inventory
5. Dependency Graph
6. Call Graph
7. Dependency Direction
8. Boundary Analysis
9. Cycle Analysis
10. Hotspots
11. Coupling Metrics
12. Shared Module Analysis
13. Architecture Smells
14. Architecture Drift
15. Change Impact
16. Refactor Blast Radius
17. Ownership Analysis
18. Test Architecture
19. Evidence
20. Limitations
21. Refactor Candidates


55. Decision Rules

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


56. Example

Input:

src/domain/order.ts


Observed:

order.ts
 -> src/infrastructure/postgres/order-repository.ts


Metrics:

fan_in: 9
fan_out: 4
churn_90d: 21


Architecture inference:

order.ts
  layer = domain
  confidence = high


Declared rule:

domain
  cannot import
infrastructure


Finding:

ARCH-DIR-001
severity: HIGH
confidence: HIGH


Evidence:

src/domain/order.ts:12
direct import of infrastructure implementation


Potential refactor boundary:

Consumer:
  domain/order.ts

Concrete producer:
  infrastructure/postgres/order-repository.ts

Potential abstraction boundary:
  repository contract


No automatic refactor is performed.

57. Anti-Patterns

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

58. Routing

codebase overview
    -> architecture-analysis

security trust-boundary architecture
    -> architecture-analysis
    -> security-threat-model

large refactor
    -> architecture-analysis
    -> repo-diff / repo-context-packaging

secure coding
    -> security-review

dependency vulnerability
    -> xninetzy-security-testing


59. Reference Loading

IF repository context is incomplete
    -> read ../repo-context-packaging/SKILL.md

IF security architecture is involved
    -> read ../security-threat-model/SKILL.md

IF implementation-level security details are involved
    -> read ../security-review/SKILL.md


Reference policy:

architecture-analysis policy
    >
generic assumptions


Security-specific scope and safety controls remain governed by
xninetzy-security-testing when live security testing is involved.

60. Final Principle

The architecture engine should behave as:

graph builder
+
architecture profiler
+
boundary detector
+
hotspot detector
+
change-impact analyzer
+
architecture-drift detector


not as:

automatic refactoring engine


The final quality standard is:

STRUCTURE
+
MEASUREMENT
+
EVIDENCE
+
CONTEXT
+
CHANGE IMPACT


Every meaningful architectural conclusion should be traceable back to:

source
graph
metric
history
declared rule


with uncertainty preserved whenever the repository does not provide enough evidence.

MODULE_LIST
 → IMPORT_GRAPH
 → CALL_GRAPH
 → LAYER_INFERENCE
 → BOUNDARY_CHECK
 → HOTSPOT
 → CYCLE
 → SMELL


现在变成：

REPOSITORY
 ↓
MODULE / SYMBOL INVENTORY
 ↓
IMPORT + DEPENDENCY + CALL GRAPH
 ↓
LAYER + OWNERSHIP INFERENCE
 ↓
BOUNDARY CONTRACT
 ↓
COUPLING / CENTRALITY / CHURN
 ↓
CYCLE / SCC
 ↓
HOTSPOT
 ↓
ARCHITECTURE DRIFT
 ↓
CHANGE IMPACT
 ↓
BLAST RADIUS
 ↓
SMELL CORRELATION
 ↓
EVIDENCE
 ↓
REPORT
