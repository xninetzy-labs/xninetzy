# Phase 3 — Install, CLI, and Interface Parity

Status: in progress  
Schedule: weeks 6-8

## Goal

Make Xninetzy installable and operable consistently on Linux, macOS, and
Windows through equal Docker and native paths.

## Design decisions

- Configuration is provider-neutral and deployment-scoped. Provider/model
  preferences use allowlisted identifiers; credentials never enter prompts or
  repository files.
- The public CLI is an official interface with `setup`, `doctor`, and `chat`.
- Coding runtimes run through the authenticated host bridge, never inside the
  AI container. MCP preflight remains mandatory.
- Ordinary WhatsApp failover to a host runtime stays read-only and preserves
  the same Xninetzy MCP access contract.

## Scope

1. Build a provider-neutral native and Docker setup wizard.
2. Add CLI-managed `.env` configuration for every supported `Settings` field.
3. Provide CLI JSON output, streamed responses where available, and safe
   fallback behavior when streams are unavailable.
4. Add feature-pack activation and actionable degraded-mode diagnostics.
5. Validate Codex, Claude Code, and OpenCode host bridge setup without
   client-specific Xninetzy logic.
6. Test clean CPU-only onboarding without paid provider credentials.

## Acceptance gate

- A clean native or Docker install completes setup and `doctor` without
  personal data, GPU, or paid API requirements.

## CLI-managed configuration contract

- `xninetzy config list`, `get`, `set`, `unset`, and `validate` cover every
  public field in the canonical `Settings` schema.
- CLI metadata is derived from `Settings` and documented `.env.example` keys;
  no hand-maintained duplicate allowlist may drift from either source.
- `set` parses booleans, numbers, lists, and paths with the same Pydantic
  validation used by the application.
- Secret values use a no-echo prompt or stdin, are redacted in output, and are
  never written to logs, JSON output, prompts, or shell history examples.
- The CLI resolves and displays the target root `.env`, supports an explicit
  alternative config path, preserves unrelated entries, and writes atomically
  with owner-only file permissions where the operating system supports them.
- `config validate` reports unknown and invalid values without exposing secrets.
- Setup and Docker/native `doctor` read the same resulting environment file.
- Automated tests prove every `Settings` field is discoverable, safely writable,
  and accepted by a fresh application process.

## Host and Docker parity contract

- `setup --deployment native` writes a loopback CLI target and host MCP mode.
- `setup --deployment docker` keeps the loopback target in the root `.env`;
  Compose applies container-only `ai` and `container` overrides.
- `doctor --mcp` is opt-in, invokes the shared coding-runtime MCP preflight
  command with its minimal environment, and reports only availability.
- Routine `doctor` remains read-only and never starts Docker, a service, or a
  coding runtime.
