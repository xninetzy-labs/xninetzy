

name: "xninetzy-security-testing"
description: 
  ---
Authorized security assessment and self-pentesting control-plane for Xninetzy MCP.
   Orchestrates open-source reconnaissance, attack-surface discovery, HTTP/API security
   testing, DAST, SAST, SCA, secret scanning, container/image analysis, IaC scanning,
   Kubernetes security checks, cloud posture assessment, TLS analysis, mobile assessment,
   evidence correlation, regression verification, and audit reporting for explicitly
   authorized owner-controlled assets. Never expands scope silently, never bypasses
   authentication or human verification, never performs destructive exploitation, and
   never treats scanner output as confirmed evidence without validation.
metadata:
            owner: "misbahul45"
            scope: "project"
authority:
   - AGENTS.md
   - global opencode AGENTS.md
interfaces:
- mcp
- http-mcp-bridge
language: "en"
version: "2.0.0"
added: "2026-09-18"
domain: "xninetzy.domains.security"
lifecycle: >
intake -> normalize -> authorize -> isolate -> discover -> enumerate ->
analyze -> correlate -> validate -> prioritize -> report -> regress -> learn

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

## 5. Target Normalization

Before any scanner runs:

### URL normalization

Normalize:

* scheme
* hostname
* lowercase hostname
* explicit port
* default port
* path
* trailing slash
* fragments
* percent encoding
* punycode
* userinfo

Reject:

```text
javascript:
data:
file:
ftp:
gopher:
file://
```

unless a separate explicitly authorized test profile supports them.

### DNS normalization

Resolve hostname and record:

```text
hostname
A records
AAAA records
CNAME chain
resolution timestamp
resolved IPs
```

The resolved addresses become part of the scan evidence.

If the hostname later resolves to an address outside the authorized scope:

```text
STOP
```

Do not automatically continue.

### Redirect normalization

Every HTTP redirect target must be checked against the ScopeManifest.

Allowed:

```text
scope.example.com
www.scope.example.com
api.scope.example.com
```

Blocked:

```text
attacker.example
169.254.169.254
localhost
10.0.0.1
```

A redirect never grants authorization to a new host.

---

## 6. DNS Rebinding Protection

Network scanners must defend against time-of-check/time-of-use target changes.

For each target:

1. Resolve.
2. Record resolved addresses.
3. Validate against scope.
4. Start scan.
5. Re-resolve at bounded checkpoints.
6. Compare resolution set.
7. Stop on unexpected transition.

Unexpected transition:

```text
allowed public IP
        ->
private IP
metadata IP
protected domain
out-of-scope IP
```

results in:

```text
SCOPE_DRIFT
```

---

## 7. Authentication and Secrets

Authenticated testing may be supported only through secure secret references.

Never accept raw credentials in normal prompt content.

Allowed model:

```yaml
auth:
  mode: secret_ref
  username_ref: secret://security/test-user
  session_cookie_ref: secret://security/staging-session
```

Disallowed model:

```text
username=admin
password=SuperSecret123
cookie=session=abcdef...
```

Secrets must be:

* injected into subprocess environment or isolated secret store
* excluded from stdout
* excluded from stderr
* redacted from reports
* redacted from debug output
* excluded from audit persistence
* excluded from model context whenever possible

Never print:

```text
Authorization: Bearer ...
Cookie: ...
Set-Cookie: ...
X-API-Key: ...
AWS_SECRET_ACCESS_KEY=...
```

Evidence should instead say:

```text
Authenticated request used.
Credential material intentionally redacted.
```

---

## 8. MCP Security Layer

Xninetzy itself is an MCP system and therefore the security layer must assess MCP-specific controls.

The MCP security model must be treated as a first-class domain.

MCP architecture separates host, client, and server responsibilities, while authorization and permissions are critical boundaries. Current MCP guidance also emphasizes that tool annotations are hints rather than hard security enforcement.

Test:

### Server authorization

* unauthenticated request
* expired token
* wrong issuer
* wrong audience
* wrong scope
* token for another user
* token for another server
* insufficient privilege
* revoked credential

### Tool authorization

For every protected tool:

```text
public?
authenticated?
role allowed?
scope allowed?
resource allowed?
environment allowed?
destructive capability?
```

### Capability exposure

Inventory:

```text
tools/list
resources/list
prompts/list
completion endpoints
sampling capability
elicitation capability
tasks/extensions
```

Check whether sensitive capability is exposed unnecessarily.

### Tool annotations

Treat:

```text
readOnlyHint
destructiveHint
idempotentHint
openWorldHint
```

as metadata rather than enforcement.

The server implementation itself must enforce behavior. MCP documentation explicitly warns that untrusted servers can misrepresent annotations.

### MCP-specific abuse classes

Detect:

```text
tool confusion
cross-tool privilege escalation
confused deputy
scope laundering
authorization boundary mismatch
resource URI traversal
unsafe remote resource retrieval
untrusted tool instructions
prompt injection via tool results
secret exfiltration paths
unexpected network egress
unsafe sampling permissions
cross-server context leakage
```

Resource URI inputs must be validated and sensitive resources must have access controls.

---

## 9. Security Testing Layers

The engine operates across these layers:

```text
L0 Governance / Scope
L1 Asset Discovery
L2 Network / Service Enumeration
L3 Web Surface Discovery
L4 HTTP Security
L5 API Security
L6 Authentication / Session
L7 Authorization
L8 Business-Logic Controls
L9 DAST
L10 SAST
L11 Dependency / SCA
L12 Secret Detection
L13 Container Security
L14 IaC Security
L15 Kubernetes Security
L16 Cloud Security
L17 TLS / Cryptography
L18 Mobile Security
L19 Supply Chain
L20 Correlation / Validation
L21 Regression / Continuous Security
```

---

## 10. Tool Catalog

The following open-source tools form the preferred baseline.

### Network / attack-surface

```text
Nmap
OWASP Amass
ProjectDiscovery Subfinder
ProjectDiscovery httpx
ProjectDiscovery Naabu
```

Nmap is an open-source network exploration and security auditing tool with host, service/version, OS, and port analysis.

OWASP Amass is designed for attack-surface mapping and external asset discovery using OSINT and active reconnaissance.

### Web discovery

```text
ProjectDiscovery Katana
ProjectDiscovery Nuclei
ffuf
OWASP ZAP
testssl.sh
```

ProjectDiscovery documents pipelines connecting Subfinder, httpx, Katana, and Nuclei for asset-to-endpoint analysis.

ffuf provides content, vhost, and parameter discovery capabilities. Its use here is constrained by the authorization and rate-limit layer.

testssl.sh analyzes TLS/SSL protocols, ciphers, and cryptographic weaknesses and supports machine-readable output.

### Code security

```text
Semgrep
Gitleaks
Trivy
OSV-Scanner
OWASP dep-scan
```

Semgrep is an open-source static-analysis tool supporting many languages and secure coding rules.

Gitleaks detects hardcoded secrets such as passwords, API keys, and tokens across repository history and working trees.

Trivy can scan filesystems, repositories, and images for vulnerabilities, secrets, and configuration issues.

OSV-Scanner maps dependencies to known vulnerabilities and supports source and container scanning across many ecosystems.

OWASP dep-scan adds dependency risk, SBOM/VDR/VEX, and reachability analysis for supported ecosystems.

### SBOM / container

```text
Syft
Grype
Trivy
Dockle
```

Syft generates SBOMs and Grype scans images, filesystems, and SBOMs against vulnerability databases.

Dockle audits container images against security and best-practice checkpoints.

### IaC

```text
Checkov
Trivy config
```

Checkov supports Terraform, CloudFormation, Kubernetes, Helm, Kustomize, Dockerfile, OpenAPI, Bicep, ARM and related IaC surfaces.

### Kubernetes

```text
kube-bench
KubeLinter
Trivy
```

kube-bench evaluates Kubernetes configuration against CIS Kubernetes Benchmark checks.

KubeLinter statically analyzes Kubernetes YAML, Helm, and Kustomize manifests for security and production-readiness issues.

### Cloud

```text
Prowler
```

Prowler provides open-source cloud security checks across AWS, Azure, GCP, Kubernetes, Microsoft 365 and GitHub, with framework-oriented assessments.

### API

```text
Schemathesis
OWASP ZAP API scan
Nuclei API templates
```

Schemathesis uses OpenAPI or GraphQL descriptions to generate API test cases, including coverage, fuzzing, and stateful testing.

### Mobile

```text
MobSF
mobsfscan
```

MobSF provides automated static and dynamic security assessment for Android, iOS, and Windows application artifacts.

---

## 11. Tool Selection Strategy

Do not automatically run everything.

The planner selects tools from the asset type.

```text
domain
 -> Amass/Subfinder
 -> httpx
 -> Naabu/Nmap
 -> Katana
 -> Nuclei
 -> ZAP
 -> testssl.sh

web app
 -> httpx
 -> Katana
 -> ZAP
 -> Nuclei
 -> ffuf
 -> testssl.sh

API
 -> OpenAPI inventory
 -> Schemathesis
 -> ZAP API
 -> Nuclei API
 -> authorization tests

repo
 -> Semgrep
 -> Gitleaks
 -> Trivy
 -> OSV-Scanner
 -> dep-scan
 -> Syft
 -> Grype

Docker
 -> Trivy
 -> Syft
 -> Grype
 -> Dockle

IaC
 -> Checkov
 -> Trivy config

Kubernetes
 -> kube-bench
 -> KubeLinter
 -> Trivy

cloud
 -> Prowler

mobile
 -> MobSF
```

---

## 12. Testing Profiles

### `passive`

Use for low-impact posture assessment.

```text
DNS / certificate observations
technology fingerprinting
headers
public metadata
dependency and source scans
SAST
secrets
SBOM
configuration analysis
```

### `baseline`

```text
passive
+
bounded web enumeration
+
ZAP baseline
+
Nuclei low-risk templates
+
TLS analysis
```

### `active-safe`

```text
baseline
+
bounded active verification
+
approved content discovery
+
API schema testing
+
authorization verification
```

Never interpret `active-safe` as unlimited scanning.

### `full-assessment`

Runs the broad security matrix, but remains constrained by:

```text
scope
rate
timeout
non-destructive policy
protected target policy
tool allowlist
template allowlist
credential boundary
```

### `repo-audit`

```text
Semgrep
Gitleaks
Trivy
OSV-Scanner
dep-scan
Syft
Grype
Checkov
KubeLinter
Dockle
```

---

## 13. Scanner Safety Profiles

Every subprocess receives a `ScannerPolicy`.

```yaml
scanner_policy:
  network:
    max_rps: 5
    max_concurrency: 10
    follow_redirects: true
    enforce_scope_on_redirect: true
    max_redirects: 5

  execution:
    timeout_seconds: 900
    memory_mb: 1024
    cpu_limit: 2
    max_output_bytes: 8000000

  behavior:
    destructive: false
    exploit_execution: false
    brute_force: false
    credential_stuffing: false
    captcha_bypass: false
    otp_bypass: false
    mfa_bypass: false

  filesystem:
    repo_mount: read_only
    write_targets:
      - ephemeral_output_directory
```

---

## 14. Nuclei Policy

Nuclei templates are executable security logic.

Therefore:

1. Never execute arbitrary unreviewed templates.
2. Prefer official/pinned template sets.
3. Record template version/hash.
4. Reject templates requesting disallowed behaviors.
5. Limit severity/profile.
6. Limit request rate.
7. Store template provenance.

Template evidence:

```yaml
template:
  id: ...
  version: ...
  sha256: ...
  source: ...
  loaded_at: ...
```

---

## 15. ZAP Policy

Supported:

```text
baseline
api
safe active verification
```

Blocked:

```text
credential brute force
destructive payload testing
unbounded spidering
out-of-scope redirect following
```

ZAP Automation may orchestrate a scan, but the Xninetzy policy layer remains authoritative.

OWASP ZAP is the preferred open-source DAST engine for web/API assessment.

---

## 16. Fuzzing Policy

Fuzzing is permitted only when:

```text
target is explicitly authorized
endpoint belongs to the scope
rate budget exists
concurrency is bounded
request size is bounded
state-changing methods are disabled by default
```

Default:

```text
GET
HEAD
OPTIONS
safe schema-conforming requests
```

POST/PUT/PATCH/DELETE require a separately declared test profile and safe target environment.

No destructive mutation is allowed by this skill.

---

## 17. Authentication Testing

Test authentication controls rather than attempting to break into accounts.

Examples:

```text
missing credential
expired credential
invalid credential
wrong audience
wrong issuer
wrong role
insufficient scope
revoked session
session invalidation
cookie security attributes
token lifetime
authorization context mismatch
```

Never:

```text
password brute force
OTP guessing
CAPTCHA solving
MFA bypass
credential stuffing
credential harvesting
```

---

## 18. Authorization Testing

Authorization is a first-class testing layer.

Model:

```text
Actor
  -> Role
  -> Resource
  -> Action
  -> Environment
```

Test:

```text
same-user same-resource
same-user different-resource
different-user same-resource
lower-privilege role
higher-privilege role
anonymous role
expired role
cross-tenant access
cross-organization access
direct-object-reference boundaries
function-level access
property-level access
```

For APIs, map tests to OWASP API Security categories including BOLA, broken authentication, property-level authorization, function-level authorization, resource consumption, SSRF, security misconfiguration, inventory, and unsafe API consumption.

---

## 19. Business-Logic Security

Automated scanners are insufficient for business logic.

The engine therefore creates a `BusinessFlowMap`.

```text
Actor
 ->
Precondition
 ->
Action
 ->
State transition
 ->
Postcondition
```

Examples:

```text
registration
login
email verification
password reset
checkout
coupon
subscription
role assignment
file upload
approval
refund
invitation
organization membership
MCP tool authorization
```

Test:

```text
order manipulation
workflow skipping
replay
state confusion
duplicate action
privilege boundary violation
rate-limit bypass
race-condition indicators
inconsistent authorization
```

Do not perform destructive financial or irreversible operations.

---

## 20. SSRF-Safe Policy

The engine may detect SSRF indicators.

It must not automatically weaponize SSRF against metadata services or internal infrastructure.

Allowed:

```text
controlled callback infrastructure
scope-approved test endpoint
non-sensitive internal canary
```

Blocked:

```text
cloud metadata
production internal services
credential endpoints
administrative interfaces
```

---

## 21. Finding Evidence Model

Every finding must contain:

```yaml
finding_id: uuid
fingerprint: deterministic_hash
title: string
severity: info | low | medium | high | critical
confidence: suspected | indicated | strong | verified

asset:
  type: domain | endpoint | api | repo | image | iac | k8s | cloud | mobile
  identifier: normalized_identifier

source:
  scanner: ...
  scanner_version: ...
  rule_or_template: ...
  template_hash: ...

evidence:
  type: request_response | source_location | dependency | configuration | scanner
  location: redacted
  summary: redacted
  captured_at: timestamp

mapping:
  cwe: []
  owasp: []
  asvs: []
  wstg: []
  api_top_10: []

impact:
  confidentiality: none | low | medium | high
  integrity: none | low | medium | high
  availability: none | low | medium | high

remediation:
  summary: ...
  verification_test: ...

status:
  open | accepted | mitigated | resolved | false_positive | duplicate
```

---

## 22. Confidence Model

### `suspected`

Scanner indicates a possible issue but no supporting evidence.

### `indicated`

Multiple independent signals suggest the condition.

### `strong`

Direct application/configuration evidence exists but security impact is not fully demonstrated.

### `verified`

The security condition is directly evidenced using a non-destructive validation method.

"Verified" does not mean weaponized exploitation.

---

## 23. Cross-Scanner Correlation

The system must correlate independent findings.

Example:

```text
Nuclei:
  exposed package version

Trivy:
  vulnerable package

OSV:
  matching advisory

Semgrep:
  reachable vulnerable API usage

dep-scan:
  vulnerable dependency reachable

Result:
  correlated finding
```

This is materially stronger than five unrelated alerts.

---

## 24. Finding Deduplication

Use deterministic fingerprints:

```text
asset
normalized_location
vulnerability_class
rule_id
package_or_component
parameter_or_symbol
```

Example:

```text
sha256(
  asset +
  endpoint +
  cwe +
  normalized_rule +
  component
)
```

Merge duplicates from:

```text
Nuclei
ZAP
Trivy
Semgrep
OSV
dep-scan
Grype
Checkov
KubeLinter
Prowler
```

Do not merge findings merely because titles look similar.

---

## 25. Independent Confirmation

High-impact findings should seek independent confirmation where safe.

Examples:

```text
Semgrep finding
 -> source inspection

Trivy CVE
 -> OSV confirmation
 -> Grype confirmation

Nuclei exposure
 -> HTTP evidence
 -> ZAP corroboration

Checkov misconfiguration
 -> raw IaC inspection

kube-bench failure
 -> K8s configuration inspection
```

Do not automatically re-run destructive tests merely to increase confidence.

---

## 26. Risk Prioritization

Security severity must combine:

```text
technical severity
+
asset exposure
+
authentication boundary
+
authorization boundary
+
data sensitivity
+
exploit preconditions
+
confidence
+
fix availability
+
environment
```

A high technical severity in a local disposable development artifact must not automatically outrank a confirmed high-impact issue on an internet-facing production boundary.

Use CVSS where applicable.

Do not invent exploitability evidence.

---

## 27. Standards Mapping

Web application assessment should map to:

```text
OWASP ASVS
OWASP WSTG
OWASP Top 10
OWASP API Security Top 10
```

OWASP ASVS provides requirements for verifying technical security controls, while WSTG provides a structured methodology and practical testing guidance.

Use versioned requirement identifiers wherever possible.

Example:

```text
ASVS v5.0.0
WSTG v4.2
API1:2023
```

The current OWASP Top 10 release is 2025.

Infrastructure findings may additionally map to:

```text
CIS Benchmarks
CIS Controls
NIST
MITRE ATT&CK
```

CIS Benchmarks provide consensus-based secure configuration guidance across cloud, operating systems, containers, databases, network devices, and other technologies.

---

## 28. Audit Event Model

Every meaningful action emits:

```yaml
event_id: uuid
timestamp: timestamp
session_id: uuid
scope_id: uuid
actor: opaque
action: ...
tool: ...
target: normalized_target
policy_decision: allow | deny | stop
reason: ...
result: success | partial | failed | timeout | missing
```

Never record:

```text
password
cookie
API key
refresh token
private secret
raw authorization header
full request body containing secrets
```

---

## 29. Audit Integrity

Use a hash chain:

```text
event_n_hash =
sha256(
  event_n +
  event_n_minus_1_hash
)
```

This allows tamper detection during an assessment session.

Example:

```yaml
audit:
  sequence: 42
  previous_hash: ...
  event_hash: ...
```

The audit log may remain in-memory for authorization state, but report artifacts may contain sanitized findings and provenance.

---

## 30. Local Repository Isolation

For repository scanning:

```text
repo
  -> read-only mount
  -> isolated scanner runner
  -> ephemeral output
```

Never give security scanners:

```text
Docker socket
host root
unrestricted filesystem write
cloud credentials
SSH agent
browser profile
full home directory
```

unless a separate explicit assessment profile requires it.

---

## 31. Scanner Execution

Every scanner invocation must go through one subprocess gateway.

Conceptually:

```python
security_execute(
    tool=...,
    args=...,
    scope=...,
    policy=...,
    timeout=...,
    output_limit=...,
)
```

The gateway enforces:

```text
binary allowlist
argument allowlist
target allowlist
environment allowlist
rate limit
timeout
memory limit
CPU limit
output limit
network policy
filesystem policy
secret redaction
audit event
```

The language model must never construct arbitrary unrestricted subprocess commands.

---

## 32. Tool Discovery

`security_check_tools` must return:

```yaml
tool:
version:
path:
healthy:
capabilities:
supported_targets:
container_available:
docker_available:
notes:
```

Example:

```text
nmap       YES  /usr/bin/nmap
nuclei     YES  /usr/local/bin/nuclei
semgrep    YES  /usr/local/bin/semgrep
gitleaks   YES  /usr/local/bin/gitleaks
trivy      YES  /usr/bin/trivy
```

A missing scanner is a degraded capability, not a reason to fabricate coverage.

---

## 33. Coverage Model

Before reporting completion calculate:

```text
asset coverage
endpoint coverage
technology coverage
scanner coverage
control coverage
evidence coverage
```

Example:

```yaml
coverage:
  assets:
    discovered: 17
    assessed: 14
    blocked: 2
    unknown: 1

  web:
    endpoints_discovered: 183
    analyzed: 167

  controls:
    authentication: 82%
    authorization: 71%
    configuration: 94%
```

Never claim:

```text
"100% secure"
```

or:

```text
"full pentest complete"
```

when significant scope remains unknown.

---

## 34. False Positive Loop

Each finding may be labeled:

```text
true_positive
false_positive
duplicate
accepted_risk
not_applicable
needs_validation
```

False-positive labels should create detector-learning records.

Example:

```yaml
learning_event:
  detector: nuclei-exposed-config
  fingerprint: ...
  verdict: false_positive
  reason: documented_false_positive_pattern
  confidence: high
  proposed_rule_change: ...
```

---

## 35. False Negative Loop

Potential false negatives are more important than merely reducing alert counts.

Signal sources:

```text
manual finding
post-incident finding
developer report
regression failure
independent scanner
historical remediation
```

The system may propose:

```text
new Semgrep rule
new Nuclei detection
new correlation rule
new API assertion
new regression fixture
new KubeLinter policy
```

But it must never automatically modify:

```text
scope policy
protected targets
authorization policy
credential policy
destructive-action policy
network egress policy
```

Self-improvement is detector improvement, not permission escalation.

---

## 36. Regression Security

Every resolved finding may become a regression test.

Example:

```text
Finding:
missing authorization on GET /api/project/{id}

Patch:
authorization middleware added

Regression:
same-user -> allowed
other-user -> denied
anonymous -> denied
```

The regression corpus is version-controlled.

---

## 37. Delta Scanning

Prefer differential assessment after changes.

Compare:

```text
previous asset graph
new asset graph

previous endpoint graph
new endpoint graph

previous dependencies
new dependencies

previous findings
new findings
```

Classify:

```text
NEW
FIXED
UNCHANGED
REGRESSED
SCOPE_CHANGED
UNKNOWN
```

---

## 38. Attack Surface Graph

Represent security data as:

```text
Organization
  |
  +-- Domain
       |
       +-- DNS
       |
       +-- IP
       |
       +-- Port
       |
       +-- Service
       |
       +-- Technology
       |
       +-- Endpoint
       |
       +-- Parameter
       |
       +-- API Operation
       |
       +-- Repository
       |
       +-- Dependency
       |
       +-- Container
       |
       +-- Cloud Resource
       |
       +-- Kubernetes Resource
       |
       +-- Finding
```

Relationships must be evidence-backed.

Examples:

```text
domain -> resolves_to -> IP
IP -> exposes -> port
port -> serves -> service
service -> uses -> technology
endpoint -> implemented_by -> repository_symbol
repository -> depends_on -> package
package -> affected_by -> CVE
```

Do not infer hard relationships from embeddings alone.

---

## 39. Attack-Path Reasoning

The engine may reason about potential attack paths:

```text
internet exposure
 -> vulnerable service
 -> authentication weakness
 -> excessive privilege
 -> sensitive resource
```

But attack-path outputs must distinguish:

```text
observed path
potential path
inferred path
blocked path
unknown path
```

Never represent a theoretical path as demonstrated compromise.

---

## 40. Resource and Lease Control

The system must detect scanner resource contention.

State:

```text
idle
running
busy
cooldown
rate_limited
failed
```

Do not launch redundant concurrent scanners against the same target without justification.

Use a target lease:

```yaml
lease:
  target: ...
  session_id: ...
  expires_at: ...
```

---

## 41. Retry Policy

Retry only:

```text
network timeout
transient DNS
temporary scanner failure
temporary service unavailable
```

Do not retry:

```text
authorization denied
scope denied
protected target
credential failure
CAPTCHA
MFA
out-of-scope redirect
policy violation
```

Never retry to defeat a security mechanism.

---

## 42. Failure Classes

```text
AUTHORIZATION_DENIED
PROTECTED_TARGET
SCOPE_DRIFT
DNS_REBINDING
REDIRECT_OUT_OF_SCOPE
TOOL_MISSING
TOOL_VERSION_UNSUPPORTED
TIMEOUT
RATE_LIMITED
NETWORK_UNAVAILABLE
CREDENTIAL_UNAVAILABLE
SECRET_REDACTION_FAILURE
SCANNER_ERROR
INVALID_TARGET
POLICY_VIOLATION
PARTIAL_EVIDENCE
```

---

## 43. Result State

The overall assessment may end in:

```text
COMPLETE
PARTIAL
BLOCKED
FAILED
UNCERTAIN
```

`COMPLETE` means the declared assessment profile executed successfully over the declared scope.

It does not mean the target is secure.

---

## 44. Standard Assessment Report

Every report contains:

```text
Executive Summary
Assessment Scope
Authorization Context
Environment
Asset Inventory
Attack Surface
Technology Inventory
Testing Matrix
Findings
Validated Evidence
False Positives / Duplicates
Risk Prioritization
Authentication Findings
Authorization Findings
API Findings
Web Findings
Code Findings
Dependency Findings
Secret Findings
Container Findings
IaC Findings
Kubernetes Findings
Cloud Findings
Mobile Findings
TLS Findings
MCP Security Findings
Coverage
Unassessed Areas
Remediation Plan
Regression Tests
Retest Status
Tool Versions
Template Versions
Assessment Timeline
Limitations
```

---

## 45. Finding Format

```text
## SEC-2026-0001 — Broken Object Authorization

Severity: HIGH
Confidence: VERIFIED
Asset: https://app.example.test
Endpoint: GET /api/projects/{id}

Observed:
User A could request a resource belonging to User B.

Evidence:
Redacted request/response pair.

Impact:
Potential cross-account data exposure.

Mapping:
API1:2023
ASVS Access Control
WSTG Authorization Testing

Remediation:
Enforce resource ownership/tenant authorization server-side.

Regression:
User A -> own project -> 200
User A -> User B project -> 403
Anonymous -> project -> 401
```

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

## 48. Interaction Protocol

When the owner requests a network assessment:

```text
1. Parse target.
2. Normalize target.
3. Check protected target policy.
4. Build ScopeManifest.
5. Determine assessment profile.
6. Check private-target requirements.
7. Check scanner availability.
8. Create ephemeral security session.
9. Lock target lease.
10. Execute least-invasive phase first.
11. Expand only within declared scope/profile.
12. Correlate evidence.
13. Validate findings.
14. Generate report.
15. Emit audit summary.
16. Store regression candidates.
```

Do not ask repetitive questions that are already explicitly answered by the current scope.

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

## 50. Final Security Principle

The Xninetzy security engine should behave like a disciplined senior security assessment system:

```text
discover broadly
within scope

enumerate systematically
within budget

test deeply
without destructive behavior

correlate independently
before escalating confidence

validate carefully
without weaponization

report precisely
with provenance

regress continuously
after remediation

learn continuously
without widening authority
```

The system is successful when it produces:

```text
high coverage
+
high evidence quality
+
low false-positive noise
+
reproducible findings
+
clear remediation
+
safe execution
+
strong auditability
```

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
