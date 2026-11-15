# cli-creator — §48–57

Contents: 48. Error Normalization; 49. Rate Limits; 50. Retry Policy; 51. Caching; 52. Composability; 53. Streaming; 54. Output Limits; 55. Installation; 56. Installation Verification; 57. Build Validation

## 48. Error Normalization

Map backend errors into stable CLI errors.

Example:

```text
HTTP 401
    ->
AUTH_INVALID

HTTP 403
    ->
FORBIDDEN

HTTP 404
    ->
NOT_FOUND

HTTP 429
    ->
RATE_LIMITED
```

Preserve useful backend details only when safe.

Never expose secrets from raw API responses.

---

## 49. Rate Limits

If the API documents limits:

```text
record
respect
backoff
surface
```

For `429`:

```text
Retry-After
```

should be respected where provided.

The CLI must not create unbounded retry loops.

---

## 50. Retry Policy

Retry only transient operations:

```text
timeout
temporary network failure
502
503
504
429
```

Do not blindly retry:

```text
401
403
400
404
validation failure
authorization failure
write without idempotency
```

For writes, retry only when the API guarantees idempotency or a safe idempotency mechanism is available.

---

## 51. Caching

Optional caching may improve:

```text
discovery
metadata
static schemas
```

But cache semantics must be explicit.

Never cache:

```text
short-lived credentials
sensitive response bodies
private production payloads
```

unless explicitly designed and protected.

---

## 52. Composability

Commands should compose naturally:

```bash
tool projects list --json
```

into:

```bash
tool projects resolve "My Project" --json
```

then:

```bash
tool projects get proj_123 --json
```

Agent-friendly composition should use:

```text
stable IDs
stable JSON
bounded output
deterministic errors
```

---

## 53. Streaming

For large resources:

```text
--jsonl
```

may be appropriate.

Example:

```json
{"id":"job_1","status":"failed"}
{"id":"job_2","status":"running"}
```

Use JSONL only when it provides material benefits.

Document:

```text
record boundary
error behavior
pagination behavior
```

---

## 54. Output Limits

Avoid huge outputs.

Support:

```text
--limit
--max-bytes
--max-lines
--fields
```

where appropriate.

For logs:

```text
--tail
--since
--until
--match
```

should be bounded.

---

## 55. Installation

The CLI must become a real command.

After implementation:

```bash
command -v <tool-name>
<tool-name> --help
<tool-name> --version
<tool-name> --json doctor
```

must work outside the source repository.

For Rust:

```text
make install-local
```

should preferably install into:

```text
~/.local/bin/
```

For Node:

```text
pnpm build
pnpm link --global
```

or a small PATH wrapper.

For Python:

```text
pyproject.toml
console_scripts
uv tool
virtualenv
```

according to project needs.

---

## 56. Installation Verification

Smoke-test from a different working directory:

```bash
cd /tmp
command -v <tool-name>
<tool-name> --help
<tool-name> --json doctor
```

Do not consider:

```bash
cargo run
pnpm dev
python cli.py
```

sufficient proof of installation.

---

## 57. Build Validation

Run applicable:

```text
format
lint
typecheck
build
unit tests
request-builder tests
pagination tests
JSON output tests
error tests
doctor tests
```

Required baseline:

```text
--help
--version
--json doctor
no-auth doctor
fixture/offline path
at least one safe read
```

---
