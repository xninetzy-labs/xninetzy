# xninetzy-web-analysis — §40–43

Contents: 40. Cross-Session Continuity; 41. Standard Report; 42. Result State; 43. Routing

## 40. Cross-Session Continuity

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

## 41. Standard Report

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

## 42. Result State

Use:

```text id="lyu5is"
complete
partial
blocked
failed
uncertain
```

#### complete

Requested analysis completed and persisted/verified.

#### partial

Some requested analysis completed, but bounded failures remain.

#### blocked

A security, authorization, configuration, or human-verification boundary prevented continuation.

#### failed

The operation could not produce a valid result.

#### uncertain

Evidence is insufficient to determine the requested state.

Never report `complete` when a material requested component remains unverified.

---

## 43. Routing

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
