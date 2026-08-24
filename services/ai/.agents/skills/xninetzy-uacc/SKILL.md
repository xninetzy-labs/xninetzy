# Xninetzy UACC OS

```yaml
---
name: xninetzy-uacc
description: General-purpose, safety-first operating system for the UNAIR UACC/UnairSatu central SSO portal. Supports authenticated session inspection, manual-CAPTCHA login, owner-bound verification, SSO page discovery, authorized read-only portal analysis, session freshness monitoring, Graph RAG and memory persistence, and audited handling of any future write request without mixing UACC state with Cyber Campus state.
metadata:
  scope: general
  platform: "UNAIR UACC / UnairSatu SSO"
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "identify -> isolate -> session-check -> authenticate -> human-verify -> read -> analyze -> persist -> checkpoint -> monitor -> propose/verify"
---
```

# Xninetzy UACC OS

This skill is the dedicated operating system for interacting with the **UNAIR UACC / UnairSatu central SSO**.

Its primary responsibilities are:

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

---

# 1. System Boundary

UACC and Cyber Campus are distinct systems.

### UACC / UnairSatu

Primary SSO domain:

```text
uacc.unair.ac.id
→
unairsatu.unair.ac.id
```

### Cyber Campus

Student academic portal:

```text
mahasiswa.unair.ac.id
```

Never:

* reuse UACC sessions for Cyber Campus,
* reuse Cyber Campus sessions for UACC,
* cross-link credentials,
* cross-link CAPTCHA challenges,
* assume the same identity/session state,
* treat one portal's authentication as proof of access to the other.

---

# 2. Source of Truth

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

---

# 3. Owner Scope

All UACC operations must be owner-bound.

Owner scope includes:

* credentials,
* authenticated session,
* CAPTCHA challenge,
* portal analysis,
* session monitoring,
* persisted observations.

A chat identifier alone does not constitute permission to authenticate or act.

---

# 4. Credential Handling

Use only the configured authorized credential source.

Conceptually:

```text
UACC_CREDENTIAL_SOURCE
default: hebat
```

Credentials must:

* remain server-side,
* never appear in logs,
* never be returned in final responses,
* never be persisted to memory,
* never be copied into research notes,
* never be included in Graph RAG nodes.

The system should report only authentication status, not credential contents.

---

# 5. CAPTCHA Boundary

CAPTCHA is a mandatory human-verification boundary.

The system may:

* capture the CAPTCHA,
* deliver it to the owner,
* wait for the owner's answer,
* submit the manually supplied answer through the supported adapter.

The system must never:

* solve CAPTCHA automatically,
* use OCR,
* infer the answer,
* poll local image files to automate solving,
* bypass institutional controls,
* reuse an expired challenge.

---

# 6. CAPTCHA Lifecycle

Use:

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

An expired challenge is invalid.

Do not restart or replay an expired challenge.

---

# 7. Authentication Commands

Where the registered interface supports them:

```text
/uacc-login
/uacc-captcha <challenge_id> <answer>
/uacc-login-cancel <challenge_id>
```

These are administrative workflow concepts, not permission to expose portal internals.

### `/uacc-login`

Starts an owner-authorized login flow.

### `/uacc-captcha`

Submits the manually supplied CAPTCHA answer for the specific live challenge.

### `/uacc-login-cancel`

Cancels the active challenge.

Do not accept a CAPTCHA answer for an unknown, completed, or expired challenge.

---

# 8. CAPTCHA Delivery

Preferred delivery:

**WhatsApp first**

Fallback:

**MCP image content**

Conceptual route:

```text
UACC login
↓
CAPTCHA captured
↓
WhatsApp available?
 ├── yes → send image to owner
 └── no  → return MCP ImageContent + metadata
```

On WhatsApp, image delivery remains the preferred owner interaction.

When fallback image content is used, preserve the challenge identity without exposing authentication secrets.

---

# 9. Local CAPTCHA Handling

If the configured fallback saves an image locally:

```text
XNINETZY_CAPTCHA_DIR
```

and optional auto-open behavior is enabled:

```text
XNINETZY_CAPTCHA_AUTO_OPEN=true
```

this is a human-facing convenience only.

Do not:

* OCR the image,
* continuously poll for the answer,
* create an automatic solving loop,
* infer the owner's response.

---

# 10. Fast-Path Login

The login flow may automate non-sensitive preparation such as:

* loading authorized server-side credentials,
* opening the login flow,
* detecting the CAPTCHA,
* delivering the challenge,
* submitting the owner's manually provided answer.

The owner remains responsible for interpreting the CAPTCHA.

Wrong answers may trigger a fresh challenge within the configured maximum attempt policy.

Never reuse the rejected challenge.

---

# 11. Session State

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

---

# 12. Session Freshness

Use the configured freshness threshold:

```text
ACADEMIC_SESSION_STALE_HOURS
```

Session inspection should report:

* whether a session exists,
* approximate/local session age when available,
* freshness state,
* last verified observation when appropriate.

Do not expose session cookies or raw browser state.

---

# 13. Session Watchdog

Where configured, a watchdog may monitor:

```text
session_watchdog_loop
```

and inspect UACC/Cyber Campus session health at:

```text
ACADEMIC_SESSION_WATCHDOG_INTERVAL_SECONDS
```

with notification cooldown:

```text
ACADEMIC_SESSION_WATCHDOG_NOTIFY_COOLDOWN_HOURS
```

The watchdog:

* reads encrypted local session state only,
* checks for missing/stale status,
* sends owner notification when configured,
* never opens a browser,
* never starts a new login,
* never touches the portal,
* never solves CAPTCHA.

---

# 14. Watchdog Notifications

Notifications should report only what is necessary.

Example:

> UACC session is stale. A fresh login may be required.

Do not include:

* credentials,
* cookies,
* challenge answers,
* private browser state.

---

# 15. Read-Only Principle

Normal UACC operations are read-only.

Supported reads may include:

* session status,
* login page structure,
* form fields,
* `_csrf` presence,
* CAPTCHA image presence,
* authorized page navigation,
* form discovery,
* web-analysis catalog,
* analysis cache status.

All standard portal reads should use the typed adapter and supported GET/HEAD behavior.

---

# 16. Page Discovery

When analyzing a page, capture only the minimum useful structure:

* page identity,
* URL/path,
* form identity,
* field names,
* navigation relationships,
* protection mechanisms,
* relevant response structure.

Do not store full raw HTML unless explicitly required by an approved analysis workflow.

---

# 17. UACC Page Analysis

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

---

# 18. Analysis Evidence

Separate:

### Observed

Directly returned by the UACC adapter.

### Derived

Reasoned from observed structure.

### Historical

Previously stored in memory.

### Unknown

Not currently verified.

Example:

```text
Observed:
Login page contains a CAPTCHA image.

Derived:
Login requires a human verification step.

Historical:
Same page contained an additional field last month.

Current status:
Needs revalidation.
```

---

# 19. Ambiguous Portal State

Stop when:

* page identity is unclear,
* response is unexpected,
* authentication state changes unexpectedly,
* CAPTCHA appears outside the expected flow,
* adapter returns ambiguous fields,
* portal behavior differs materially from known state.

Do not guess what the page means.

Return control to the owner or require fresh verification.

---

# 20. Write Boundary

The current UACC workflow has **no ordinary write operations**.

If a future write is explicitly supported, use:

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

---

# 21. Future Write Safety

A proposed UACC write must identify:

* target,
* exact change,
* expected result,
* consequence,
* approval state,
* verification method.

Approval must apply to the exact proposed action.

Do not reuse an old approval for a changed action.

---

# 22. Revalidation Before Future Writes

Immediately before execution:

1. verify UACC session,
2. verify target page,
3. verify current state,
4. verify proposed diff,
5. verify approval scope,
6. execute exactly once,
7. re-read,
8. verify final state.

If any material state changed:

**invalidate the previous approval and stop.**

---

# 23. UACC vs Cyber Campus Integrity

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

A shared student may exist across both systems, but the session and authentication records remain separate.

Do not create relationships such as:

> UACC session = Cyber Campus session

unless a verified external system explicitly establishes that relationship for the specific purpose.

---

# 24. Graph RAG Integration

Store only verified structural relationships.

Useful examples:

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

Do not store:

* credentials,
* authentication secrets,
* active cookies,
* private challenge answers.

Graph relationships must be supported by observed portal analysis.

---

# 25. Memory Integration

Persist durable UACC observations such as:

* portal structure,
* page inventory,
* stable workflow,
* verified protection mechanism,
* analysis version,
* important corrections,
* current investigation state.

Do not persist secrets or live authentication state unless the approved secure session system specifically requires encrypted local state.

---

# 26. Checkpoint Structure

For UACC analysis:

```yaml
goal:
scope:
completed:
decisions:
constraints:
sources:
artifacts:
failed_attempts:
open_questions:
next_actions:
resume_hint:
```

Example:

> Portal analysis completed for `/site/login`; CAPTCHA is present; login remains manual; page catalog persisted; next action is to inspect only the authorized authenticated pages that remain unresolved.

---

# 27. Analysis Freshness

Portal structure can change.

Mark analysis:

```text
current
stale
unknown
```

Refresh when:

* the user asks for current portal behavior,
* login flow changes,
* session behavior differs,
* a page previously found no longer matches,
* analysis exceeds its intended freshness window.

Never treat an old HTML structure as current without verification.

---

# 28. Artifact Persistence

Useful artifacts may include:

* portal catalog,
* analysis JSON,
* analysis Markdown,
* screenshots when appropriate,
* Mermaid diagrams,
* page notes.

Record:

```yaml
artifact:
path:
version:
source:
status:
```

Verify the file exists before treating it as persistent evidence.

---

# 29. Security Boundary

Never expose:

* UACC username/password,
* session cookies,
* CSRF values,
* CAPTCHA answers,
* authentication tokens,
* browser state,
* internal authorization headers.

A CSRF field name may be documented as page structure when necessary, but its actual secret value must not be surfaced.

---

# 30. Error Handling

Handle structured errors explicitly.

Examples:

```text
NOT_FOUND
→ refine page/identifier

AUTH_REQUIRED
→ verify UACC session

CHALLENGE_REQUIRED
→ return to owner CAPTCHA flow

CHALLENGE_EXPIRED
→ invalidate challenge; start fresh login

INVALID_INPUT
→ correct adapter arguments

POLICY_HELD
→ stop and request approval
```

Never retry a stale or expired CAPTCHA challenge.

---

# 31. Idempotency

For any supported retryable mutation or persistent analysis operation:

* use a stable `idempotency_key` when supported,
* do not duplicate records after retries,
* verify actual state before replaying.

A failed network response does not prove the portal did not change.

For future writes, re-read the state before retry.

---

# 32. Monitoring vs Automation

Monitoring is allowed within the configured read-only watchdog boundary.

Automation of authentication is not.

This distinction is deliberate:

```text
monitor state
✓

notify owner
✓

start browser automatically
✗

answer CAPTCHA automatically
✗

submit unattended action
✗
```

---

# 33. Standard UACC Status Output

```text
Portal:
Session:
Session Freshness:
Authentication:
Current Challenge:
Analysis Status:
Last Verified:
Known Pages:
Uncertainty:
Next Action:
```

Do not include secrets.

---

# 34. Standard Analysis Output

```text
UACC Scope
Session State
Page Catalog
Verified Structures
Protection / CAPTCHA Behavior
Known Navigation
Current vs Historical State
Graph / Memory Persistence
Open Questions
Next Analysis Action
```

---

# 35. Completion Contract

Every meaningful UACC workflow should return the relevant subset of:

**Portal identity**
UACC / UnairSatu.

**Session status**
Current, stale, expired, or unavailable.

**Authentication status**
Whether login is complete or human verification is pending.

**Challenge status**
Only non-secret challenge state.

**Read/analyze result**
Verified structured observations.

**Freshness**
Whether the analysis is current enough for the request.

**Persistence status**
Graph/memory/checkpoint state when applicable.

**Approval status**
Only relevant for future supported writes.

**Verification evidence**
What was directly observed.

**Next action**
One bounded safe continuation step.

---

# 36. Standard Operating Rules

The system must:

**keep UACC and Cyber Campus strictly separate,**

**use only authorized owner-bound credentials,**

**keep credentials and tokens out of logs and responses,**

**treat CAPTCHA as a mandatory human-verification boundary,**

**never solve CAPTCHA automatically,**

**never bypass institutional controls,**

**invalidate expired challenges,**

**use typed deterministic portal adapters,**

**prefer read-only analysis,**

**persist only minimum durable portal structure,**

**distinguish observed data from inference and historical memory,**

**revalidate stale portal state,**

**require explicit confirmation for any future write,**

**re-read and verify after any supported mutation,**

**preserve provenance when integrating with Graph RAG and Memory.**

The canonical lifecycle is:

**Identify → Isolate → Session Check → Authenticate → Human Verify → Read → Analyze → Persist → Checkpoint → Monitor → Propose/Verify**

The central objective is:

> **Provide reliable, owner-controlled access to UACC information while preserving a strict security and state boundary from Cyber Campus, keeping CAPTCHA human-only, and ensuring every persistent portal observation remains traceable and verifiable.**
