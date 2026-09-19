---
name: "secret-audit"
description: "Hunt for accidentally-committed secrets (API keys, tokens, private keys, .env leaks) inside authorized scope. Use after a commit, before a release, or when the operator asks \"did we leak anything?\"."
metadata:
  author: "xninetzy"
  version: "1.0.0"
  scope: "domain"
  priority: "P1"
  required_tools:
    - repo_search
    - repo_symbol
    - security_scope
    - security_sast
    - security_validate_finding
    - lightning_record_action
  optional_tools:
    - repo_diff
    - security_assets
    - hitl_request_approval
    - memory_security_store
  trigger_conditions:
    - a commit lands on a shared branch
    - a PR is about to be merged
    - the operator asks to audit before release
    - an external secret-scanner reports a hit
  prerequisites:
    - explicit authorized scope (via `security_scope`)
    - target repo path reachable
---

# secret-audit

Detect committed or live secret material inside authorized scope.
Companion to `security-review` and the `security_sast` MCP tool.

## Pipeline

```
TARGET_REPO
   ↓
FILE_DISCOVERY
   ↓
PATTERN_SCAN
   ↓
ENTROPY_SCAN
   ↓
PROVENANCE_CHECK
   ↓
VALIDATION
   ↓
SecurityFinding
```

Pattern scans alone produce too many false positives; entropy scans
alone miss structured secrets. Always run both and intersect.

## Operating procedure

```
SCOPE
   ↓
LIST_TRACKED_FILES
   ↓
EXCLUDE_VENDOR + BINARY
   ↓
PATTERN_REGEX_SET
   ↓
ENTROPY_TOP_N
   ↓
CROSS_REFERENCE_GIT_HISTORY
   ↓
EMIT_FINDINGS
   ↓
HANDOFF_TO_ROTATION
```

## Operating rules

1. Never write a found secret to a log file, telemetry event, or
   memory record — redact to `{kind}:{first2}***{last2}` at most.
2. Treat any hit in a `.env`, `.pem`, `id_rsa`, `*.key`, or
   `credentials.*` as a **critical** finding regardless of context.
3. Always report git-blame for the offending line so the operator
   knows who introduced the secret and when.
4. Never auto-revoke or auto-rotate a secret — the operator owns the
   rotation flow.
5. False positives must be added to an allowlist file the operator
   reviews, never silently dropped.

## Required outputs

- One `SecurityFinding` per distinct secret hit, severity tiered:
  - `critical` — production-grade credential
  - `high` — dev / staging credential
  - `medium` — internal token with limited scope
  - `low` — public-but-rotation-sensitive identifier
- Git blame `{author, commit, date}` for each line
- Redacted preview `{kind}:{first2}***{last2}` (never the full secret)

## Anti-patterns

- Echoing the matched secret in chat for verification
- Suggesting "just rotate it" without identifying which system owns
  the credential
- Treating an `example.com` placeholder as a real secret
