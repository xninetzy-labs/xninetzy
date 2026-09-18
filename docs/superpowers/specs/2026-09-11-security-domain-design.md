# Security Domain Design — xninetzy.domains.security

**Status:** Implemented (v1.0)
**Added:** 2026-09-11
**Owner:** misbahul45
**Scope:** `xninetzy/domains/security/`, `xninetzy/tools/internal/security.py`, `tests/domains/security/`, `.agents/skills/xninetzy-security-testing/`

## 1. Motivation

Xninetzy already shipped a v2.2 MCP-only pivot that consolidated knowledge, learning, life-OS, and academic sub-systems into one `xninetzy` MCP package. The owner runs personal servers (`misbah.dev`, lab VMs, staging environments) and asked for a thin, audit-friendly wrapper around widely-used open-source security scanners — without changing the project's stance on responsible disclosure.

Three constraints framed the design:

1. **Authorization is per chat command, not file-based** — the owner explicitly chose this so authorization state never persists to disk. The same target must be re-declared in each new session.
2. **No auto-exploit, no auth bypass** — the wrappers detect, they never exploit. No `sqlmap --os-shell`, no Metasploit module, no `nmap -sS` raw SYN scans.
3. **Universal protection list cannot be overridden** — `*.gov`, `*.mil`, `*.ac.id`, `kemenkes`, `kemkes`, etc. are blocked by hard-coded suffix matching. There is no escape hatch over chat.

## 2. Architecture

Domain follows the canonical Xninetzy layering (AGENTS.md §2.3):

```text
interfaces/
  ↑ (registered via xninetzy.tools.internal.security + xninetzy.interfaces.mcp_tool_adapter)
tools/internal/security.py          ← MCP wrappers (@tool-decorated)
  ↓
domains/security/
  ├── __init__.py                  ← re-exports + SECURITY_TOOL_NAMES
  ├── tools.py                     ← entry point (mirror it_learning/tools.py)
  ├── scope.py                     ← AuthorizeScan + BlockedHostSuffixes
  ├── audit.py                     ← in-memory audit log (max 500 FIFO)
  ├── reporter.py                  ← Markdown formatter
  └── runners/
      ├── base.py                  ← run_subprocess (timeout + bounds)
      ├── zap.py                   ← OWASP ZAP baseline/full/api
      ├── nuclei.py                ← ProjectDiscovery Nuclei
      ├── trivy.py                 ← Trivy FS/Image/IaC
      └── sast.py                  ← Semgrep + Gitleaks bundle
  ↓
os (no dependency)
db (no dependency)
schemas (no dependency)
core (no dependency)
ecosystem (no dependency)
```

Domain modules never import `httpx`, `fastapi`, or MCP primitives (AGENTS.md §2.3). Domain speaks to the OS only via subprocess and pure functions.

## 3. Authorization model

Three scan types enforced by `scope.py`:

| `scan_type` | Attestation required | Typical use |
|---|---|---|
| `passive` | No | fingerprinting, header info, dependency scan, SAST |
| `active` | Only if target is private (RFC1918 / loopback / link-local) | OWASP ZAP baseline, Nuclei exposures |
| `full_pentest` | Always, on any host | orchestrated recon → enumerate → report |

Attestation regex (`ATTESTATION_PATTERN`):

```regex
^(i am the owner of|i own|i am authorized to test|saya adalah pemilik|saya memiliki izin)
```

Owner types a sentence; the regex anchors to one of the recognized declarative phrases in English or Bahasa Indonesia.

`authorize_scan(target, scan_type, attestation, session_id, scope)` returns a `ScanAuthorization` dataclass; raises `ValueError` on malformed input, `PermissionError` on universal protection list or missing attestation.

## 4. Audit log

`xninetzy.domains.security.audit.SecurityAudit` is a thread-safe FIFO deque capped at 500 entries (default; `MAX_AUDIT_ENTRIES`). Every authorization, every scan, and every nested SastBundle component lands as an `AuditEntry` with:

```python
entry_id: str             UUID
scanner: str              "authorization" | "owasp_zap" | "nuclei" | "trivy" | "semgrep" | "gitleaks"
target: str               original target string
scan_type: str            "passive" | "active" | "full_pentest" | "local_fs" | "local_sast" | ...
status: str               ScanStatus enum value
started_at: str           ISO 8601
finished_at: str          ISO 8601
session_id: str           UUID prefix
authorization: dict       full ScanAuthorization dict
summary: str              human-readable summary
artifacts: list[str]      output file paths
findings_count: int       count (0 for passive inventory)
```

`export_jsonl(file_path)` writes the snapshot to JSONL on demand; no automatic flush to disk.

## 5. Tool wrapper contract

Each runner in `xninetzy/domains/security/runners/` exposes:

* `build_<scanner>_command(...)` — pure function, no side effects
* `run_<scanner>_scan(...)` — calls `run_subprocess` from `base.py`
* `describe_<scanner>()` — metadata for `security_check_tools` and the skill

`run_subprocess(scanner, command, timeout_seconds, cwd, extra_env)`:

* resolves the binary via `shutil.which`
* returns `ScanStatus.TOOL_MISSING` if not on PATH (no exception; actionable error)
* bounds timeout between 10s and 7200s
* truncates stdout/stderr to 8000 chars each
* never raises; caller gets a structured `BaseScanResult` dataclass

## 6. MCP surface

Nine tools, all prefixed `security_`, registered in `xninetzy/tools/registry.py`:

```python
from xninetzy.tools.internal.security import (
    security_check_tools,
    security_declare_target,
    security_run_zap,
    security_run_nuclei,
    security_run_trivy,
    security_run_sast,
    security_run_pentest,
    security_list_scans,
    security_generate_report,
)
```

A new `security` group is exposed in `get_tool_groups()` so the architecture test in `tests/architecture/test_tools_grouping.py` continues to pass.

## 7. Failure modes & refusal semantics

| Failure class | Action |
|---|---|
| Target in universal protection list | `PermissionError`, refuses outright |
| Target on private/loopback/link-local without attestation | `PermissionError`, refuses |
| Empty or whitespace attestation when required | `PermissionError`, refuses |
| Subprocess binary missing on PATH | `ScanStatus.TOOL_MISSING`, no partial execution |
| Subprocess timeout exceeded | `ScanStatus.TIMEOUT`, structured result, no exception |
| Return code 0 | `ScanStatus.SUCCESS` |
| Return code 1 or 2 | `ScanStatus.PARTIAL` |
| Return code anything else | `ScanStatus.FAILED` |

Every refusal produces a structured error message that the orchestrator can present verbatim to the owner; no opaque Python tracebacks reach chat.

## 8. Tests

`tests/domains/security/test_security_domain.py` mirrors `tests/domains/it_learning/test_it_learning_domain.py`:

* `test_scope_blocks_universal_protection_list` — `gov`, `ac.id`, `mil`, `kemenkes`
* `test_scope_blocks_private_without_attestation`
* `test_scope_accepts_attested_private_target`
* `test_scope_accepts_passive_public_target`
* `test_audit_records_and_retrieves`
* `test_audit_respects_max_entries`
* `test_zap_modes_validate`
* `test_nuclei_template_groups_validate`
* `test_trivy_scan_types_validate`
* `test_semgrep_configs_validate`
* `test_security_tools_entrypoint_lists_all_nine_tools`
* `test_security_tool_names_match_entrypoint`

## 9. Why thin wrappers, not an SDK

Three reasons:

1. **Provenance.** Scanners are upstream Go / Java / Python projects with versioned security practices. Wrapping the binary keeps the project's security model identical to the scanner's official stance.
2. **Coverage.** Local install or Docker. No new transitive dependencies on third-party Python SDKs (`python-owasp-zap`, `pynuclei`, etc.), each of which drifts faster than the binaries.
3. **Failure surface.** When something goes wrong in a scanner, the upstream binary's exit code is the contract. Subprocess call is the simplest possible interface — easier to reason about, easier to audit.

The tradeoff is higher dependency on the operator having the binaries installed. `security_check_tools` makes that dependency observable.

## 10. Roadmap (v1.1+)

* Docker-mode runners (each scanner wrapped in a one-shot container) so the host doesn't need pre-installed binaries.
* Optional persistent audit log gated by an explicit owner-controlled file path.
* HTML report aggregation across multiple scans (`security_generate_html_report`).
* Slack / Discord / WhatsApp webhook for `security_run_pentest` completion notifications.
* Integration with `xninetzy.os.web_analysis.security` so findings get cross-referenced with the existing GET-only endpoint catalog.
