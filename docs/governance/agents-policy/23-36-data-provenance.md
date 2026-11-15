# AGENTS.md — §23–36

Part of the AGENTS.md policy; binds equally.

Contents: 23. Data Provenance; 24. Research Autonomy; 25. Autonomous Source Expansion; 26. Contradiction Resolution; 27. Autonomous Coding; 28. Autonomous Debugging; 29. Autonomous Refactoring; 30. Autonomous Artifact Generation; 31. Artifact Verification; 32. Autonomous Memory; 33. Autonomous Checkpointing; 34. Autonomous Recovery; 35. Failure Budget; 36. Autonomous Self-Improvement

## 23. Data Provenance

Every acquired record should retain:

```text
source_url
source_type
retrieved_at
content_hash
record_hash
adapter_version
parser_version
extraction_method
crawl_context
```

This allows every result to be traced back to its source.

---

## 24. Research Autonomy

Research should continue until the configured stopping criteria are reached.

```text
QUESTION
→ DECOMPOSE
→ SEARCH
→ FETCH
→ EXTRACT
→ CROSS-CHECK
→ FIND GAPS
→ SEARCH GAPS
→ GRADE
→ SYNTHESIZE
→ CRITIQUE
→ FINALIZE
```

Do not stop after the first useful result.

---

## 25. Autonomous Source Expansion

If the initial sources are insufficient, the agent may autonomously discover additional sources.

Preferred:

```text
official source
→ primary source
→ authoritative dataset
→ reputable secondary source
→ additional independent source
```

Every new source must be recorded.

---

## 26. Contradiction Resolution

When sources disagree:

```text
DETECT
→ IDENTIFY EXACT CLAIM
→ COMPARE SOURCE AUTHORITY
→ COMPARE RECENCY
→ CHECK ORIGINAL SOURCE
→ SEARCH ADDITIONAL EVIDENCE
→ PRESERVE UNCERTAINTY
```

Do not silently select one source without documenting the basis.

---

## 27. Autonomous Coding

When asked to implement a feature, the agent may autonomously:

```text
inspect repository
→ understand architecture
→ locate relevant modules
→ inspect tests
→ design change
→ implement
→ run formatter
→ lint
→ typecheck
→ test
→ inspect diff
→ run broader validation
→ report
```

No confirmation is required for ordinary local development work within the requested scope.

---

## 28. Autonomous Debugging

When tests fail:

```text
FAIL
→ REPRODUCE
→ LOCALIZE
→ INSPECT
→ FORM HYPOTHESIS
→ PATCH
→ TEST
→ COMPARE
```

The agent may repeat this loop autonomously.

Stop only when:

```text
fixed
or
blocked
or
scope exhausted
or
authorization boundary reached.
```

---

## 29. Autonomous Refactoring

Refactoring may be performed automatically when:

- it is required for the requested feature,
- it preserves behavior,
- tests protect the affected behavior,
- the change remains inside scope.

Avoid unrelated architectural rewrites.

---

## 30. Autonomous Artifact Generation

The agent may autonomously generate:

```text
PDF
DOCX
PPTX
XLSX
CSV
JSON
Markdown
HTML
reports
datasets
research manifests
security reports
```

The agent must validate the generated artifact before completion.

---

## 31. Artifact Verification

Verification may include:

```text
file existence
file size
checksum
schema validation
parse validation
render validation
visual inspection
content inspection
cross-reference validation
```

Never claim artifact completion based solely on generator exit status.

---

## 32. Autonomous Memory

The system may autonomously create execution memories when they are:

```text
stable
useful
non-secret
relevant
provenance-backed
```

The agent should avoid storing temporary noise.

---

## 33. Autonomous Checkpointing

Checkpoint automatically:

```text
after major milestones
before risky transitions
after external actions
after large data acquisition
after authentication boundaries
before expensive operations
after recovery
```

---

## 34. Autonomous Recovery

The recovery engine should attempt:

```text
retry
→ backoff
→ fallback
→ alternate source
→ alternate parser
→ alternate browser strategy
→ state reconciliation
→ resume
```

before declaring failure.

Do not retry indefinitely.

---

## 35. Failure Budget

Each task receives:

```text
max_retries
max_runtime
max_requests
max_cost
max_recovery_attempts
```

When exhausted:

```text
CHECKPOINT
→ MARK PARTIAL
→ CONTINUE INDEPENDENT TASKS
→ REPORT
```

---

## 36. Autonomous Self-Improvement

After execution:

```text
OBSERVE
→ MEASURE
→ IDENTIFY BOTTLENECK
→ PROPOSE IMPROVEMENT
→ BENCHMARK
→ TEST
→ COMPARE
```

Low-risk improvements may proceed autonomously when they do not modify protected policy or security boundaries.

High-risk architectural changes require explicit owner authorization.

---
