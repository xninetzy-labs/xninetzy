# Xninetzy UACC — Analysis, Write Boundary, and Persistence

This reference expands analysis freshness, artifact persistence, security boundary, analysis evidence, ambiguous portal state, write boundary, future write safety, revalidation, UACC vs Cyber Campus integrity, Graph RAG integration, memory integration, checkpoint structure, and standard UACC status output. Read it when analyzing the portal structure or planning a future write.

## Analysis freshness

Portal structure can change. Mark analysis:

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

## Artifact persistence

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

## Security boundary

Never expose:

* UACC username/password,
* session cookies,
* CSRF values,
* CAPTCHA answers,
* authentication tokens,
* browser state,
* internal authorization headers.

A CSRF field name may be documented as page structure when necessary, but its actual secret value must not be surfaced.

## Analysis evidence

Separate:

* **Observed** — directly returned by the UACC adapter.
* **Derived** — reasoned from observed structure.
* **Historical** — previously stored in memory.
* **Unknown** — not currently verified.

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

## Ambiguous portal state

Stop when:

* page identity is unclear,
* response is unexpected,
* authentication state changes unexpectedly,
* CAPTCHA appears outside the expected flow,
* adapter returns ambiguous fields,
* portal behavior differs materially from known state.

Do not guess what the page means. Return control to the owner or require fresh verification.

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

A proposed UACC write must identify:

* target,
* exact change,
* expected result,
* consequence,
* approval state,
* verification method.

Approval must apply to the exact proposed action. Do not reuse an old approval for a changed action.

## Revalidation before future writes

Immediately before execution:

1. verify UACC session,
2. verify target page,
3. verify current state,
4. verify proposed diff,
5. verify approval scope,
6. execute exactly once,
7. re-read,
8. verify final state.

If any material state changed, invalidate the previous approval and stop.

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

Persist durable UACC observations such as:

* portal structure,
* page inventory,
* stable workflow,
* verified protection mechanism,
* analysis version,
* important corrections,
* current investigation state.

Do not persist secrets or live authentication state unless the approved secure session system specifically requires encrypted local state.

## Checkpoint structure

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