---
name: xninetzy-security-testing
description: Authorized self-pentest workflow for Xninetzy MCP — wraps OWASP ZAP, ProjectDiscovery Nuclei, Trivy, Semgrep, and Gitleaks as thin subprocess tool wrappers. Use when the owner asks to scan their own domain, staging server, or local repo; surface pentest findings as audit-logged reports; or orchestrate a full recon→enumerate→vuln-scan→report cycle. Never use for third-party targets, government/education/military hosts, unauthenticated active scans on private IPs, CAPTCHA/OTP bypass, or anything outside the owner-declared scope.
metadata:
  owner: misbahul45
  scope: project
  authority:
    - AGENTS.md
    - global opencode AGENTS.md
  interfaces:
    - mcp
    - http-mcp-bridge
  language: en
  version: "1.0.0"
  added: 2026-09-11
  domain: xninetzy.domains.security
---

# Xninetzy Security Testing Skill

This skill is the **workflow layer** for the `xninetzy.domains.security` domain. The domain itself contains thin subprocess wrappers around well-known open-source scanners (OWASP ZAP, Nuclei, Trivy, Semgrep, Gitleaks); this skill teaches the orchestrator how to combine those tools safely, with explicit authorization gates and audit logging.

The core principle:

> **The owner declares the target in chat; Xninetzy refuses anything outside that declaration, refuses anything on the universal protection list, and records every scan to an in-memory audit log.**

## When to use this skill

* the owner asks to scan a domain they own (e.g. `https://app.perusahaan-saya.id`)
* the owner wants a SAST scan of a local repo (`Semgrep + Gitleaks`)
* the owner wants the full recon→enumerate→report cycle via `security_run_pentest`
* the owner needs a Markdown pentest report saved from past scans
* the owner wants to check which scanners are installed locally

## When NOT to use this skill

* third-party targets, government (`*.gov`, `*.go.id`), military (`*.mil`), education (`*.ac.id`, `*.sch.id`), hospitals (`kemenkes`, `kemkes`), or any other universally-protected host
* CAPTCHA, OTP, MFA bypass requests
* unauthenticated active scans on private IP ranges (`10/8`, `172.16/12`, `192.168/16`, `127/8`, `169.254/16`, `fc00::/7`) without explicit owner attestation
* any target where the owner has not declared ownership in the current chat session
* production cloud metadata services (`169.254.169.254`, `metadata.google.internal`)

## Authorization model

Authorization is **per chat command**, not file-based. The owner must explicitly type the target URL into each `security_*` tool invocation. Every active scan produces a `session_id` UUID that lands in the in-memory audit log.

Two scan types require explicit **attestation** (a sentence the owner types):

| Scan type | Attestation needed? |
|---|---|
| `passive` (GET-only fingerprinting, dependency scan, SAST) | No |
| `active` against public host | No |
| `active` against private/internal host | **Yes** |
| `full_pentest` (any host) | **Yes** |

Attestation is validated against the regex `^(i am the owner of | saya adalah pemilik | i own | i am authorized to test | saya memiliki izin)`.

The universal protection list (always refused, even with attestation) lives at `xninetzy/domains/security/scope.py:BLOCKED_HOST_SUFFIXES` and `BLOCKED_HOST_LITERALS`.

## Tool inventory

`xninetzy.domains.security` exposes nine MCP tools, all prefixed with `security_`:

| Tool | Purpose | Scope |
|---|---|---|
| `security_check_tools` | Inventory of installed scanners on `$PATH` | local read |
| `security_declare_target` | Issue authorization session for a target | owner gate |
| `security_run_zap` | OWASP ZAP baseline / full / api scan | network |
| `security_run_nuclei` | ProjectDiscovery Nuclei template scan | network |
| `security_run_trivy` | FS / Image / IaC vulnerability scan | local path |
| `security_run_sast` | Semgrep + Gitleaks on a local repo | local path |
| `security_run_pentest` | Orchestrated recon → scan → report | both |
| `security_list_scans` | Read in-memory audit log (last 100) | local read |
| `security_generate_report` | Markdown report from audit entry | local read |

Five of these require network access (`zap`, `nuclei`, `pentest` always, plus `trivy image`); the rest are fully local.

## Standard workflow

```text
1. security_check_tools
   ↓ confirm binaries installed on $PATH
2. security_declare_target(target=..., scan_type=..., attestation=...)
   ↓ issue session_id
3. security_run_<scanner>(target=..., ...)
   ↓ bind scans to the declared session
4. security_list_scans(limit=20)
   ↓ verify audit entries
5. security_generate_report(scan_id=...)
   ↓ produce Markdown report
```

Each scan produces one audit entry. The audit log holds at most 500 entries (FIFO rotation) and is purely in-memory; persistence is a deliberate non-feature (the owner wants no file leak of authorization state).

## Safety invariants

The skill enforces these rules in `xninetzy/domains/security/scope.py`:

1. **Universal protection list** — `*.gov`, `*.mil`, `*.ac.id`, `*.sch.id`, `kemenkes`, `kemkes`, `polri`, `tni`, etc. cannot be scanned at all.
2. **Loopback / cloud-metadata literals** are blocked (`localhost`, `127.0.0.1`, `169.254.169.254`, `metadata.google.internal`).
3. **Private networks** are recognized (`10/8`, `172.16/12`, `192.168/16`, `127/8`, `169.254/16`, `::1`, `fc00::/7`) and trigger the attestation gate for active/full scans.
4. **Tool missing ≠ failure** — when a scanner binary is absent, `run_subprocess` returns `ScanStatus.TOOL_MISSING` with an actionable install hint; no partial silent execution.
5. **Timeout bounded** — every subprocess call has a 10s–7200s timeout window.
6. **Output truncated** — stdout/stderr are truncated to 8000 chars before being attached to the audit log so a runaway scanner cannot blow up memory.
7. **No auto-exploit** — the wrappers only ever spawn scanners in detection / report mode; no `sqlmap --os-shell`, no Metasploit, no auth bypass automation.

## Interaction model

When the owner asks "scan my website":

1. **Confirm target ownership.** Ask the owner to restate the URL.
2. **Confirm scan type.** Ask `passive` vs `active` vs `full_pentest`.
3. **If active or full**, ask for an attestation sentence.
4. **Pre-check tool inventory** with `security_check_tools`.
5. **Issue authorization** with `security_declare_target`.
6. **Run the scan(s)** and stream the report back to chat.
7. **Persist audit entry**, surface the `session_id` so the owner can quote it later.

If the owner names a target in the universal protection list, **refuse immediately** and explain why — do not invent workarounds.

## Routing

* vulnerability report → `xninetzy-security-testing` (this skill)
* code review for security → `security-best-practices`
* bus factor / ownership map → `security-ownership-map`
* design-time threat model → `security-threat-model`

## Reference map

* `references/install.md` — installing the five scanner toolchains on Linux/macOS.
* `references/workflow.md` — concrete examples for each common scan scenario.
