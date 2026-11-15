# cli-creator — §11–12

## 11. Curl Extraction

When existing curl examples are the primary source, sanitize them first.

Extract:

```yaml
endpoint:
  method:
  path:
  query:
  headers:
  authentication:
  request_body:
  response:
  pagination:
  identifiers:
  errors:
```

Remove:

```text
cookies
bearer tokens
API keys
CSRF tokens
customer data
private identifiers
temporary upload URLs
session IDs
```

Never commit copied production authentication material.

---

## 12. Web-App Reverse Engineering

When source is a web/admin application:

```text
UI
 ↓
network request
 ↓
endpoint
 ↓
request schema
 ↓
response schema
 ↓
ID fields
 ↓
state transitions
```

Prefer browser DevTools network evidence over DOM assumptions.

Identify:

```text
resource
method
path
request body
headers
auth
response IDs
pagination
errors
```

Screenshots may be used for:

```text
workflow vocabulary
field names
confirmation steps
navigation
```

but not as authoritative protocol evidence.

---
