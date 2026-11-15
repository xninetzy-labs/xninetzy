# api-security — §26–34

Contents: 26. Rate-Limit Dimensions; 27. Security Headers; 28. CORS; 29. HTTP Method Security; 30. Content-Type and Parser Boundaries; 31. File Upload Security; 32. Resource Exhaustion; 33. Error Handling; 34. Sensitive Data Exposure

## 26. Rate-Limit Dimensions

Determine whether limits are based on:

```text
IP
user
API key
tenant
session
route
resource
global
```

Check for inconsistent enforcement:

```text
per-IP limit
but unlimited authenticated requests

or

per-route limit
but expensive operation bypasses route limiter
```

---

## 27. Security Headers

Use:

```text
security_headers
```

Check relevant headers according to the endpoint/application context:

```text
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
Permissions-Policy
Cache-Control
Set-Cookie attributes
CORS response headers
```

Never report:

```text
missing header
```

without explaining:

```text
expected policy
actual policy
affected resource
security consequence
```

Example:

```text
Expected:
Secure + HttpOnly + SameSite policy

Observed:
Secure absent

Impact:
session cookie may be exposed over an unintended transport path
```

Only claim the impact supported by evidence.

---

## 28. CORS

Check:

```text
origin reflection
wildcard origin
credentialed requests
preflight behavior
method restrictions
header restrictions
null origin
subdomain trust
```

Important:

```text
Access-Control-Allow-Origin: *
```

is not automatically a vulnerability.

Determine whether:

```text
credentials
sensitive response data
browser-readable endpoints
```

make the policy dangerous.

CORS is not an authorization control.

---

## 29. HTTP Method Security

Inventory:

```text
GET
HEAD
OPTIONS
POST
PUT
PATCH
DELETE
TRACE
CONNECT
```

Check:

```text
unexpected enabled methods
authorization consistency
method override
X-HTTP-Method-Override
routing differences
```

A method must be tested against the same authorization model as its resource.

---

## 30. Content-Type and Parser Boundaries

Check:

```text
application/json
multipart/form-data
application/x-www-form-urlencoded
text/plain
XML
GraphQL
protobuf
WebSocket messages
```

Look for parser inconsistencies:

```text
frontend validation
      !=
backend validation

proxy interpretation
      !=
application interpretation
```

Potential class:

```text
REQUEST_SMUGGLING_INDICATOR
PARSER_CONFUSION
VALIDATION_BYPASS
```

Do not escalate into destructive exploitation.

---

## 31. File Upload Security

For file-upload endpoints check:

```text
authentication
authorization
extension validation
MIME validation
content validation
size limit
filename normalization
storage location
download authorization
public exposure
virus/malware scanning
processing pipeline
```

Test only benign controlled files.

Never upload real malware.

---

## 32. Resource Exhaustion

Check bounded controls for:

```text
request size
response size
pagination
query complexity
GraphQL depth
batch size
file size
concurrent connections
expensive operations
background jobs
```

Use small safe test budgets.

Do not intentionally take services offline.

---

## 33. Error Handling

Check whether API errors reveal:

```text
stack traces
filesystem paths
SQL/database information
internal service names
cloud identifiers
tokens
debug state
framework internals
```

Classify:

```text
expected client error
operational error
security-sensitive leakage
```

Do not preserve secrets found in error messages.

---

## 34. Sensitive Data Exposure

Inventory:

```text
PII
tokens
credentials
internal identifiers
financial information
authorization metadata
security configuration
debug information
```

Check:

```text
response
logs
headers
error messages
OpenAPI examples
GraphQL schema
MCP tool output
gRPC errors
WebSocket events
```

Findings must use minimal evidence.

---
