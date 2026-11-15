# xninetzy-security-testing — §40–45

Contents: 40. Resource and Lease Control; 41. Retry Policy; 42. Failure Classes; 43. Result State; 44. Standard Assessment Report; 45. Finding Format

## 40. Resource and Lease Control

The system must detect scanner resource contention.

State:

```text
idle
running
busy
cooldown
rate_limited
failed
```

Do not launch redundant concurrent scanners against the same target without justification.

Use a target lease:

```yaml
lease:
  target: ...
  session_id: ...
  expires_at: ...
```

---

## 41. Retry Policy

Retry only:

```text
network timeout
transient DNS
temporary scanner failure
temporary service unavailable
```

Do not retry:

```text
authorization denied
scope denied
protected target
credential failure
CAPTCHA
MFA
out-of-scope redirect
policy violation
```

Never retry to defeat a security mechanism.

---

## 42. Failure Classes

```text
AUTHORIZATION_DENIED
PROTECTED_TARGET
SCOPE_DRIFT
DNS_REBINDING
REDIRECT_OUT_OF_SCOPE
TOOL_MISSING
TOOL_VERSION_UNSUPPORTED
TIMEOUT
RATE_LIMITED
NETWORK_UNAVAILABLE
CREDENTIAL_UNAVAILABLE
SECRET_REDACTION_FAILURE
SCANNER_ERROR
INVALID_TARGET
POLICY_VIOLATION
PARTIAL_EVIDENCE
```

---

## 43. Result State

The overall assessment may end in:

```text
COMPLETE
PARTIAL
BLOCKED
FAILED
UNCERTAIN
```

`COMPLETE` means the declared assessment profile executed successfully over the declared scope.

It does not mean the target is secure.

---

## 44. Standard Assessment Report

Every report contains:

```text
Executive Summary
Assessment Scope
Authorization Context
Environment
Asset Inventory
Attack Surface
Technology Inventory
Testing Matrix
Findings
Validated Evidence
False Positives / Duplicates
Risk Prioritization
Authentication Findings
Authorization Findings
API Findings
Web Findings
Code Findings
Dependency Findings
Secret Findings
Container Findings
IaC Findings
Kubernetes Findings
Cloud Findings
Mobile Findings
TLS Findings
MCP Security Findings
Coverage
Unassessed Areas
Remediation Plan
Regression Tests
Retest Status
Tool Versions
Template Versions
Assessment Timeline
Limitations
```

---

## 45. Finding Format

```text
## SEC-2026-0001 — Broken Object Authorization

Severity: HIGH
Confidence: VERIFIED
Asset: https://app.example.test
Endpoint: GET /api/projects/{id}

Observed:
User A could request a resource belonging to User B.

Evidence:
Redacted request/response pair.

Impact:
Potential cross-account data exposure.

Mapping:
API1:2023
ASVS Access Control
WSTG Authorization Testing

Remediation:
Enforce resource ownership/tenant authorization server-side.

Regression:
User A -> own project -> 200
User A -> User B project -> 403
Anonymous -> project -> 401
```

---
