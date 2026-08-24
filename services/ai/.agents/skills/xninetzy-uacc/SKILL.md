---
name: xninetzy-uacc
description: Safely retrieve and analyze the UNAIR UACC/UnairSatu SSO portal with manual CAPTCHA challenges, keeping UACC sessions strictly separate from Cyber Campus.
metadata:
  owner: xninetzy
  version: "1.1.0"
---

# UACC / UnairSatu SSO

## Scope

UACC is the central UNAIR SSO (`uacc.unair.ac.id` -> `unairsatu.unair.ac.id`).
It is separate from Cyber Campus (`mahasiswa.unair.ac.id`). Never mix,
reuse, or cross-link UACC sessions, identities, or challenge flows with Cyber
Campus.

## Authentication

* use authorized credentials only (`UACC_CREDENTIAL_SOURCE`, default hebat);
* never expose credentials in logs;
* CAPTCHA stays manual; never solve automatically;
* commands are admin-only and separate:
  * `/uacc-login` starts login and sends the CAPTCHA to the owner;
  * `/uacc-captcha <challenge_id> <answer>` submits the manual answer;
  * `/uacc-login-cancel <challenge_id>` cancels an active challenge;
* if no CAPTCHA is detected, login may proceed directly;
* invalidate expired challenges; if a challenge expired, run `/uacc-login`
  again for a fresh one;
* do not bypass institutional controls.

## CAPTCHA delivery (whatsapp first, MCP image fallback)

`uacc_login_start` / `uacc_login_submit_captcha` return
`list[TextContent | ImageContent]` (or a plain string when WhatsApp is used):

* WhatsApp available (`WA_MCP_BASE_URL/health` OK, socket ready) -> CAPTCHA is
  sent as an image to the owner chat; the tool returns plain text;
* WhatsApp unavailable or send fails -> the CAPTCHA is delivered as an MCP
  `ImageContent` block plus metadata text, saved to `XNINETZY_CAPTCHA_DIR`,
  and opened with `xdg-open` when `XNINETZY_CAPTCHA_AUTO_OPEN=true`;
* on the WhatsApp channel, the fallback returns a text hint with the local
  PNG path (image blocks are not usable there);
* never fall back to OCR, auto-solving, or local file polling; the owner must
  read the CAPTCHA and reply manually;
* do not restart or replay a challenge: expired challenges are invalidated by
  the login coordinator; start a fresh login instead.

## Fast-path login pipeline & session watchdog

* `/uacc-login` is one-shot: credentials are auto-filled from server config,
  the CAPTCHA is captured and delivered to WhatsApp automatically, and a wrong
  answer triggers an automatic retry with a fresh CAPTCHA image up to
  `UACC_LOGIN_MAX_ATTEMPTS` — total owner effort is reading one image and
  typing one short answer;
* `uacc_session_status` and `uacc_info` report the local session age
  (`ACADEMIC_SESSION_STALE_HOURS` threshold);
* a background session watchdog (`session_watchdog_loop`) checks both portals
  every `ACADEMIC_SESSION_WATCHDOG_INTERVAL_SECONDS` and notifies the owner on
  WhatsApp when a session is missing or stale, with a notification cooldown of
  `ACADEMIC_SESSION_WATCHDOG_NOTIFY_COOLDOWN_HOURS`;
* the watchdog only reads encrypted local state and sends notifications — it
  never starts a browser and never touches the portal;
* the owner still reads and answers every CAPTCHA manually; OCR, auto-solving,
  and unattended submission remain prohibited.

## Read operations

May retrieve:

* login and session status;
* SSO page structure (`/site/login`, form fields, `_csrf`, captcha image);
* authorized page navigation and form discovery;
* web analysis catalog and cache status.

All reads are GET/HEAD only. Store only minimum durable information.

## Analysis workflow

```text
uacc_session_status
-> web_analysis_refresh("uacc", authenticated=True)
-> inspect catalog
-> analyze each page section
-> persist results to Graph RAG + memory
-> checkpoint
```

Stop when the portal response is ambiguous or a human verification challenge
appears; return control to the owner.

## Write operations

There are no UACC write operations. If a write is ever requested, use:

```text
current state
-> proposed exact diff
-> confirmation
-> execute once
-> re-read
-> verify
-> receipt
```
