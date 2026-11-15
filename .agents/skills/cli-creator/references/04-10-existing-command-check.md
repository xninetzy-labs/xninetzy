# cli-creator — §4–10

Contents: 4. Existing Command Check; 5. Machine Inspection; 6. Runtime Selection; 7. Runtime Decision Record; 8. Source Inventory; 9. Source Priority; 10. OpenAPI First

## 4. Existing Command Check

Before choosing the binary name:

```bash
command -v <tool-name> || true
```

Also inspect:

```bash
which <tool-name> 2>/dev/null || true
```

If the name already exists:

```text
choose a clearer name
```

Do not silently overwrite an unrelated installed command.

---

## 5. Machine Inspection

Before selecting the runtime:

```bash
command -v cargo rustc node pnpm npm python3 uv go || true
```

Inspect relevant source requirements.

Do not choose a runtime solely from personal preference.

Choose based on:

```text
installed toolchain
official SDK availability
existing project conventions
dependency footprint
distribution model
startup time
installation simplicity
cross-platform requirements
```

---

## 6. Runtime Selection

### Rust

Prefer Rust when:

```text
durable standalone binary
low runtime dependency
high portability
high invocation frequency
strong typed CLI contract
```

Defaults:

```text
clap
reqwest
serde
serde_json
toml
anyhow
```

---

### TypeScript / Node

Prefer TypeScript when:

```text
official JavaScript SDK
existing Node authentication
existing TypeScript codebase
browser/web ecosystem dependency
Node-native tooling
```

Defaults:

```text
commander or cac
fetch or official SDK
zod when external validation is valuable
tsup / tsc / tsx according to project
package.json bin
```

---

### Python

Prefer Python when:

```text
Python SDK
data transformation
CSV/JSON/SQLite
local administration
notebooks/data workflows
existing Python-heavy ecosystem
```

Defaults:

```text
argparse
httpx / requests
pathlib
json
csv
sqlite3
subprocess
```

Use `typer` when the command surface becomes significantly clearer.

---

## 7. Runtime Decision Record

Before scaffolding, state one sentence:

```text
Runtime: Rust.
Reason: durable standalone binary with minimal runtime dependencies.
Available toolchain: cargo + rustc.
```

This decision should be recorded in the README or project metadata.

---

## 8. Source Inventory

Inspect source material for:

```text
authentication
base URL
API version
resources
IDs
slugs
pagination
filters
sorting
search
rate limits
errors
write operations
draft/preview
uploads
downloads
presigned URLs
webhooks
polling
async jobs
status transitions
permissions
scopes
headers
CSRF
request bodies
response schemas
```

Do not implement from a single happy-path example.

---

## 9. Source Priority

When multiple sources exist:

```text
official API specification
    >
official API documentation
    >
official SDK behavior
    >
stable curl/network example
    >
existing local implementation
    >
web UI behavior
    >
screenshots
    >
inference
```

Screenshots are workflow evidence, not authoritative API evidence.

A UI field should not become an API contract unless supported by:

```text
OpenAPI
network request
SDK
documentation
fixture
```

---

## 10. OpenAPI First

When OpenAPI is available:

```text
download
↓
validate
↓
inspect servers
↓
inspect security schemes
↓
inspect tags
↓
inspect paths
↓
inspect operation IDs
↓
inspect request schemas
↓
inspect response schemas
↓
inspect parameters
↓
inspect pagination
↓
inspect errors
```

Do not manually guess endpoints that already exist in the schema.

Preserve:

```text
operationId
HTTP method
path parameters
query parameters
request body
response types
security scheme
```

---
