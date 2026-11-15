---
name: api-security
description: Assesses authorized API surfaces (HTTP/REST, GraphQL, MCP, WebSocket, gRPC) for authn/authz gaps, IDOR, injection, SSRF, rate limits, CORS, headers and TLS. Use when an endpoint, tool or auth policy is added or changed.
metadata:
  keywords: access asks assessment audit audits authentication authorization boundaries boundary business controls drift driven enforcement evidence exhaustion exposure function header input insecure inside inventory limiter limiting logic method middleware missing object operator property resource review route schema scope secret security strictly surface trust validation
---


# 1. Security Model

Every API review must analyze:

```text
Asset
  ↓
Entry Point
  ↓
Identity
  ↓
Authorization Context
  ↓
Input
  ↓
Validation
  ↓
Business Logic
  ↓
Sensitive Sink
  ↓
External Dependency
  ↓
Response / State Change
```

The review must distinguish:

```text
PRESENT
EFFECTIVE
VERIFIED
UNKNOWN
```

---

# 2. Core Invariants

1. Scope must be established before live probing.
2. Every live target must belong to the authorized scope.
3. Schema evidence and runtime evidence must remain distinguishable.
4. Authentication presence does not prove authentication correctness.
5. Authorization middleware presence does not prove authorization correctness.
6. An HTTP `401` or `403` alone does not prove secure authorization.
7. CORS configuration does not replace authentication or authorization.
8. A security header is not automatically effective merely because it exists.
9. Rate-limit configuration does not prove an effective runtime limit.
10. Input validation configuration does not prove sink safety.
11. Scanner output is evidence, not final truth.
12. High-impact findings should be independently corroborated where feasible.
13. Unknown must not become safe merely because no scanner reported a finding.
14. Unknown must not become vulnerable merely because a scanner raised an alert.
15. No destructive request.
16. No credential attack.
17. No bypass of CAPTCHA, OTP, MFA, or anti-bot controls.
18. No scope expansion through redirects, DNS, API references, or imported schemas.
19. No secrets in findings, logs, or model output.
20. Every confirmed exploitable condition should generate a regression candidate.

---

# 3. Assessment Pipeline

```text
SCOPE
  ↓
INVENTORY
  ↓
PROTOCOL CLASSIFICATION
  ↓
AUTHENTICATION MAP
  ↓
AUTHORIZATION MAP
  ↓
INPUT / OUTPUT MAP
  ↓
RATE-LIMIT MAP
  ↓
HEADER / CORS MAP
  ↓
TRUST-BOUNDARY MAP
  ↓
THREAT MODEL
  ↓
STATIC ANALYSIS
  ↓
RUNTIME ANALYSIS
  ↓
CORRELATION
  ↓
SAFE VALIDATION
  ↓
RISK TRIAGE
  ↓
REGRESSION
  ↓
REPORT
```

---

# 4. Phase 0 — Scope

Use:

```text
security_scope
```

Required:

```text
target
protocol
environment
allowed methods
allowed paths
allowed identities
testing profile
rate budget
time budget
```

Example:

```yaml
scope:
  target: https://api.example.test
  environment: staging

  methods:
    - GET
    - HEAD
    - OPTIONS

  paths:
    - /api/*
    - /graphql

  profiles:
    - api-baseline
    - authorization

  limits:
    requests_per_second: 5
    concurrency: 5
```

Any live assessment outside the manifest is blocked.

---

# 51. Output

Required outputs:

```text
route_inventory.json
control_matrix.json
threat_model.json
security_findings.json
api-security-report.md
regression-tests.md
coverage.json
```

Optional:

```text
SARIF
HTML
PDF
```

---

# 53. Routing

```text
endpoint security review
    -> api-security

overall web security assessment
    -> xninetzy-security-testing

secure coding review
    -> security-review
    -> security-sast

architecture threat model
    -> security-threat-model

dependency vulnerability
    -> xninetzy-security-testing

MCP-specific surface
    -> api-security
    -> xninetzy-security-testing
```

---

# 55. Completion Contract

An API security review is complete only when:

```text
[ ] scope validated
[ ] endpoint inventory available
[ ] protocol classified
[ ] authentication mapped
[ ] authorization mapped
[ ] tenant boundary considered
[ ] input boundaries mapped
[ ] rate limiting assessed
[ ] security headers assessed
[ ] CORS assessed where relevant
[ ] SSRF sinks considered
[ ] schema drift assessed
[ ] business logic considered
[ ] applicable protocol-specific controls assessed
[ ] static evidence correlated
[ ] runtime evidence validated where authorized
[ ] findings deduplicated
[ ] confidence assigned
[ ] limitations recorded
[ ] regression candidates produced
[ ] report generated
```

---

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/05-09-phase-1-inventory.md` — §5–9: Phase 1 — Inventory, Protocol Classification, API Surface Completeness, Phase 2 — Authentication Map, Authentication Effectiveness
- `references/10-17-phase-3-authorization-map.md` — §10–17: Phase 3 — Authorization Map, Authorization Dimensions, IDOR / BOLA, Property-Level Authorization, Function-Level Authorization, Tenant Isolation, GraphQL Security, WebSocket Security
- `references/18-25-grpc-security.md` — §18–25: gRPC Security, MCP Security, MCP Tool Authorization Matrix, Phase 4 — Input Validation, Input Boundary Classes, Injection Boundaries, SSRF, Rate Limiting
- `references/26-34-rate-limit-dimensions.md` — §26–34: Rate-Limit Dimensions, Security Headers, CORS, HTTP Method Security, Content-Type and Parser Boundaries, File Upload Security, Resource Exhaustion, Error Handling, Sensitive Data Exposure
- `references/35-42-business-logic.md` — §35–42: Business Logic, API Schema Enforcement, Schema Drift, Threat Model, Static + Runtime Correlation, Finding Confidence, SecurityFinding Schema, One Finding Per Control Failure
- `references/43-50-evidence-requirements-by-finding.md` — §43–50: Evidence Requirements by Finding, Validation, Correlation, Deduplication, API Top-Level Coverage, Regression Generation, Change-Aware Review, Risk Prioritization
- `references/52-final-report-structure.md` — §52: Final Report Structure
- `references/54-reference-loading.md` — §54: Reference Loading
- `references/56-final-principle.md` — §56: Final Principle
