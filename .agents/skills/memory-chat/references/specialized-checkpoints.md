# Memory Chat — Specialized Checkpoints

This reference expands research, learning, academic, graph, artifact, external-action, and long-generation checkpoints. Read it when persisting a checkpoint in one of these domains.

## External action checkpoints

After external actions, persist:

```text
Action:
Target:
Result:
Timestamp:
Confirmation:
Current state:
Next action:
```

Examples: HEBAT download, Cyber Campus KRS staging, portal submission, file upload, artifact publication. Do not claim an external action succeeded without confirmation.

## Artifact checkpoints

When a meaningful artifact is produced, store:

* artifact type,
* exact path,
* filename,
* relevant version,
* QA status,
* associated task/project,
* remaining work.

Example: `Artifact: /mnt/data/final_report.pdf; rendered and visually checked; cover verified as one page; upload not performed.`

## Research checkpoints

For research milestones, persist:

* research question,
* sources consulted,
* major findings,
* decisions influenced,
* unresolved questions,
* source paths/identifiers when available,
* next research step.

Do not store a giant paper summary unless specifically necessary.

## Learning checkpoints

For Learning OS integration, persist:

```text
Target
Concept
Current mastery state
Evidence produced
Weakness
Next practice
Recall checkpoint
```

Example:

> Goal: independently build a Dockerized backend. Evidence: Dockerfile works locally and integration tests pass. Weakness: networking configuration. Next: debug container-to-database connectivity.

Memory should preserve **learning state**, not merely "studied Docker."

## Academic checkpoints

For HEBAT/Cyber Campus workflows, persist useful continuity such as:

* course/activity,
* academic period,
* assignment requirement,
* material path,
* plan ID,
* approval state,
* staged/submitted state,
* verification status.

Never persist credentials, CAPTCHA solutions, private tokens, or cookies.

## Graph checkpoints

For Graph RAG operations, persist:

* graph objective,
* entities created/identified,
* verified relationships,
* evidence,
* proposed writes,
* completed writes,
* projection status,
* next graph action.

Example:

> Proposed edge `ResearchPaper → supports → Concept` remains unapproved; canonical graph unchanged.

This distinguishes a graph proposal from an actual mutation.

## Long-generation checkpoint

Before beginning a context-heavy generation:

1. capture current objective,
2. record completed research/build steps,
3. record files and relevant paths,
4. record key decisions,
5. record what must not be repeated,
6. persist the checkpoint.

This provides a recovery point if the generation is interrupted.

## Checkpoint frequency

Do not save every conversational turn. Checkpoint when there is a **state transition** or significant context boundary.

Good:

* Research finished
* PDF created
* External upload completed
* KRS staged
* Major decision changed
* Session ending

Not necessary:

* User said "okay."

The system should minimize memory noise.