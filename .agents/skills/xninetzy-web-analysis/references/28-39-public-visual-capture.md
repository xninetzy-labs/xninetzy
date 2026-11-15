# xninetzy-web-analysis — §28–39

Contents: 28. Public Visual Capture; 29. PixelRAG Integration; 30. Visual Privacy Check; 31. Knowledge Ingestion; 32. Graph RAG Integration; 33. Graph Verification; 34. Knowledge Verification; 35. Resource and Rate Control; 36. Lease / Busy Handling; 37. Failure Classification; 38. Retry Policy; 39. Checkpointing

## 28. Public Visual Capture

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

## 29. PixelRAG Integration

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

## 30. Visual Privacy Check

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

## 31. Knowledge Ingestion

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

## 32. Graph RAG Integration

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

## 33. Graph Verification

After persistence, verify:

* expected nodes exist
* expected relationships exist
* source/target identity is correct
* provenance exists
* no sensitive content was accidentally persisted

A successful graph-write response is not sufficient evidence of correct persistence.

---

## 34. Knowledge Verification

After ingestion, verify:

* expected source exists
* expected page identity exists
* provenance exists
* sensitive values were excluded
* content corresponds to the analyzed page

Do not report ingestion as successful without a verification signal.

---

## 35. Resource and Rate Control

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

## 36. Lease / Busy Handling

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

## 37. Failure Classification

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

## 38. Retry Policy

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

## 39. Checkpointing

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
