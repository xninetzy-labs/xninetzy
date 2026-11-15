# cli-creator — §39–47

Contents: 39. Download Workflow; 40. Logs; 41. Raw Escape Hatch; 42. Raw Request Safety; 43. API Client Boundary; 44. Domain Client; 45. Response Normalization; 46. API Compatibility; 47. Request Builders

## 39. Download Workflow

For downloads:

```text
resolve object
↓
retrieve metadata
↓
download
↓
verify file
```

Support:

```text
--output
--stdout
--format
```

Avoid binary data on stdout unless explicitly requested.

For JSON mode:

```text
metadata
not binary bytes
```

should normally be emitted.

---

## 40. Logs

For log-oriented CLIs:

```text
download
↓
slice
↓
filter
↓
extract
```

Keep deterministic processing separate from model interpretation.

Prefer:

```text
filename
line number
byte range
matched rule
short excerpt
```

instead of dumping massive logs.

---

## 41. Raw Escape Hatch

Provide:

```text
request
```

or equivalent.

Example:

```bash
tool request GET /v1/projects
```

But:

```text
raw request
```

must not replace high-level commands.

The CLI should first-class common workflows such as:

```text
projects list
projects resolve
jobs logs
```

The raw escape hatch exists for:

```text
new endpoints
rare fields
debugging
temporary API capabilities
```

---

## 42. Raw Request Safety

Default:

```text
GET
HEAD
OPTIONS
```

are preferred.

For write methods:

```text
POST
PUT
PATCH
DELETE
```

require the user to explicitly request the operation.

The raw escape hatch must not silently turn into:

```text
arbitrary shell
arbitrary subprocess
unrestricted HTTP
```

---

## 43. API Client Boundary

Separate:

```text
CLI parsing
    ↓
command layer
    ↓
domain/resource client
    ↓
HTTP transport
```

Example:

```text
commands/
resources/
client/
auth/
config/
output/
errors/
```

Do not put authentication, HTTP parsing, and command behavior into one large file.

---

## 44. Domain Client

Each resource should have a small typed client.

Example:

```text
ProjectsClient
  list()
  get()
  resolve()

JobsClient
  list()
  get()
  logs()

DeploymentsClient
  create()
  status()
  cancel()
```

This makes:

```text
unit tests
mocking
future commands
```

easier.

---

## 45. Response Normalization

Normalize API responses at the client boundary.

Separate:

```text
API schema
from
CLI output schema
```

The CLI should not blindly expose unstable backend internals.

However:

```text
do not destroy useful fields
```

without documenting the transformation.

---

## 46. API Compatibility

When backend API responses change:

```text
detect
validate
normalize
```

Do not silently reinterpret missing fields.

Possible state:

```text
UNKNOWN_SCHEMA
```

is preferable to silently returning incorrect data.

---

## 47. Request Builders

Test request construction independently.

Tests should cover:

```text
path
query
headers
body
pagination
auth
filters
sorting
multipart
```

This is especially important when converting curl examples.

---
