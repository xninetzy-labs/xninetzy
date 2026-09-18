---
name: dependency-audit
description: Audit third-party dependencies for known vulnerabilities, license risk, supply-chain exposure, and outdated transitive packages. Strictly inside authorized scope. Use when a dependency is added, a lockfile changes, or the operator asks for a dependency surface review.
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: domain
  priority: P1
  required_tools:
    - repo_dependency
    - security_dependencies
    - security_scope
    - security_validate_finding
    - lightning_record_action
  optional_tools:
    - repo_search
    - security_assets
    - hitl_request_approval
    - os_inbox
    - memory_security_store
  trigger_conditions:
    - a new dependency is added or upgraded
    - the lockfile changes
    - the operator asks "is X safe?"
    - a CVE advisory is published for a dep we use
  prerequisites:
    - explicit authorized scope (via `security_scope`) when network is touched
    - local lockfile or manifest reachable
---

# dependency-audit

Supply-chain and dependency-surface review inside authorized scope.
Companion to `security-review` and the `security_dependencies` MCP tool.

## Pipeline

```
MANIFEST
   ↓
LOCKFILE_DIFF
   ↓
TRANSITIVE_GRAPH
   ↓
CVE_MATCH
   ↓
LICENSE_RISK
   ↓
MAINTAINER_TRUST
   ↓
EXPLOIT_REACHABILITY
   ↓
SecurityFinding
```

Every finding cites the package, the version, and the exact CVE / advisory
ID. No "this dep looks shady" without evidence.

## Operating procedure

```
SCOPE
   ↓
INVENTORY_LOCKFILE
   ↓
DIFF_AGAINST_BASELINE
   ↓
RESOLVE_TRANSITIVES
   ↓
ENRICH_CVE_FEED
   ↓
CLASSIFY_REACHABILITY
   ↓
EMIT_FINDINGS
   ↓
HANDOFF_TO_REGRESSION_TEST
```

## Operating rules

1. Never query a public CVE feed without an active `security_scope`.
2. Never propose a downgrade without first confirming the operator's
   policy on version pinning.
3. Never publish a vulnerability disclosure externally — the operator
   owns disclosure.
4. Always pair a CVE finding with the **call sites** in our code that
   reach the vulnerable symbol.
5. For transitive deps, walk the parent chain so the operator sees the
   direct package that pulled the vulnerable version.

## Required outputs

- One `SecurityFinding` per distinct CVE / advisory
- One summary block: `{added, removed, upgraded, downgraded}` count
- License inventory grouped by SPDX identifier
- Reachability matrix: `{vulnerable_symbol → caller_path:line}`

## Anti-patterns

- "This version is old, consider upgrading" without a CVE reference
- "We use many dependencies" hand-waving
- Treating any advisory as immediately exploitable without call-site
  confirmation
