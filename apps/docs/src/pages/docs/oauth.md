---
layout: ../../layouts/DocsLayout.astro
title: OAuth flows
description: Authorization Code + PKCE, provider definitions, and the loopback callback.
section: Operations
---

OAuth in Xninetzy follows **OAuth 2.1 + OIDC** standards with PKCE
S256. The default loopback callback is
`http://127.0.0.1:8765/auth/callback`. The full redirect URI is
overridable via `XNINETZY_OAUTH_REDIRECT_URI`.

## Provider definitions

`xninetzy/os/auth/oauth/providers.py` ships built-ins for:

| Provider | Authorization endpoint | Token endpoint | Default scopes |
|---|---|---|---|
| `google` | `https://accounts.google.com/o/oauth2/v2/auth` | `https://oauth2.googleapis.com/token` | `openid email profile` |
| `github` | `https://github.com/login/oauth/authorize` | `https://github.com/login/oauth/access_token` | `read:user user:email` |
| `kaggle` | `https://www.kaggle.com/oauth/authorize` | `https://www.kaggle.com/oauth/access_token` | `public private` |

Custom providers can be added with `register_provider(...)` and are
persisted to the same `auth_session` table.

## Authorization Code + PKCE S256

```
+--------+        +-----------+        +----------------+
|  host  |  ─1─▶  |  Xninetzy |  ─2─▶  |  auth provider |
| (LLM)  |        |  MCP      |        |  authorize URL  |
+--------+        +-----------+        +----------------+
                       │                       │
                       │   3. user authorizes  │
                       │ ◀─────────────────────┘
                       │   4. browser redirects to loopback :8765
                       │
                       ▼   5. exchange code + verifier
                access_token + refresh_token
                       │
                       │   6. encrypt → SecretStore
                       ▼
                credential_ref → toolchain
```

Step 1 — host calls `auth_session_create`:

```json
{
  "provider": "kaggle",
  "method": "oauth",
  "account": "default",
  "scopes": ["public", "private"]
}
```

Step 2 — Xninetzy generates a 32-byte state token (`secrets.token_urlsafe(32)`),
a PKCE verifier (RFC 7636 S256 challenge), and an authorization URL.
Response returns `authorization_url` and `session_id`.

Step 3 — host opens the URL in the user's browser (or relays it
to the user). User consents.

Step 4 — provider redirects to the loopback callback with `code`
and the original `state`.

Step 5 — Xninetzy's callback handler reads `state`, validates the
session is in `WAITING_FOR_USER`, exchanges the code for tokens
against the provider's token endpoint, and decrypts the verifier
matches the saved challenge (PKCE).

Step 6 — the encrypted access+refresh token pair lands in
`auth_secret_store` under a fresh `credential_ref`. The session
transitions to `AUTHENTICATED`.

Tools like `kaggle_dataset_search` only see the `credential_ref`.

## State token table

The `state` parameter is the **only** cross-channel binding
between the provider and Xninetzy.

```sql
CREATE TABLE auth_session (
    session_id      TEXT PRIMARY KEY,
    owner           TEXT NOT NULL,
    provider        TEXT NOT NULL,
    account         TEXT NOT NULL,
    method          TEXT NOT NULL,
    state           TEXT NOT NULL,
    state_token     TEXT NOT NULL UNIQUE,  -- the OAuth state param
    pkce_verifier   TEXT NOT NULL,
    authorization_url TEXT NOT NULL,
    redirect_uri    TEXT NOT NULL,
    scopes_json     TEXT NOT NULL,
    credential_ref  TEXT,
    ...
);
```

The UNIQUE constraint on `state_token` defeats replay: any second
callback with the same state fails to insert, and Xninetzy returns
`OAUTH_STATE_REPLAY_DETECTED`.

## CSRF / mix-up defense

- **CSRF**: the state token is bound to `session_id` and
  `owner`; the host cannot forge a callback that crosses accounts.
- **Mix-up attacks**: PKCE S256 proves the verifier matches the
  challenge issued by *this* Xninetzy instance. Token exchange is
  refused otherwise.
- **Authorization response tampering**: the redirect URI is a
  fixed loopback URL (or one in `XNINETZY_OAUTH_REDIRECT_URI`),
  validated against `xninetzy/os/auth/policies/url_policy.py::is_allowed_origin`.

## Token refresh

`refresh_token` is encrypted the same way as `access_token`. A
background scheduler refreshes tokens whose `expires_at` is within
5 minutes, provided the owner remains authenticated. The
authorization server's compliance with OIDC refresh is assumed; if
the provider revokes the refresh token, the session transitions to
`EXPIRED` and the host receives a structured error.

## Configuration

| Env | Meaning |
|---|---|
| `XNINETZY_OAUTH_REDIRECT_URI` | Loopback callback; override for production HTTP bridge |
| `XNINETZY_GOOGLE_CLIENT_ID/SECRET` | OAuth app credentials |
| `XNINETZY_GITHUB_CLIENT_ID/SECRET` | OAuth app credentials |
| `XNINETZY_KAGGLE_CLIENT_ID/SECRET` | OAuth app credentials |

Set both `*_CLIENT_ID` and `*_CLIENT_SECRET` for each provider
before invoking `auth_session_create` against that provider.

## What this is NOT

- Not a generic OAuth reverse-proxy. Xninetzy is the relying party
  for **itself**, not for an arbitrary third-party browser agent.
- Not a token vault for arbitrary apps. The encrypted store only
  holds tokens whose providers are in `oauth_provider_list`.
- Not a credential phisher. The LLM never sees the
  `code_verifier` value or the raw `access_token` — only `credential_ref`.
