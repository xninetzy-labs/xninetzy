---
name: "security-review"
description: "Application and code-level security review for Xninetzy itself and the projects it audits. Drives the structured Asset → Entry point → Trust boundary → Input → Processing → Sink → Security control → Failure mode → Exploitability → Impact → Mitigation pipeline. Emits `SecurityFinding` objects with reproduction evidence, severity rationale, and remediation. Operates strictly inside authorized scope. Use whenever the operator asks to audit a code change, a new dependency, a new MCP tool signature, or a third-party code surface."
metadata:
  author: "xninetzy"
  version: "1.0.0"
  scope: "domain"
  priority: "P1"
  required_tools:
    - repo_search
    - repo_dependency
    - grep_search
    - read_file
    - security_scope
    - security_assets
    - security_sast
    - security_dependencies
    - security_threat_model
    - security_validate_finding
    - security_regression
  optional_tools:
    - hitl_request_approval
    - os_inbox
    - lightning_record_action
    - memory_security_store
  trigger_conditions:
    - the operator asks for a security audit
    - a PR or branch is about to be merged
    - a new dependency is added
    - a new MCP tool is registered
  prerequisites:
    - explicit authorized scope (via `security_scope`)
    - target surface identified
    - background research / reference files loaded if applicable
---

# security-review

Application and code-level security review inside authorized scope.
Companion skill to the `Security` MCP capability family.

## Threat-model pipeline

```
ASSET
   ↓
ENTRY_POINT
   ↓
TRUST_BOUNDARY
   ↓
INPUT
   ↓
PROCESSING
   ↓
SINK
   ↓
SECURITY_CONTROL
   ↓
FAILURE_MODE
   ↓
EXPLOITABILITY
   ↓
IMPACT
   ↓
MITIGATION
```

Every finding traces evidence back to a file/line. No pattern-only
claims.

## Operating procedure

```
SCOPE
   ↓
INVENTORY
   ↓
TRACE
   ↓
MODEL
   ↓
PROVE
   ↓
REMEDIATE
   ↓
REGRESS
   ↓
TRANSCRIBE
```

### 1. SCOPE

Always start with `security_scope(targets=[...])`. No review without
explicit authorized scope. Unknown scope → refuse + escalate.

### 2. INVENTORY

Run `security_assets(scope)` and `security_dependencies(scope)` to
produce:

- surface inventory (code modules, public APIs, MCP tool signatures,
  HTTP endpoints, internal interfaces)
- dependency inventory (versions, CVEs, license, supply-chain origin)
- configuration inventory (secrets handling, network scope, auth
  providers)
- data flow inventory (which inputs reach which sinks)

Persist inventory to durable store so subsequent reviews can diff.

### 3. TRACE

For each input class, run `security_sast(slice=..., patterns=[...])`
to surface:

- input validation surface (where unsanitized values cross trust
  boundaries)
- secret handling surface (where credentials flow)
- network scope surface (where requests leave the host)
- privilege boundaries (operator code vs user code)
- injection surface (SQL, command, path traversal, SSRF, XSS, LDAP)
- unsafe deserialization surface (pickle, yaml.load, eval)
- race condition surface (TOCTOU, lock ordering)

Capture findings as raw `SecurityFinding` envelopes, never as plain
text.

### 4. MODEL

Run `security_threat_model(inventory=..., threat_classes=[...])` to
produce the structured Asset→Sink graph. Each edge in the graph
gets:

- threat class
- existing security control
- residual risk
- exploitability rating

Threat modeling is single-authoritative at a time. Do not run two
threat models in parallel for the same surface — they would produce
contradicting edges.

### 5. PROVE

For each candidate finding, run `security_validate_finding(id,
allow_runtime_proof=true|false)` to produce reproduction evidence.

Two modes:

- `runtime_proof: false` — static reproduction (paths, signatures,
  data flow). Used for any finding in a non-test environment.
- `runtime_proof: true` — only allowed in authorized lab fixtures with
  isolated data.

A finding without a reproduction is not a finding; it is a hypothesis.
Mark it `UNVERIFIED` and let the owner decide whether to invest in
lab reproduction.

### 6. REMEDIATE

For each verified finding, propose:

- patch (with regression test, per `tdd-workflow`)
- alternative mitigations (rate-limit, header, CSP, secret rotation,
  scope narrowing)
- owner decision pending

Concrete code patches must go through `tdd-workflow`. Documentation
changes alone are never sufficient.

### 7. REGRESS

Persist the regression test alongside the fix:

- run `security_regression(test_id)` to confirm the patched code is
  not regression-prone
- add the test to `tests/security/`
- the test must fail without the patch and pass with it

Without a regression test, the fix is not considered complete.

### 8. TRANSCRIBE

Persist the full finding + remediation + regression evidence to
`memory_security_store` with explicit confidence and scope. This
memory survives across sessions and is the basis for future audits.

## Output contract

A security-review invocation returns:

```
security-review report
scope_token: <uuid>
assets: [...]
findings: [
    SecurityFinding {
  id: <uuid>
  title: <short>
  asset: <module path>
  location: <file:line>
  category: <class>
  evidence: { ... }
  precondition: <string>
  reproduction: <runtime_proof_used>
  impact: <string>
  confidence: 0.0..1.0
  severity_rationale: <string>
  remediation: { code_patch, alternative_mitigations, owner_decision_pending: bool }
  regression_test: <path>
    }
    ...
]
verdict: CLEAN | FINDINGS_PENDING_OWNER_DECISION | FINDINGS_REMEDIATED
```

## What this skill never does

- security tests against unauthorized targets
- runtime reproduction outside an authorized lab fixture
- secret exfiltration under any pretext
- skipping the regression test step
- producing findings without reproduction evidence

## Failure classification

| Class                          | Cause                              | Action                                |
|--------------------------------|------------------------------------|---------------------------------------|
| `SCOPE_DENIED`                 | target not authorized              | stop; HITL                            |
| `NO_REPRODUCTION`              | finding lacks evidence             | mark `UNVERIFIED`; require evidence    |
| `PATCH_BROKEN`                 | remediation regression-tested fail | revert; isolate fix                   |
| `DEPENDENCY_CVE_UNPATCHED`    | new CVE surfaced for an in-scope dep | block; recommend upgrade          |

## Recovery

- failed prove step → mark `UNVERIFIED`; surface to owner
- failed remediation → revert; rerun `tdd-workflow` cycle
- lab fixture unavailable → fall back to static reproduction only

## See also

- `skill-security-review` — gates third-party skills; complementary surface
- `playwright-mcp-workflows` — for browser-driven security verification
- `tdd-workflow` — discipline for the remediation step
- `multi-agent-orchestration` — distributes per-asset security review
- `structured-project-execution` — durable spine for multi-week audits
