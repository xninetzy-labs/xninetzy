---
name: api-security
description: Audit API surface for authn/authz gaps, missing rate limits, insecure headers, IDOR, and SSRF. Strictly inside authorized scope. Use when an endpoint is added or changed, or the operator asks for an API surface review.
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: domain
  priority: P1
  required_tools:
    - security_api_inventory
    - security_headers
    - security_threat_model
    - security_scope
    - security_sast
    - security_validate_finding
    - lightning_record_action
  optional_tools:
    - repo_search
    - repo_symbol
    - repo_architecture
    - hitl_request_approval
    - os_inbox
    - memory_security_store
  trigger_conditions:
    - a new HTTP / MCP / WebSocket endpoint is added
    - an auth middleware is changed
    - the operator asks "is this endpoint safe?"
    - a CORS / CSP policy is touched
  prerequisites:
    - explicit authorized scope (via `security_scope`) for live probing
    - target endpoint list reachable (route table or OpenAPI doc)
---

# api-security

API-surface review across HTTP, MCP, WebSocket, and gRPC boundaries.
Companion to `security-review` and the `security_api_inventory` /
`security_headers` MCP tools.

## Pipeline

```
ROUTE_TABLE
   ↓
AUTH_DECORATOR_MAP
   ↓
INPUT_VALIDATION_MAP
   ↓
RATE_LIMIT_MAP
   ↓
HEADER_POLICY_MAP
   ↓
THREAT_MODEL
   ↓
EXPLOITABILITY
   ↓
SecurityFinding
```

The pipeline deliberately separates **presence** of a control from
**effectiveness** of the control. A `Bearer` middleware that accepts any
non-empty token is "present" but not "effective".

## Operating procedure

```
SCOPE
   ↓
INVENTORY_ROUTES
   ↓
MAP_AUTH_DECORATORS
   ↓
FUZZ_INPUT_BOUNDARIES
   ↓
INSPECT_HEADERS
   ↓
CHECK_RATE_LIMITS
   ↓
MODEL_TRUST_BOUNDARIES
   ↓
EMIT_FINDINGS
   ↓
HANDOFF_TO_REGRESSION_TEST
```

## Operating rules

1. Never run live auth-bypass attempts against a system the operator
   does not own.
2. Always pair an IDOR finding with the exact request shape that
   succeeds against an unauthorized ID.
3. Header findings must cite the **expected** value, not just "missing".
4. Rate-limit findings must cite the actual observed limit and the
   burst that bypassed it.
5. SSRF findings must show the response body (truncated) that confirms
   the internal callback landed.

## Required outputs

- Route inventory: `{method, path, auth_decorator, rate_limit, headers}`
- One `SecurityFinding` per missing / ineffective control
- Threat-model matrix: `{asset, entry_point, trust_boundary, sink, control, failure_mode}`
- Regression test stub for every exploitable finding

## Anti-patterns

- "Add authentication" without naming the scheme and the enforcement
  point
- "Use HTTPS" on a server that terminates TLS but re-encrypts internally
  without auth between hops
- Treating CORS `*` as acceptable for credentialed endpoints
