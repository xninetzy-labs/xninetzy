# context-engineering — §4–10

Contents: 4. Context Value Model; 5. Criticality Override; 6. L0 — Intent; 7. Intent Normalization; 8. L1 — Immediate State; 9. State Classification; 10. L2 — Tool and Skill Routing

## 4. Context Value Model

Each candidate context item receives:

```yaml
context_score:
  relevance:
  freshness:
  confidence:
  uniqueness:
  decision_value:
  provenance_quality:
  token_cost:
```

Conceptually:

```text
context_value =
(
  relevance
  × freshness
  × confidence
  × decision_value
  × provenance_quality
)
/
token_cost
```

This is a ranking heuristic, not a factual score.

The engine must retain enough critical information even when its token efficiency is poor.

---

## 5. Criticality Override

Some information must survive compaction regardless of token efficiency.

Protected context includes:

```text
user constraints
authorization state
scope
deadlines
error state
resource IDs
file paths
branch/base/head
approval state
unresolved contradictions
security restrictions
required evidence
current task state
```

Never drop these merely because they have low textual relevance.

---

## 6. L0 — Intent

Parse:

```yaml
task:
  goal:
  context:
  constraints:
  assumptions:
  required_evidence:
  candidate_tools:
  candidate_skills:
  dependencies:
  execution_steps:
  verification_steps:
  rollback_strategy:
  risk_level:
  approval_requirement:
```

Intent must be expressed in one sentence:

```text
"Review the current branch for merge-blocking security and architecture issues."
```

Avoid vague intent:

```text
"do it"
"fix this"
"check everything"
```

When the intent is underspecified, derive the narrowest reasonable interpretation
from existing context before asking the user.

Do not invent missing success criteria.

---

## 7. Intent Normalization

Normalize intent into:

```text
OBJECT
ACTION
SCOPE
CONSTRAINTS
EXPECTED_OUTPUT
RISK
```

Example:

```yaml
intent:
  object: repository
  action: security_review
  scope: current_feature_branch
  constraints:
    - no source modifications
  expected_output:
    - findings
    - severity
    - evidence
  risk: medium
```

---

## 8. L1 — Immediate State

Use only the most relevant recent state.

Potential sources:

```text
recent user messages
recent tool outputs
current errors
current files
current task state
active approvals
active TODO
```

Do not simply copy the last ten messages.

Instead:

```text
retrieve recent
↓
rank by current-state relevance
↓
promote only necessary items
```

Prefer:

```text
most recent unresolved state
```

over:

```text
most recent text
```

---

## 9. State Classification

Every L1 item should be classified:

```text
FACT
OBSERVATION
DECISION
CONSTRAINT
ERROR
REQUEST
UNRESOLVED
STALE
```

Example:

```yaml
state:
  type: ERROR
  value: "build fails because module X cannot resolve dependency Y"
  observed_at:
  resolved: false
```

Do not treat historical observations as active failures after they are resolved.

---

## 10. L2 — Tool and Skill Routing

Use:

```text
skill_suggest_for_request
tool_catalog
meta_for
skill_list
skill_get
```

Pipeline:

```text
intent
 ↓
candidate domains
 ↓
candidate skills
 ↓
candidate tools
 ↓
metadata inspection
 ↓
final execution set
```

Do not load every tool schema.

---
