# cli-creator — §66–75

Contents: 66. Observability; 67. Request ID / Trace ID; 68. Configuration Profiles; 69. Environment Safety; 70. Production Write Guard; 71. URL Safety; 72. Local Script Conversion; 73. Existing Tool Conversion; 74. SDK Wrapping; 75. API Coverage

## 66. Observability

Optional verbose diagnostics:

```bash
tool --verbose ...
```

may expose:

```text
HTTP method
endpoint path
latency
retry count
request ID
response status
```

but must redact:

```text
Authorization
Cookie
API key
secret
password
session token
```

---

## 67. Request ID / Trace ID

When the API provides:

```text
request-id
trace-id
correlation-id
```

preserve it in:

```text
human output
--verbose
JSON metadata
```

Example:

```json
{
  "ok": false,
  "error": {
    "code": "API_ERROR",
    "request_id": "req_123"
  }
}
```

Do not fabricate IDs if the backend does not supply them.

---

## 68. Configuration Profiles

For multi-environment services:

```text
--profile dev
--profile staging
--profile prod
```

or equivalent.

Configuration must make environment explicit.

Never silently point a destructive command at production.

Recommended:

```text
profile
base_url
auth source
timeout
```

---

## 69. Environment Safety

For services with multiple environments:

```text
development
staging
production
```

the CLI should expose the current environment in:

```text
doctor
verbose output
write confirmation
```

Example:

```text
Environment: staging
Action: publish
Target: project proj_123
```

---

## 70. Production Write Guard

When practical:

```text
production
+
destructive write
```

should require explicit confirmation.

The guard must be implemented in code, not merely documented.

---

## 71. URL Safety

Normalize:

```text
scheme
host
port
path
```

Reject malformed URLs.

If a CLI supports arbitrary endpoints through a raw request command:

```text
validate allowed base URL
```

unless the user explicitly requests a separately authorized endpoint configuration.

---

## 72. Local Script Conversion

When source is an existing script:

```text
inspect script
↓
identify inputs
↓
identify outputs
↓
identify phases
↓
identify environment variables
↓
identify side effects
```

Then split:

```text
setup
discovery
download
transform
draft
upload
poll
write
verify
```

Do not merely copy the script behind a new binary name.

---

## 73. Existing Tool Conversion

When source is an existing internal command:

```text
preserve behavior
```

but improve:

```text
stable arguments
stable IDs
JSON output
error handling
doctor
installation
tests
```

Do not intentionally break existing workflows without documenting it.

---

## 74. SDK Wrapping

When an official SDK exists:

```text
CLI
 ↓
domain client
 ↓
SDK
```

prefer using the SDK when it materially improves:

```text
auth
pagination
typing
retries
uploads
webhooks
```

Do not wrap every SDK method automatically.

Expose the subset that future workflows actually need.

---

## 75. API Coverage

Do not implement every endpoint merely because the API exposes them.

Prioritize:

```text
common discovery
common resolve
common reads
common status
common logs
requested writes
rare operations through raw escape hatch
```

This keeps the CLI compact and predictable.

---
