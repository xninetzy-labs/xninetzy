---

name: xninetzy-web-analysis

description: Safety-first read-only web and portal analysis operating system for explicitly allowlisted academic portals, authenticated applications, institutional SSO systems, documentation sites, and dynamic public websites. Use for bounded structural discovery, navigation and module mapping, permitted public-page analysis, evidence and provenance tracking, safe knowledge ingestion, public visual capture, freshness-aware cache management, change detection, and cross-session analysis checkpoints. Never use for mutation, form submission, CAPTCHA solving, credential extraction, access-control bypass, or authenticated personal-page visual capture.

metadata:
        scope: general
        owner: xninetzy
        language: en
        version: "3.0.0"
        lifecycle: "scope -> authorize -> inspect -> classify -> session-check -> refresh -> discover -> filter -> persist -> verify -> checkpoint -> report"
-----------------------------------------------------------------------------------------------------------------------------------------------------

# Xninetzy Web Analysis OS

## 1. Purpose

This skill is the read-only web analysis and portal discovery control layer for Xninetzy.

It provides one consistent operating model for:

* academic portals
* LMS platforms
* institutional SSO systems
* student portals
* questionnaire portals
* public documentation sites
* public institutional websites
* dynamic web applications
* permitted authenticated structural analysis

Its purpose is to build a trustworthy structural representation of an authorized web system without mutating the target.

The operating principle is:

> **Scope first. Observe only. Preserve provenance. Isolate sessions. Stop at human verification. Verify persistence. Never convert analysis into unauthorized interaction.**

---

# 2. Core Lifecycle

The canonical lifecycle is:

```text id="9n2nq7"
Scope
  ↓
Authorize
  ↓
Inspect
  ↓
Classify
  ↓
Session Check
  ↓
Refresh
  ↓
Discover
  ↓
Filter
  ↓
Persist
  ↓
Verify
  ↓
Checkpoint
  ↓
Report
```

Every operation should execute only the stages relevant to the requested task.

---

# 3. Scope

Use this skill for:

* portal structure analysis
* navigation mapping
* page discovery
* module inventory
* read-only endpoint/page inventory
* public website analysis
* permitted authenticated structural analysis
* public-page visual capture
* Graph RAG web-page relationship creation
* permitted knowledge ingestion
* analysis-cache verification
* historical change detection
* cross-session analysis checkpoints

---

# 4. Explicit Non-Goals

Never use this skill for:

* form submission
* questionnaire completion
* assignment upload
* assignment submission
* KRS submission
* profile modification
* academic-record modification
* grade modification
* sending messages
* creating content
* deleting content
* credential extraction
* CAPTCHA solving
* CAPTCHA OCR
* authentication bypass
* access-control bypass
* CSRF bypass
* rate-limit bypass
* exploiting application vulnerabilities
* authenticated personal-page screenshots
* collecting private academic records

Those operations belong to explicit domain-specific workflows with their own authorization and human-approval controls.

---

# 5. Authorization Model

Analysis requires an explicit target scope.

A valid target should provide, directly or through a trusted preset:

```text id="x5zqfr"
site_slug
allowed_hosts
seed_urls
authentication_mode
authenticated_analysis_allowed
visual_capture_allowed
depth_limit
max_pages
```

Do not invent an allowlist entry.

Do not broaden an allowlist because a discovered page links to another host.

Do not treat ownership of one portal as authorization for another portal.

---

# 6. Scope Enforcement

Before every discovery operation:

1. resolve target host
2. normalize URL
3. compare host against allowlist
4. classify access mode
5. verify operation is permitted
6. apply depth limit
7. apply page limit
8. reject out-of-scope targets

The analyzer must fail closed.

If scope cannot be determined:

```text id="g4d2ly"
STOP
→ mark target as unknown
→ do not crawl
→ report configuration/authorization ambiguity
```

---

# 7. Domain Boundary

Every discovered link must be classified.

```text id="qz6h2v"
same_allowlisted_domain
allowed_related_domain
external_unknown
```

Default behavior:

```text
same_allowlisted_domain → may continue
allowed_related_domain  → continue only if explicitly configured
external_unknown        → do not crawl
```

A link appearing on an allowlisted page does not automatically authorize crawling its destination.

---

# 8. Portal Isolation

Every portal is an independent security and state domain.

Never mix:

* cookies
* credentials
* access tokens
* encrypted sessions
* browser profiles
* identities
* challenge state
* cache namespaces
* screenshots
* analysis records
* academic records

between portals.

Conceptually:

```text id="9p4s7x"
Portal A
├── session A
├── cache A
├── graph evidence A
└── visual evidence A

Portal B
├── session B
├── cache B
├── graph evidence B
└── visual evidence B
```

A common user does not make portal state interchangeable.

---

# 9. Source-of-Truth Hierarchy

Use:

```text id="2ox8v1"
Current verified portal response
        ↓
Current typed analyzer result
        ↓
Verified analysis cache
        ↓
Verified Graph RAG state
        ↓
Verified knowledge state
        ↓
Checkpoint/memory
        ↓
Historical analysis
```

Historical information supports comparison and change detection.

It does not override current verified state.

---

# 10. Evidence Model

Every material structural observation should have provenance.

Represent evidence conceptually as:

```text id="3q6p5z"
Observation
├── source URL
├── page identity
├── access class
├── retrieval timestamp
├── portal/site identity
├── discovery method
├── evidence level
└── version/checkpoint where applicable
```

Never create a factual relationship without an observable source.

---

# 11. Evidence Levels

Classify observations as:

```text id="x4v6cb"
direct
derived
historical
unknown
```

### direct

Observed in the current analysis.

### derived

Reasoned from current observations.

### historical

Observed during an earlier verified analysis.

### unknown

Insufficient evidence exists.

Never present:

```text
derived
historical
unknown
```

as equivalent to current direct observation.

---

# 12. Structural Analysis Model

The analyzer should conceptually model:

```text id="h3qv4j"
Site
├── Host
├── Page
├── Route
├── Module
├── Navigation
├── Link
├── Access Class
└── Structural Metadata
```

Possible relationships:

```text id="4c7x0d"
page
  └── links_to → page

module
  └── contains → page

page
  └── belongs_to → module
```

Only create relationships supported by observed navigation or verified analyzer output.

Do not infer relationships solely from:

* URL similarity
* page-name similarity
* embeddings
* search ranking
* semantic similarity
* guessed conventions

---

# 13. Access Classification

Every page should be classified as:

```text id="2j4f1k"
public
login
authenticated
unknown
```

### public

Accessible without authentication.

### login

Authentication entry/challenge page.

### authenticated

Requires an authenticated session.

### unknown

Access classification cannot be reliably established.

If access classification is unknown, default to the more restrictive interpretation.

---

# 14. Session Check

Authenticated analysis may occur only when:

* authenticated analysis is explicitly allowed
* a valid approved session exists
* the session belongs to the intended portal
* the session is isolated
* the analyzer is permitted to inspect the requested scope

If the required session is unavailable:

```text id="0d1p4t"
STOP
→ authentication_missing
```

Do not silently fall back to an unrelated session.

---

# 15. Session Security

Never persist or expose:

* passwords
* cookies
* bearer tokens
* session IDs
* CSRF tokens
* authentication headers
* refresh tokens
* browser storage secrets
* raw authenticated request payloads

Encrypted session material must remain inside the approved authentication/session mechanism.

The analysis layer consumes authorization state; it must not extract or reveal its secrets.

---

# 16. Read-Only Invariant

The analyzer is observational.

Ordinary discovery must be limited to safe read operations:

```text
GET
HEAD
```

Mutation methods are prohibited by default:

```text
POST
PUT
PATCH
DELETE
```

Do not follow a GET URL merely because its effect appears to be harmless if the operation is known to mutate state.

The analyzer must not submit forms.

---

# 17. Mutation Boundary

If discovery encounters:

* a form
* a submission endpoint
* an upload control
* a delete action
* a state-changing button
* a workflow transition
* an API mutation

record its structural existence if safe, then stop before invoking it.

Return:

```text id="p6n7qt"
mutation_boundary_reached
```

and route the action to the appropriate domain-specific skill.

---

# 18. Human Verification Boundary

Human verification includes:

* CAPTCHA
* reCAPTCHA
* hCaptcha
* image challenges
* math challenges
* challenge-response login
* anti-bot interstitials
* equivalent human-presence mechanisms

When detected:

```text id="o9qv9k"
page identified
      ↓
verification detected
      ↓
record safe structural observation
      ↓
STOP
      ↓
return control to human/domain-specific authentication workflow
```

Never:

* solve CAPTCHA
* OCR CAPTCHA
* infer CAPTCHA answers
* automate challenge interaction
* bypass challenge endpoints
* poll challenge state repeatedly
* use another route to avoid the challenge

---

# 19. Discovery Bounds

Discovery must always be bounded.

Default controls:

```text id="z5z5c7"
depth_limit
max_pages
allowed_hosts
seed_urls
```

Do not crawl an entire portal unintentionally.

For public documentation sites, larger bounds may be justified when explicitly configured.

Bound:

* page count
* crawl depth
* retries
* request frequency
* response size where supported
* redirect chains

---

# 20. Discovery Workflow

Conceptually:

```text id="g0g5iy"
1. inspect status
2. determine freshness
3. refresh if necessary
4. discover from approved seeds
5. enforce host boundaries
6. enforce depth/page limits
7. classify pages
8. filter sensitive content
9. persist safe evidence
10. verify persistence
```

Do not perform unnecessary discovery.

---

# 21. Freshness

Track:

```text id="4p4o2u"
fresh
stale
unknown
```

Refresh when:

* user asks for current structure
* cache is stale
* portal may have changed
* important page is missing
* current navigation matters
* authenticated structure may have changed
* change detection is requested

Historical cache is useful but cannot be reported as current without qualification.

---

# 22. Cache Model

The analysis cache should contain structural information:

* site identity
* page identity
* routes
* modules
* navigation
* access classification
* structural metadata
* timestamps
* provenance

It should not contain:

* credentials
* cookies
* access tokens
* private academic records
* private form submissions
* session secrets

The cache is a structural model, not a private-record database.

---

# 23. Discovery Artifact

Persist discovery output under:

```text
<WEB_ANALYSIS_DATA_DIR>/discoveries/<site_slug>/latest.json
```

Treat `latest.json` as generated state.

After persistence:

1. verify file exists
2. verify it is readable
3. verify expected structure
4. verify site identity
5. verify timestamp/version

Do not report successful persistence solely because a write operation returned successfully.

---

# 24. Historical Snapshots

Where practical, preserve historical snapshots separately from `latest.json`.

Conceptually:

```text id="5d0q3f"
discoveries/
└── <site_slug>/
    ├── latest.json
    └── history/
        ├── <timestamp-1>.json
        ├── <timestamp-2>.json
        └── ...
```

Historical snapshots support:

* change detection
* regression analysis
* portal migration tracking
* navigation evolution

Do not destroy historical evidence merely because a new analysis exists.

---

# 25. Change Detection

Compare verified historical and current catalogs.

Possible changes:

```text id="1w6e8x"
page_added
page_removed
page_renamed
route_changed
navigation_changed
module_changed
access_class_changed
content_changed
```

Distinguish:

```text structural change
```

from:

```text content change
```

Do not claim that a page was removed merely because discovery failed once.

Require sufficient evidence.

---

# 26. Sensitive Content Filtering

Before persistence, inspect content for:

* credentials
* cookies
* tokens
* session identifiers
* private query parameters
* personal academic records
* private form values
* sensitive identifiers

Strip or exclude sensitive material.

When a page mixes public and sensitive information:

```text id="9g4w5c"
retain safe public structure/content
discard sensitive values
```

Never persist an entire authenticated page merely because part of it is structurally useful.

---

# 27. Query Parameter Safety

Treat query parameters as potentially sensitive.

Potentially sensitive examples:

```text
token
session
auth
code
key
signature
student_id
user_id
record_id
```

Do not persist sensitive parameter values.

Where possible, normalize URLs before persistence:

```text
/path/resource?token=<redacted>
```

rather than storing the actual secret.

---

# 28. Public Visual Capture

Visual capture is permitted only for:

```text id="4efx6r"
public
login
```

Visual capture is prohibited for:

```text id="u2k8q3"
authenticated personal pages
private dashboards
grades
schedules
KRS data
academic records
private submissions
```

If access classification is uncertain:

```text
DO NOT CAPTURE
```

---

# 29. PixelRAG Integration

Public visual captures may support:

* UI documentation
* layout analysis
* public navigation analysis
* visual regression
* public design inspection
* page comparison

Images must not be used to extract private authenticated information.

Visual evidence should retain:

* source URL
* page identity
* access classification
* capture timestamp
* analysis context

---

# 30. Visual Privacy Check

Before persistence:

1. verify page classification
2. verify URL is in scope
3. verify capture target
4. capture only permitted page
5. inspect the output when appropriate
6. reject accidental sensitive captures

If a supposedly public page unexpectedly contains private data:

```text id="d7d2q8"
STOP
→ discard/restrict capture
→ report privacy boundary
```

---

# 31. Knowledge Ingestion

When enabled:

```text id="4j4b6n"
discover
→ extract permitted text
→ filter sensitive values
→ attach provenance
→ ingest
→ verify
```

Preserve, where available:

* source URL
* page identity
* access class
* retrieval time
* provider/discovery context
* source version

Knowledge ingestion must not silently convert authenticated private content into durable knowledge.

---

# 32. Graph RAG Integration

Public or otherwise permitted structural discovery may create:

```text
web_page
links_to
belongs_to
contains
```

relationships.

Every graph relationship must be supported by:

* observed navigation
* verified analyzer output
* source page
* target page
* timestamp/version when relevant

Do not create relationships from embeddings alone.

---

# 33. Graph Verification

After persistence, verify:

* expected nodes exist
* expected relationships exist
* source/target identity is correct
* provenance exists
* no sensitive content was accidentally persisted

A successful graph-write response is not sufficient evidence of correct persistence.

---

# 34. Knowledge Verification

After ingestion, verify:

* expected source exists
* expected page identity exists
* provenance exists
* sensitive values were excluded
* content corresponds to the analyzed page

Do not report ingestion as successful without a verification signal.

---

# 35. Resource and Rate Control

Use:

* bounded crawl depth
* bounded page count
* deduplication
* cache reuse
* controlled retries
* request pacing
* response-size limits where supported

Do not repeatedly hit a stable site without reason.

The objective is:

```text
maximum useful evidence
with minimum unnecessary requests
```

---

# 36. Lease / Busy Handling

If the analyzer reports:

```text
busy
```

then:

1. recognize another analysis owns the resource
2. avoid duplicate crawling
3. retry once according to supported workflow
4. stop if still unavailable
5. report the blocker

Do not create parallel crawls to bypass a lease.

---

# 37. Failure Classification

Use explicit failure classes:

```text
configuration_required
scope_denied
authentication_missing
authentication_expired
human_verification_required
busy
not_found
forbidden
timeout
network_error
parser_error
unsupported_structure
mutation_boundary
privacy_boundary
unknown
```

Each failure should map to an appropriate next action.

Do not blindly retry failures that are:

* authorization-related
* human-verification-related
* scope-related
* mutation-related
* privacy-related

---

# 38. Retry Policy

Retry only when the failure is plausibly transient.

Reasonable candidates:

```text
timeout
temporary network_error
temporary busy
```

Avoid repeated retries for:

```text
forbidden
not_found
scope_denied
authentication_missing
human_verification_required
mutation_boundary
privacy_boundary
unsupported_structure
```

Never use retries to circumvent security controls.

---

# 39. Checkpointing

Material analysis should be checkpointed.

A checkpoint should preserve:

```text id="u5zjz6"
site identity
scope
analysis mode
last verified state
freshness
pages discovered
important findings
persisted artifacts
verification state
known blockers
next safe action
timestamp
```

Do not checkpoint secrets or private authenticated values.

---

# 40. Cross-Session Continuity

A later session may use a prior checkpoint to resume analysis.

However:

```text id="5qj6z8"
checkpoint
≠
current portal truth
```

Before reporting current state after a long gap:

```text
checkpoint
→ freshness evaluation
→ refresh if necessary
→ current verification
```

Historical checkpoints provide continuity, not authorization.

---

# 41. Standard Report

A completed analysis should report the relevant subset of:

```text id="qg8i0m"
Target
Scope
Analysis Mode
Access Classification
Freshness
Pages Discovered
Structural Findings
Changed Since Previous Analysis
Graph State
Knowledge State
Visual State
Verification State
Blockers
Artifacts
Checkpoint
Next Action
```

Avoid exposing internal session details.

---

# 42. Result State

Use:

```text id="lyu5is"
complete
partial
blocked
failed
uncertain
```

### complete

Requested analysis completed and persisted/verified.

### partial

Some requested analysis completed, but bounded failures remain.

### blocked

A security, authorization, configuration, or human-verification boundary prevented continuation.

### failed

The operation could not produce a valid result.

### uncertain

Evidence is insufficient to determine the requested state.

Never report `complete` when a material requested component remains unverified.

---

# 43. Routing

Route specialized operations:

```text
HEBAT workflow
→ hebat-academic

Cyber Campus
→ xninetzy-cyber-campus

UACC authentication/operations
→ xninetzy-uacc

Assignment orchestration
→ xninetzy-assignment-orchestrator

Research
→ xninetzy-deep-research

Obsidian ingestion
→ xninetzy-obsidian-orchestra

Graph relationships
→ graph-rag

Cross-session memory
→ xninetzy-memory

Artifact generation
→ xninetzy-artifact-orchestrator
```

This skill remains the **read-only web analysis control layer**.

---

# 44. Operating Invariants

The following are non-negotiable:

```text id="v3x9p1"
1. Scope before discovery.

2. Authorization before authenticated analysis.

3. Allowlist before crawling.

4. Read-only means genuinely read-only.

5. Never invoke mutation routes.

6. Never solve or bypass human verification.

7. Never extract or expose secrets.

8. Never mix portal sessions.

9. Never visually capture authenticated personal pages.

10. Never cross domain boundaries without explicit configuration.

11. Never persist sensitive values.

12. Never infer factual relationships from embeddings alone.

13. Never report stale data as current.

14. Never claim persistence without verification.

15. Never claim submission or mutation success because analysis succeeded.

16. Never retry to bypass a security control.

17. Never use historical evidence as a substitute for current verification.

18. Never silently broaden scope.

19. Never convert an unknown state into a positive state.

20. Fail closed whenever authorization, scope, privacy, or mutation state is ambiguous.
```

---

# 45. Completion Contract

Every completed operation should expose the relevant subset of:

```text
site_identity
scope_status
analysis_mode
access_classification
freshness
discovery_status
pages_discovered
structural_findings
change_detection
knowledge_ingestion_status
graph_persistence_status
visual_capture_status
verification_status
blockers
checkpoint_status
artifacts
next_safe_action
```

The report must distinguish:

```text
observed
derived
historical
unknown
```

when the distinction matters.

---

# 46. Final Objective

The objective of Xninetzy Web Analysis OS is:

> **Build a trustworthy, provenance-preserving, freshness-aware structural model of explicitly authorized web systems while minimizing requests, isolating security state, protecting privacy, respecting human-verification boundaries, and preventing read-only analysis from becoming unauthorized interaction.**

The analyzer should prefer:

```text
verified partial result
```

over:

```text
unverified complete result
```

and:

```text
safe stop
```

over:

```text
unsafe continuation
```
