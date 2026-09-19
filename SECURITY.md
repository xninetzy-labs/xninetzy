# Xninetzy Security Model

Xninetzy's security model is aligned to NSA Cybersecurity Sheet
**U/OO/6030316-26** — *Model Context Protocol (MCP): Security Design
Considerations for AI-Driven Automation* (20 May 2026) — and to the
2026-07-28 MCP specification's authorization hardening guidance.

## Threat model scope

External content (web pages, PDFs, repos, issues, job postings, external
MCP tool descriptions/outputs, HEBAT course material) is **untrusted**.
Instructions embedded in that content must never be treated as
authorization to call a tool, change a permission, or skip an approval
step. This is the "context poisoning" risk category named explicitly in
the NSA CSI.

## Risk categories and how Xninetzy addresses them

| NSA CSI risk category | Xninetzy control |
|---|---|
| Access-control gaps | Per-tool `RiskClass` (READ/DRAFT/WRITE/FINAL) in `xninetzy/os/policy/action_policy.py`. HIGH_RISK_WRITE / FINAL tools require HITL approval server-side. |
| Insecure serialization | Tool input/output validated against declared schemas; no `pickle`/`eval` on external data; `yaml.safe_load` / `yaml.safe_dump` everywhere. |
| Poor approval workflows | HITL approval layer `xninetzy/os/hitl/approval_service.py`. Owner check via `xninetzy/os/research/permissions.py::is_owner_admin`. |
| Token/session security | stdio = OS process boundary is the trust boundary. Streamable HTTP defaults to loopback; non-loopback requires explicit opt-in with warning. |
| Misconfiguration from rapid deployment | `xninetzy release-check` verifies defaults at runtime; transport defaults to stdio; HTTP host defaults to 127.0.0.1. |
| Inconsistent behavior between components | Single source of truth: `xninetzy/tools/registry.py` + `xninetzy/tools/manifest.py`. Every tool has a manifest; manifests drive authorization. |
| Weak observability | `xninetzy/observability/trace.py` provides request_id + W3C traceparent/tracestate propagation through MCP `_meta` per SEP-414. |
| Uncontrolled automated actions | `xninetzy/cli/orchestrator.py::_effective_tier` rejects owner-supplied tier downgrade — FINAL tools always require HITL regardless of declared tier. |
| Lack of input screening | `xninetzy/os/security/guards.py::safe_fetch` rejects non-http(s) schemes, blocks private/loopback hosts, enforces response size cap. `redact_secrets` strips known secret patterns from any logged text. |

## MCP server-side guarantees

- **stdio** (primary transport): no network auth needed. Trust boundary =
  OS process boundary. Tool-level authorization still enforced inside the
  process.
- **Streamable HTTP** bound to loopback (127.0.0.1 / ::1): local API key is
  reasonable but not strictly required for single-user local use.
- **Streamable HTTP** bound beyond loopback (self-hosted mode): treat as a
  real deployment. OAuth 2.1-aligned bearer tokens, Resource Indicators
  (RFC 8707), and Client ID Metadata Documents (CIMD) are the path
  forward — never roll a custom auth scheme.

## External MCP servers

External MCP servers are **untrusted by default** (NSA "external
components" risk class). Registry entries in
`xninetzy/interfaces/external_mcp.py` require:

- `risk_level` ∈ `unreviewed` / `low` / `medium` / `high`
- explicit `allowed_tools` allowlist (empty = no calls permitted)
- `last_reviewed_at` timestamp on add
- owner-scoped registration via `is_owner_admin`

`external_mcp_call` rejects any tool not in `allowed_tools` before
issuing the upstream call. Every result is tagged `untrusted_source=True`.

## Authorized-testing boundary

Security-analysis tools (`security_*` group, `repo_*` group) operate only
against:

- the local Xninetzy repository
- repositories or URLs the owner has explicitly stated authorization for

There is no "scan arbitrary internet target" mode.

## Secret handling

`xninetzy/os/security/guards.py::redact_secrets` strips these patterns
from any text passed to logs, citations, or tool output:

- OpenAI keys (`sk-…`)
- Anthropic keys (`sk-ant-…`)
- GitHub PATs (`ghp_…`, `github_pat_…`)
- Google API keys (`AIza…`)
- AWS access keys (`AKIA…`)
- PEM private-key blocks

## Logging policy

Structured JSON logs locally by default. OpenTelemetry export is opt-in.
`request_id`, `trace_id`, `span_id` propagate per W3C Trace Context.

## Memory poisoning threat model

The memory layer (`xninetzy/os/memory/`) stores long-lived user data that
is later replayed into prompts. Mitigations:

- `<memory_quarantine>` fence in `format_memories_for_prompt`
  (`xninetzy/os/memory/memory_store.py`) wraps retrieved memories in a
  block instructing the model to treat them as DATA, not INSTRUCTIONS.
- System policy overrides any conflicting memory content.
- Memory write paths are typed (`memory_type` field) and quota-bounded.

Operators: do not bypass `format_memories_for_prompt` when injecting
memories into a prompt context. Strip the fence and the system loses
prompt-injection containment.

## Secret redaction taxonomy

`xninetzy/core/security.py:redact_secrets()` strips these patterns from
any tool output before it leaves the MCP server. Redaction marker:
`[REDACTED]`. The function is the single sink; do not duplicate the
regex in callers.

| Pattern | Provider |
|---|---|
| `sk-...` (16+ chars) | OpenAI / Anthropic generic |
| `sk-ant-...` (16+ chars) | Anthropic-specific |
| `ghp_...`, `github_pat_...` (16+ chars) | GitHub PATs |
| `xox[abps]-...` (10+ chars) | Slack tokens |
| `AIza...` (16+ chars) | Google API keys |
| `AKIA...` (12+ chars) | AWS access key IDs |
| `-----BEGIN ... PRIVATE KEY-----` | PEM private keys |

Patterns live in `_SECRET_PATTERNS` (`xninetzy/core/security.py:17-26`).
Add new provider prefixes there, not at call sites.

## CAPTCHA OCR lockout

`XNINETZY_CAPTCHA_OCR_COOLDOWN_SECONDS` (default 3600) gates CAPTCHA OCR
tools after a lockout. The cooldown is the sole rate-limit policy; no
per-call captcha solver is enabled by default. Owner fallback via
`XNINETZY_CAPTCHA_WA_PREFERRED` applies. The guard at
`xninetzy/os/security/captcha/lockout.py` enforces:

- `XNINETZY_CAPTCHA_OCR_MIN_CONFIDENCE` (default 0.6)
- `XNINETZY_CAPTCHA_OCR_LOCKOUT_THRESHOLD` (default 3 failures)
- `XNINETZY_CAPTCHA_OCR_LOCKOUT_WINDOW_SECONDS` (default 600)
