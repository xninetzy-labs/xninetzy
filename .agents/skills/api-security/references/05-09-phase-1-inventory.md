# api-security — §5–9

Contents: 5. Phase 1 — Inventory; 6. Protocol Classification; 7. API Surface Completeness; 8. Phase 2 — Authentication Map; 9. Authentication Effectiveness

## 5. Phase 1 — Inventory

Use:

```text
security_api_inventory
```

Accept inventory sources:

```text
route table
OpenAPI
GraphQL schema
protobuf/gRPC descriptors
MCP tool inventory
WebSocket route registry
source code
observed application calls
```

Normalize to:

```yaml
route:
  protocol:
  method:
  path:
  operation_id:
  authentication:
  authorization:
  input_schema:
  output_schema:
  rate_limit:
  security_headers:
  owner:
  source:
```

---

## 6. Protocol Classification

Every endpoint must be classified:

```text
HTTP
REST
GraphQL
WebSocket
gRPC
MCP
```

Then select protocol-specific controls.

```text
REST
 -> route + resource + method

GraphQL
 -> operation + resolver + object + field

WebSocket
 -> connection + message + event + channel

gRPC
 -> service + method + message + metadata

MCP
 -> server + capability + tool/resource + caller
```

---

## 7. API Surface Completeness

Compare multiple inventory sources:

```text
route table
      +
OpenAPI
      +
frontend/network calls
      +
source symbols
      +
runtime observations
```

Classify differences:

```text
DOCUMENTED_ONLY
IMPLEMENTED_ONLY
RUNTIME_ONLY
DEPRECATED
SHADOW_ENDPOINT
DRIFT
UNKNOWN
```

An undocumented live endpoint is a security finding candidate even when it is not obviously vulnerable.

---

## 8. Phase 2 — Authentication Map

For every protected operation identify:

```text
authentication mechanism
credential location
issuer
audience
token type
session type
expiration
refresh behavior
revocation
required scopes
```

Test, where authorized:

```text
anonymous
missing credential
invalid credential
expired credential
revoked credential
wrong audience
wrong issuer
insufficient scope
wrong authentication scheme
```

Do not test credential guessing.

---

## 9. Authentication Effectiveness

Model:

```text
Expected:
GET /api/profile
  requires authenticated user

Observed:
GET /api/profile
  anonymous -> 200
```

Finding:

```text
AUTHN_BYPASS
```

But:

```text
middleware_exists = true
```

is not enough to prove:

```text
authentication_effective = true
```

Evidence must come from actual enforcement or equivalent strong source evidence.

---
