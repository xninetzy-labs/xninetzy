# architecture-analysis — §58–60

Contents: 58. Routing; 59. Reference Loading; 60. Final Principle

## 58. Routing

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

## 59. Reference Loading

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

## 60. Final Principle

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
