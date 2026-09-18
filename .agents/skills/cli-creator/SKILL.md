---

name: cli-creator

description: Build durable, composable, agent-friendly command-line interfaces from API
documentation, OpenAPI specifications, SDKs, curl examples, web applications,
admin tools, local scripts, exports, or shell history. Produces installable
commands with stable subcommands, deterministic JSON output, discovery and
ID-resolution flows, pagination, authentication/config management, safe
read/write boundaries, dry-run or draft support, raw API escape hatches,
smoke tests from outside the source repository, and a companion skill for
future agent threads.

metadata:
author: xninetzy
owner: misbahul45
version: "2.0.0"
scope: project
priority: P1
domain: xninetzy.domains.cli
lifecycle: >
source -> inventory -> contract -> runtime -> scaffold ->
implement -> validate -> install -> smoke-test -> document -> companion-skill

trigger_conditions:

* the user wants a durable CLI
* an API should become a reusable command-line tool
* an OpenAPI specification is available
* existing curl commands should become a CLI
* an SDK should be wrapped as a CLI
* a web/admin workflow should become repeatable
* a local script should become an installed command
* future Codex threads need repeatable access to a service

non_goals:

* one-off shell scripts
* hardcoded production credentials
* hidden destructive operations
* generic request-only CLIs
* browser automation when a stable API exists
* automatic live writes without explicit approval

references:
agent_patterns:
file: references/agent-cli-patterns.md
required_when:
- designing command surface
- designing JSON output
- designing discovery/resolve commands
- creating companion skill
security:
file: ../xninetzy-security-testing/SKILL.md
required_when:
- CLI touches security-sensitive endpoints
- CLI performs authorized security operations
- credential/session handling is security-critical
--------------------------------------------------

# CLI Creator

## 1. Mission

Create a **real installed CLI**, not a wrapper that only works from its source
directory.

A successful CLI must:

```text
work from any repository
have deterministic commands
have stable machine-readable output
have explicit authentication behavior
separate read and write operations
support composable workflows
be discoverable through --help
be diagnosable through doctor
be installable on PATH
be usable by future agents
```

Core principle:

> **Design the command contract before implementation.**

Second principle:

> **The CLI is an interface contract, not a collection of scripts.**

---

# 2. CLI Quality Standard

A mature CLI should provide:

```text
DISCOVER
   ↓
RESOLVE
   ↓
READ
   ↓
FILTER
   ↓
DRAFT / DRY-RUN
   ↓
WRITE
   ↓
VERIFY
```

Never force future agents to:

```text
scrape terminal prose
grep arbitrary output
reconstruct IDs repeatedly
reuse undocumented curl commands
parse unstable human-readable tables
```

Prefer:

```bash
tool projects list --json
tool projects resolve my-project --json
tool projects get proj_123 --json
tool jobs logs job_123 --json
tool deploy create --dry-run --json
```

---

# 3. Start

Before scaffolding, determine:

```text
target tool name
source
primary resources
first jobs
authentication method
read/write requirements
installation target
runtime availability
```

Example:

```text
Source:
OpenAPI + existing curl examples

Primary jobs:
list projects
resolve project
get project
list jobs
get job logs

Install name:
project-cli
```

The command name must be short, shell-friendly, and stable.

---

# 4. Existing Command Check

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

# 5. Machine Inspection

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

# 6. Runtime Selection

## Rust

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

## TypeScript / Node

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

## Python

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

# 7. Runtime Decision Record

Before scaffolding, state one sentence:

```text
Runtime: Rust.
Reason: durable standalone binary with minimal runtime dependencies.
Available toolchain: cargo + rustc.
```

This decision should be recorded in the README or project metadata.

---

# 8. Source Inventory

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

# 9. Source Priority

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

# 10. OpenAPI First

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

# 11. Curl Extraction

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

# 12. Web-App Reverse Engineering

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

# 13. Command Contract

The command contract must be written before implementation.

At minimum define:

```text
binary
version
help
doctor
init/config
discovery
resolve
read
write
raw escape hatch
JSON behavior
authentication
exit codes
```

Example:

```text
project-cli
├── doctor
├── init
├── projects
│   ├── list
│   ├── get
│   └── resolve
├── jobs
│   ├── list
│   ├── get
│   └── logs
├── deploy
│   ├── create
│   ├── status
│   └── cancel
└── request
```

---

# 14. Command Naming

Prefer:

```text
resource action
```

Examples:

```text
projects list
projects get
projects resolve
jobs list
jobs logs
members list
deployments create
deployments status
```

Avoid vague commands:

```text
fix
manage
process
run-all
debug
do-it
auto
```

The command name should reveal:

```text
resource
action
risk
```

---

# 15. Discovery Commands

Discovery commands locate top-level resources.

Examples:

```text
projects list
workspaces list
teams list
channels list
queues list
repositories list
dashboards list
```

Discovery should support:

```text
--limit
--cursor
--offset
--query
--search
--json
```

Pagination must be bounded.

Default limits must be documented.

---

# 16. Resolve Commands

A resolve command converts human input into stable IDs.

Examples:

```text
projects resolve "My Project"
repos resolve github.com/org/repo
jobs resolve "latest failed build"
```

Resolution inputs may include:

```text
name
slug
URL
permalink
external ID
human identifier
```

Output:

```json
{
  "id": "proj_123",
  "name": "My Project",
  "matched_by": "name",
  "confidence": "exact"
}
```

A future command should consume the stable ID rather than repeatedly performing broad searches.

---

# 17. Resolve Ambiguity

Never silently choose among multiple matches.

Example:

```text
My Project
  ├── proj_123
  └── proj_981
```

Return:

```text
AMBIGUOUS_RESOLUTION
```

with candidates.

Allow:

```text
--id
--slug
--workspace
```

to disambiguate.

---

# 18. Read Commands

Every major resource should support precise reads where practical:

```text
get
show
list
search
logs
history
status
```

A read command should request only the data required for the command.

Prefer:

```text
tool jobs get job_123
```

over:

```text
tool request GET /everything
```

---

# 19. Pagination

Pagination must be explicit and bounded.

Support whichever API model provides:

```text
cursor
offset
page
next_token
link
```

CLI contract:

```text
--limit N
--cursor VALUE
--page N
```

Never silently fetch unlimited pages.

For aggregation commands:

```text
max_items
max_pages
max_runtime
```

must be enforced.

---

# 20. Stable JSON Contract

`--json` is a first-class interface.

Machine-readable output must be:

```text
deterministic
stable
documented
parseable
secret-safe
```

The README must document:

```text
success shape
error shape
pagination shape
one example per command family
```

---

# 21. JSON Success Shape

Pick one convention and use it consistently.

Example:

```json
{
  "ok": true,
  "data": {
    "id": "proj_123",
    "name": "My Project"
  }
}
```

For lists:

```json
{
  "ok": true,
  "data": [
    {
      "id": "proj_123",
      "name": "My Project"
    }
  ],
  "pagination": {
    "next_cursor": "abc"
  }
}
```

Do not alternate randomly between:

```text
[]
{}
{"items":[]}
{"data":[]}
```

without a documented reason.

---

# 22. JSON Error Shape

Errors must also be machine-readable.

Example:

```json
{
  "ok": false,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication is not configured.",
    "retryable": false
  }
}
```

Possible error codes:

```text
AUTH_REQUIRED
AUTH_INVALID
FORBIDDEN
NOT_FOUND
AMBIGUOUS
INVALID_ARGUMENT
RATE_LIMITED
NETWORK_ERROR
TIMEOUT
API_ERROR
CONFIG_ERROR
NOT_SUPPORTED
WRITE_REQUIRES_APPROVAL
```

Never place raw credentials in error output.

---

# 23. Exit Codes

Use deterministic exit codes.

Suggested classes:

```text
0  success
1  generic failure
2  invalid CLI usage
3  authentication/configuration failure
4  permission failure
5  resource not found
6  network/API failure
7  timeout/rate limit
8  write approval required
9  ambiguous resolution
10 unsupported capability
```

Document the mapping.

Do not use successful exit code `0` for a failed API operation merely because JSON was printed.

---

# 24. Human vs Machine Output

Default output may be human-friendly.

`--json` must be machine-friendly.

Example:

```text
default:
Project: My Project
ID: proj_123
Status: active

--json:
{"ok":true,"data":{"id":"proj_123","status":"active"}}
```

Never mix human prose into `--json`.

---

# 25. Global Flags

Prefer a minimal global surface:

```text
--json
--quiet
--verbose
--config
--profile
--timeout
--no-color
--help
--version
```

Do not create dozens of global flags unless the service requires them.

---

# 26. Doctor

Every durable CLI should provide:

```bash
tool-name doctor
```

and:

```bash
tool-name --json doctor
```

Doctor checks:

```text
CLI version
config path
auth availability
auth source category
base URL
API reachability
dependency health
runtime environment
offline mode
fixture mode
missing setup
```

Example:

```json
{
  "ok": true,
  "cli_version": "1.2.0",
  "auth": {
    "configured": true,
    "source": "env"
  },
  "endpoint": {
    "reachable": true
  }
}
```

Never return the actual token.

---

# 27. Init

When environment variables are inconvenient, provide:

```bash
tool-name init
```

Possible configuration:

```toml
base_url = "https://api.example.com"
profile = "default"
```

Sensitive values should use:

```text
OS credential store
secure secret reference
environment variable
file permission 0600
```

rather than plaintext configuration where practical.

---

# 28. Authentication Precedence

Use:

```text
1. explicit one-off flag
2. environment variable
3. config
4. provider/system credential
5. missing
```

But for normal usage recommend:

```text
environment
or
config/credential store
```

Flags are less desirable for secrets because they may appear in:

```text
shell history
process listings
debugging tools
```

---

# 29. Authentication Sources

`doctor --json` should report only the source category:

```text
flag
env
config
provider
missing
```

Never:

```text
token value
full token
partial token
credential header
```

Prefer:

```json
{
  "configured": true,
  "source": "env"
}
```

---

# 30. Offline / Fixture Mode

If the CLI supports offline mode, expose it explicitly:

```text
doctor --json
```

should report:

```json
{
  "offline_mode": true,
  "fixture_data": true,
  "network_required": false
}
```

This prevents agents from interpreting fixture-backed success as live API success.

---

# 31. Write Command Design

Each write should correspond to one explicit business action.

Examples:

```text
create
update
delete
upload
schedule
retry
comment
draft
publish
cancel
```

Do not hide multiple writes inside:

```text
fix
sync
auto
repair
deploy-all
```

---

# 32. Write Safety

Write commands should support one or more:

```text
--dry-run
--preview
--draft
--confirm
--idempotency-key
```

where supported by the service.

Default:

```text
read-only
```

Write behavior must be obvious from the command name.

---

# 33. Write Approval Boundary

Before live write:

```text
target
resource
action
payload summary
environment
reversibility
```

must be clear.

For interactive workflows:

```text
preview
↓
explicit confirmation
↓
write
↓
verify
```

Do not hide live writes inside a read command.

---

# 34. Idempotency

For write APIs that support idempotency:

```text
--idempotency-key
```

must be exposed.

For create commands:

```text
same request
same idempotency key
```

should not unintentionally create duplicates.

If the API is naturally idempotent:

```text
document it
```

Do not invent fake idempotency guarantees at the CLI layer.

---

# 35. Destructive Operations

Destructive commands should be explicit:

```text
delete
destroy
remove
cancel
overwrite
publish
```

Where feasible:

```text
require --confirm
```

or:

```text
--dry-run
```

Never interpret:

```text
tool resource sync
```

as permission to delete unrelated resources.

---

# 36. Write Verification

A successful HTTP status is not necessarily a completed business action.

After a write, verify when the service supports it:

```text
create
 ↓
returned ID
 ↓
get/status
 ↓
confirmed state
```

For async jobs:

```text
create
 ↓
job ID
 ↓
poll
 ↓
terminal state
 ↓
read result
```

Possible states:

```text
queued
running
succeeded
failed
cancelled
unknown
```

---

# 37. Polling

For asynchronous APIs:

```text
--timeout
--interval
```

should be bounded.

Example:

```text
create
↓
status every 2s
↓
maximum 5 minutes
↓
STOP
```

Never poll forever.

---

# 38. Upload Workflow

For media/artifact uploads:

```text
create upload
↓
receive upload URL
↓
transfer bytes
↓
poll processing
↓
receive resource ID
↓
attach/reference
↓
verify
```

Treat each phase independently.

Never print:

```text
presigned URL
```

when it contains sensitive credentials or signatures.

---

# 39. Download Workflow

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

# 40. Logs

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

# 41. Raw Escape Hatch

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

# 42. Raw Request Safety

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

# 43. API Client Boundary

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

# 44. Domain Client

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

# 45. Response Normalization

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

# 46. API Compatibility

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

# 47. Request Builders

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

# 48. Error Normalization

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

# 49. Rate Limits

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

# 50. Retry Policy

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

# 51. Caching

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

# 52. Composability

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

# 53. Streaming

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

# 54. Output Limits

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

# 55. Installation

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

# 56. Installation Verification

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

# 57. Build Validation

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

# 58. Test Matrix

Every durable CLI should test:

| Area       | Test                   |
| ---------- | ---------------------- |
| CLI        | help/version           |
| Config     | missing config         |
| Auth       | no credential          |
| Auth       | invalid credential     |
| HTTP       | request builder        |
| HTTP       | timeout                |
| HTTP       | retry                  |
| HTTP       | rate limit             |
| Read       | single object          |
| Read       | list                   |
| Pagination | cursor/offset          |
| Resolve    | exact match            |
| Resolve    | ambiguous match        |
| JSON       | success                |
| JSON       | error                  |
| Write      | dry-run                |
| Write      | confirmation gate      |
| Async      | polling timeout        |
| Fixture    | offline                |
| Install    | execution outside repo |

---

# 59. Repository Layout

Preferred durable layout:

```text
~/code/clis/<tool-name>/
```

when the user does not specify an existing repository.

Example Rust:

```text
tool-name/
├── Cargo.toml
├── README.md
├── Makefile
├── src/
│   ├── main.rs
│   ├── cli.rs
│   ├── config.rs
│   ├── auth.rs
│   ├── client/
│   ├── commands/
│   ├── output.rs
│   └── error.rs
├── tests/
└── references/
```

---

# 60. Documentation Contract

README must contain:

```text
installation
authentication
doctor
command overview
resource discovery
resolve
read
write
dry-run
JSON output
errors
pagination
raw request
examples
exit codes
limitations
```

Do not hide important operational information in source code only.

---

# 61. Command Documentation

Every major command should answer:

```text
What does it do?
What inputs does it need?
Is it read-only?
Can it modify state?
What JSON does it return?
What errors can occur?
```

Example:

```text
tool deploy create

ACTION:
Creates a deployment.

MUTATION:
Yes.

SAFE PREVIEW:
--dry-run

REQUIRES:
project_id
artifact_id

RETURNS:
deployment ID

FOLLOW-UP:
deployments status <id>
```

---

# 62. Companion Skill

After the CLI works, create/update:

```text
$CODEX_HOME/skills/<tool-name>/SKILL.md
```

unless the user specifies another location.

The companion skill should explain:

```text
verify binary
doctor
auth
first discovery
resolve
safe read
write path
raw escape hatch
approval boundaries
```

Do not duplicate the entire API reference.

---

# 63. Companion Skill Example

Future agent sequence:

```text
1. command -v tool-name
2. tool-name --json doctor
3. tool-name <resource> list --json
4. tool-name <resource> resolve "<name>" --json
5. tool-name <resource> get <id> --json
6. use narrow write command only when explicitly requested
```

Include three practical examples.

---

# 64. Skill Reference Loading

When this skill is invoked:

```text
IF command-surface design is required
    -> read references/agent-cli-patterns.md

IF security-sensitive service interaction exists
    -> read ../xninetzy-security-testing/SKILL.md

IF both apply
    -> read both
```

Do not invent conventions that the reference already defines.

---

# 65. Agent-Friendly Design

A good CLI minimizes model uncertainty.

Prefer:

```text
stable nouns
stable verbs
stable IDs
stable JSON
stable errors
bounded results
```

Avoid:

```text
interactive-only flows
terminal-only tables
random IDs
implicit defaults
hidden pagination
silent writes
unstable prose
```

---

# 66. Observability

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

# 67. Request ID / Trace ID

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

# 68. Configuration Profiles

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

# 69. Environment Safety

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

# 70. Production Write Guard

When practical:

```text
production
+
destructive write
```

should require explicit confirmation.

The guard must be implemented in code, not merely documented.

---

# 71. URL Safety

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

# 72. Local Script Conversion

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

# 73. Existing Tool Conversion

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

# 74. SDK Wrapping

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

# 75. API Coverage

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

# 76. Command Surface Review

Before implementation, emit:

```text
Binary:
tool-name

Discovery:
tool-name projects list

Resolve:
tool-name projects resolve <name>

Read:
tool-name projects get <id>

Write:
tool-name deployments create --dry-run

Verify:
tool-name deployments status <id>

Raw:
tool-name request GET /...

Auth:
tool-name init

Diagnostics:
tool-name --json doctor
```

The user should be able to understand the main workflow immediately.

---

# 77. Completion Contract

CLI creation is complete only when:

```text
[ ] source inventoried
[ ] runtime selected
[ ] command contract designed
[ ] discovery implemented
[ ] resolve implemented
[ ] read path implemented
[ ] requested write path implemented safely
[ ] raw escape hatch implemented
[ ] auth/config documented
[ ] doctor implemented
[ ] stable JSON implemented
[ ] stable errors implemented
[ ] pagination bounded
[ ] retries bounded
[ ] secrets redacted
[ ] tests pass
[ ] binary installed
[ ] command works outside source repo
[ ] README written
[ ] companion skill created
[ ] three practical examples documented
```

---

# 78. Final Principle

The resulting CLI should feel like:

```text
a stable API for agents
```

rather than:

```text
a collection of shell commands
```

The ideal architecture is:

```text
SOURCE
  ↓
API/WORKFLOW MODEL
  ↓
COMMAND CONTRACT
  ↓
DOMAIN CLIENT
  ↓
AUTH + CONFIG
  ↓
STABLE JSON
  ↓
INSTALLABLE BINARY
  ↓
COMPANION SKILL
```

The final quality bar is:

```text
portable
composable
deterministic
machine-readable
safe by default
explicit about writes
easy to diagnose
easy to install
easy for future agents to reuse
```

And the governing rule is:

> **Build high-level commands for real workflows; keep the raw API escape hatch as an escape hatch, not as the entire CLI.**

---

Struktur ini juga sengaja membuat **`doctor` + `resolve` + stable JSON + verification** menjadi bagian inti, bukan fitur tambahan. Jadi future Codex thread bisa mengikuti pola:

```text
tool --json doctor
        ↓
resource list
        ↓
resource resolve
        ↓
resource get
        ↓
narrow action
        ↓
status/verify
```
