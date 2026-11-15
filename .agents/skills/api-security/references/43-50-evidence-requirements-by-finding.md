# api-security — §43–50

Contents: 43. Evidence Requirements by Finding; 44. Validation; 45. Correlation; 46. Deduplication; 47. API Top-Level Coverage; 48. Regression Generation; 49. Change-Aware Review; 50. Risk Prioritization

## 43. Evidence Requirements by Finding

### IDOR/BOLA

Required:

```text
actor
resource ownership
request shape
observed authorization failure
```

### Rate limiting

Required:

```text
expected limit
observed behavior
bounded test window
identity dimension
```

### Header

Required:

```text
expected policy
actual header
affected resource
security consequence
```

### CORS

Required:

```text
Origin
response headers
credential behavior
data sensitivity
browser-relevant impact
```

### SSRF

Required:

```text
controlled target
controlled callback evidence
request correlation
```

### Injection

Required:

```text
source
validation/encoding path
sink
safe evidence
```

---

## 44. Validation

Use:

```text
security_validate_finding
```

Validation must check:

```text
scope
target
repeatability
evidence quality
non-destructive nature
```

If validation is incomplete:

```text
confidence = UNCERTAIN
```

Do not promote findings merely because the scanner severity is high.

---

## 45. Correlation

Correlate:

```text
security_api_inventory
security_headers
security_sast
Nuclei
ZAP
Schemathesis
source analysis
threat model
runtime evidence
```

Example:

```text
ZAP:
  missing authorization signal

Semgrep:
  route missing authorization guard

Runtime:
  unauthorized object accepted

=> one correlated finding
```

---

## 46. Deduplication

Fingerprint from:

```text
protocol
host
endpoint
operation
control
rule
resource
parameter
```

Do not merge findings solely based on:

```text
title
severity
CVE
scanner
```

---

## 47. API Top-Level Coverage

Every review should report coverage across:

```text
Authentication
Authorization
Object-level authorization
Property-level authorization
Function-level authorization
Tenant isolation
Input validation
Injection
SSRF
Rate limiting
Resource exhaustion
CORS
Security headers
TLS
Error handling
Sensitive data
File upload
Business logic
Schema enforcement
Inventory drift
MCP capabilities
```

---

## 48. Regression Generation

For every exploitable finding generate:

```text
security regression candidate
```

Example:

```text
Finding:
BOLA on GET /api/projects/{id}

Regression:

anonymous -> 401
user A own object -> 200
user A other-user object -> 403
admin -> 200
```

For rate limiting:

```text
within budget -> allowed
above configured threshold -> limited
after retry window -> allowed
```

For headers:

```text
response -> required policy present
```

---

## 49. Change-Aware Review

When an endpoint changes, prioritize:

```text
changed route
changed middleware
changed schema
changed authorization policy
changed sink
changed dependency
changed headers
changed rate limiter
```

Then assess adjacent trust boundaries.

Example:

```text
auth middleware changed
    ↓
all protected routes using middleware
    ↓
authorization regression set
```

---

## 50. Risk Prioritization

Consider:

```text
severity
confidence
internet exposure
authentication boundary
authorization boundary
tenant impact
data sensitivity
preconditions
affected population
environment
remediation availability
```

Do not automatically equate:

```text
scanner severity = confirmed impact
```

---
