# Xninetzy Research Memory — State Schemas

This reference collects detailed field shapes for research session, source, claim, counterevidence, worker result, gap, artifact, and checkpoint records. Read it when designing or persisting a typed research record.

## Research session identity

```yaml
session_id:
question:
scope:
created_at:
status:
```

## Canonical research state

```yaml
session_id:
question:
scope:
manifest:
sources:
claims:
counterevidence:
worker_results:
synthesis_status:
unresolved:
next_queries:
artifacts:
```

Recommended additional state when supported: `status`, `last_checkpoint`, `last_verified`, `source_count`, `claim_count`, `completed_rounds`, `research_version`. Do not add fields to a persistence tool unless the tool supports them.

## Manifest

```yaml
manifest:
  research_question:
  personal_context:
  scope:
  subquestions:
  queries:
  databases:
  year_range:
  inclusion:
  exclusion:
  source_hierarchy:
  worker_assignments:
  deliverable:
  freshness_requirement:
  evidence_standard:
```

## Source records

```yaml
source_id:
title:
authors:
publication_date:
source_type:
identifier:
canonical_url:
access_status:
provider:
relevance:
evidence_level:
used_for:
claims_supported:
claims_contradicted:
status:
```

Preserve only fields actually verified.

## Claim records

```yaml
claim_id:
claim:
scope:
supporting_sources:
counterevidence:
evidence_strength:
direct_or_inferred:
status:
```

Possible claim states: `supported`, `mixed`, `uncertain`, `insufficient`, `contradicted`, `superseded`.

## Claim-source relationships

```text
Claim
  ├── supported_by → Source A
  ├── supported_by → Source B
  └── contradicted_by → Source C
```

Do not flatten conflicting evidence into a single source list.

## Counterevidence

```yaml
counterevidence:
  - claim_id: C12
    source_id: S31
    observation: "Finds no significant effect under the tested conditions."
    status: unresolved
```

## Worker results

```yaml
worker_results:
  - worker_id:
    assignment:
    completed:
    sources:
    findings:
    counterevidence:
    gaps:
    next_queries:
    status:
```

Worker results should remain attributable to their assigned subquestion.

## Worker completion states

`completed | partial | blocked | insufficient_evidence`

## Research round state

```yaml
round_1:
  purpose: landscape
  status: complete

round_2:
  purpose: evidence closure
  status: active
```

Possible state: `planned | active | complete | partial | blocked`.

## Synthesis state

```yaml
synthesis_status:
  stage:
  claims_covered:
  unresolved_claims:
  contradictions_reviewed:
  draft_status:
```

Possible stages: `not_started | outline | evidence_synthesis | conflict_analysis | drafting | auditing | final`.

## Unresolved research gaps

```yaml
gap_id:
question:
importance:
evidence_attempted:
current_status:
next_queries:
blocked_by:
```

Importance: `critical | important | minor`.

## Research artifact memory

```yaml
artifact:
  path:
  type:
  version:
  purpose:
  status:
  created_at:
```

Artifact states: `planned | created | verified | superseded | missing | invalid`.

## Provider provenance

```yaml
providers:
  - provider: arxiv
    raw_rank: 2
  - provider: crossref
    raw_rank: 5
```

## Research decision memory

```yaml
decision:
  content: "Use peer-reviewed studies and official documentation as the primary evidence set."
  reason: "Research question concerns both empirical effectiveness and current implementation."
```

## Research checkpoint

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

Add research-specific context through the session record rather than duplicating all data inside every checkpoint.

## Checkpoint timing

Checkpoint after major search rounds, source discovery milestones, worker completion, evidence synthesis, before long synthesis, after artifact generation, after major contradiction resolution, before context compaction, and at session end. Do not checkpoint every single search.

## Failed research attempts

```yaml
attempt:
query:
provider:
result:
reason:
lesson:
next_strategy:
```

## Standard research resume output

```text
Research Session
Question
Current Scope
Completed Research
Verified Sources
Important Claims
Counterevidence
Synthesis Status
Open Gaps
Next Queries
Artifacts
Resume Action
```

Keep the output proportional to the size of the research session.