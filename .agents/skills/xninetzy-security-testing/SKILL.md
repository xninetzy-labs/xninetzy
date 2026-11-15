---
name: xninetzy-security-testing
description: 'Orchestrates authorized security assessments with Xninetzy scanners (Semgrep, Trivy, ZAP, Gitleaks, OSV, Schemathesis, SBOM): scope, run, correlate, validate findings non-destructively and report remediation evidence. Use for multi-scanner security testing.'
metadata:
  keywords: description manual pending review skill
---

# Xninetzy Security Testing

## 1. Mission

This skill is the security-assessment workflow layer for `xninetzy.domains.security`.

It coordinates multiple specialized scanners into one evidence-driven assessment pipeline.

The objective is not:

> run as many scanners as possible.

The objective is:

> build the most trustworthy security model possible for the explicitly authorized asset set, identify meaningful weaknesses, validate findings non-destructively, preserve provenance, and produce reproducible remediation evidence.

The core principle is:

> **Verified evidence > scanner volume.**
>
> **Verified partial result > unverified complete result.**

Security testing must be systematic, bounded, reproducible, and explainable.
---

## 2. Operating Doctrine

The security engine follows these invariants:

1. Scope before discovery.
2. Authorization before active testing.
3. Asset normalization before scanner execution.
4. Explicit allowlist before network egress.
5. No silent scope expansion.
6. Read-only by default.
7. No destructive exploitation.
8. No credential brute force.
9. No CAPTCHA, OTP, MFA, or anti-bot bypass.
10. No session-token extraction.
11. No secret material in prompts, reports, logs, or finding evidence.
12. No scanner may redirect testing outside the declared scope.
13. No DNS rebinding may silently move a scan outside scope.
14. No metadata-service access.
15. No scanner template may be trusted solely because its filename says "safe".
16. Tool output is evidence, not truth.
17. A suspected finding must be distinguishable from a verified finding.
18. Historical findings do not prove current exposure.
19. A remediation claim requires post-fix verification.
20. Missing tools produce explicit `TOOL_MISSING`; never fake success.
21. Timeouts are bounded.
22. Output is size bounded.
23. Resource use is rate limited.
24. Credentials are injected by secure reference, never raw prompt text.
25. Audit logs must not retain secrets.
26. Self-improvement may improve detectors, correlation, and regression coverage, but may not expand authorization scope.
27. Model reasoning never overrides deterministic security policy.
28. Unknown security state is never promoted to safe or vulnerable without evidence.
29. Fail closed on authorization, target identity, privacy, or mutation ambiguity.

---

## 3. Scope Model

Every assessment begins with a `ScopeManifest`.

```yaml
scope_id: uuid
principal:
  type: owner | authorized_operator
  identity: opaque_identifier
authorization:
  mode: chat_attestation | written_authorization_reference | local_owner_control
  attestation: opaque
  authorization_reference: opaque_hash_or_id
  valid_from: timestamp
  valid_until: timestamp

targets:
  urls: []
  hostnames: []
  ipv4: []
  ipv6: []
  cidrs: []
  repositories: []
  container_images: []
  kubernetes_contexts: []
  cloud_accounts: []
  mobile_artifacts: []

constraints:
  allowed_ports: []
  excluded_ports: []
  allowed_paths: []
  excluded_paths: []
  allowed_methods:
    - GET
    - HEAD
    - OPTIONS
  allowed_environments:
    - local
    - development
    - staging
    - production

limits:
  max_requests_per_second: 5
  max_concurrency: 10
  max_runtime_seconds: 3600
  max_output_bytes: 8000000

actions:
  passive: true
  safe_active: true
  state_changing_requests: false
  destructive_testing: false
  exploit_execution: false
  credential_attack: false
```

### Scope requirements

A scope is valid only when all of these are known:

* principal
* target
* target type
* environment
* allowed testing profile
* validity period
* resource limits

A target string alone does not establish ownership.

A chat attestation is an authorization gate used by the toolchain; it is not independent legal proof of ownership.

---

## 4. Protected Target Policy

The engine refuses targets matching the universal protection policy.

At minimum the protected set includes:

* government domains
* military domains
* education domains
* healthcare/government health infrastructure
* law-enforcement infrastructure
* defense infrastructure
* cloud metadata endpoints
* loopback literals
* link-local metadata addresses
* unspecified/private targets when not explicitly authorized by the private-target gate

Example protected classes:

```text
*.gov
*.gov.*
*.go.id
*.mil
*.mil.*
*.ac.id
*.sch.id
*.edu
*.edu.*
metadata.google.internal
169.254.169.254
localhost
127.0.0.0/8
::1
```

The exact implementation must live in:

```text
xninetzy/domains/security/scope.py
```

The policy engine is authoritative over the language model.

The orchestrator must never suggest:

```text
remove the block
edit BLOCKED_HOSTS
disable the safety check
use another scanner
change the hostname slightly
scan the resolved IP instead
```

to bypass a protected-target rule.

---

## 46. Completion Contract

Before returning success, verify:

```text
[ ] scope created
[ ] authorization gate satisfied
[ ] protected-target policy checked
[ ] target normalized
[ ] redirects scope-checked
[ ] DNS revalidation performed where applicable
[ ] scanners inventoried
[ ] selected scanners executed
[ ] missing tools surfaced
[ ] output limits enforced
[ ] secrets redacted
[ ] findings deduplicated
[ ] evidence categorized
[ ] high-impact findings independently validated where feasible
[ ] coverage measured
[ ] limitations recorded
[ ] report generated
[ ] audit event available
[ ] regression candidates identified
```

---

## 47. Core Tool Routing

```text
"scan website"
    -> xninetzy-security-testing

"review secure coding"
    -> security-best-practices

"build threat model"
    -> security-threat-model

"scan repository"
    -> xninetzy-security-testing
    -> Semgrep + Gitleaks + Trivy + OSV + dep-scan

"scan API"
    -> xninetzy-security-testing
    -> OpenAPI + Schemathesis + ZAP + Nuclei

"scan Docker"
    -> xninetzy-security-testing
    -> Trivy + Syft + Grype + Dockle

"scan Kubernetes"
    -> xninetzy-security-testing
    -> kube-bench + KubeLinter + Trivy

"scan cloud"
    -> xninetzy-security-testing
    -> Prowler

"scan mobile"
    -> xninetzy-security-testing
    -> MobSF
```

---

## 49. Human Approval Boundaries

Explicit human approval is required before:

```text
scope expansion
new domain
new IP range
new cloud account
new repository
state-changing requests
production active testing beyond baseline
credentialed testing with a new identity
new destructive capability
new external callback target
```

The standard message is:

```text
Target:
Scope:
Environment:
Profile:
Allowed actions:
Excluded actions:
Potential impact:
Approval required:
```

---

## not when it merely produces the largest number of scanner alerts.


---

## References

This skill has two operational reference documents.

### Installation Reference

Use when the task involves:

```text
tool installation
tool availability
scanner prerequisites
PATH configuration
Docker images
Python/Go environments
version compatibility
version pinning
checksums
tool health checks
security-tools.lock
scanner output directories
```

Read:

```text
references/install.md
```

### Workflow Reference

Use when the task involves:

```text
security scan orchestration
scanner execution order
scan profiles
website assessment
API assessment
repository audit
Docker/container assessment
IaC assessment
Kubernetes assessment
cloud assessment
mobile assessment
MCP security assessment
finding correlation
finding validation
regression testing
delta assessment
full-assessment orchestration
failure handling
```

Read:

```text
references/workflow.md
```

### Reference Loading Rule

```text
IF task requires installation/tooling knowledge
    -> READ references/install.md

IF task requires operational security workflow
    -> READ references/workflow.md

IF task requires both
    -> READ both references/install.md AND references/workflow.md

IF a reference conflicts with this SKILL.md
    -> SKILL.md policy and safety invariants take precedence

IF required reference cannot be read
    -> do not invent missing procedures
    -> report the missing reference
    -> continue only with information explicitly available in SKILL.md
```

### Mandatory Principle

The orchestrator must treat:

```text
SKILL.md
    =
security policy + authorization + safety + core architecture

references/install.md
    =
toolchain + installation + runtime + reproducibility

references/workflow.md
    =
operational execution + orchestration + assessment procedures
```

Do not duplicate large installation or workflow procedures inside `SKILL.md` when the authoritative detail already exists in the reference files.

## Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/05-09-target-normalization.md` — §5–9: Target Normalization, DNS Rebinding Protection, Authentication and Secrets, MCP Security Layer, Security Testing Layers
- `references/10-13-tool-catalog.md` — §10–13: Tool Catalog, Tool Selection Strategy, Testing Profiles, Scanner Safety Profiles
- `references/14-22-nuclei-policy.md` — §14–22: Nuclei Policy, ZAP Policy, Fuzzing Policy, Authentication Testing, Authorization Testing, Business-Logic Security, SSRF-Safe Policy, Finding Evidence Model, Confidence Model
- `references/23-31-cross-scanner-correlation.md` — §23–31: Cross-Scanner Correlation, Finding Deduplication, Independent Confirmation, Risk Prioritization, Standards Mapping, Audit Event Model, Audit Integrity, Local Repository Isolation, Scanner Execution
- `references/32-39-tool-discovery.md` — §32–39: Tool Discovery, Coverage Model, False Positive Loop, False Negative Loop, Regression Security, Delta Scanning, Attack Surface Graph, Attack-Path Reasoning
- `references/40-45-resource-and-lease-control.md` — §40–45: Resource and Lease Control, Retry Policy, Failure Classes, Result State, Standard Assessment Report, Finding Format
- `references/48-interaction-protocol.md` — §48: Interaction Protocol
- `references/50-final-security-principle.md` — §50: Final Security Principle
