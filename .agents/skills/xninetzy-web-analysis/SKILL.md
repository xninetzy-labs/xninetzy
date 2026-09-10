---
name: xninetzy-web-analysis
description: Safety-first web and portal analysis operating system for allowlisted academic portals, authenticated applications, and dynamic public websites. Use for bounded structural discovery, read-only analysis, graph relationship creation, knowledge ingestion, public-page visual capture, evidence verification, freshness tracking, and cross-session checkpointing.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "scope -> inspect -> classify -> session-check -> refresh -> discover -> filter -> persist -> verify -> checkpoint -> report"
---

# Xninetzy Web Analysis OS

This skill is the **read-only web analysis and portal discovery layer** for Xninetzy. It provides one consistent workflow for academic portals, institutional SSO systems, LMS platforms, student portals, questionnaire portals, dynamic public websites, technical documentation sites, and structured web applications.

Its purpose is to understand **web structure, navigation, available modules, public content, and evidence relationships** without mutating the target system.

The core principle is:

> **Analyze structure, preserve evidence, keep sessions isolated, stop at human verification, and never turn analysis into unauthorized interaction.**

The canonical lifecycle is:

**Scope → Inspect → Classify → Session Check → Refresh → Discover → Filter → Persist → Verify → Checkpoint → Report**

## Scope

Use this skill for:

* portal structure analysis,
* page discovery,
* navigation mapping,
* module and endpoint inventory,
* public web discovery,
* authenticated read-only structural analysis,
* Graph RAG web-page mapping,
* knowledge ingestion of permitted page text,
* public-page visual capture,
* analysis-cache verification,
* cross-session analysis checkpoints.

Do not use it for portal mutation, form submission, assignment uploads, KRS submission, questionnaire completion, CAPTCHA solving, credential extraction, authenticated personal-page screenshots, or bypassing institutional controls. Those actions belong to the relevant domain-specific skills and approval workflows.

## When to use

* the user asks to analyze a public or allowlisted portal structure,
* the user wants a page catalog, navigation map, or Mermaid structure diagram of an allowlisted site,
* the user asks to ingest permitted page text into the knowledge base,
* the user asks for public-page visual capture for documentation.

## When NOT to use

* HEBAT workflow beyond structural analysis — use `hebat-academic`;
* Cyber Campus operations — use `xninetzy-cyber-campus`;
* UACC operations — use `xninetzy-uacc`;
* questionnaire completion — never use this skill for that.

## Allowlisted portal model

The analyzer may operate on explicitly supported portal presets such as `hebat`, `mahasiswa`, `uacc`, and `qa`, and on permitted dynamic public HTTPS sites.

A portal preset should define `site_slug`, `allowed_hosts`, `seed_urls`, `authentication_mode`, `authenticated_analysis_allowed`, `visual_capture_allowed`, `depth_limit`, and `max_pages`. Do not invent an allowlist entry for an unverified host.

## Portal isolation

Every portal is its own security and state domain. Never mix cookies, encrypted sessions, credentials, identities, challenge IDs, cache namespaces, analysis records, screenshots, or academic records. A shared owner does not make portal sessions interchangeable.

## Source-of-truth hierarchy

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

## Safety invariants

The web analyzer must enforce:

* **Read-only operation** — use GET / HEAD for ordinary analysis. Mutation routes should be blocked at the analyzer boundary.
* **Human verification boundary** — when CAPTCHA or equivalent human verification appears, stop.
* **Secret protection** — never persist or expose credentials, cookies, tokens, private query values, academic record values, or session identifiers.
* **Visual privacy boundary** — visual capture is limited to public and login pages only. Do not capture authenticated personal pages.
* **Bounded discovery** — do not crawl an entire portal unintentionally. Use small bounded depth and page limits unless the target is a genuinely public documentation site where larger bounds are justified.

## Human verification

Human verification includes CAPTCHA, reCAPTCHA, math challenges, challenge-response login, and other anti-automation controls. When detected:

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

Never OCR the CAPTCHA, solve it automatically, infer the answer, repeatedly poll challenge state, or bypass the gate. The portal-specific authentication skill owns the manual verification process.

## Standard workflow

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

## Core workflow

1. **Scope.** Identify the allowlisted target, allowed hosts, authentication mode, and depth/page limits.
2. **Inspect.** Run `web_analysis_status(site_slug)` to determine whether a fresh verified result already exists.
3. **Classify.** Distinguish public, login, authenticated, and unknown access. Visual capture is permitted only for public and login pages.
4. **Session check.** Determine whether an approved encrypted local session is required and present. Surface missing configuration errors explicitly rather than silently degrading.
5. **Refresh.** Refresh structural analysis when the cache is stale, the user requests current analysis, the portal may have changed, or an important page is missing.
6. **Discover.** Run bounded public discovery within configured depth and page limits. Persist only non-sensitive page text and metadata.
7. **Filter.** Exclude credentials, cookies, tokens, session secrets, personal academic records, sensitive query parameters, and private authenticated values before ingestion.
8. **Persist.** Create graph relationships from observed navigation, ingest permitted text, and capture public visuals.
9. **Verify.** Confirm graph nodes, knowledge ingestion, visual captures, and cache existence rather than trusting discovery tool responses.
10. **Checkpoint.** Persist analysis state when the work is material.
11. **Report.** Return site identity, analysis mode, freshness, pages discovered, structural findings, graph state, knowledge ingestion state, visual capture state, verification, blockers, artifacts, and next action.

## Public vs authenticated content

Classify each page:

```text
public
login
authenticated
unknown
```

Visual capture is permitted only for `public` and `login`. Authenticated personal pages receive structural analysis only.

## PixelRAG visual capture

Public visual capture can support layout analysis, visual navigation, UI documentation, public-page comparison, and page-design inspection. It must never be used to capture grades, schedules, names, KRS data, private dashboard content, personal academic records, or authenticated user pages. Images can expose information that text filtering misses.

## Visual capture safety

Before capturing:

1. determine page access class,
2. verify page is public/login,
3. verify the capture target,
4. capture only permitted pages,
5. inspect output for accidental sensitive information where appropriate.

If access classification is uncertain, do not capture visually.

## Analysis cache

The analysis cache should store structure such as modules, routes, endpoint patterns, navigation, page identity, access classification, and structural metadata. It should not store credentials, cookies, token values, academic record values, or private form submissions. The cache is a **structural model**, not a content database.

## Discovery output

Persist the discovery result under the configured directory:

```text
<WEB_ANALYSIS_DATA_DIR>/discoveries/<site_slug>/latest.json
```

Treat `latest.json` as a generated cache artifact. Verify that it exists and is readable before reporting successful persistence.

## Graph RAG integration

Public discovery may create `web_page` nodes and `links_to` edges. Only create graph relationships from actually observed navigation or verified discovery results. Never infer links from semantic similarity alone.

## Graph evidence

A graph relationship should preserve:

* source page,
* target page,
* relationship type,
* discovery/source context,
* timestamp/version where relevant.

Do not create factual relationships from page-name similarity, embeddings alone, search rank, or guessed navigation.

## Knowledge ingestion

When enabled:

```text
web_discover
→ inspect page text
→ ingest permitted text
→ attach source/provenance
```

Knowledge ingestion should preserve source URL, page identity, access class, retrieval time, and provider/discovery context when available. Do not ingest sensitive academic values.

## Knowledge safety

Before ingestion, exclude credentials, cookies, tokens, session secrets, personal academic records, sensitive query parameters, and private authenticated values. When a page contains mixed public and sensitive material, ingest only the non-sensitive portion that is explicitly safe.

## Evidence levels

Classify web-analysis observations:

```text
direct
derived
historical
unknown
```

* **Direct** — observed in the current analysis.
* **Derived** — reasoned from current observations.
* **Historical** — known from previous analysis.
* **Unknown** — not sufficiently verified.

Do not present derived or historical structure as though it were directly observed now.

## Portal presets

### HEBAT

Use for Moodle structure, activity pages, course navigation, and material discovery. Do not analyze assignment upload, submission, or grading mutation. Those belong to HEBAT Academic.

### Cyber Campus / `mahasiswa`

Use for read-only page structure, navigation, and academic page discovery. KRS submission remains outside the analyzer. Use `xninetzy-cyber-campus` for KRS operations.

### UACC

Use for SSO structure, login page discovery, and authorized authenticated structural analysis. Typical seed: `/mhs`. Allowed hosts may include `uacc.unair.ac.id` and `unairsatu.unair.ac.id`. Use `xninetzy-uacc` for manual CAPTCHA authentication.

### QA

Use for allowed structural analysis, public/login analysis, and authenticated structural analysis only when explicitly supported. Questionnaire completion is outside this skill.

## Public dynamic sites

For genuinely public sites:

* use HTTPS where appropriate,
* respect configured domain boundaries,
* keep depth bounded by default,
* avoid forms that mutate state,
* avoid login bypass,
* capture public visuals only,
* ingest public text with provenance.

Larger crawl limits may be justified for documentation sites.

## Domain boundary

Do not cross from an allowlisted site into arbitrary external domains merely because a page links there.

Classify external links:

```text
same_allowlisted_domain
allowed_related_domain
external_unknown
```

Only continue discovery where the configured policy permits it.

## Rate and resource control

Avoid unnecessarily expensive crawling. Use bounded page limits, bounded depth, fresh cache reuse, deduplication, one retry for temporary lease conflicts, and provider/tool health where available. Do not repeatedly refresh a stable public site without a reason.

## Lease / busy handling

If the analyzer returns `busy`, recognize that another analysis holds the lease, avoid concurrent duplicate work, retry once according to the supported workflow, and stop if the resource remains unavailable. Do not spawn parallel duplicate crawls against the same portal.

## Human verification errors

If the analyzer returns `human_verification_required`, report affected site, affected page, verification state, and what analysis was completed before stopping. Then stop. Do not continue discovery through another route intended to avoid the challenge.

## Repeated page failures

When a page repeatedly fails, record the error class, identify the affected page, avoid persisting sensitive error details, and continue only if the remaining analysis remains valid.

## Failure classification

Useful failure classes: `configuration_required`, `busy`, `human_verification_required`, `authentication_missing`, `authentication_expired`, `not_found`, `forbidden`, `timeout`, `network_error`, `parser_error`, `unsupported_structure`, `unknown`. Each error should lead to an appropriate next action rather than blind retry.

## Change detection

When historical analysis exists, compare `previous catalog` against `current catalog` and identify new pages, removed pages, renamed pages, changed navigation, changed forms, and changed access classification. Preserve historical records. Do not overwrite them without retaining enough provenance to understand the change.

## Freshness

Track analysis freshness:

```text
fresh
stale
unknown
```

Refresh when the user requests current structure, a portal changed, cached results are old, current navigation matters, or authenticated structure changed. Do not silently treat yesterday's analysis as today's portal structure when current verification matters.

## Reference map

* `references/policies.md` — security and privacy, credential and session separation, read-only enforcement, no form submission, public visual safety, completion contract, standard analysis report, and operating rules.
* `references/discovery-and-integration.md` — knowledge ingestion, knowledge safety, evidence levels, cross-portal evidence, portal presets, public dynamic sites, domain boundary, rate control, lease handling, human verification errors, repeated page failures, failure classification, verification workflow, result classification, freshness, change detection, memory integration, research memory integration, and artifact integration.

## Routing

* HEBAT workflow → `hebat-academic`.
* Cyber Campus operations → `xninetzy-cyber-campus`.
* UACC operations → `xninetzy-uacc`.
* Obsidian structure → `xninetzy-obsidian-orchestra`.
* Graph relationships → `graph-rag`.
* Cross-session continuity → `xninetzy-memory`.

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

The central objective is:

> **Build a trustworthy structural map of authorized web systems without turning analysis into interaction, preserving evidence and privacy while keeping every portal session strictly isolated and every result verifiable.**