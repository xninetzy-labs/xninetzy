# xninetzy-artifact-orchestrator — §33–38

Contents: 33. Phase 13 — FREEZE; 34. Final Artifact Identity; 35. Phase 14 — CHECKPOINT; 36. Phase 15 — DELIVER; 37. Output Package; 38. Artifact State Contract

## 33. Phase 13 — FREEZE

Freeze only after required QA passes.

Freeze record:

```yaml
freeze:
  artifact_id:
  version:
  final_path:
  checksum:
  frozen_at:
  qa_state:
```

After freeze:

```text
unplanned edit
→ new version
```

Do not modify a frozen artifact silently.

---

## 34. Final Artifact Identity

The final response should identify:

```text
artifact type
artifact name
artifact version
exact path
package contents
QA state
```

Do not give ambiguous labels such as:

```text
final.pdf
latest.pdf
new-final.pdf
```

without an identifiable version/state when multiple variants exist.

---

## 35. Phase 14 — CHECKPOINT

For long-running work, preserve:

```yaml
checkpoint:
  artifact_goal:
  artifact_id:
  version:
  completed_stages: []
  artifact_paths: []
  important_decisions: []
  qa_state:
  unresolved_defects: []
  next_action:
  resume_hint:
```

Use durable memory only when persistence is required.

Do not turn artifact checkpoints into a general project-management database.

---

## 36. Phase 15 — DELIVER

Delivery should provide:

```text
verified final artifact
required companion artifacts
required links
package manifest
known exceptions
current state
```

The delivery result must distinguish:

```text
local delivery
external handoff
external submission
submission confirmation
```

---

## 37. Output Package

For multi-file artifacts:

```text
deliverable/
├── primary artifact
├── supporting artifacts
├── required dataset/data
├── required links
└── package manifest
```

Do not include:

```text
temporary files
debug artifacts
intermediate drafts
internal logs
```

unless required.

---

## 38. Artifact State Contract

Every substantial operation should expose:

```yaml
artifact_result:
  artifact_id:
  version:
  type:
  state:

  requirements:
    coverage:
    unresolved: []

  evidence:
    verified:
    unresolved: []

  generation:
    status:
    paths: []

  validation:
    content:
    structural:
    technical:
    visual:

  qa:
    critical:
    high:
    medium:
    low:

  freeze:
    status:

  delivery:
    package:
    status:

  next_action:
```

---
