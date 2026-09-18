# Xninetzy Security Testing — Installation & Toolchain

## 1. Purpose

`xninetzy.domains.security` does not bundle security scanners.

The security domain provides thin, policy-controlled wrappers around external open-source security tools.

The operator is responsible for installing and maintaining the binaries or container images used by the scanner layer.

The Xninetzy orchestrator is responsible for:

```text
tool discovery
version detection
capability detection
health checks
scope enforcement
execution policy
timeout control
output limits
secret redaction
artifact collection
provenance recording
```

The installation layer is intentionally separate from the security workflow layer.

---

# 2. Supported Security Stack

Xninetzy should support the following tool families.

| Layer             | Tool           | Primary Function                        | Execution         |
| ----------------- | -------------- | --------------------------------------- | ----------------- |
| Network           | Nmap           | Port/service enumeration                | Native/Docker     |
| Attack Surface    | OWASP Amass    | Asset/DNS mapping                       | Native/Docker     |
| Passive DNS       | Subfinder      | Passive subdomain discovery             | Native/Docker     |
| HTTP              | httpx          | HTTP probing/fingerprinting             | Native/Docker     |
| Port Discovery    | Naabu          | Fast port discovery                     | Native/Docker     |
| Web Crawler       | Katana         | Endpoint crawling                       | Native/Docker     |
| DAST              | OWASP ZAP      | Web/API security testing                | Docker preferred  |
| Vulnerability     | Nuclei         | Template-based detection                | Native/Docker     |
| Content Discovery | ffuf           | Bounded content/vhost discovery         | Native/Docker     |
| TLS               | testssl.sh     | TLS/SSL analysis                        | Native/Docker     |
| SAST              | Semgrep        | Source-code security analysis           | Native/Docker     |
| Secrets           | Gitleaks       | Secret detection                        | Native/Docker     |
| SCA               | Trivy          | Dependency/filesystem/image/config scan | Native/Docker     |
| SCA               | OSV-Scanner    | Known dependency vulnerabilities        | Native/Docker     |
| SCA               | OWASP dep-scan | Dependency/security risk analysis       | Docker/Native     |
| SBOM              | Syft           | SBOM generation                         | Native/Docker     |
| Vulnerability     | Grype          | SBOM/image vulnerability scanning       | Native/Docker     |
| IaC               | Checkov        | Infrastructure-as-code security         | Native/Docker     |
| Kubernetes        | kube-bench     | CIS Kubernetes benchmark                | Docker/Native     |
| Kubernetes        | KubeLinter     | Kubernetes manifest analysis            | Native/Docker     |
| Container         | Dockle         | Container image hardening               | Native/Docker     |
| Cloud             | Prowler        | Cloud security posture                  | Native/Docker     |
| API               | Schemathesis   | OpenAPI/GraphQL testing                 | uvx/Native/Docker |
| Mobile            | MobSF          | Mobile application security testing     | Docker preferred  |
| Mobile SAST       | mobsfscan      | Mobile source analysis                  | Native/Docker     |

---

# 3. Installation Philosophy

Xninetzy uses three installation classes.

## Class A — Native CLI

Use when:

```text
low startup latency matters
scanner is frequently called
filesystem access is local
scanner output needs easy integration
```

Examples:

```text
nmap
subfinder
httpx
naabu
katana
nuclei
ffuf
semgrep
gitleaks
trivy
syft
grype
```

## Class B — Isolated Container

Prefer when:

```text
scanner has a large dependency tree
scanner exposes a service
scanner requires special runtime
scanner has potentially risky dependencies
portable reproducibility is important
```

Examples:

```text
ZAP
MobSF
Prowler
Schemathesis
Checkov
Trivy
testssl.sh
```

## Class C — Kubernetes / Infrastructure Runner

Use for:

```text
kube-bench
Prowler
cluster-level checks
cloud posture checks
```

These tools may require access beyond a normal user process, so they must run inside a dedicated restricted security runner.

---

# 4. Base System Requirements

Recommended baseline:

```text
Linux x86_64
Linux ARM64
macOS ARM64/x86_64
Git
curl
wget
jq
tar
unzip
gzip
bash
Docker
Docker Compose
Python
Go
Node.js
Java
```

Verify:

```bash
git --version
curl --version
wget --version
jq --version
tar --version
unzip -v
bash --version
docker --version
docker compose version
python3 --version
go version
node --version
java -version
```

---

# 5. Ubuntu / Debian Base Packages

```bash
sudo apt update

sudo apt install -y \
  bash \
  ca-certificates \
  curl \
  wget \
  git \
  jq \
  unzip \
  zip \
  tar \
  gzip \
  xz-utils \
  gnupg \
  lsb-release \
  build-essential \
  pkg-config \
  libpcap-dev \
  openssl \
  python3 \
  python3-venv \
  python3-pip
```

For Docker:

```bash
docker --version
docker compose version
```

Do not expose `/var/run/docker.sock` to arbitrary scanner containers.

The Docker socket is equivalent to a highly privileged control surface and must only be mounted for tools that genuinely require access to the local container engine.

---

# 6. Go Runtime

ProjectDiscovery tooling currently requires a relatively recent Go toolchain. Current upstream documentation lists Go 1.26+ for Subfinder and Katana, while Nuclei requires Go 1.24.2+ and httpx requires Go 1.25+. Therefore Xninetzy should standardize its build environment on Go 1.26+ rather than maintaining different minimums for individual scanners.

Verify:

```bash
go version
```

Recommended policy:

```text
minimum:
  Go 1.26+

record:
  go_version
  GOOS
  GOARCH
```

Set the binary path:

```bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
echo "$PATH"
```

---

# 7. ProjectDiscovery Installation

## 7.1 Subfinder

Subfinder is intended for passive subdomain enumeration and supports provider integrations through its configuration.

Install:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

Verify:

```bash
subfinder -version
```

Xninetzy capability:

```text
PASSIVE_SUBDOMAIN_ENUMERATION
```

---

## 7.2 httpx

ProjectDiscovery httpx performs HTTP probing and technology/fingerprint extraction. Current upstream installation guidance requires Go 1.25+.

Install:

```bash
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
```

Verify:

```bash
httpx -version
```

Capability:

```text
HTTP_PROBING
TECHNOLOGY_FINGERPRINTING
STATUS_DETECTION
TLS_METADATA
REDIRECT_METADATA
```

---

## 7.3 Naabu

Naabu requires `libpcap` on Linux/macOS for packet capture.

Ubuntu/Debian:

```bash
sudo apt install -y libpcap-dev
```

Install:

```bash
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
```

Verify:

```bash
naabu -version
```

Capability:

```text
PORT_DISCOVERY
```

Naabu must always receive targets from the Xninetzy scope layer.

---

## 7.4 Katana

Current Katana documentation requires Go 1.26+ and supports standard and headless crawling.

Install:

```bash
CGO_ENABLED=1 go install github.com/projectdiscovery/katana/cmd/katana@latest
```

Verify:

```bash
katana -version
```

Capability:

```text
WEB_CRAWLING
JS_ENDPOINT_DISCOVERY
HEADLESS_DISCOVERY
```

Recommended Xninetzy defaults:

```text
depth:
  3

max_response_size:
  4 MiB

max_concurrency:
  policy controlled

scope:
  explicit

redirects:
  scope validated
```

Katana itself supports scope controls and exclusions, which should be configured consistently with the Xninetzy scope manifest.

---

## 7.5 Nuclei

Current upstream Nuclei requires Go 1.24.2+ and supports installation through Go, Homebrew, Docker, and releases.

Install:

```bash
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

Verify:

```bash
nuclei -version
```

Capability:

```text
TEMPLATE_BASED_VULNERABILITY_DETECTION
HTTP
DNS
TCP
SSL
FILE
```

Nuclei templates must be versioned.

Record:

```text
nuclei_version
template_commit
template_version
template_hash
```

Do not execute arbitrary third-party templates through the default Xninetzy profile.

---

# 8. OWASP Amass

Amass focuses on attack-surface mapping and external asset discovery. The project provides prebuilt binaries, Docker support, and package-based installation options.

Install through a release binary or the maintained package route.

Ubuntu/Kali/Parrot:

```bash
sudo apt update
sudo apt install -y amass
```

Verify:

```bash
amass -version
```

Alternative Docker:

```bash
docker pull amass
```

Capability:

```text
DNS_DISCOVERY
ASSET_MAPPING
EXTERNAL_ATTACK_SURFACE
```

---

# 9. OWASP ZAP

ZAP is the primary DAST engine.

For Xninetzy, Docker is preferred.

Pull:

```bash
docker pull zaproxy/zap-stable
```

Check:

```bash
docker run --rm zaproxy/zap-stable zap.sh -version
```

The ZAP Baseline scan is designed around spidering followed by passive scanning rather than active attacks, which makes it suitable for the Xninetzy baseline profile.

Example:

```bash
docker run --rm \
  -v "$PWD/security-output/zap:/zap/wrk:rw" \
  zaproxy/zap-stable \
  zap-baseline.py \
  -t https://authorized.example
```

Xninetzy wrapper requirements:

```text
target:
  injected by policy layer

redirect:
  scope checked

timeout:
  mandatory

output:
  mounted only to ephemeral assessment directory

API:
  never exposed publicly
```

---

# 10. ffuf

ffuf is a Go-based web fuzzer with support for content and virtual-host discovery.

Install:

```bash
go install github.com/ffuf/ffuf/v2@latest
```

Verify:

```bash
ffuf -V
```

Homebrew:

```bash
brew install ffuf
```

Xninetzy restrictions:

```text
bounded wordlist
bounded concurrency
bounded request rate
scope-only target
non-destructive profile
```

Parameter and POST fuzzing must not be enabled by the default profile.

---

# 11. TLS — testssl.sh

testssl.sh is a standalone TLS/SSL analysis tool that supports JSON, CSV, and HTML output and can run without a complex installation.

Clone stable release:

```bash
git clone --depth 1 \
  --branch 3.2 \
  https://github.com/testssl/testssl.sh.git \
  tools/testssl.sh
```

Verify:

```bash
./tools/testssl.sh/testssl.sh --version
```

Docker alternative:

```bash
docker pull ghcr.io/testssl/testssl.sh:3.3dev
```

For production/reproducibility, prefer a stable version rather than the development tag.

Machine-readable output is preferred:

```text
JSON
CSV
```

---

# 12. Semgrep

Semgrep should normally run inside an isolated Python environment or dedicated container.

Create virtual environment:

```bash
python3 -m venv ~/.venvs/xninetzy-security
source ~/.venvs/xninetzy-security/bin/activate
```

Install:

```bash
python -m pip install --upgrade pip
python -m pip install semgrep
```

Verify:

```bash
semgrep --version
```

Recommended profiles:

```text
security
correctness
framework-specific
custom-xninetzy-rules
```

For CI, pin the installed package version.

---

# 13. Gitleaks

Gitleaks supports Homebrew, Docker, Go, and release binaries.

Go installation:

```bash
go install github.com/gitleaks/gitleaks/v8@latest
```

Verify:

```bash
gitleaks version
```

Docker:

```bash
docker pull ghcr.io/gitleaks/gitleaks:latest
```

Run against a read-only repository mount:

```bash
docker run --rm \
  -v "$PWD:/repo:ro" \
  ghcr.io/gitleaks/gitleaks:latest \
  detect \
  --source=/repo
```

Never expose discovered secret contents to Xninetzy logs.

---

# 14. Trivy

Trivy has official binaries, packages, Homebrew support, and official container images. Current documentation lists `docker.io/aquasec/trivy`, GHCR, and AWS ECR images as official container distributions.

Native install:

```bash
brew install trivy
```

Ubuntu/Debian may use the official Trivy repository or release package.

Docker:

```bash
docker pull aquasec/trivy:latest
```

Verify:

```bash
trivy --version
```

Capabilities:

```text
FS
REPO
IMAGE
CONFIG
K8S
SECRET
VULNERABILITY
```

For reproducible assessments, pin the container tag/digest or native release version.

---

# 15. OSV-Scanner

OSV-Scanner provides official prebuilt binaries, Homebrew, Arch, Alpine, Windows package-manager options, and source installation. Current V2 source installation requires Go 1.26.2+.

Install from source:

```bash
go install github.com/google/osv-scanner/v2/cmd/osv-scanner@latest
```

Verify:

```bash
osv-scanner --version
```

Repository scan:

```bash
osv-scanner scan source -r .
```

Capability:

```text
DEPENDENCY_VULNERABILITY
```

For high-value findings, use OSV as an independent source alongside Trivy/Grype.

---

# 16. OWASP dep-scan

dep-scan can be installed using Python and optionally its extended dependency set. Its project documentation uses `pip install owasp-depscan` and supports local project analysis and reports.

Install:

```bash
python -m pip install owasp-depscan
```

Optional full installation:

```bash
python -m pip install 'owasp-depscan[all]'
```

Verify:

```bash
depscan --help
```

Run:

```bash
depscan \
  --src "$PWD" \
  --reports-dir "$PWD/security-output/depscan"
```

Capability:

```text
DEPENDENCY_RISK
REACHABILITY
SBOM/VDR
VEX
LICENSE_RISK
```

---

# 17. Syft

Syft is the canonical Xninetzy SBOM generator.

Official installation supports release binaries, Homebrew, Docker, and an installation script. The project also provides optional signature verification through Cosign.

Install:

```bash
curl -sSfL https://get.anchore.io/syft \
  | sudo sh -s -- -b /usr/local/bin
```

Verify:

```bash
syft version
```

Generate CycloneDX:

```bash
syft . -o cyclonedx-json=security-output/sbom.cdx.json
```

Generate SPDX:

```bash
syft . -o spdx-json=security-output/sbom.spdx.json
```

Capability:

```text
SBOM
COMPONENT_INVENTORY
```

For high-assurance environments, verify downloaded artifacts before installation.

---

# 18. Grype

Grype is used as an independent vulnerability engine over containers, filesystems, and SBOMs. Official installation supports its installation script and container/binary distributions.

Install:

```bash
curl -sSfL https://get.anchore.io/grype \
  | sudo sh -s -- -b /usr/local/bin
```

Verify:

```bash
grype version
```

Scan filesystem:

```bash
grype .
```

Scan SBOM:

```bash
grype sbom:security-output/sbom.cdx.json
```

Record:

```text
grype_version
database_version
database_timestamp
```

Use Grype primarily as an independent confirmation layer.

---

# 19. Checkov

Checkov currently supports Python 3.9–3.12 according to its project documentation. It can be installed through pip, Homebrew, or Docker.

Recommended isolated installation:

```bash
python3.12 -m venv ~/.venvs/xninetzy-checkov
source ~/.venvs/xninetzy-checkov/bin/activate
python -m pip install --upgrade pip
python -m pip install checkov
```

Verify:

```bash
checkov --version
```

Docker:

```bash
docker pull bridgecrew/checkov
```

Run:

```bash
checkov \
  --directory ./terraform \
  --output json \
  --output-file-path security-output/checkov
```

Capability:

```text
TERRAFORM
KUBERNETES
HELM
KUSTOMIZE
DOCKERFILE
CLOUDFORMATION
BICEP
ARM
OPENAPI
```

Avoid installing Checkov into the system Python on environments where distribution-managed packages may conflict; use a virtual environment.

---

# 20. KubeLinter

KubeLinter can run locally, in CI, or through its Docker image. Its documentation also supports direct binary installation and pre-commit integration.

Binary:

```bash
mkdir -p "$HOME/.local/bin"
```

Download an official release and install:

```bash
install -m 0755 kube-linter "$HOME/.local/bin/kube-linter"
```

Verify:

```bash
kube-linter version
```

Run:

```bash
kube-linter lint ./k8s
```

Docker:

```bash
docker pull ghcr.io/stackrox/kube-linter:latest
```

Capability:

```text
KUBERNETES_MANIFEST_SECURITY
HELM_SECURITY
KUSTOMIZE_SECURITY
CUSTOM_POLICY_CHECKS
```

---

# 21. kube-bench

kube-bench evaluates Kubernetes configuration against CIS Kubernetes Benchmark checks. The upstream project supports container execution and provides a Kubernetes Job example.

Docker:

```bash
docker pull aquasec/kube-bench:latest
```

Run in a dedicated assessment context:

```bash
docker run --rm \
  --pid=host \
  aquasec/kube-bench:latest
```

For Kubernetes Job execution:

```bash
kubectl apply -f job.yaml
```

Do not grant `hostPID`, host filesystem mounts, or cluster-wide privileges unless that exact assessment requires them.

If elevated access is required, use a dedicated security context and record it in the assessment manifest.

Capability:

```text
CIS_KUBERNETES
NODE_CONFIGURATION
CONTROL_PLANE_CONFIGURATION
```

---

# 22. Dockle

Dockle evaluates container image security and best-practice configuration.

Install through the official release/package channel.

Verify:

```bash
dockle --version
```

Run:

```bash
dockle myorg/myapp:latest
```

Prefer machine-readable output for Xninetzy ingestion.

Capability:

```text
CONTAINER_HARDENING
IMAGE_CONFIGURATION
CREDENTIAL_IN_IMAGE
```

---

# 23. Prowler

Prowler provides cloud security assessment capabilities and supports multiple deployment styles. Current project documentation provides a CLI package using Python 3.10 through <3.13, as well as Docker/Compose deployment.

Preferred isolated Python installation:

```bash
python3.12 -m venv ~/.venvs/xninetzy-prowler
source ~/.venvs/xninetzy-prowler/bin/activate
python -m pip install --upgrade pip
python -m pip install prowler
```

Verify:

```bash
prowler -v
```

Docker:

```bash
docker pull prowlercloud/prowler:latest
```

Cloud credentials must never be entered into normal Xninetzy prompt text.

Preferred credential model:

```text
short-lived credentials
OIDC
role assumption
environment injection
secret reference
```

Capability:

```text
AWS
AZURE
GCP
KUBERNETES
GITHUB
MICROSOFT_365
```

---

# 24. Schemathesis

Schemathesis supports OpenAPI and GraphQL property-based API testing. Its current documentation recommends `uvx schemathesis` for an isolated run and also provides Docker images.

Preferred installation-free method:

```bash
uvx schemathesis run ./openapi.yaml
```

Verify:

```bash
uvx schemathesis --version
```

Persistent installation:

```bash
uv tool install schemathesis
```

Docker:

```bash
docker pull ghcr.io/schemathesis/schemathesis:stable
```

For reproducible CI, pin an exact release tag rather than `latest`; Schemathesis documents version-specific Docker tags as immutable release references.

Capability:

```text
OPENAPI
GRAPHQL
PROPERTY_TESTING
STATEFUL_API_TESTING
SCHEMA_COVERAGE
```

Xninetzy default:

```text
safe endpoints first
bounded examples
bounded runtime
scope-checked requests
sanitized output
```

---

# 25. testssl.sh

The local install was defined in Section 11.

Recommended runtime:

```bash
./tools/testssl.sh/testssl.sh \
  --jsonfile security-output/tls/report.json \
  https://authorized.example
```

Record:

```text
testssl_version
openssl_version
target
timestamp
```

---

# 26. MobSF

MobSF is best run in Docker. Its documentation provides a prebuilt Docker image and static-analysis workflow.

Pull:

```bash
docker pull opensecurity/mobile-security-framework-mobsf:latest
```

Run:

```bash
docker run --rm \
  -p 8000:8000 \
  opensecurity/mobile-security-framework-mobsf:latest
```

For persistent artifacts:

```bash
mkdir -p security-output/mobsf
```

Then use the mounted application-data directory according to the MobSF deployment requirements.

Dynamic analysis requires an explicitly controlled Android/iOS analysis environment and is not part of the default passive installation profile. MobSF's current documentation describes additional emulator/device requirements for dynamic testing.

---

# 27. Global PATH Layout

Recommended native binary layout:

```text
$HOME/go/bin/
$HOME/.local/bin/
/usr/local/bin/
```

Verify:

```bash
command -v nmap
command -v amass
command -v subfinder
command -v httpx
command -v naabu
command -v katana
command -v nuclei
command -v ffuf
command -v semgrep
command -v gitleaks
command -v trivy
command -v osv-scanner
command -v syft
command -v grype
command -v checkov
command -v kube-linter
command -v kube-bench
command -v dockle
command -v prowler
command -v schemathesis
```

A missing command must result in:

```text
TOOL_MISSING
```

not:

```text
scan succeeded
```

---

# 28. Xninetzy Tool Manifest

Create:

```text
security-tools.lock
```

Example:

```yaml
schema_version: "1"

generated_at: ""

platform:
  os: ""
  arch: ""
  kernel: ""
  container_runtime: ""

tools:

  nmap:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  amass:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  subfinder:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  httpx:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  naabu:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  katana:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  zap:
    enabled: true
    image: ""
    digest: ""
    execution: docker

  nuclei:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    template_version: ""
    template_commit: ""
    template_sha256: ""
    execution: native

  ffuf:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  testssl:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  semgrep:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: venv

  gitleaks:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  trivy:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  osv_scanner:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  dep_scan:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: venv

  syft:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  grype:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    database_version: ""
    database_timestamp: ""
    execution: native

  checkov:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: venv

  kube_bench:
    enabled: true
    image: ""
    digest: ""
    execution: docker

  kube_linter:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  dockle:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: native

  prowler:
    enabled: true
    path: ""
    version: ""
    sha256: ""
    execution: venv

  schemathesis:
    enabled: true
    version: ""
    sha256: ""
    execution: uv

  mobsf:
    enabled: true
    image: ""
    digest: ""
    execution: docker
```

---

# 29. Version Policy

Do not hardcode old versions such as:

```text
nuclei v3.x
trivy 0.50+
semgrep 1.85+
gitleaks 8.18+
```

as permanent Xninetzy requirements.

Instead:

```text
minimum_version
tested_version
latest_verified_version
```

must be tracked independently.

Example:

```yaml
nuclei:
  minimum_version: ""
  tested_version: ""
  installed_version: ""
```

This avoids silently becoming incompatible as security tools evolve.

---

# 30. Reproducible Installation

For CI and release assessment:

```text
DO NOT USE:
  @latest
  :latest
  mutable git branches
  floating Docker tags

PREFER:
  exact version
  exact release
  exact commit
  exact image digest
  exact template commit
  exact vulnerability database version
```

Example:

```yaml
image:
  repository: ghcr.io/schemathesis/schemathesis
  tag: "X.Y.Z"
  digest: "sha256:..."

templates:
  nuclei:
    commit: "..."
    sha256: "..."
```

Schemathesis specifically documents exact release Docker tags as immutable, while `latest` tracks unreleased changes; Xninetzy should therefore pin exact releases in CI.

---

# 31. Integrity Verification

Security tools are themselves supply-chain dependencies.

For each critical binary:

```text
download
↓
verify checksum/signature where available
↓
install
↓
record version
↓
record hash
↓
health check
```

Record:

```text
sha256
release_version
source_url
download_timestamp
verification_method
```

Where upstream provides provenance/signature verification, use it.

OSV-Scanner releases provide SLSA provenance metadata, and Syft supports optional signature verification through Cosign.

---

# 32. Health Check

`security_check_tools` should run lightweight checks only.

Example:

```bash
nmap --version
amass -version
subfinder -version
httpx -version
naabu -version
katana -version
nuclei -version
ffuf -V
semgrep --version
gitleaks version
trivy --version
osv-scanner --version
syft version
grype version
checkov --version
kube-linter version
kube-bench version
dockle --version
prowler -v
uvx schemathesis --version
```

For Docker tools:

```bash
docker image inspect zaproxy/zap-stable
docker image inspect opensecurity/mobile-security-framework-mobsf
docker image inspect aquasec/kube-bench
```

Return:

```yaml
tool: nuclei
installed: true
version: ""
healthy: true
execution: native
capabilities:
  - vulnerability_detection
```

---

# 33. Security Runner Directory

Create:

```text
security-runtime/
```

Recommended:

```text
security-runtime/
├── bin/
├── config/
├── profiles/
├── templates/
├── cache/
├── output/
├── reports/
├── evidence/
├── logs/
└── locks/
```

Do not store secrets under this directory.

---

# 34. Output Directory Layout

Recommended:

```text
security-output/
├── session/
│   └── <session-id>/
│
├── discovery/
│   ├── amass/
│   ├── subfinder/
│   ├── httpx/
│   ├── naabu/
│   └── nmap/
│
├── web/
│   ├── katana/
│   ├── nuclei/
│   ├── zap/
│   ├── ffuf/
│   └── testssl/
│
├── code/
│   ├── semgrep/
│   ├── gitleaks/
│   ├── trivy/
│   ├── osv/
│   └── depscan/
│
├── containers/
│   ├── syft/
│   ├── grype/
│   ├── trivy/
│   └── dockle/
│
├── iac/
│   ├── checkov/
│   └── trivy/
│
├── kubernetes/
│   ├── kube-bench/
│   ├── kube-linter/
│   └── trivy/
│
├── cloud/
│   └── prowler/
│
├── api/
│   └── schemathesis/
│
├── mobile/
│   └── mobsf/
│
├── correlation/
│
├── evidence/
│
├── reports/
│
└── regression/
```

---

# 35. Sensitive Output Policy

Never preserve:

```text
passwords
API keys
tokens
cookies
private keys
cloud credentials
session identifiers
authorization headers
OTP codes
MFA secrets
```

Sanitize before writing:

```text
stdout
stderr
JSON
SARIF
HTML
Markdown
audit events
```

For example:

```text
Authorization: Bearer eyJ...
```

becomes:

```text
Authorization: Bearer [REDACTED]
```

Gitleaks findings should contain:

```text
rule
file
line
fingerprint
redacted evidence
```

not the actual secret.

---

# 36. Cache Strategy

Recommended caches:

```text
Nuclei templates
Trivy vulnerability DB
Grype vulnerability DB
Prowler package metadata
Python wheels
Go module cache
Docker layers
```

Cache metadata must include:

```yaml
cache:
  version: ""
  created_at: ""
  expires_at: ""
  source: ""
  integrity_hash: ""
```

Never treat stale vulnerability databases as current.

---

# 37. Update Procedure

Tool updates are security-sensitive.

Procedure:

```text
1. Discover new release.
2. Read changelog.
3. Run local compatibility tests.
4. Run smoke scan.
5. Compare CLI arguments.
6. Compare output schema.
7. Update security-tools.lock.
8. Update integration tests.
9. Promote only after verification.
```

Do not automatically upgrade scanner versions in production assessment environments.

---

# 38. Docker Security Baseline

All Xninetzy scanner containers should prefer:

```text
--rm
read-only filesystem
non-root user
limited CPU
limited memory
limited PIDs
minimal capabilities
restricted network
explicit volume mounts
```

Example:

```bash
docker run --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  -v "$PWD:/src:ro" \
  scanner-image
```

Additional capabilities may be granted only to scanners that technically require them.

Never mount:

```text
/
$HOME
~/.ssh
~/.aws
~/.config
/var/run/docker.sock
browser profiles
```

by default.

---

# 39. Docker Socket Exception

Some local image scanners may need access to a container engine.

If a scanner requires:

```text
/var/run/docker.sock
```

then:

```text
1. create a dedicated runner
2. restrict scanner image source
3. pin image digest
4. never expose runner externally
5. execute only approved scanner arguments
6. destroy the runner after assessment
```

The Docker socket should be considered privileged infrastructure access.

---

# 40. Python Environment Policy

Use isolated environments.

Recommended:

```text
~/.venvs/xninetzy-security
~/.venvs/xninetzy-checkov
~/.venvs/xninetzy-prowler
```

or:

```text
uv tool
```

Avoid:

```bash
sudo pip install ...
```

for security tooling.

Use:

```bash
python3 -m venv ...
python -m pip install ...
```

or:

```bash
uv tool install ...
```

Schemathesis explicitly supports `uvx` for isolated execution.

---

# 41. CI Installation Profile

CI should install only required capabilities.

Example:

```text
PR:
  semgrep
  gitleaks
  trivy
  osv-scanner

build:
  syft
  grype
  dockle

deploy:
  zap
  nuclei

infrastructure:
  checkov
  kube-linter

cluster:
  kube-bench

cloud:
  prowler
```

Do not install the complete attack-surface stack into every CI runner unnecessarily.

---

# 42. Developer Workstation Profile

Recommended workstation:

```text
nmap
amass
subfinder
httpx
naabu
katana
nuclei
ffuf
testssl.sh
semgrep
gitleaks
trivy
osv-scanner
syft
grype
checkov
kube-linter
dockle
```

Optional:

```text
ZAP
Schemathesis
Prowler
MobSF
kube-bench
```

---

# 43. Security Assessment Runner Profile

Dedicated assessment worker:

```text
Nmap
Amass
Subfinder
httpx
Naabu
Katana
Nuclei
ZAP
ffuf
testssl.sh
Schemathesis
```

Repository worker:

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

Infrastructure worker:

```text
kube-bench
Prowler
Trivy
```

Mobile worker:

```text
MobSF
mobsfscan
Semgrep
Gitleaks
```

---

# 44. Full Installation Verification

Run:

```bash
echo "=== Network ==="
nmap --version
amass -version
subfinder -version
httpx -version
naabu -version
katana -version

echo "=== Web ==="
nuclei -version
ffuf -V
./tools/testssl.sh/testssl.sh --version

echo "=== Code ==="
semgrep --version
gitleaks version
trivy --version
osv-scanner --version
depscan --help

echo "=== SBOM ==="
syft version
grype version

echo "=== IaC/Kubernetes ==="
checkov --version
kube-linter version
kube-bench version
dockle --version

echo "=== Cloud/API ==="
prowler -v
uvx schemathesis --version

echo "=== Docker ==="
docker --version
docker compose version
```

Then:

```bash
command -v nmap
command -v amass
command -v subfinder
command -v httpx
command -v naabu
command -v katana
command -v nuclei
command -v ffuf
command -v semgrep
command -v gitleaks
command -v trivy
command -v osv-scanner
command -v syft
command -v grype
command -v checkov
command -v kube-linter
command -v kube-bench
command -v dockle
command -v prowler
```

---

# 45. Xninetzy Capability Status

`security_check_tools` should normalize everything into:

```text
READY
DEGRADED
MISSING
UNHEALTHY
UNSUPPORTED
```

Example:

```yaml
capabilities:
  network_recon:
    status: READY
    tools:
      - nmap
      - amass
      - subfinder
      - httpx
      - naabu

  web_assessment:
    status: READY
    tools:
      - katana
      - nuclei
      - zap
      - ffuf
      - testssl

  code_assessment:
    status: READY
    tools:
      - semgrep
      - gitleaks
      - trivy
      - osv-scanner

  supply_chain:
    status: READY
    tools:
      - syft
      - grype
      - dep-scan

  infrastructure:
    status: PARTIAL
    tools:
      - checkov
      - kube-linter

  cloud:
    status: MISSING
    tools:
      - prowler
```

---

# 46. Recommended Xninetzy Minimum

For a serious web security assessment, minimum recommended capability is:

```text
Nmap
Amass
Subfinder
httpx
Naabu
Katana
Nuclei
OWASP ZAP
ffuf
testssl.sh
```

For repository security:

```text
Semgrep
Gitleaks
Trivy
OSV-Scanner
Syft
Grype
```

For cloud-native:

```text
Checkov
KubeLinter
kube-bench
Dockle
Prowler
```

For API:

```text
Schemathesis
ZAP API
```

For mobile:

```text
MobSF
```

---

# 47. Installation Completion Contract

Installation is considered complete only when:

```text
[ ] base environment available
[ ] Docker available
[ ] Go available
[ ] Python environment available
[ ] PATH configured
[ ] core binaries installed
[ ] optional binaries classified
[ ] Docker images available
[ ] versions detected
[ ] hashes recorded where appropriate
[ ] template provenance recorded
[ ] vulnerability DB freshness recorded
[ ] health checks passed
[ ] output directories created
[ ] cache directories configured
[ ] security-tools.lock generated
[ ] missing capabilities explicitly reported
[ ] no credentials embedded in configuration
```

---

# 48. Final Installation Principle

The installation layer should make Xninetzy capable of operating as:

```text
attack-surface mapper
+
network enumerator
+
web/API assessor
+
SAST engine
+
secret scanner
+
dependency analyzer
+
SBOM engine
+
container security engine
+
IaC analyzer
+
Kubernetes security engine
+
cloud security posture engine
+
TLS analyzer
+
mobile security engine
+
MCP security assessment runner
```

The installation layer must remain:

```text
reproducible
version-aware
integrity-aware
isolated
auditable
least-privilege
```

A scanner being installed does not authorize its use.

Authorization, scope, execution policy, and target safety remain controlled by:

```text
xninetzy-security-testing/SKILL.md
```

while operational sequencing remains controlled by:

```text
xninetzy-security-testing/references/workflow.md
```
