# Xninetzy Web Analysis — Discovery, Integration, and Verification

This reference expands knowledge ingestion, knowledge safety, evidence levels, cross-portal evidence, portal presets, public dynamic sites, domain boundary, rate control, lease handling, human verification errors, repeated page failures, failure classification, verification workflow, result classification, freshness, change detection, memory integration, research memory integration, and artifact integration. Read it when running discovery, persisting outputs, or producing integration evidence.

## Knowledge ingestion

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

## Knowledge safety

Before ingestion, exclude:

* credentials,
* cookies,
* tokens,
* session secrets,
* personal academic records,
* sensitive query parameters,
* private authenticated values.

When a page contains mixed public and sensitive material, ingest only the non-sensitive portion that is explicitly safe.

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

## Cross-portal evidence

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

If the analyzer returns `busy`, then:

1. recognize that another analysis holds the lease,
2. avoid concurrent duplicate work,
3. retry once according to the supported workflow,
4. stop if the resource remains unavailable.

Do not spawn parallel duplicate crawls against the same portal.

## Human verification errors

If the analyzer returns `human_verification_required`, report affected site, affected page, verification state, and what analysis was completed before stopping. Then stop. Do not continue discovery through another route intended to avoid the challenge.

## Repeated page failures

When a page repeatedly fails, record the error class, identify the affected page, avoid persisting sensitive error details, and continue only if the remaining analysis remains valid.

## Failure classification

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

## Verification workflow

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

## Result classification

After analysis:

```text
analysis_success
partial_analysis
blocked
failed
uncertain
```

* **analysis_success** — requested analysis completed and verified.
* **partial_analysis** — some pages failed, but the requested evidence is still adequately covered.
* **blocked** — a required configuration/session/human verification step prevented completion.
* **failed** — the core analysis did not complete.
* **uncertain** — external or persistence state could not be confirmed.

## Change detection

When historical analysis exists, compare `previous catalog` against `current catalog` and identify new pages, removed pages, renamed pages, changed navigation, changed forms, and changed access classification. Preserve historical records. Do not overwrite them without retaining enough provenance to understand the change.

## Memory integration

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

For web-analysis-specific continuity, include site slug, analysis version, cache location, graph state, knowledge state, visual-capture state, and unresolved pages. Never store secrets.

## Research memory integration

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

## Artifact integration

Useful web-analysis artifacts may include `latest.json`, catalog exports, visual tiles, structural reports, Mermaid diagrams, and portal overview notes. Store exact paths only after verifying them.

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