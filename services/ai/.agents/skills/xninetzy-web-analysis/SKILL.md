---
name: xninetzy-web-analysis
description: "Consistent cross-portal web analysis workflow for Xninetzy portals (hebat, mahasiswa/cyber campus, uacc, qa, and dynamic public sites): structural analyzer refresh, discovery graphing into Graph RAG, knowledge ingestion, PixelRAG visual capture of public pages only, and memory checkpointing."
metadata:
  owner: xninetzy
  version: "1.0.0"
---

# Portal Web Analysis & Graphing

## Scope

One consistent runbook for every allowlisted portal preset (`hebat`,
`mahasiswa`, `uacc`, `qa`) and dynamic public HTTPS sites. The workflow is
read-only structure analysis plus evidence persistence; it never mutates a
portal, never submits forms, and never solves human verification challenges.

Portal sessions stay strictly separate: UACC (`uacc.unair.ac.id` /
`unairsatu.unair.ac.id`) is not Cyber Campus (`mahasiswa.unair.ac.id`), is not
HEBAT Moodle, and is not QA. Never mix storage states, cookies, or identities.

## Safety invariants

* GET/HEAD only; mutation routes are blocked client-side by the analyzer.
* Stop immediately when human verification is detected; return control to the
  owner. Never solve CAPTCHA automatically.
* Credential, cookie, token, query value, and academic record values are never
  written to analysis output, graph nodes, knowledge chunks, or screenshots.
* PixelRAG captures are for public/login pages only. Never screenshot an
  authenticated personal page: tiles are images and can leak names, grades,
  or schedules. Authenticated pages get structural analysis only.
* Analysis cache stores page structure (modules, endpoints), never content
  values.

## Standard workflow

```text
1. web_analysis_status(site_slug)
2. web_analysis_refresh(site_slug, authenticated=True when an encrypted
   session exists locally, else authenticated=False)
3. web_analysis_catalog(site_slug)
4. web_discover(seed URL, ingest_to_knowledge=True, capture_visual=True)
   - creates GraphRAG V3 web_page nodes + links_to edges
   - ingests page text as knowledge sources
   - captures public-page tiles via pixelshot
5. optional standalone pixelrag_capture for missing public pages
6. verify: web_analysis_status, graph_v3_stats / graph_v3_search
7. memory_add checkpoint + report
```

Notes per step:

* Step 2 requires `WEB_ANALYSIS_ENABLED` and, for authenticated crawls,
  `WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED` plus an existing encrypted local
  session. If the session is missing, run the portal login flow first
  (manual CAPTCHA via the portal-specific skill) and retry once. If CAPTCHA
  fails, auto-retry up to 3 times before stopping.
* Step 4 discovery runs without a session (public context). Portals whose seed
  page is a login/CAPTCHA gate will stop at human verification after recording
  that single page node; this is expected and correct.
* Discovery saves `latest.json` under
  `<WEB_ANALYSIS_DATA_DIR>/discoveries/<site_slug>/`.
* Keep `depth` small (0-1) and `max_pages` bounded for portal presets; use
  larger bounds only for genuinely public documentation sites.

## Portal specifics

* `hebat`: Moodle structure; activity pages read-only; assignment upload and
  submission excluded from analysis.
* `mahasiswa` (Cyber Campus): KRS submit is competitive and protected; only
  GET pages are analyzed.
* `uacc`: SSO login uses a manual math CAPTCHA; `/mhs` is the seed. Allowed
  hosts include `unairsatu.unair.ac.id`. See `xninetzy-uacc` for login.
* `qa`: portal-owned reCAPTCHA; session must be captured headed by the owner;
  questionnaire filling is never part of analysis.

## Failure handling

* `configuration_required`: surface the exact setting that is off; do not
  degrade into unauthenticated crawling when the request needs session data.
* `busy`: another analysis holds the lease; wait and retry once.
* `human_verification_required`: report which page triggered it and stop.
* **CAPTCHA auto-retry**: when portal login is needed and CAPTCHA fails or
  expires, automatically start new login → deliver CAPTCHA to owner → owner
  answers → submit → max 3 retries; human verification gate is never removed.
* Repeated failures on one page: log error type only; sensitive details are
  never persisted.
