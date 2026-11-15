# architecture-analysis — §4–12

Contents: 4. Repository Inventory; 5. Module Identity; 6. Import Graph; 7. Dependency Graph; 8. Call Graph; 9. Dependency Direction; 10. Layer Inference; 11. Declared Architecture; 12. Boundary Model

## 4. Repository Inventory

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

## 5. Module Identity

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

## 6. Import Graph

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

## 7. Dependency Graph

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

## 8. Call Graph

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

## 9. Dependency Direction

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

## 10. Layer Inference

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

## 11. Declared Architecture

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

## 12. Boundary Model

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
