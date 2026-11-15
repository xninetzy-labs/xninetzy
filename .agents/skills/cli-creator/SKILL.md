---
name: cli-creator
description: Builds agent-friendly CLIs from API docs, OpenAPI specs, SDKs, curl examples or scripts, with stable subcommands, JSON output, auth/config, pagination, dry-run and smoke tests. Use when a service or tool needs a CLI.
metadata:
  keywords: admin applications authentication boundaries build command commands companion composable deterministic discovery documentation draft durable escape exports flows for future hatches history installable interfaces line local management outside produces raw read repository resolution safe shell skill source specifications support threads tools web write
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

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/04-10-existing-command-check.md` — §4–10: Existing Command Check, Machine Inspection, Runtime Selection, Runtime Decision Record, Source Inventory, Source Priority, OpenAPI First
- `references/11-12-curl-extraction.md` — §11–12: Curl Extraction, Web-App Reverse Engineering
- `references/14-19-command-naming.md` — §14–19: Command Naming, Discovery Commands, Resolve Commands, Resolve Ambiguity, Read Commands, Pagination
- `references/21-29-json-success-shape.md` — §21–29: JSON Success Shape, JSON Error Shape, Exit Codes, Human vs Machine Output, Global Flags, Doctor, Init, Authentication Precedence, Authentication Sources
- `references/30-38-offline-fixture-mode.md` — §30–38: Offline / Fixture Mode, Write Command Design, Write Safety, Write Approval Boundary, Idempotency, Destructive Operations, Write Verification, Polling, Upload Workflow
- `references/39-47-download-workflow.md` — §39–47: Download Workflow, Logs, Raw Escape Hatch, Raw Request Safety, API Client Boundary, Domain Client, Response Normalization, API Compatibility, Request Builders
- `references/48-57-error-normalization.md` — §48–57: Error Normalization, Rate Limits, Retry Policy, Caching, Composability, Streaming, Output Limits, Installation, Installation Verification, Build Validation
- `references/58-64-test-matrix.md` — §58–64: Test Matrix, Repository Layout, Documentation Contract, Command Documentation, Companion Skill, Companion Skill Example, Skill Reference Loading
- `references/66-75-observability.md` — §66–75: Observability, Request ID / Trace ID, Configuration Profiles, Environment Safety, Production Write Guard, URL Safety, Local Script Conversion, Existing Tool Conversion, SDK Wrapping, API Coverage
- `references/76-command-surface-review.md` — §76: Command Surface Review
- `references/78-final-principle.md` — §78: Final Principle
