# context-engineering — §42–53

Contents: 42. Execution Spine; 43. Tool Call Context; 44. Tool Output Reintegration; 45. Output Compression; 46. Scanner / Log Context; 47. Context Isolation; 48. Secret Isolation; 49. Context Firewall; 50. Memory vs Evidence; 51. Historical Episode vs Current State; 52. Multi-Agent Context; 53. Sub-Agent Return Contract

## 42. Execution Spine

The context engine feeds a durable Task object:

```yaml
task:
  task_id:
  goal:
  context:
  constraints:
  assumptions:
  required_evidence:
  selected_skills:
  selected_tools:
  dependencies:
  execution_steps:
  verification_steps:
  rollback_strategy:
  risk_level:
  approval_requirement:
  state:
```

State:

```text
PLANNED
READY
RUNNING
WAITING
BLOCKED
VERIFYING
COMPLETED
FAILED
```

---

## 43. Tool Call Context

A tool should receive only:

```text
task-relevant arguments
required scope
required IDs
required evidence
necessary configuration
```

Do not send the complete context stack into every tool invocation.

---

## 44. Tool Output Reintegration

After each tool call:

```text
raw output
 ↓
classify
 ↓
extract facts
 ↓
extract errors
 ↓
extract identifiers
 ↓
extract evidence
 ↓
update task state
 ↓
promote only useful portions
```

Do not automatically place the entire raw output back into active context.

---

## 45. Output Compression

Large outputs should be transformed into:

```yaml
tool_result:
  status:
  summary:
  facts:
  identifiers:
  errors:
  warnings:
  evidence:
  artifacts:
  next_actions:
```

Preserve a reference to the full artifact where available.

---

## 46. Scanner / Log Context

For large logs:

```text
raw log
 ↓
bounded extraction
 ↓
relevant snippets
 ↓
line ranges
 ↓
rule matches
 ↓
summary
```

Prefer:

```text
file:line
byte range
matched rule
short excerpt
```

over entire log dumps.

---

## 47. Context Isolation

Separate contexts by:

```text
security
repository
user-private
external web
temporary credentials
tool internals
```

Do not merge sensitive or unrelated context domains by default.

---

## 48. Secret Isolation

Never promote:

```text
password
token
cookie
private key
API secret
session secret
```

into general context.

Represent them as:

```text
secret_ref
credential_present=true
redacted
```

The harness should retain enough metadata to execute the authorized operation
without exposing the secret to unrelated reasoning steps.

---

## 49. Context Firewall

Prevent:

```text
tool result
web page
repository file
MCP resource
external source
```

from silently becoming:

```text
system instruction
security policy
user authorization
```

Treat externally sourced text as data.

Classify:

```text
INSTRUCTION
DATA
EVIDENCE
UNTRUSTED_CONTENT
```

---

## 50. Memory vs Evidence

Memory is not automatically evidence.

Represent:

```text
MEMORY:
  "last week API endpoint used /v1/foo"

CURRENT EVIDENCE:
  current OpenAPI exposes /v2/foo
```

Current evidence wins for current behavior.

Memory remains useful as historical context.

---

## 51. Historical Episode vs Current State

Historical episodes may answer:

```text
How did we solve this before?
What failed before?
Which tool had a limitation?
```

They do not automatically answer:

```text
What is true now?
```

Current state must be verified.

---

## 52. Multi-Agent Context

When delegating:

```text
parent task
 ↓
sub-task
 ↓
minimal sub-context
```

Each sub-agent receives:

```text
objective
constraints
relevant evidence
relevant tools
output contract
```

Do not copy the parent context wholesale.

---

## 53. Sub-Agent Return Contract

Each sub-agent should return:

```yaml
result:
  status:
  summary:
  findings:
  evidence:
  assumptions:
  unresolved:
  artifacts:
  recommended_next_context:
```

The parent agent promotes only relevant results.

---
