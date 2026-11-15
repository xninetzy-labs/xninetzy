---
name: xninetzy-web-analysis
description: 'Read-only analysis of allowlisted portals, authenticated apps, SSO systems and dynamic public sites: structure and navigation mapping, evidence capture, knowledge ingestion, change detection; never submits forms, solves CAPTCHAs or bypasses access. Use for bounded site analysis.'
metadata:
  keywords: academic applications aware bypass cache captcha checkpointing checkpoints control creation credential cross discovery documentation explicitly extraction first form freshness graph institutional management module mutation operating page permitted portal provenance relationship safe safety session solving structural submission system tracking verification visual web websites
---

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

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/06-15-scope-enforcement.md` — §6–15: Scope Enforcement, Domain Boundary, Portal Isolation, Source-of-Truth Hierarchy, Evidence Model, Evidence Levels, Structural Analysis Model, Access Classification, Session Check, Session Security
- `references/18-27-human-verification-boundary.md` — §18–27: Human Verification Boundary, Discovery Bounds, Discovery Workflow, Freshness, Cache Model, Discovery Artifact, Historical Snapshots, Change Detection, Sensitive Content Filtering, Query Parameter Safety
- `references/28-39-public-visual-capture.md` — §28–39: Public Visual Capture, PixelRAG Integration, Visual Privacy Check, Knowledge Ingestion, Graph RAG Integration, Graph Verification, Knowledge Verification, Resource and Rate Control, Lease / Busy Handling, Failure Classification, Retry Policy, Checkpointing
- `references/40-43-cross-session-continuity.md` — §40–43: Cross-Session Continuity, Standard Report, Result State, Routing
- `references/46-final-objective.md` — §46: Final Objective
