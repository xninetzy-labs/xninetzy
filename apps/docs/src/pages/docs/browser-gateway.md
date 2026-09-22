---
layout: ../../layouts/DocsLayout.astro
title: Browser gateway
description: Internal browser backends (LOCAL/CDP/REMOTE) used by authentication flows.
section: Operations
---

The browser gateway is an **internal adapter** inside the Xninetzy
MCP server. It is intentionally not a sibling MCP server, a child
process, or a separate daemon. There is exactly one
`xninetzy` MCP server; the browser gateway is one of its internal
backends.

The browser is only invoked when authentication requires it:
OAuth code + PKCE handles most provider logins without a browser at
all. The browser exists for the cases where a provider uses CAPTCHA,
MFA, or a non-public login flow.

## Backends

`BrowserBackend` enum:

| Backend | When it is selected | Persistent storage |
|---|---|---|
| `NONE` | Probe shows no runtime available | n/a |
| `LOCAL` | Headful Chromium via Playwright (default when available) | Per-owner, per-account storage-state under `~/.local/share/xninetzy/auth/profiles/<owner>/<ref>/` (chmod 700) |
| `CDP` | `XNINETZY_BROWSER_CDP_ENDPOINT` is set | Reuses the **user's** existing Chrome / Edge / Brave instance |
| `REMOTE` | `XNINETZY_BROWSER_REMOTE_ENDPOINT` is set | Connects to a remote Playwright worker that the user controls |

Selection is done by `BrowserGateway.select_backend()`. It honors
`XNINETZY_BROWSER_BACKEND` (`auto` | `local` | `cdp` | `remote`)
when supplied; otherwise it picks the first available backend.

## Persistent state ownership

A browser storage-state may contain cookies, IndexedDB databases,
service-worker registrations, and downloaded files. The gateway:

1. Creates a profile directory under
   `~/.local/share/xninetzy/auth/profiles/<owner>/<account>/<ref>/`
   with mode 0700 owned by the install user.
2. Stores the Playwright `storage_state.json` encrypted under
   `SecretStore` keyed by `<ref>`. Plain bytes leave the store only
   when the adapter launches the browser.
3. Reuses the profile **only** when `<owner>` and the account
   nickname match. Two accounts of the same provider never share
   a profile dir.
4. Deletes the profile dir on `auth_session_revoke`.

## URL safety

`xninetzy/os/auth/policies/url_policy.py::assert_safe_url` is the
gate every backend calls before navigating anywhere. It rejects:

- Schemes: `javascript:`, `data:`, `file:`, `chrome:`, `about:`,
  `vbscript:`.
- Hosts in private space: `10.0.0.0/8`, `172.16.0.0/12`,
  `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `::1`,
  `fc00::/7`, `fe80::/10`.
- Origins not in the provider's allowlist (Kaggle, Google, GitHub)
  unless the OAuth callback domain is explicitly whitelisted.

The backend raises `URLBlockedError` and surfaces a structured
diagnostic. The host cannot override the gate by passing a "raw"
URL; the gate runs server-side.

## Redaction

Every tool result the gateway produces funnels through
`redact_payload` from `xninetzy/os/auth/policies/redaction.py`.
Specifically stripped:

- `Authorization: Bearer …` headers
- `access_token=…`, `refresh_token=…`, `id_token=…`
- `client_secret=…`
- `Set-Cookie: …`
- Common API-key prefixes (`sk-…`, `sk-ant-…`, `ghp_…`, `github_pat_…`,
  `AIza…`, `AKIA…`, `ya29…`, `xox…`)
- PEM private-key blocks

This is a hard scrub — redaction **removes** the secret, then
returns the redacted text. No "redacted:true" flag is set. The host
model never sees raw material.

## Capabilities snapshot

```python
browser_capabilities() → {
    "browser_available": bool,
    "backends": ["local", "cdp", "remote"],
    "active_backend": "local" | "cdp" | "remote" | "none",
    "headless": bool,
    "playwright_version": "1.x.y" | None,
    "allowed_domains": ["kaggle.com", "accounts.google.com", ...],
}
```

The host uses this to decide whether to ask for a browser login, or
to fall back to OAuth.

## Configuration

| Env | Default | Meaning |
|---|---|---|
| `XNINETZY_BROWSER_ENABLED` | `true` | Master enable; `false` returns `BROWSER_DISABLED` |
| `XNINETZY_BROWSER_BACKEND` | `auto` | Override backend selection |
| `XNINETZY_BROWSER_HEADLESS` | `false` | Visible browser; never `true` for headless serverless sandboxes |
| `XNINETZY_BROWSER_PROFILE_DIR` | (computed) | Override base dir for profiles |
| `XNINETZY_BROWSER_REMOTE_ENDPOINT` | unset | Playwright remote WS endpoint |
| `XNINETZY_BROWSER_CDP_ENDPOINT` | unset | CDP HTTP/WS endpoint |
| `XNINETZY_BROWSER_ALLOWED_DOMAINS` | `kaggle.com,…,github.com,api.github.com` | Comma-separated allowlist |

## What this is NOT

- Not a headless serverless browser. Vercel Functions and similar
  cannot host a persistent Playwright instance; the gateway
  therefore supports the `REMOTE` backend exactly so a persistent
  worker (e.g. owned by the user elsewhere) can do the work.
- Not a sibling MCP server. `xninetzy` remains the only MCP server.
- Not an autonomous click-on-CAPTCHA agent. The user resolves
  CAPTCHA / MFA manually.
- Not a session hijacker. The gateway will not attach to a browser
  it does not own.
