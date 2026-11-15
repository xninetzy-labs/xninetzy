# xninetzy-security-testing — §14–22

Contents: 14. Nuclei Policy; 15. ZAP Policy; 16. Fuzzing Policy; 17. Authentication Testing; 18. Authorization Testing; 19. Business-Logic Security; 20. SSRF-Safe Policy; 21. Finding Evidence Model; 22. Confidence Model

## 14. Nuclei Policy

Nuclei templates are executable security logic.

Therefore:

1. Never execute arbitrary unreviewed templates.
2. Prefer official/pinned template sets.
3. Record template version/hash.
4. Reject templates requesting disallowed behaviors.
5. Limit severity/profile.
6. Limit request rate.
7. Store template provenance.

Template evidence:

```yaml
template:
  id: ...
  version: ...
  sha256: ...
  source: ...
  loaded_at: ...
```

---

## 15. ZAP Policy

Supported:

```text
baseline
api
safe active verification
```

Blocked:

```text
credential brute force
destructive payload testing
unbounded spidering
out-of-scope redirect following
```

ZAP Automation may orchestrate a scan, but the Xninetzy policy layer remains authoritative.

OWASP ZAP is the preferred open-source DAST engine for web/API assessment.

---

## 16. Fuzzing Policy

Fuzzing is permitted only when:

```text
target is explicitly authorized
endpoint belongs to the scope
rate budget exists
concurrency is bounded
request size is bounded
state-changing methods are disabled by default
```

Default:

```text
GET
HEAD
OPTIONS
safe schema-conforming requests
```

POST/PUT/PATCH/DELETE require a separately declared test profile and safe target environment.

No destructive mutation is allowed by this skill.

---

## 17. Authentication Testing

Test authentication controls rather than attempting to break into accounts.

Examples:

```text
missing credential
expired credential
invalid credential
wrong audience
wrong issuer
wrong role
insufficient scope
revoked session
session invalidation
cookie security attributes
token lifetime
authorization context mismatch
```

Never:

```text
password brute force
OTP guessing
CAPTCHA solving
MFA bypass
credential stuffing
credential harvesting
```

---

## 18. Authorization Testing

Authorization is a first-class testing layer.

Model:

```text
Actor
  -> Role
  -> Resource
  -> Action
  -> Environment
```

Test:

```text
same-user same-resource
same-user different-resource
different-user same-resource
lower-privilege role
higher-privilege role
anonymous role
expired role
cross-tenant access
cross-organization access
direct-object-reference boundaries
function-level access
property-level access
```

For APIs, map tests to OWASP API Security categories including BOLA, broken authentication, property-level authorization, function-level authorization, resource consumption, SSRF, security misconfiguration, inventory, and unsafe API consumption.

---

## 19. Business-Logic Security

Automated scanners are insufficient for business logic.

The engine therefore creates a `BusinessFlowMap`.

```text
Actor
 ->
Precondition
 ->
Action
 ->
State transition
 ->
Postcondition
```

Examples:

```text
registration
login
email verification
password reset
checkout
coupon
subscription
role assignment
file upload
approval
refund
invitation
organization membership
MCP tool authorization
```

Test:

```text
order manipulation
workflow skipping
replay
state confusion
duplicate action
privilege boundary violation
rate-limit bypass
race-condition indicators
inconsistent authorization
```

Do not perform destructive financial or irreversible operations.

---

## 20. SSRF-Safe Policy

The engine may detect SSRF indicators.

It must not automatically weaponize SSRF against metadata services or internal infrastructure.

Allowed:

```text
controlled callback infrastructure
scope-approved test endpoint
non-sensitive internal canary
```

Blocked:

```text
cloud metadata
production internal services
credential endpoints
administrative interfaces
```

---

## 21. Finding Evidence Model

Every finding must contain:

```yaml
finding_id: uuid
fingerprint: deterministic_hash
title: string
severity: info | low | medium | high | critical
confidence: suspected | indicated | strong | verified

asset:
  type: domain | endpoint | api | repo | image | iac | k8s | cloud | mobile
  identifier: normalized_identifier

source:
  scanner: ...
  scanner_version: ...
  rule_or_template: ...
  template_hash: ...

evidence:
  type: request_response | source_location | dependency | configuration | scanner
  location: redacted
  summary: redacted
  captured_at: timestamp

mapping:
  cwe: []
  owasp: []
  asvs: []
  wstg: []
  api_top_10: []

impact:
  confidentiality: none | low | medium | high
  integrity: none | low | medium | high
  availability: none | low | medium | high

remediation:
  summary: ...
  verification_test: ...

status:
  open | accepted | mitigated | resolved | false_positive | duplicate
```

---

## 22. Confidence Model

### `suspected`

Scanner indicates a possible issue but no supporting evidence.

### `indicated`

Multiple independent signals suggest the condition.

### `strong`

Direct application/configuration evidence exists but security impact is not fully demonstrated.

### `verified`

The security condition is directly evidenced using a non-destructive validation method.

"Verified" does not mean weaponized exploitation.

---
