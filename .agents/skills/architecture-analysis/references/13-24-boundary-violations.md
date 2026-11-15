# architecture-analysis — §13–24

Contents: 13. Boundary Violations; 14. Public API Detection; 15. Private Surface Leakage; 16. Fan-In / Fan-Out; 17. Coupling Metrics; 18. Cohesion Signals; 19. Cycle Detection; 20. Strongly Connected Components; 21. Architecture Hotspots; 22. Change Frequency; 23. Hotspot Ranking; 24. God Module Detection

## 13. Boundary Violations

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

## 14. Public API Detection

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

## 15. Private Surface Leakage

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

## 16. Fan-In / Fan-Out

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

## 17. Coupling Metrics

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

## 18. Cohesion Signals

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

## 19. Cycle Detection

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

## 20. Strongly Connected Components

Compute strongly connected components where graph support exists.

Classify:

singleton
small cycle
medium cycle
large component

Large strongly connected components are architectural hotspot candidates.

Never label them "bad" without contextual evidence.

## 21. Architecture Hotspots

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

## 22. Change Frequency

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

## 23. Hotspot Ranking

Required table:

module
fan_in
fan_out
churn
cycle_membership
centrality
hotspot_score

The ranking is a prioritization aid, not an architectural verdict.

## 24. God Module Detection

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
