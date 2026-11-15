# xninetzy-security-testing — §23–31

Contents: 23. Cross-Scanner Correlation; 24. Finding Deduplication; 25. Independent Confirmation; 26. Risk Prioritization; 27. Standards Mapping; 28. Audit Event Model; 29. Audit Integrity; 30. Local Repository Isolation; 31. Scanner Execution

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

Implemented in `xninetzy/ecosystem/scanners/runner.py` and exposed through `security_run_gitleaks`, `security_run_trivy`, `security_run_osv`, `security_run_semgrep`, `security_sbom`, `security_run_zap` and `security_run_schemathesis`. There is no generic `security_execute`: each scanner has its own adapter and fixed argument template.

Every run is `docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges` with memory, pid and CPU limits, a non-root user, a read-only source mount and an output directory under the scope. The docker socket is never mounted and images are never pulled automatically: a missing image returns `TOOL_MISSING`.

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
