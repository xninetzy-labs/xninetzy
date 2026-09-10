# Xninetzy Web Analysis — Policies and Reports

This reference expands security and privacy, credential and session separation, read-only enforcement, no form submission, public visual safety, the completion contract, the standard analysis report, and the operating rules. Read it when auditing safety boundaries or producing the closing analysis report.

## Security and privacy

Never write to analysis output:

* credentials,
* cookies,
* CSRF values,
* session tokens,
* CAPTCHA answers,
* grade data,
* names from authenticated personal pages,
* private schedules,
* KRS details,
* sensitive query values.

Never place such values into:

* Graph RAG nodes,
* knowledge chunks,
* screenshots,
* memory checkpoints,
* research ledgers.

## Credential and session separation

The analyzer should receive only the minimum session context required through the supported adapter. It should never:

* read browser cookies directly,
* extract credentials,
* copy session tokens into analysis state,
* reuse another portal's session.

## Read-only enforcement

The analyzer should reject mutation-oriented routes before they reach the target:

```text
request
↓
route classification
↓
read?
├── yes → allow analysis
└── no  → block
```

This is a safety invariant, not merely a user instruction.

## No form submission

The analyzer must not:

* click submit,
* send POST mutations,
* upload files,
* finalize academic actions,
* fill questionnaires,
* alter KRS,
* alter course state.

Even if the page exposes a visible form, analysis remains structural/read-only.

## Public visual safety

PixelRAG visual capture is specifically for:

```text
public pages
login pages
```

Not:

```text
authenticated personal pages
student dashboards
grades
schedules
KRS
private profile pages
```

When in doubt: **structural analysis only.**

## Completion contract

Every meaningful web-analysis run should return the relevant subset of:

**Site / portal identity**

**Analysis mode** — public, authenticated read-only, or blocked.

**Freshness**

**Pages/structure discovered**

**Graph state**

**Knowledge-ingestion state**

**Visual-capture state**

**Verification status**

**Human-verification blockers**

**Uncertainty**

**Artifacts/cache**

**Memory/checkpoint status**

**Next action**

## Standard analysis report

```text
Portal / Site
Analysis Mode
Session State
Freshness
Pages Discovered
Structural Findings
Graph Persistence
Knowledge Persistence
Visual Capture
Verification
Blockers / Uncertainty
Artifacts
Next Action
```

## Operating rules

The system must:

* use one consistent read-only workflow across supported portals,
* keep all portal sessions and identities separate,
* enforce GET/HEAD-only analysis,
* stop at human verification,
* never solve CAPTCHA automatically,
* keep credentials and private portal values out of persistence,
* capture visuals only from public/login pages,
* bound crawl depth and page count,
* reuse fresh analysis cache,
* deduplicate discovery results,
* persist only verified graph relationships,
* preserve source/access provenance,
* verify graph, knowledge, cache, and visual outputs,
* handle busy/configuration errors explicitly,
* checkpoint meaningful analysis state,
* never claim completion without verification.

The canonical lifecycle is:

**Scope → Inspect → Classify → Session Check → Refresh → Discover → Filter → Persist → Verify → Checkpoint → Report**