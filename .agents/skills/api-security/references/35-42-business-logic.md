# api-security — §35–42

Contents: 35. Business Logic; 36. API Schema Enforcement; 37. Schema Drift; 38. Threat Model; 39. Static + Runtime Correlation; 40. Finding Confidence; 41. SecurityFinding Schema; 42. One Finding Per Control Failure

## 35. Business Logic

API security must not stop at transport controls.

For important workflows model:

```text
precondition
  ↓
action
  ↓
state transition
  ↓
postcondition
```

Test safe indicators for:

```text
workflow skipping
replay
duplicate action
state confusion
authorization inconsistency
price/quantity manipulation
approval bypass
resource ownership transition
```

Do not execute irreversible transactions.

---

## 36. API Schema Enforcement

Compare declared schema with implementation.

Check:

```text
required fields
types
enum restrictions
maximum values
minimum values
unknown fields
response shape
additionalProperties
nullable fields
authentication requirements
security schemes
```

Potential issue:

```text
schema says field is restricted
implementation accepts arbitrary value
```

---

## 37. Schema Drift

Create:

```text
DOCUMENTED
IMPLEMENTED
OBSERVED
```

matrix.

Example:

```text
OpenAPI:
POST /users/{id}

Runtime:
POST /users/{id}/admin

Source:
POST /users/{id}/admin

Result:
SHADOW_ENDPOINT / DOCUMENTATION_DRIFT
```

Drift should be reviewed because undocumented routes often escape normal security testing.

---

## 38. Threat Model

Use:

```text
security_threat_model
```

Required matrix:

```yaml
threat:
  asset:
  entry_point:
  actor:
  trust_boundary:
  input:
  sink:
  control:
  failure_mode:
  evidence:
  impact:
  mitigation:
```

At minimum model:

```text
internet
reverse proxy
gateway
API
service
database
queue
third-party service
browser
MCP server
```

---

## 39. Static + Runtime Correlation

Preferred:

```text
route inventory
      +
source analysis
      +
threat model
      +
runtime evidence
```

Example:

```text
Route:
PATCH /users/:id

Semgrep:
authorization middleware absent

Runtime:
other-user update -> 200

Conclusion:
strong / verified finding
```

This is substantially stronger than either source-only or scanner-only analysis.

---

## 40. Finding Confidence

```text
SUSPECTED
INDICATED
STRONG
VERIFIED
```

#### SUSPECTED

Single heuristic.

#### INDICATED

Multiple independent signals.

#### STRONG

Direct source/configuration evidence exists.

#### VERIFIED

Safe runtime behavior directly confirms the security condition.

---

## 41. SecurityFinding Schema

Every finding must contain:

```yaml
finding:
  id:
  title:
  category:
  severity:
  confidence:
  evidence_level:

asset:
  protocol:
  host:
  endpoint:
  operation:

control:
  expected:
  observed:
  effectiveness:

evidence:
  source:
  runtime:
  timestamps:
  redacted_request:
  redacted_response:

impact:
  confidentiality:
  integrity:
  availability:

mapping:
  cwe:
  owasp:
  asvs:
  api_top_10:
  wstg:

remediation:
  root_cause:
  recommendation:
  validation_method:

regression:
  exists:
  test_stub:

status:
  open
  false_positive
  duplicate
  accepted_risk
  mitigated
  resolved
  regressed
```

---

## 42. One Finding Per Control Failure

Do not create one giant finding:

```text
"API is insecure"
```

Prefer:

```text
SEC-001
Broken object authorization

SEC-002
Missing rate-limit enforcement

SEC-003
Sensitive response exposure
```

This makes:

```text
triage
ownership
remediation
regression
```

precise.

---
