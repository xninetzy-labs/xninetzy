---
name: xninetzy-uacc
description: Safety-first operating system for the UNAIR UACC/UnairSatu central SSO portal. Use for authenticated session inspection, manual-CAPTCHA login, owner-bound verification, SSO page discovery, authorized read-only portal analysis, session freshness monitoring, Graph RAG and memory persistence, and audited handling of future write requests without mixing UACC state with Cyber Campus state.
metadata:
  scope: general
  platform: "UNAIR UACC / UnairSatu SSO"
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "identify -> isolate -> session-check -> authenticate -> human-verify -> read -> analyze -> persist -> checkpoint -> monitor -> propose/verify"
---

# Xninetzy UACC OS

This skill is the dedicated operating system for interacting with the **UNAIR UACC / UnairSatu central SSO**. Its primary responsibilities are:

* UACC session inspection,
* authorized login,
* manual CAPTCHA handling,
* SSO page analysis,
* read-only discovery,
* session freshness,
* portal structure documentation,
* Graph RAG integration,
* durable memory/checkpointing,
* safe handling of future write requests.

The central rule is:

> **UACC is a separate authentication domain from Cyber Campus. Its identity, session, challenge, evidence, and state must never be silently mixed with Cyber Campus.**

The canonical lifecycle is:

**Identify → Isolate → Session Check → Authenticate → Human Verify → Read → Analyze → Persist → Checkpoint → Monitor → Propose/Verify**

## System boundary

UACC and Cyber Campus are distinct systems.

### UACC / UnairSatu

Primary SSO domain:

```text
uacc.unair.ac.id
→
unairsatu.unair.ac.id
```

### Cyber Campus

Student academic portal: `mahasiswa.unair.ac.id`.

Never:

* reuse UACC sessions for Cyber Campus,
* reuse Cyber Campus sessions for UACC,
* cross-link credentials,
* cross-link CAPTCHA challenges,
* assume the same identity/session state,
* treat one portal's authentication as proof of access to the other.

## When to use

* the user asks to log in to UACC, inspect its session, or analyze its SSO structure;
* the user wants to monitor UACC session freshness through the supported watchdog;
* the user wants UACC page notes or portal structure diagrams persisted into Obsidian or memory.

## When NOT to use

* Cyber Campus operations — use `xninetzy-cyber-campus`;
* HEBAT or Moodle operations — use `hebat-academic`;
* general web analysis on public sites without an authenticated UACC session — use `xninetzy-web-analysis`.

## Source of truth

For current UACC state, use:

```text
current verified portal state
>
typed UACC adapter result
>
verified local encrypted session state
>
durable memory
>
conversation context
>
general assumptions
```

Memory may preserve historical UACC state, but it does not replace a current session or portal verification.

## Owner scope

All UACC operations must be owner-bound. Owner scope includes credentials, authenticated session, CAPTCHA challenge, portal analysis, session monitoring, and persisted observations. A chat identifier alone does not constitute permission to authenticate or act.

## Credential handling

Use only the configured authorized credential source. Credentials must remain server-side, never appear in logs, never be returned in final responses, never be persisted to memory, never be copied into research notes, and never be included in Graph RAG nodes. The system should report only authentication status, not credential contents.

## CAPTCHA boundary

CAPTCHA is a mandatory human-verification boundary. The system may capture the CAPTCHA, deliver it to the owner through the supported image channel, wait for the owner's answer, and submit the manually supplied answer through the supported adapter.

The system must never:

* solve CAPTCHA automatically,
* use OCR,
* infer the answer,
* poll local image files to automate solving,
* bypass institutional controls,
* reuse an expired challenge.

## CAPTCHA lifecycle

```text
challenge_created
↓
challenge_delivered
↓
owner_reads
↓
owner_answers
↓
adapter_submits
↓
authenticated / rejected
```

If rejected:

```text
fresh challenge
↓
owner reads again
↓
manual answer
```

An expired challenge is invalid. Do not restart or replay an expired challenge.

## Authentication commands

Where the registered interface supports them:

* `/uacc-login` starts an owner-authorized login flow.
* `/uacc-captcha <challenge_id> <answer>` submits the manually supplied CAPTCHA answer for the specific live challenge.
* `/uacc-login-cancel <challenge_id>` cancels the active challenge.

These are administrative workflow concepts, not permission to expose portal internals. Do not accept a CAPTCHA answer for an unknown, completed, or expired challenge.

## Core workflow

1. **Identify.** Determine that the request is for UACC/UnairSatu and isolate it from Cyber Campus.
2. **Isolate.** Use only UACC-specific credentials, sessions, and challenge IDs.
3. **Session check.** Inspect whether a valid session exists before any protected operation.
4. **Authenticate.** Trigger the supported login flow when required.
5. **Human verify.** Deliver the CAPTCHA, wait for the owner-supplied answer, and submit through the supported adapter.
6. **Read.** Use the typed UACC adapter for authorized page navigation, form discovery, login structure, and CAPTCHA presence.
7. **Analyze.** Capture the minimum useful structure: page identity, URL/path, form identity, field names, navigation relationships, protection mechanisms, and relevant response structure.
8. **Persist.** Persist verified structural relationships to Graph RAG and durable portal notes to memory. Never persist credentials, session tokens, CAPTCHA answers, or private browser state.
9. **Checkpoint.** Persist a continuity checkpoint with goal, scope, completed, decisions, constraints, sources, artifacts, failed attempts, open questions, next actions, and resume hint.
10. **Monitor.** Use the configured watchdog to inspect session freshness without touching the portal. Send owner notifications through the supported channel only.
11. **Propose/verify.** Surface any future write as a proposal that requires explicit approval. Verify the actual portal response after any supported mutation.

## CAPTCHA delivery

CAPTCHA delivery uses the configured image channel. When fallback image content is used, preserve the challenge identity without exposing authentication secrets.

## Local CAPTCHA handling

If the configured fallback saves an image locally and optional auto-open behavior is enabled, this is a human-facing convenience only. Do not OCR the image, continuously poll for the answer, create an automatic solving loop, or infer the owner's response.

## Fast-path login

The login flow may automate non-sensitive preparation such as:

* loading authorized server-side credentials,
* opening the login flow,
* detecting the CAPTCHA,
* delivering the challenge,
* submitting the owner's manually provided answer.

The owner remains responsible for interpreting the CAPTCHA. Wrong answers may trigger a fresh challenge within the configured maximum attempt policy. Never reuse the rejected challenge.

## Session state

Represent UACC session state explicitly:

```text
unknown
missing
active
stale
expired
challenge_required
blocked
unavailable
```

Do not assume that a previous successful login means the current session is still valid.

## Session freshness

Use the configured freshness threshold. Session inspection should report whether a session exists, approximate/local session age when available, freshness state, and last verified observation when appropriate. Do not expose session cookies or raw browser state.

## Session watchdog

Where configured, a watchdog may monitor session health at the configured interval with notification cooldown. The watchdog reads encrypted local session state only, checks for missing/stale status, sends owner notification when configured, and never opens a browser, never starts a new login, never touches the portal, and never solves CAPTCHA.

## Watchdog notifications

Notifications should report only what is necessary.

Example:

> UACC session is stale. A fresh login may be required.

Do not include credentials, cookies, challenge answers, or private browser state.

## Read-only principle

Normal UACC operations are read-only. Supported reads may include session status, login page structure, form fields, CSRF presence, CAPTCHA image presence, authorized page navigation, form discovery, web-analysis catalog, and analysis cache status. All standard portal reads should use the typed adapter and supported GET/HEAD behavior.

## Page discovery

When analyzing a page, capture only the minimum useful structure: page identity, URL/path, form identity, field names, navigation relationships, protection mechanisms, and relevant response structure. Do not store full raw HTML unless explicitly required by an approved analysis workflow.

## UACC page analysis

Use the structured analysis workflow:

```text
uacc_session_status
↓
web_analysis_refresh("uacc", authenticated=True)
↓
inspect catalog
↓
analyze relevant page sections
↓
persist verified findings
↓
checkpoint
```

Do not analyze beyond the authenticated scope available to the owner.

## Analysis evidence

Separate observed (directly returned by the UACC adapter), derived (reasoned from observed structure), historical (previously stored in memory), and unknown (not currently verified). Do not present derived or historical structure as though it were directly observed now.

## Ambiguous portal state

Stop when page identity is unclear, response is unexpected, authentication state changes unexpectedly, CAPTCHA appears outside the expected flow, the adapter returns ambiguous fields, or portal behavior differs materially from known state. Do not guess what the page means. Return control to the owner or require fresh verification.

## Write boundary

The current UACC workflow has **no ordinary write operations**. If a future write is explicitly supported, use:

```text
current verified state
↓
proposed exact diff
↓
explicit confirmation
↓
execute once
↓
re-read
↓
verify
↓
receipt
```

Never convert a read capability into an implicit write.

## Future write safety

A proposed UACC write must identify target, exact change, expected result, consequence, approval state, and verification method. Approval must apply to the exact proposed action. Do not reuse an old approval for a changed action.

## Revalidation before future writes

Immediately before execution, verify UACC session, target page, current state, proposed diff, and approval scope; execute exactly once; re-read; and verify final state. If any material state changed, invalidate the previous approval and stop.

## UACC vs Cyber Campus integrity

Maintain separate records:

```text
UACC:
  identity
  session
  challenge
  analysis

Cyber Campus:
  identity
  session
  grades
  KRS
  academic data
```

A shared student may exist across both systems, but the session and authentication records remain separate. Do not create relationships such as `UACC session = Cyber Campus session` unless a verified external system explicitly establishes that relationship for the specific purpose.

## Graph RAG integration

Store only verified structural relationships. Useful examples:

```text
UACC Portal
  ── contains ──>
Login Page

Login Page
  ── includes ──>
CAPTCHA Challenge

UACC Portal
  ── routes_to ──>
UnairSatu
```

Do not store credentials, authentication secrets, active cookies, or private challenge answers. Graph relationships must be supported by observed portal analysis.

## Memory integration

Persist durable UACC observations such as portal structure, page inventory, stable workflow, verified protection mechanism, analysis version, important corrections, and current investigation state. Do not persist secrets or live authentication state unless the approved secure session system specifically requires encrypted local state.

## Reference map

* `references/error-handling-and-monitoring.md` — error handling, idempotency, monitoring vs automation, and standard outputs.
* `references/analysis-and-persistence.md` — analysis freshness, artifact persistence, security boundary, analysis evidence, ambiguous portal state, write boundary, future write safety, revalidation, UACC vs Cyber Campus integrity, Graph RAG integration, memory integration, checkpoint structure, and standard UACC status output.

## Operating rules

The system must:

* keep UACC and Cyber Campus strictly separate,
* use only authorized owner-bound credentials,
* keep credentials and tokens out of logs and responses,
* treat CAPTCHA as a mandatory human-verification boundary,
* never solve CAPTCHA automatically,
* never bypass institutional controls,
* invalidate expired challenges,
* use typed deterministic portal adapters,
* prefer read-only analysis,
* persist only minimum durable portal structure,
* distinguish observed data from inference and historical memory,
* revalidate stale portal state,
* require explicit confirmation for any future write,
* re-read and verify after any supported mutation,
* preserve provenance when integrating with Graph RAG and Memory.

The canonical lifecycle is:

**Identify → Isolate → Session Check → Authenticate → Human Verify → Read → Analyze → Persist → Checkpoint → Monitor → Propose/Verify**

The central objective is:

> **Provide reliable, owner-controlled access to UACC information while preserving a strict security and state boundary from Cyber Campus, keeping CAPTCHA human-only, and ensuring every persistent portal observation remains traceable and verifiable.**