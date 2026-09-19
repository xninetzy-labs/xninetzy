---
layout: ../../layouts/DocsLayout.astro
title: Security and hardening
description: Secrets, network, identity, filesystem, HEBAT, MCP, and coding-runtime boundaries.
section: Operations
---

Xninetzy processes personal data and can trigger external actions. The default
deployment targets one owner's machine, not a public multi-tenant service.

The security model is aligned to NSA Cybersecurity Sheet **U/OO/6030316-26**
*Model Context Protocol (MCP): Security Design Considerations for AI-Driven
Automation* (20 May 2026). See `/SECURITY.md` at repo root for the full
mapping.

## Minimum checklist

- [ ] `.env` has mode `600` and is ignored by Git.
- [ ] Secrets do not appear in documentation, screenshots, or chat logs.
- [ ] `AI_API_KEY` is set if exposing the FastAPI HTTP surface.
- [ ] `AI_API_AUTH_REQUIRED=true` so the service fails closed when the
      server key is missing.
- [ ] `AGENT_DEBUG_ENDPOINTS=false`.
- [ ] FastAPI port `8000` and Streamable HTTP port `8765` are not exposed
      to the internet; Streamable HTTP bound to `127.0.0.1` only by
      default.
- [ ] Owner identity is explicit; display name is not identity. MCP
      server injects the trusted local-owner principal at startup; tools
      that require owner scope check via
      `xninetzy/os/research/permissions.py::is_owner_admin`.
- [ ] `OBSIDIAN_ALLOW_DELETE=false`.
- [ ] `HEBAT_ALLOW_AUTO_SUBMIT=false` and confirmation is enabled.
- [ ] Every CAPTCHA / OTP is solved by the owner manually; auto-OCR is
      opt-in via `XNINETZY_CAPTCHA_OCR_ENABLED` with lockout.
- [ ] MCP-driven approvals (`hitl_approve`, `improvement_approve`) require
      the admin principal, server-side, never by tool prompt alone.
- [ ] Coding runtimes use an explicit `CODING_AGENT_ALLOWED_ROOT` and
      `CODING_AGENT_ADMIN_ONLY=true`.
- [ ] Vault and database backups have passed a restore test.
- [ ] Every exposed secret has been rotated.

## Secret management

```bash
cp .env.example .env
chmod 600 .env
```

Never add provider API keys to global MCP configuration. The MCP process
reads the same project environment.

## Network boundary

The FastAPI HTTP surface (`/health`, `/api/reminders/*`, debug routes)
uses the `AI_API_KEY` bearer token. The MCP server itself runs over
stdio (no network auth needed; trust boundary = OS process boundary) or
Streamable HTTP bound to loopback.

Streamable HTTP bound beyond loopback is opt-in via
`XNINETZY_MCP_TRANSPORT=streamable-http` and logs a warning to stderr at
startup. Before binding beyond loopback, configure OAuth 2.1-aligned bearer
tokens, Resource Indicators (RFC 8707), and Client ID Metadata Documents
(CIMD). Never roll a custom auth scheme.

Docker deployments publish the FastAPI port only on `127.0.0.1`. Do not
change that binding to `0.0.0.0` without audited authentication, TLS,
allowlists, and firewall rules.

## Identity

The MCP server injects the trusted local-owner principal at startup
(`xninetzy/interfaces/mcp_tool_adapter.py::mcp_principal()`). Tools receive
`sender_id` / `sender_name` from the host call, but those values are never
authorization evidence on their own. Tools that require owner scope
(`external_mcp_*`, `obsidian_organize_apply`, `improvement_approve`, etc.)
check via `xninetzy/os/research/permissions.py::is_owner_admin`.

FINAL-class tools always require HITL approval. The CLI orchestrator
enforces this via `_effective_tier = max(declared, manifest_tier)` so
owner-supplied tier downgrade is rejected.

## Filesystem and Obsidian

- Tool paths are relative to the vault.
- Traversal and absolute paths are rejected.
- The `.backup` directory is blocked at the safety layer
  (`xninetzy/os/notes/safety.py`).
- Deletion is disabled by default.
- Backup-before-write is not a complete backup strategy.
- Use [Backup and restore](/docs/backup-restore/) for SQLite and FAISS.
- Back up the vault separately.
- Align UID and GID; never solve permissions with mode `777`.

## Academic portals

A browser session is equivalent to an authenticated credential. Protect
HEBAT profiles, cookies, debug screenshots, and downloaded materials.
Final assignment submission requires owner review via HITL approval.

CAPTCHA / OTP handling is opt-in. The default is owner manual solve. Auto-OCR
is gated by `XNINETZY_CAPTCHA_OCR_ENABLED` and `lockout.py` enforces a
threshold + cooldown so OCR failures auto-disable without bypassing the gate.

Grade tokens travel through deterministic owner-only routes. They never
enter prompts, MCP persistence, snapshots, or logs and are discarded after
one attempt.

## Global MCP

Global configuration gives every project opened by that client access to
personal Xninetzy tools. Therefore:

- treat repository prompts as untrusted;
- preserve the client's approval policy;
- do not auto-approve writes without understanding scope;
- disable MCP on a shared machine;
- update paths when the repository moves.

Global availability is not global authorization for high-risk actions.

## External MCP servers

External MCP servers are **untrusted by default**. Registry entries in
`xninetzy/interfaces/external_mcp.py` require:

- `risk_level` ∈ `unreviewed` / `low` / `medium` / `high`
- explicit `allowed_tools` allowlist (empty = no calls permitted)
- `last_reviewed_at` timestamp on add
- owner-scoped registration via `is_owner_admin`

`external_mcp_call` rejects any tool not in `allowed_tools` before issuing
the upstream call. Every result is tagged `untrusted_source=True`.

## Coding runtimes

```dotenv
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_ALLOWED_ROOT=/absolute/path/to/single-workspace
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_TIMEOUT_SECONDS=600
```

Never mount a home directory, SSH keys, cloud credentials, or the Docker
socket into the service without a specific need and threat review.

## Data that must not enter Git

- `.env` and credentials;
- SQLite, WAL, and SHM;
- personal FAISS indexes;
- HEBAT browser profiles and storage state;
- HEBAT course downloads and submission files;
- audit output containing sensitive prompts.

All `xninetzy/data/**` content is private per installation and ignored
except its policy README. Removing a file from the latest branch does not
remove Git history. Rotate secrets and sanitize history before publication
if private data was ever pushed.

## Incident response

1. revoke or rotate the secret at its provider;
2. stop affected services;
3. remove it from the working tree and history when committed;
4. inspect sanitized logs and recent actions;
5. restart with a new secret;
6. document the root cause without copying the secret.
