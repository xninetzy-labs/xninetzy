# Installing the five security scanners

The `xninetzy.domains.security` domain only **wraps** these tools — it does not bundle them. The owner (or operator) is responsible for installing binaries on `$PATH` before invoking any active scanner. The `security_check_tools` MCP tool inventories the current state.

## Recommended installation matrix

| Tool | Ubuntu / Debian | macOS (brew) | Arch |
|------|-----------------|--------------|------|
| OWASP ZAP (Docker preferred) | `docker pull owasp/zap2docker-stable` | `brew install --cask owasp-zap` | `yay -S zaproxy` |
| ProjectDiscovery Nuclei | `go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` | `brew install nuclei` | `yay -S nuclei` |
| Trivy | `apt-get install -y wget gnupg lsb-release && wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key \| gpg --dearmor \| sudo tee /usr/share/keyrings/trivy.gpg >/dev/null && echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" \| sudo tee /etc/apt/sources.list.d/trivy.list && sudo apt-get update && sudo apt-get install -y trivy` | `brew install trivy` | `yay -S trivy` |
| Semgrep | `pip install semgrep` | `brew install semgrep` | `yay -S semgrep` |
| Gitleaks | `go install github.com/gitleaks/gitleaks/v8@latest` | `brew install gitleaks` | `yay -S gitleaks` |

OWASP ZAP requires Java 11+. Nuclei, Gitleaks require Go 1.21+.

## Verifying installation

Run from any shell:

```bash
which zap-baseline.py nuclei trivy semgrep gitleaks
```

Expected output: a one-line path per binary. Missing tools are not blockers — `security_check_tools` returns them as `NO` and refuses to launch scans against them, returning `ScanStatus.TOOL_MISSING`.

## Recommended stable versions

| Tool | Tested version |
|------|----------------|
| zap-baseline.py | 2.16.x (bundled with ZAP weekly) |
| nuclei | v3.x |
| trivy | 0.50+ |
| semgrep | 1.85+ |
| gitleaks | 8.18+ |

Always prefer releases from each tool's official GitHub Releases page; the package managers above track stable channels.

## Docker alternative

For sandbox isolation, you can run every scanner in Docker:

```bash
docker run --rm -v "$PWD:/src" returntocorp/semgrep semgrep --config p/security-audit /src
docker run --rm -v "$PWD:/src" aquasec/trivy fs --severity HIGH,CRITICAL /src
```

`xninetzy.domains.security` currently invokes binaries directly (not via Docker); a Docker-mode is on the roadmap for v1.1.

## Output directories

By default, output artifacts land under:

```text
/tmp/xninetzy-zap/        ← HTML + Markdown reports from OWASP ZAP
/tmp/xninetzy-nuclei/     ← JSON findings from Nuclei
/tmp/xninetzy-trivy/      ← JSON / SARIF report from Trivy
/tmp/xninetzy-sast/       ← JSON from Semgrep + Gitleaks
```

These are gitignored by Xninetzy default. Move them to a persistent location before container shutdown if you need to keep them.
