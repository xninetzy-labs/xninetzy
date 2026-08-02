---
layout: ../../layouts/DocsLayout.astro
title: Cyber Campus and grade tokens
description: Manual CAPTCHA login, encrypted sessions, deterministic academic readers, and WhatsApp-admin verification.
section: Integrations
---

Cyber Campus is an academic adapter separate from HEBAT. HEBAT handles Moodle
courses and materials; Cyber Campus handles academic profile, status, grades,
schedule, and KRS planning.

## Current capabilities

- Credentials come from `HEBAT_USERNAME` and `HEBAT_PASSWORD` in memory only.
- `/cyber-login` opens headless Chromium and fills those credentials.
- The login CAPTCHA image is sent only to the WhatsApp `ADMIN_JID`.
- The owner answers the image, sends one answer during the active challenge, or uses `/captcha <challenge-id> <answer>`.
- The common `/catchpa` typo is normalized before the AI request.
- Challenges have a TTL, owner binding, and attempt limit.
- Successful sessions are stored through the encrypted session manager.
- The authenticated crawler prioritizes KRS, KPRS, grades, schedule, and academic draft pages, including framed menus.
- `/jadwal` reads the current schedule deterministically.
- `/cyber-profile` returns only name, student identifier, faculty, and program.
- `/status-akademik` reads academic status by semester.
- `/krs status` reads selected courses, classes, state, and total credits without mutation.
- `/nilai` opens the KHS page, waits for the portal's official token, and sends a WhatsApp challenge to the administrator.
- Token replies go directly to the KHS reader without LLM, MCP persistence, a Telegram bot, or a Xninetzy Telegram engine.
- Final KRS write and submission remain gated until selectors, fixtures, and bound approval have sufficient coverage.

## Login flow

```text
/cyber-login from the WhatsApp administrator
  → headless Chromium opens the portal
  → local HEBAT credentials are filled
  → the CAPTCHA element is captured
  → the image is sent to ADMIN_JID
  → the owner replies with the answer or /captcha <id> <answer>
  → the resulting page is validated
  → the encrypted session is stored
```

The agent does not OCR, guess, or bypass the CAPTCHA. A failed or expired
challenge produces a new image or requires a new login. A single unprefixed
answer is converted to a command only while a challenge is active and only for
the administrator. WhatsApp JIDs are normalized so Baileys device suffixes
remain bound to the correct owner.

After login:

```text
/portal-nav
/krs-capabilities
/web-refresh mahasiswa
/web-analysis mahasiswa
/portalinfo
/cyber-profile
/status-akademik
/krs status
/jadwal
/nilai
```

These read-only capabilities live in the shared adapter. WhatsApp uses direct
slash commands, natural chat uses LangGraph, and Codex, Claude Code, and OpenCode
use `portal_profile`, `portal_academic_status`, `portal_current_krs`, and
`portal_schedule` through MCP.

For the `mahasiswa` site, `/web-refresh` automatically loads the encrypted
owner session. The crawler forwards only GET or HEAD, blocks mutation requests
and sensitive routes, and stores structure without field values, credentials,
cookies, tokens, grades, or visible academic data.

## Verified KRS structure

Read-only portal analysis identified:

```text
/modul/mhs/akademik-krs.php
/modul/mhs/akademik-kprs.php
/modul/mhs/akademik-khs.php
/modul/mhs/akademik-transkrip.php
/modul/mhs/akademik-jadwal.php
/modul/mhs/akademik-draft.php
```

The KRS page contains course offerings, cross-cluster courses, selected courses,
and print views. Outside an active KRS window the portal exposes no selection
form or checkbox. Xninetzy reports that state and does not guess or call an
internal write endpoint.

The selected-course reader uses the fixed display endpoint with
`aksi=tampil` and validates the six-column header before creating typed
models. Academic status uses the same fail-closed parser approach. When portal
structure changes, readers fail explicitly instead of guessing column order.

A future write workflow must read offerings and academic state, prepare a
mutation-free plan, request WhatsApp approval, revalidate the portal, apply the
selection, and request a separate final approval.

`/portal-nav` inventories same-origin labels and paths across frames and marks
them as `read_only`, `krs_guarded`, or `blocked_write`.
`/krs-capabilities` inventories forms, controls, tabs, and internal targets and
produces a new structure hash whenever portal DOM or JavaScript changes. Raw
scripts are not placed in prompts or executed as LLM-generated code.

## Confirmation and media

Every confirmation, KRS approval, upload, and verification goes to the WhatsApp
administrator. The engine supports Approve and Reject buttons plus text-command
fallbacks. Images and documents can be forwarded through the durable media
store; tools never accept an arbitrary local path from an LLM.

## Grade tokens through WhatsApp

Cyber Campus states that KHS tokens are delivered to the Telegram account
registered with the portal. That is the portal's official channel, not a
Xninetzy Telegram integration. Xninetzy requires no `TELEGRAM_BOT_TOKEN`. The
owner forwards the received token by replying to the WhatsApp administrator
prompt.

The token is bound to one short-lived challenge, bypasses the LLM, is never
persisted, and can be used for one read attempt.

## Required KHS sequence

The portal validates the token against page interaction order. Xninetzy keeps
one browser page alive and performs:

```text
1. Open the KHS page
2. Wait for a new verified token
3. Fill the token field
4. Select the requested semester
5. Fetch and parse the KHS table
```

Never select the semester before filling the token. Doing so invokes the KHS
handler with an empty token and may invalidate the next token. A command such
as `/nilai semester 1` binds a target period to the challenge but leaves the
dropdown untouched until the owner replies.

Use `/nilai` for the latest semester, `/nilai semester 1` for the first study
semester, or `/nilai <period-code>` for an exact period. Reply to the
**Verified Token Cyber Campus** prompt with the numeric token. The prompt always
shows the target semester. The explicit alternative is
`/grade-token <challenge-id> <token>`.

That private command is not registered for LangGraph or external coding clients.
Authenticated local MCP or CLI owners can call
`portal_grade_token_submit`; the token still is not stored or logged.

The reader fills the token, updates the dropdown, and uses same-origin
`fetch` for the display endpoint without depending on page jQuery. Success is
declared only when the active token produces a valid KHS table.

## Snapshots and grade changes

Successful KHS results are normalized to course identity, code, credits, grade,
and source fields. Xninetzy hashes normalized content before storing a local
SQLite snapshot. Identical results are replay-safe.

```text
/nilai changes
/nilai perubahan
```

The commands compare the two most recent distinct snapshots for one period.
Changes are classified as a new course, changed grade, or removed course. The
first snapshot is a baseline, not a change notification. Shared tool
`portal_grade_changes` provides the same result to LangGraph and MCP.

Verified tokens are never stored with snapshots. The database remains local and
ignored by Git.

## Configuration

```dotenv
CYBER_CAMPUS_ENABLED=true
CYBER_CAMPUS_BASE_URL=https://mahasiswa.unair.ac.id
CYBER_CAMPUS_CREDENTIAL_SOURCE=hebat
CYBER_CAMPUS_BROWSER_HEADLESS=true
CYBER_CAMPUS_LOGIN_CHALLENGE_TTL_SECONDS=180
CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS=3
WEB_ANALYSIS_ENCRYPTION_KEY=
WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED=true
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net

CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS=180
CYBER_CAMPUS_GRADE_TOKEN_MAX_ATTEMPTS=3
CYBER_CAMPUS_ENTRY_YEAR=0
```

`CYBER_CAMPUS_ENTRY_YEAR` resolves aliases such as `semester 1`. A value of
`0` attempts to derive the entry year from a UNAIR identifier. Installations
with a different format must set it explicitly.

Do not enable Cyber Campus before the encryption key and administrator JID are
configured.

```bash
cd services/ai
uv run python scripts/configure_internal_auth.py --enable-cyber-campus
```

The script validates HEBAT credentials and `ADMIN_JID`, generates a Fernet key
when missing, enables GET/HEAD-only authenticated crawling, and prints no secret.

## Structural page catalog

The web-analysis service includes `hebat`, `mahasiswa`, and `qa` presets.
Use `/web-pages <site>` to inspect safe seed routes and
`/web-refresh <site>` after the relevant encrypted owner session is available.
Refresh follows discovered same-host GET-only links within
`WEB_ANALYSIS_PORTAL_MAX_PAGES`.

QA remains protected by its portal-owned reCAPTCHA flow. Structural analysis
never solves a CAPTCHA, submits a form, or stores token values.
