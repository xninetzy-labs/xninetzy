# architecture-analysis — §48–51

## 48. Test Architecture

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

## 49. Generated Code

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

## 50. Dynamic Resolution

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

## 51. Architecture Confidence

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
