# Workflow examples for `xninetzy-security-testing`

Seven concrete scenarios, with the exact MCP tool sequence the orchestrator should run.

## 1. Owner wants a quick posture check on their personal site

```text
owner: scan https://misbah.dev
orchestrator:
  1. security_check_tools                       → confirm nuclei + trivy installed
  2. security_declare_target(
       target="https://misbah.dev",
       scan_type="passive"
     )                                          → session_id=sec-1a2b3c
  3. security_run_nuclei(
       target="https://misbah.dev",
       templates="technologies,exposures",
       rate_limit=10
     )                                          → nuclei passive JSON in /tmp/xninetzy-nuclei/
  4. security_list_scans(limit=10)               → audit log entry visible
  5. security_generate_report(scan_id="")        → Markdown summary
```

`scan_type="passive"` because the owner only wants fingerprinting — no auth bypass, no payload fuzzing.

## 2. Owner wants a full OWASP ZAP baseline on their staging app

```text
owner: jalankan zap baseline di staging.perusahaan-saya.id
orchestrator:
  1. security_check_tools                       → confirm zap-baseline.py installed
  2. security_declare_target(
       target="https://staging.perusahaan-saya.id",
       scan_type="passive"
     )                                          → session_id issued
  3. security_run_zap(
       target="https://staging.perusahaan-saya.id",
       mode="baseline",
       timeout_seconds=600
     )                                          → report di /tmp/xninetzy-zap/
```

OWASP ZAP **baseline** is designed for passive + light active scanning during CI/CD; it does not brute-force credentials or fuzz inputs.

## 3. Owner wants authenticated active scan on their intranet app

```text
owner: saya butuh zap full scan di http://10.0.5.23:8080
orchestrator:
  1. (refuse if on universal protection list — intranet is not)
  2. security_declare_target(
       target="http://10.0.5.23:8080",
       scan_type="active",
       attestation="I am the owner of 10.0.5.23 internal staging server"
     )                                          → session_id issued (gated)
  3. security_run_zap(
       target="http://10.0.5.23:8080",
       mode="full",
       attestation="I am the owner of 10.0.5.23 internal staging server",
       timeout_seconds=1800
     )                                          → full active scan
```

The `attestation` regex (English or Bahasa Indonesia) is the second authorization layer for any active scan against a private IP.

## 4. Owner wants SAST scan of their codebase

```text
owner: scan kerentanan di repo saya ~/code/myapp
orchestrator:
  1. security_run_sast(
       repo_path="/home/owner/code/myapp",
       semgrep_config="p/security-audit"
     )                                          → semgrep + gitleaks local-only
```

100% local — no target on a network, so no attestation needed.

## 5. Owner wants dependency vulnerability scan on their Docker image

```text
owner: scan image docker saya myorg/myapp:1.4.2
orchestrator:
  1. security_run_trivy(
       scan_path="myorg/myapp:1.4.2",
       scan_type="image",
       severity="HIGH,CRITICAL",
       output_format="sarif"
     )                                          → SARIF report di /tmp/xninetzy-trivy/
```

Trivy pulls the image locally (no network egress beyond the image registry).

## 6. Owner wants a full recon→report cycle

```text
owner: saya mau pentest lengkap di https://app.perusahaan-saya.id
orchestrator:
  1. security_check_tools                       → inventory
  2. security_declare_target(
       target="https://app.perusahaan-saya.id",
       scan_type="full_pentest",
       attestation="Saya adalah pemilik https://app.perusahaan-saya.id"
     )                                          → session_id issued
  3. security_run_pentest(
       target="https://app.perusahaan-saya.id",
       profile="standard",
       attestation="Saya adalah pemilik https://app.perusahaan-saya.id",
       timeout_seconds=900
     )                                          → 5-step orchestrated report
  4. security_generate_report()                  → Markdown summary across 5 entries
```

`profile="standard"` runs Nuclei passive + ZAP baseline + Trivy FS + Semgrep + Gitleaks. `profile="aggressive"` upgrades to vulnerabilities + zap full (needs stronger attestation).

## 7. Refusal example — third-party / protected host

```text
owner: scan fst.unair.ac.id
orchestrator:
  → refuse immediately.
  → reason: target matches BLOCKED_HOST_SUFFIXES (".ac.id")
  → offer alternative: "if you own this faculty site and have written authorization,
    run `security_declare_target` after adding the host to the local bypass — otherwise
    use a self-hosted dev mirror"
```

This refusal is **hard-coded** in `xninetzy/domains/security/scope.py` and **cannot** be overridden by the owner over chat.

## Audit log patterns

The audit log is **purely in-memory**, holds at most 500 entries FIFO, and never persists to disk by design. To export:

```bash
xc_secret = os.environ['XNINETZY_INTERNAL_TOKEN']   # noqa
# (no public export tool — fetch via debug endpoint if available)
```

Practically the log is for in-session review via `security_list_scans` and `security_generate_report` only. Long-term persistence is a future v1.1 feature gated by the owner.
