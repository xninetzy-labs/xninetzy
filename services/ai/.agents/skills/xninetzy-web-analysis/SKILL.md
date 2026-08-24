# Xninetzy Web Analysis OS

```yaml
---
name: xninetzy-web-analysis
description: General-purpose, safety-first web and portal analysis operating system for allowlisted academic portals, authenticated applications, and dynamic public websites. Performs bounded structural discovery, read-only analysis, graph relationship creation, knowledge ingestion, public-page visual capture, evidence verification, freshness tracking, and cross-session checkpointing while strictly separating portal sessions, identities, credentials, academic records, and authenticated visual data. Never mutates target systems, submits forms, bypasses human verification, or captures authenticated personal pages visually.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "scope -> inspect -> classify -> session-check -> refresh -> discover -> filter -> persist -> verify -> checkpoint -> report"
---
```

# Xninetzy Web Analysis OS

This skill is the **read-only web analysis and portal discovery layer** for Xninetzy.

It provides one consistent workflow for:

* academic portals,
* institutional SSO systems,
* LMS platforms,
* student portals,
* questionnaire portals,
* dynamic public websites,
* technical documentation sites,
* structured web applications.

Its purpose is to understand **web structure, navigation, available modules, public content, and evidence relationships** without mutating the target system.

The core principle is:

> **Analyze structure, preserve evidence, keep sessions isolated, stop at human verification, and never turn analysis into unauthorized interaction.**

The canonical lifecycle is:

**Scope → Inspect → Classify → Session Check → Refresh → Discover → Filter → Persist → Verify → Checkpoint → Report**

---

# 1. Scope

Use this skill for:

* portal structure analysis,
* page discovery,
* navigation mapping,
* module/endpoint inventory,
* public web discovery,
* authenticated read-only structural analysis,
* Graph RAG web-page mapping,
* knowledge ingestion of permitted page text,
* public-page visual capture,
* analysis-cache verification,
* cross-session analysis checkpoints.

Do **not** use it for:

* portal mutation,
* form submission,
* assignment uploads,
* KRS submission,
* questionnaire completion,
* CAPTCHA solving,
* credential extraction,
* authenticated personal-page screenshots,
* bypassing institutional controls.

Those actions belong to the relevant domain-specific skills and approval workflows.

---

# 2. Allowlisted Portal Model

The analyzer may operate on explicitly supported portal presets such as:

```text
hebat
mahasiswa
uacc
qa
```

and on permitted dynamic public HTTPS sites.

A portal preset should define:

```yaml
site_slug:
allowed_hosts:
seed_urls:
authentication_mode:
authenticated_analysis_allowed:
visual_capture_allowed:
depth_limit:
max_pages:
```

Do not invent an allowlist entry for an unverified host.

---

# 3. Portal Isolation

Every portal is its own security and state domain.

Example:

```text
HEBAT
≠ Cyber Campus
≠ UACC / UnairSatu
≠ QA
```

Never mix:

* cookies,
* encrypted sessions,
* credentials,
* identities,
* challenge IDs,
* cache namespaces,
* analysis records,
* screenshots,
* academic records.

A shared owner does not make portal sessions interchangeable.

---

# 4. Source-of-Truth Hierarchy

For web analysis, prefer:

```text
current verified portal response
        ↓
typed analyzer result
        ↓
verified analysis cache
        ↓
Graph RAG persistence
        ↓
knowledge persistence
        ↓
memory/checkpoint
        ↓
historical analysis
```

Historical analysis is useful for change detection, but it does not override the current portal.

---

# 5. Safety Invariants

The web analyzer must enforce:

### Read-only operation

Use:

**GET / HEAD**

for ordinary analysis.

Mutation routes should be blocked at the analyzer boundary.

### Human verification boundary

When CAPTCHA or equivalent human verification appears:

**stop.**

### Secret protection

Never persist or expose:

* credentials,
* cookies,
* tokens,
* private query values,
* academic record values,
* session identifiers.

### Visual privacy boundary

Visual capture is limited to:

**public/login pages only.**

Do not capture authenticated personal pages.

### Bounded discovery

Do not crawl an entire portal unintentionally.

Use small bounded depth and page limits unless the target is a genuinely public documentation site where larger bounds are justified.

---

# 6. Human Verification

Human verification includes:

* CAPTCHA,
* reCAPTCHA,
* math challenges,
* challenge-response login,
* other anti-automation controls.

When detected:

```text
page identified
↓
verification detected
↓
record safe structural observation
↓
stop analysis
↓
return control to owner
```

Never:

* OCR the CAPTCHA,
* solve it automatically,
* infer the answer,
* repeatedly poll challenge state,
* bypass the gate.

The portal-specific authentication skill owns the manual verification process.

---

# 7. Standard Workflow

Use:

```text
1. web_analysis_status(site_slug)

2. web_analysis_refresh(
     site_slug,
     authenticated=<only when an approved encrypted session exists>
   )

3. web_analysis_catalog(site_slug)

4. web_discover(
     seed_url,
     ingest_to_knowledge=true,
     capture_visual=true
   )

5. optional public pixelrag_capture

6. verify:
     web_analysis_status
     graph_v3_stats / graph_v3_search

7. checkpoint and report
```

Only perform the steps relevant to the request.

---

# 8. Step 1: Analysis Status

Start by checking:

```text
web_analysis_status(site_slug)
```

Determine:

* enabled/disabled,
* current analysis state,
* cache freshness,
* last refresh,
* active lease,
* authenticated-session availability where applicable.

Do not start an expensive refresh when an adequately fresh verified result already exists.

---

# 9. Step 2: Refresh

Refresh structural analysis when:

* cache is stale,
* user requests current analysis,
* portal structure may have changed,
* an important page is missing,
* current session state differs from the cached analysis.

For authenticated analysis, require:

* `WEB_ANALYSIS_ENABLED`,
* `WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED`,
* existing encrypted local session,
* correct portal identity.

Do not silently downgrade an authenticated request to unauthenticated analysis when authenticated evidence is essential.

---

# 10. Configuration Errors

If the analyzer returns:

```text
configuration_required
```

surface the exact missing/disabled configuration.

Do not silently degrade to a weaker mode when the requested result depends on authenticated analysis.

Example:

> Authenticated analysis is unavailable because the authenticated-crawl capability is disabled.

---

# 11. Authentication Dependency

If an authenticated session is required but missing:

```text
analysis request
↓
session missing
↓
portal-specific login workflow
↓
manual CAPTCHA if required
↓
encrypted local session established
↓
retry analysis once
```

Do not implement portal-specific login logic in the generic analyzer.

Use:

* `xninetzy-uacc` for UACC,
* `cyber-campus` for Cyber Campus,
* `hebat-academic` for HEBAT.

---

# 12. Retry Policy

Retries must be bounded.

For login dependencies where the portal-specific workflow allows CAPTCHA retry:

```text
fresh login
→ owner receives CAPTCHA
→ owner answers
→ submit
→ verify
```

Use the configured maximum retry limit.

Never retry an expired challenge.

Never retry blindly after uncertain external state.

---

# 13. Step 3: Catalog

After refresh:

```text
web_analysis_catalog(site_slug)
```

Inspect:

* pages,
* sections,
* navigation,
* modules,
* discovered endpoints,
* analysis metadata,
* access classification.

The catalog is structural evidence, not necessarily semantic content.

---

# 14. Step 4: Public Discovery

For public discovery:

```text
web_discover(
  seed URL,
  ingest_to_knowledge=true,
  capture_visual=true
)
```

Discovery may produce:

* `web_page` graph nodes,
* `links_to` relationships,
* page-text knowledge records,
* public visual tiles.

All outputs must remain within the configured domain and crawl bounds.

---

# 15. Discovery Boundaries

Default portal discovery should remain small:

```text
depth: 0–1
max_pages: bounded
```

Larger limits are appropriate only for genuinely public documentation sites or another explicitly authorized public corpus.

Do not expand crawl depth simply because more pages are available.

---

# 16. Public vs Authenticated Content

Classify each page:

```text
public
login
authenticated
unknown
```

Visual capture is permitted only for:

```text
public
login
```

Authenticated personal pages receive:

```text
structural analysis only
```

---

# 17. PixelRAG Visual Capture

Public visual capture can support:

* layout analysis,
* visual navigation,
* UI documentation,
* public-page comparison,
* page-design inspection.

It must never be used to capture:

* grades,
* schedules,
* names,
* KRS data,
* private dashboard content,
* personal academic records,
* authenticated user pages.

Images can expose information that text filtering misses.

---

# 18. Visual Capture Safety

Before capturing:

1. determine page access class,
2. verify page is public/login,
3. verify the capture target,
4. capture only permitted pages,
5. inspect output for accidental sensitive information where appropriate.

If access classification is uncertain:

**do not capture visually.**

---

# 19. Analysis Cache

The analysis cache should store structure such as:

* modules,
* routes,
* endpoint patterns,
* navigation,
* page identity,
* access classification,
* structural metadata.

It should not store:

* credentials,
* cookies,
* token values,
* academic record values,
* private form submissions.

The cache is a **structural model**, not a content database.

---

# 20. Discovery Output

Persist the discovery result under the configured directory:

```text
<WEB_ANALYSIS_DATA_DIR>/discoveries/<site_slug>/latest.json
```

Treat `latest.json` as a generated cache artifact.

Verify that it exists and is readable before reporting successful persistence.

---

# 21. Graph RAG Integration

Public discovery may create:

```text
web_page
```

nodes and:

```text
links_to
```

edges.

Conceptually:

```text
Page A
  ── links_to ──>
Page B
  ── links_to ──>
Page C
```

Only create graph relationships from actually observed navigation or verified discovery results.

Never infer links from semantic similarity alone.

---

# 22. Graph Evidence

A graph relationship should preserve:

* source page,
* target page,
* relationship type,
* discovery/source context,
* timestamp/version where relevant.

Do not create factual relationships from:

* page-name similarity,
* embeddings alone,
* search rank,
* guessed navigation.

---

# 23. Knowledge Ingestion

When enabled:

```text
web_discover
→ inspect page text
→ ingest permitted text
→ attach source/provenance
```

Knowledge ingestion should preserve:

* source URL,
* page identity,
* access class,
* retrieval time,
* provider/discovery context when available.

Do not ingest sensitive academic values.

---

# 24. Knowledge Safety

Before ingestion, exclude:

* credentials,
* cookies,
* tokens,
* session secrets,
* personal academic records,
* sensitive query parameters,
* private authenticated values.

When a page contains mixed public and sensitive material:

**ingest only the non-sensitive portion that is explicitly safe.**

---

# 25. Evidence Levels

Classify web-analysis observations:

```text
direct
derived
historical
unknown
```

### Direct

Observed in the current analysis.

### Derived

Reasoned from current observations.

### Historical

Known from previous analysis.

### Unknown

Not sufficiently verified.

Do not present derived or historical structure as though it were directly observed now.

---

# 26. Cross-Portal Evidence

Keep source identity attached to every observation.

Example:

```yaml
site: uacc
page: /mhs
observation: "login page contains CAPTCHA"
```

is separate from:

```yaml
site: mahasiswa
page: /login
observation: "student portal login page"
```

Never flatten both into one generic "UNAIR login" record.

---

# 27. Portal Presets

## HEBAT

Use for:

* Moodle structure,
* activity pages,
* course navigation,
* material discovery.

Do not analyze:

* assignment upload,
* submission,
* grading mutation.

Those belong to HEBAT Academic.

---

## Cyber Campus / `mahasiswa`

Use for:

* read-only page structure,
* navigation,
* academic page discovery.

KRS submission remains outside the analyzer.

Use `cyber-campus` for KRS operations.

---

## UACC

Use for:

* SSO structure,
* login page discovery,
* authorized authenticated structural analysis.

Typical seed:

```text
/mhs
```

Allowed hosts may include:

```text
uacc.unair.ac.id
unairsatu.unair.ac.id
```

Use `xninetzy-uacc` for manual CAPTCHA authentication.

---

## QA

Use for:

* allowed structural analysis,
* public/login analysis,
* authenticated structural analysis only when explicitly supported.

Questionnaire completion is outside this skill.

---

# 28. Public Dynamic Sites

For genuinely public sites:

* use HTTPS where appropriate,
* respect configured domain boundaries,
* keep depth bounded by default,
* avoid forms that mutate state,
* avoid login bypass,
* capture public visuals only,
* ingest public text with provenance.

Larger crawl limits may be justified for documentation sites.

---

# 29. Domain Boundary

Do not cross from an allowlisted site into arbitrary external domains merely because a page links there.

Classify external links:

```text
same_allowlisted_domain
allowed_related_domain
external_unknown
```

Only continue discovery where the configured policy permits it.

---

# 30. Rate and Resource Control

Avoid unnecessarily expensive crawling.

Use:

* bounded page limits,
* bounded depth,
* fresh cache reuse,
* deduplication,
* one retry for temporary lease conflicts,
* provider/tool health where available.

Do not repeatedly refresh a stable public site without a reason.

---

# 31. Lease / Busy Handling

If the analyzer returns:

```text
busy
```

then:

1. recognize that another analysis holds the lease,
2. avoid concurrent duplicate work,
3. retry once according to the supported workflow,
4. stop if the resource remains unavailable.

Do not spawn parallel duplicate crawls against the same portal.

---

# 32. Human Verification Errors

If the analyzer returns:

```text
human_verification_required
```

report:

* affected site,
* affected page,
* verification state,
* what analysis was completed before stopping.

Then stop.

Do not continue discovery through another route intended to avoid the challenge.

---

# 33. Repeated Page Failures

When a page repeatedly fails:

* record the error class,
* identify the affected page,
* avoid persisting sensitive error details,
* continue only if the remaining analysis remains valid.

Example:

> Page `/dashboard` returned repeated access errors. Error details were not persisted. Public structure analysis remains valid.

---

# 34. Failure Classification

Useful failure classes:

```text
configuration_required
busy
human_verification_required
authentication_missing
authentication_expired
not_found
forbidden
timeout
network_error
parser_error
unsupported_structure
unknown
```

Each error should lead to an appropriate next action rather than blind retry.

---

# 35. Verification Workflow

After discovery:

```text
web_analysis_status
+
graph_v3_stats
+
graph_v3_search
```

Verify:

* analysis completed,
* expected pages exist,
* graph nodes were persisted where requested,
* relationships exist where observed,
* knowledge ingestion completed where requested,
* visual captures exist where permitted.

Do not claim graph persistence because the discovery tool merely returned candidate pages.

---

# 36. Result Classification

After analysis:

```text
analysis_success
partial_analysis
blocked
failed
uncertain
```

### analysis_success

Requested analysis completed and verified.

### partial_analysis

Some pages failed, but the requested evidence is still adequately covered.

### blocked

A required configuration/session/human verification step prevented completion.

### failed

The core analysis did not complete.

### uncertain

External or persistence state could not be confirmed.

---

# 37. Freshness

Track analysis freshness:

```text
fresh
stale
unknown
```

Refresh when:

* the user requests current structure,
* a portal changed,
* cached results are old,
* current navigation matters,
* authenticated structure changed.

Do not silently treat yesterday's analysis as today's portal structure when current verification matters.

---

# 38. Change Detection

When historical analysis exists:

```text
previous catalog
vs
current catalog
```

identify:

* new pages,
* removed pages,
* renamed pages,
* changed navigation,
* changed forms,
* changed access classification.

Preserve historical records.

Do not overwrite them without retaining enough provenance to understand the change.

---

# 39. Memory Integration

After a meaningful run, checkpoint:

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

For web-analysis-specific continuity, include:

* site slug,
* analysis version,
* cache location,
* graph state,
* knowledge state,
* visual-capture state,
* unresolved pages.

Never store secrets.

---

# 40. Research Memory Integration

If the analysis contributes to a research project:

```text
Web Analysis
↓
verified web evidence
↓
Research Memory
↓
claim/source ledger
```

Do not treat raw page discovery as a research conclusion.

---

# 41. Artifact Integration

Useful web-analysis artifacts may include:

* `latest.json`,
* catalog exports,
* visual tiles,
* structural reports,
* Mermaid diagrams,
* portal overview notes.

Store exact paths only after verifying them.

---

# 42. Security and Privacy

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

---

# 43. Credential and Session Separation

The analyzer should receive only the minimum session context required through the supported adapter.

It should never:

* read browser cookies directly,
* extract credentials,
* copy session tokens into analysis state,
* reuse another portal's session.

---

# 44. Read-Only Enforcement

The analyzer should reject mutation-oriented routes before they reach the target.

Conceptually:

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

---

# 45. No Form Submission

The analyzer must not:

* click submit,
* send POST mutations,
* upload files,
* finalize academic actions,
* fill questionnaires,
* alter KRS,
* alter course state.

Even if the page exposes a visible form, analysis remains structural/read-only.

---

# 46. Public Visual Safety

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

When in doubt:

**structural analysis only.**

---

# 47. Completion Contract

Every meaningful web-analysis run should return the relevant subset of:

**Site / portal identity**

**Analysis mode**

* public,
* authenticated read-only,
* blocked.

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

---

# 48. Standard Analysis Report

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

---

# 49. Operating Rules

The system must:

**use one consistent read-only workflow across supported portals,**

**keep all portal sessions and identities separate,**

**enforce GET/HEAD-only analysis,**

**stop at human verification,**

**never solve CAPTCHA automatically,**

**keep credentials and private portal values out of persistence,**

**capture visuals only from public/login pages,**

**bound crawl depth and page count,**

**reuse fresh analysis cache,**

**deduplicate discovery results,**

**persist only verified graph relationships,**

**preserve source/access provenance,**

**verify graph, knowledge, cache, and visual outputs,**

**handle busy/configuration errors explicitly,**

**checkpoint meaningful analysis state,**

**never claim completion without verification.**

The canonical lifecycle is:

**Scope → Inspect → Classify → Session Check → Refresh → Discover → Filter → Persist → Verify → Checkpoint → Report**

The central objective is:

> **Build a trustworthy structural map of authorized web systems without turning analysis into interaction, preserving evidence and privacy while keeping every portal session strictly isolated and every result verifiable.**
