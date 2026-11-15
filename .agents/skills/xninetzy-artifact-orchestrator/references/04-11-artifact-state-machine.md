# xninetzy-artifact-orchestrator — §4–11

Contents: 4. Artifact State Machine; 5. Artifact Identity; 6. Version Semantics; 7. Artifact Manifest; 8. Requirement Contract; 9. Requirement Coverage; 10. Source Ledger; 11. Evidence Contract

## 4. Artifact State Machine

Canonical:

```text
DISCOVERED
   ↓
BOUND
   ↓
SPECIFIED
   ↓
ARCHITECTED
   ↓
PRODUCING
   ↓
INTEGRATING
   ↓
VALIDATING
   ↓
RENDERED
   ↓
QA_PASSED
   ↓
FROZEN
   ↓
DELIVERED
```

Alternative states:

```text
DRAFT
PARTIAL
BLOCKED
REWORK_REQUIRED
INVALIDATED
UNKNOWN
```

External submission states are separate:

```text
SUBMITTED
CONFIRMED
```

---

## 5. Artifact Identity

Every substantial artifact should have:

```yaml
artifact_identity:
  artifact_id:
  artifact_version:
  artifact_type:
  title:
  purpose:
  target:
  source_version:
  created_at:
  updated_at:
```

`artifact_id` identifies the logical artifact.

`artifact_version` identifies a specific content/design state.

---

## 6. Version Semantics

Example:

```text
artifact_id:
report-2026-01

versions:
v1 draft
v2 integrated
v3 qa-revision
v4 frozen
```

Do not label an artifact:

```text
FINAL
```

before required QA passes.

After freeze, changes create a new version and invalidate the previous frozen
state.

---

## 7. Artifact Manifest

For substantial artifacts:

```yaml
artifact_manifest:
  identity:
    artifact_id:
    version:
    type:

  purpose:
  audience:
  target_environment:

  requirements: []

  sources: []

  architecture:
    sections: []
    components: []

  design_system:
  output_formats: []

  validators: []

  delivery:
    required_files: []
    required_links: []

  qa_requirements:
    content:
    structural:
    evidence:
    visual:
    technical:
    accessibility:
```

Simple artifacts may use a reduced manifest.

Do not create artificial metadata when it has no operational value.

---

## 8. Requirement Contract

Each material artifact requirement should map to:

```text
Requirement
→ Artifact Element
→ Evidence
→ Validator
→ Status
```

Conceptual schema:

```yaml
requirement:
  requirement_id:
  statement:
  source:
  mandatory:
  artifact_location:
  evidence_refs: []
  validator:
  status:
```

Possible status:

```text
MISSING
PLANNED
IN_PROGRESS
PRESENT
VERIFIED
BLOCKED
NOT_APPLICABLE
```

---

## 9. Requirement Coverage

For mandatory requirements:

```text
coverage =
verified_requirements / mandatory_requirements
```

Readiness should require:

```text
mandatory requirement coverage = 100%
```

unless an explicit exception is accepted.

Do not count:

```text
PRESENT
```

as:

```text
VERIFIED
```

when substantive validation is required.

---

## 10. Source Ledger

Substantial artifacts should maintain:

```yaml
source:
  source_id:
  title:
  type:
  origin:
  access_status:
  date:
  relevance:
  used_for:
  citation:
  verification_status:
```

Distinguish:

```text
PROVIDED_SOURCE
DISCOVERED_SOURCE
USER_CONTEXT
GENERATED_CONTENT
DERIVED_CALCULATION
```

Generated content must not be represented as an external source.

---

## 11. Evidence Contract

Important claims should map:

```text
Claim
→ Source
→ Evidence
→ Interpretation
→ Artifact location
```

Conceptually:

```yaml
evidence:
  evidence_id:
  claim_id:
  source_id:
  observation:
  interpretation:
  target_location:
  verification_status:
```

Do not use an evidence system to hide unsupported assumptions.

---
