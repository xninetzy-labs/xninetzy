# architecture-analysis — §25–36

Contents: 25. Responsibility Smell; 26. Utility Explosion; 27. Stable-Core Violations; 28. Dependency Inversion Signals; 29. Framework Leakage; 30. Database Leakage; 31. Cross-Feature Coupling; 32. Shared Module Analysis; 33. Architecture Drift; 34. Architecture Drift Over Time; 35. Change Impact Analysis; 36. Refactor Blast Radius

## 25. Responsibility Smell

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

## 26. Utility Explosion

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

## 27. Stable-Core Violations

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

## 28. Dependency Inversion Signals

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

## 29. Framework Leakage

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

## 30. Database Leakage

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

## 31. Cross-Feature Coupling

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

## 32. Shared Module Analysis

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

## 33. Architecture Drift

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

## 34. Architecture Drift Over Time

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

## 35. Change Impact Analysis

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

## 36. Refactor Blast Radius

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
