# api-security — §18–25

Contents: 18. gRPC Security; 19. MCP Security; 20. MCP Tool Authorization Matrix; 21. Phase 4 — Input Validation; 22. Input Boundary Classes; 23. Injection Boundaries; 24. SSRF; 25. Rate Limiting

## 18. gRPC Security

Model:

```text
service
  ↓
method
  ↓
metadata
  ↓
identity
  ↓
authorization
```

Check:

```text
TLS
authentication metadata
authorization interceptor
method-level authorization
message validation
reflection exposure
resource limits
error leakage
```

Each sensitive RPC must be individually authorized.

---

## 19. MCP Security

For MCP:

```text
server
  ↓
capability
  ↓
tool/resource/prompt
  ↓
caller identity
  ↓
authorization
```

Check:

```text
tools/list
resources/list
prompts/list
tool authorization
resource authorization
scope propagation
tenant isolation
URI validation
annotation consistency
unexpected network access
secret exposure
cross-tool privilege escalation
```

An advertised tool capability is not proof that the capability is safely enforced.

---

## 20. MCP Tool Authorization Matrix

Example:

```yaml
actor:
  anonymous:
    tools:
      read_public: allow
      admin_action: deny

  user:
    tools:
      read_public: allow
      read_own_data: allow
      read_other_data: deny
      admin_action: deny

  admin:
    tools:
      admin_action: allow
```

Compare:

```text
expected authorization
       vs
observed behavior
```

---

## 21. Phase 4 — Input Validation

For each input:

```text
path
query
header
cookie
body
JSON
form
multipart
GraphQL argument
gRPC field
WebSocket message
MCP tool argument
```

map:

```text
source
validator
normalizer
sink
```

Pipeline:

```text
UNTRUSTED INPUT
   ↓
PARSER
   ↓
NORMALIZER
   ↓
VALIDATOR
   ↓
BUSINESS LOGIC
   ↓
SINK
```

---

## 22. Input Boundary Classes

Check for:

```text
type confusion
missing required field
unexpected property
oversized input
nested object depth
array explosion
string length
numeric bounds
encoding ambiguity
duplicate parameters
content-type confusion
path normalization
```

Focus on security-relevant validation rather than simply generating arbitrary payload volume.

---

## 23. Injection Boundaries

Identify sinks:

```text
SQL
NoSQL
command
template
HTML
JavaScript
LDAP
XPath
expression
log
filesystem
URL
HTTP
```

Source-to-sink analysis should combine:

```text
Semgrep
repo_symbol
repo_search
threat model
runtime evidence
```

Do not call something exploitable solely because an input eventually reaches a sink; establish the relevant escaping/parameterization boundary.

---

## 24. SSRF

Identify URL-fetching sinks:

```text
webhook
URL preview
image import
document fetch
proxy
callback
remote file import
integration endpoint
```

Safe validation may use:

```text
controlled callback endpoint
scope-approved canary
```

Evidence should establish:

```text
application made the outbound request
target was controlled
callback was observed
```

Do not request:

```text
cloud metadata
production internal services
credential endpoints
```

as part of validation.

Do not place internal response bodies containing sensitive data in findings.

---

## 25. Rate Limiting

Distinguish:

```text
configured limit
observed limit
effective limit
```

For each protected route record:

```yaml
rate_limit:
  configured:
  observed:
  window:
  burst:
  identity_key:
  response:
  retry_after:
```

A rate-limit finding requires reproducible evidence that the effective control is weaker than intended.

Do not run unrestricted high-volume traffic.

Use a bounded test budget.

---
