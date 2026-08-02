---
layout: ../../layouts/DocsLayout.astro
title: Security and hardening
description: Secrets, network, identity, filesystem, HEBAT, WhatsApp, MCP, and coding-runtime boundaries.
section: Operations
---

Xninetzy processes personal data and can trigger external actions. The default
deployment targets one owner's machine, not a public multi-tenant service.

## Minimum checklist

- [ ] `.env` has mode `600` and is ignored by Git.
- [ ] Secrets do not appear in documentation, screenshots, or chat logs.
- [ ] `MCP_API_KEY` and `WA_MCP_API_KEY` are set and equal.
- [ ] `AI_API_KEY` is set and `AI_API_AUTH_REQUIRED=true`.
- [ ] `AGENT_DEBUG_ENDPOINTS=false`.
- [ ] Ports `8000` and `8081` are not exposed to the internet.
- [ ] `ADMIN_JID` is explicit; display name is not identity.
- [ ] `OBSIDIAN_ALLOW_DELETE=false`.
- [ ] `HEBAT_ALLOW_AUTO_SUBMIT=false` and confirmation is enabled.
- [ ] The owner manually answers every CAPTCHA or OTP.
- [ ] Approvals and verification go only to the WhatsApp `ADMIN_JID`.
- [x] Grade tokens are accepted only through an owner challenge.
- [ ] Coding runtimes are administrator-only with a narrow allowed root.
- [ ] Vault and database backups have passed a restore test.
- [ ] Every exposed secret has been rotated.

## Secret management

```bash
cp .env.example .env
chmod 600 .env
cd services/ai && uv run python scripts/configure_flaz.py
```

Never add provider API keys to global MCP configuration. The MCP process reads
the same project environment.

## Network boundary

`/api/chat`, reminders, and debug routes use the `AI_API_KEY` bearer token.
With `AI_API_AUTH_REQUIRED=true`, the service fails closed when the server key
is missing. The health endpoint remains public.

Application authentication does not replace a firewall. Bind to loopback or a
private network and use VPN or a TLS reverse proxy for cross-host access. Docker
Compose publishes AI and WhatsApp ports only on `127.0.0.1`. Do not change that
binding to `0.0.0.0` without audited authentication, TLS, allowlists, and
firewall rules.

## WhatsApp identity

```dotenv
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
```

Display names can change or be forged. Group triggers should not process every
message. In `SINGLE_OWNER_MODE=true`, the chat API checks `sender_id` against
`ADMIN_JID` and `OWNER_ALLOWED_JIDS`. A valid bearer token does not make a
caller the WhatsApp owner.

Baileys may report a sender as an `@lid` JID. The engine attempts to map it to
a phone JID. Add an unmapped owner alias explicitly; the system does not infer a
new owner.

High-impact approvals use Approve and Reject buttons sent only to
`ADMIN_JID`. A text fallback with `/approve <id>` and `/reject <id>` goes
to the same target when interactive buttons are unavailable.

## Filesystem and Obsidian

- Tool paths are relative to the vault.
- Traversal and absolute paths are rejected.
- Deletion is disabled by default.
- Backup-before-write is not a complete backup strategy.
- Use [Backup and restore](/docs/backup-restore/) for SQLite and FAISS.
- Back up the vault separately.
- Align UID and GID; never solve permissions with mode `777`.

## Academic portals

A browser session is equivalent to an authenticated credential. Protect HEBAT
profiles, cookies, debug screenshots, and downloaded materials. Final assignment
submission requires owner review.

Cyber Campus reads HEBAT credentials in memory. It may fill the login form, but
never solves or bypasses CAPTCHA or OTP. The challenge image is sent to the
WhatsApp administrator with a TTL and attempt limit. Successful sessions are
stored encrypted.

Grade tokens travel through deterministic owner-only routes. They never enter
prompts, MCP persistence, snapshots, or logs and are discarded after one
attempt.

## Global MCP

Global configuration gives every project opened by that client access to
personal Xninetzy tools. Therefore:

- treat repository prompts as untrusted;
- preserve the client's approval policy;
- do not auto-approve writes without understanding scope;
- disable MCP on a shared machine;
- update paths when the repository moves.

Global availability is not global authorization for high-risk actions.

## Coding runtimes

```dotenv
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_ALLOWED_ROOT=/absolute/path/to/single-workspace
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_TIMEOUT_SECONDS=600
```

Never mount a home directory, SSH keys, cloud credentials, or the Docker socket
into the service without a specific need and threat review.

## Data that must not enter Git

- `.env` and credentials;
- SQLite, WAL, and SHM;
- personal FAISS indexes;
- browser profiles and storage state;
- Baileys sessions;
- WhatsApp media;
- course downloads and submission files;
- audit output containing sensitive prompts.

All `services/ai/data/**` content is private per installation and ignored
except its policy README. Removing a file from the latest branch does not remove
Git history. Rotate secrets and sanitize history before publication if private
data was ever pushed.

## Incident response

1. revoke or rotate the secret at its provider;
2. stop affected services;
3. remove it from the working tree and history when committed;
4. invalidate relevant WhatsApp or HEBAT sessions;
5. inspect sanitized logs and recent actions;
6. restart with a new secret;
7. document the root cause without copying the secret.
