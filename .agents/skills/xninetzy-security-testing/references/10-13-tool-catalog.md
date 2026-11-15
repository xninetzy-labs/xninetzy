# xninetzy-security-testing — §10–13

Contents: 10. Tool Catalog; 11. Tool Selection Strategy; 12. Testing Profiles; 13. Scanner Safety Profiles

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
