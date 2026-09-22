---
layout: ../../layouts/DocsLayout.astro
title: Authentication
description: User-owned OAuth + browser auth, scope of authority, and credential storage.
section: Operations
---

Xninetzy authenticates **on behalf of the user** for upstream services
the user owns accounts on (Kaggle, Google, GitHub, etc.). The LLM
host and the MCP server never hold raw passwords; credentials live
only in an owner-scoped, Fernet-encrypted SQLite store on disk.

The MCP server stays a **single server**. Playwright is not introduced
as a sibling MCP server; it is one of three browser backends inside
an internal BrowserGateway adapter. See
[Browser gateway](/docs/browser-gateway/).

## Authoritative constraints

The following hard rules bind every auth flow. They are not policy —
they are enforced in code.

- DO NOT scrape passwords.
- DO NOT ask the LLM to receive passwords.
- DO NOT store passwords in tool arguments.
- DO NOT expose cookies in normal tool output.
- DO NOT expose OAuth access tokens in normal tool output.
- DO NOT expose refresh tokens.
- DO NOT put credentials into logs.
- DO NOT put cookies into traces.
- DO NOT dump localStorage blindly into model context.
- DO NOT automatically bypass CAPTCHA.
- DO NOT bypass MFA.
- DO NOT defeat access controls.
- DO NOT treat browser state as equivalent to application authorization
  without verification.
- DO NOT use persistent browser state across unrelated user identities.
- The user must remain the principal controlling authentication.
- The browser may assist the user.
- The LLM must never become the holder of the user's raw credentials
  unnecessarily.

## Identity layers

Xninetzy distinguishes four layers; the public MCP surface talks
about them explicitly so the host model cannot conflate them.

| Layer | What it represents | Who holds it |
|---|---|---|
| `UserIdentity` | The local MCP operator (owner principal) | MCP server, signed by `XNINETZY_AUTH_MASTER_KEY` |
| `ExternalIdentity` | An identity at an upstream provider (Google account, GitHub account) | Upstream, mirrored as public claims inside Xninetzy |
| `OAuthConnection` | A scoped OAuth token pair (access + refresh + expiry) bound to one external identity | Fernet-encrypted SQLite on disk |
| `BrowserSession` | An optional, isolated browser storage-state bound to one external identity and one account nickname | Local profile dir, owner-scoped, never reused across identities |

Each OAuth or browser login produces a unique
`session_id` (`auth-<provider>-<24hex>`) and an opaque
`credential_ref` (`cred-<provider>-<24hex>`). Tools exchange the
ref; raw values stay inside the trusted adapter that needs them.

## Modes of authentication

The same provider may be entered via three modes. Tools that need a
connection request it via `auth_connections_list` and pick the
preferred one in this order:

1. **OAuth (Authorization Code + PKCE, S256)** — recommended
   wherever the provider publishes an authorization endpoint.
   Built-in providers: `google`, `github`, `kaggle`.
2. **Browser (Playwright / CDP / remote)** — interactive login in a
   user-controlled browser. Needed when an upstream uses CAPTCHA,
   MFA, or a custom login flow with no public OAuth.
3. **Existing browser session** — connect to a CDP endpoint or
   remote Playwright worker the user already owns. Useful for
   repeated runs in the same user account.

Tools that need an authenticated identity never ask for
`username` + `password`. When no credential is available, they
return a structured error of shape:

```json
{
  "error_code": "<PROVIDER>_AUTH_REQUIRED",
  "message": "Use auth_session_create with provider='<provider>' to start an OAuth or browser login flow, then retry. Never send username or password via tool arguments.",
  "next_steps": ["auth_capabilities", "auth_providers_list", "auth_session_create(...)", "auth_session_status(...)"],
  "retryable": false
}
```

The host treats the absence of a session as a state to be fixed by a
call to `auth_session_create`, never as an implicit prompt to guess
credentials.

## Persistence

| Object | Table / location | Encryption |
|---|---|---|
| Secret values | `auth_secret_store.ciphertext` (BLOB) | Fernet (AES-128 HMAC SHA-256) under `XNINETZY_AUTH_MASTER_KEY` (env) or `~/.local/share/xninetzy/auth-master.key` (chmod 600) |
| Session metadata | `auth_session` row | Plain (no secrets stored here; `credential_ref` is a pointer) |
| Browser storage-state | `~/.local/share/xninetzy/auth/profiles/<owner>/<ref>/` | Per-owner-mode 0700 directory; raw value still encrypted on disk via Fernet when stored in SecretStore |

`SecretStore` only exposes opaque refs and HMAC-tagged metadata. Raw
bytes leave the store only when an internal adapter passes them to
an HTTP client.

## Tool summary

| Tool | Purpose |
|---|---|
| `auth_capabilities` | Snapshot of OAuth/browser/credential capabilities |
| `auth_providers_list` | List of provider adapters (Google, GitHub, Kaggle) |
| `auth_session_create` | Begin a new session; returns authorization URL or browser handoff |
| `auth_session_status` | Inspect state machine (CREATED → … → AUTHENTICATED) |
| `auth_session_cancel` | Cancel a WAITING_FOR_USER session |
| `auth_session_revoke` | Revoke an AUTHENTICATED session, delete secret bytes |
| `auth_connections_list` | List active connections for the owner (no secrets) |
| `auth_identity_get` | Public identity claims (sanitized via redaction) |
| `oauth_provider_list` / `oauth_provider_get` | OAuth metadata, scopes, allowed origins |
| `browser_capabilities` | Browser backend probe (LOCAL/CDP/REMOTE/NONE) |
| `browser_session_status` | Per-owner browser profile state (no cookies) |

## State machine

```
CREATED
  │ (started by auth_session_create)
  ▼
WAITING_FOR_USER ───────► CANCELLED
  │ (user authorizes)
  ▼
AUTHORIZING
  │
CALLBACK_RECEIVED
  │
EXCHANGING
  │
VERIFYING
  │
AUTHENTICATED ───► EXPIRED
  │           ──────► REVOKED
  │           ──────► FAILED
  ▼
(AUTHENTICATED is the only state from which tools may use the connection)
```

The set of valid transitions is enforced in
`xninetzy/os/auth/sessions/state.py::is_valid_transition`. The host
cannot bypass the machine by editing metadata; storage constraints
back it up.

## Multi-account support

A single provider may host multiple accounts under nicknames
(`kaggle:personal`, `kaggle:work`, `google:work-1`). Every session
and credential_ref includes the nickname. Tools that take an
`account` parameter (`kaggle_*`) call
`resolve_kaggle_auth(owner=..., account=...)` and pick the matching
session.

Two accounts of the same provider never share browser profile dirs,
nor cookies, nor token bytes.

## Configuration

| Env | Default | Meaning |
|---|---|---|
| `XNINETZY_AUTH_ENABLED` | `true` | Master enable; `false` disables all auth tools |
| `XNINETZY_AUTH_MASTER_KEY` | (unset → bootstrap file) | Fernet master key seed |
| `XNINETZY_AUTH_SESSION_TTL_SECONDS` | `900` | Maximum time from CREATED to AUTHENTICATED |
| `XNINETZY_AUTH_IDLE_TIMEOUT_SECONDS` | `1800` | Refresh / expire idle sessions after this long |
| `XNINETZY_AUTH_REQUIRE_CONFIRMATION` | `true` | Owner must confirm `auth_session_create` calls |
| `XNINETZY_OAUTH_REDIRECT_URI` | `http://127.0.0.1:8765/auth/callback` | Loopback callback |
| `XNINETZY_GOOGLE_CLIENT_ID/SECRET` | unset | OAuth app credentials for Google |
| `XNINETZY_GITHUB_CLIENT_ID/SECRET` | unset | OAuth app credentials for GitHub |
| `XNINETZY_KAGGLE_CLIENT_ID/SECRET` | unset | OAuth app credentials for Kaggle |

## Threat boundaries

- Replay: the OAuth state token is `secrets.token_urlsafe(32)` with a
  UNIQUE column constraint. A forged state never enters the DB.
- Mix-up: PKCE S256 verifies the verifier before exchange.
- CSRF: state token bound to the local session_id.
- Cookie theft: browser storage-state lives in
  `~/.local/share/xninetzy/auth/profiles/<owner>/<ref>/` at 0700 and
  is never serialized into tool output.
- Token log leakage: all stdout/stderr paths funnel through
  `redact_text` which strips `Bearer …`, `access_token=…`,
  `client_secret`, `Set-Cookie`, `Authorization:`.
- Path traversal: browser profiles are confined to the owner-scoped
  base dir; CDP / remote endpoints come from allowlisted env vars.

## What this is NOT

- Not an IdP. The user remains the principal; Xninetzy just holds
  encrypted pointers.
- Not a sibling MCP server. Playwright is internal to the auth domain.
- Not a headless password wallet. Tools never see passwords.
- Not an autoclicker for CAPTCHA / MFA. The user does those steps.
