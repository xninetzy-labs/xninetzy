# code-review — §30–38

Contents: 30. API Compatibility; 31. Public API Expansion; 32. Authentication Review; 33. Authorization Review; 34. Input Validation; 35. Security-Sensitive Sinks; 36. Secrets; 37. Dependencies; 38. Configuration Changes

## 30. API Compatibility

Classify changes:

```text
BACKWARD_COMPATIBLE
POTENTIALLY_BREAKING
BREAKING
UNKNOWN
```

Examples:

```text
new optional response field
  -> usually compatible

remove response field
  -> potentially breaking

make optional field required
  -> potentially breaking

change enum semantics
  -> potentially breaking
```

Do not call a change breaking without consumer evidence or a clearly defined contract.

---

## 31. Public API Expansion

Check whether the patch accidentally exports:

```text
internal symbol
debug endpoint
implementation detail
database type
framework object
credential-bearing object
```

Compare:

```text
before exports
vs
after exports
```

---

## 32. Authentication Review

When auth changes, verify:

```text
authentication mechanism
credential extraction
token validation
issuer
audience
expiration
revocation
session lifecycle
```

Check all callers and affected routes.

Do not consider:

```text
middleware added
```

equivalent to:

```text
authentication enforced correctly
```

---

## 33. Authorization Review

When access control changes, build:

```text
actor
role
resource
action
tenant
```

matrix.

Check for:

```text
BOLA
function-level authorization
property-level authorization
tenant bypass
privilege escalation
```

Use `api-security` where the changed surface is an API endpoint.

---

## 34. Input Validation

Check changed inputs:

```text
path
query
headers
body
files
MCP arguments
WebSocket messages
gRPC fields
```

Trace:

```text
input
 ↓
parser
 ↓
validator
 ↓
business logic
 ↓
sink
```

Potential issues:

```text
missing validation
wrong validator
validation after dangerous sink
validation mismatch
unexpected fields
unsafe defaults
```

---

## 35. Security-Sensitive Sinks

When changed code reaches:

```text
SQL
shell
filesystem
template
HTML
URL fetch
HTTP client
deserialization
command execution
authorization
```

perform deeper analysis.

Where available:

```text
security_sast
```

should corroborate source-to-sink findings.

---

## 36. Secrets

Detect newly introduced:

```text
API key
token
password
private key
cloud credential
database credential
service credential
```

Use:

```text
Gitleaks
Trivy
security_sast
```

Never put secret contents in the review.

Show:

```text
file
line
secret type
redacted evidence
```

---

## 37. Dependencies

When dependency files change:

```text
package.json
package-lock.json
pnpm-lock.yaml
Cargo.lock
Cargo.toml
pyproject.toml
requirements.txt
go.mod
go.sum
```

check:

```text
direct dependency
transitive dependency
version change
license
known vulnerability
runtime/build scope
```

Where available use:

```text
repo_dependency
OSV
Trivy
dep-scan
```

Do not report a dependency as vulnerable without identifying the actual version.

---

## 38. Configuration Changes

Review changes to:

```text
environment variables
feature flags
timeouts
rate limits
CORS
headers
TLS
logging
database
queues
storage
container
deployment
```

Potential issue:

```text
secure default
  ↓
insecure default
```

or:

```text
production-safe configuration
  ↓
developer convenience default
```

---
