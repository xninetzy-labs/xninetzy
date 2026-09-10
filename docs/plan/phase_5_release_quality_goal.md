# Phase 5 — Quality Gates and V1 Release Readiness

Status: planned  
Schedule: weeks 11-12

## Goal

Produce a reproducible, trustworthy Apache-2.0 open-source V1 release.

## Design decisions

- Telemetry is local-only by default.
- Runtime data, generated documents, downloads, cookies, browser sessions, and
  secrets stay out of Git.
- Quality gates validate behavior, safety boundaries, and the empty-data path.

## Scope

1. Add CI gates for AI, WhatsApp, CLI, and documentation.
2. Add Apache-2.0 license, release checklist, threat-model summary, support
   matrix, and upgrade notes.
3. Validate onboarding, backup/restore, missing network, unsupported provider,
   and external-service failure modes.
4. Document ignore rules and verify no personal runtime data is tracked.

## Acceptance gate

- Fresh native and Docker installations pass smoke checks on supported
  platforms.
- No V1-required capability depends on a GPU, personal cloud account, or paid
  API.
- Release tests and documentation match delivered behavior.
