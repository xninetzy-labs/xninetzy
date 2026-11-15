# xninetzy-security-testing — §32–39

Contents: 32. Tool Discovery; 33. Coverage Model; 34. False Positive Loop; 35. False Negative Loop; 36. Regression Security; 37. Delta Scanning; 38. Attack Surface Graph; 39. Attack-Path Reasoning

## 32. Tool Discovery

`security_check_tools` reads `security-tools.lock` (image tag and digest per scanner) and reports one row per scanner:

```yaml
tool:
capability:
status: READY | DEGRADED | MISSING | UNHEALTHY
image:
version:
digest:
detail:
```

`READY` means the image is present locally and its digest matches the pin in the lock. `DEGRADED` means the image is present but the digest is unpinned or differs from the lock. `MISSING` means the image is not installed; `detail` carries the `docker pull` command for the owner to run. `UNHEALTHY` means docker or its daemon is unreachable. `security_check_tools(pin=True)` writes the digests of locally installed images into the lock. The tool never pulls an image and never runs a scanner.

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
