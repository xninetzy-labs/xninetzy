# Xninetzy OS — Routing, Workflows, and Verification

This reference expands capture/triage/goal/plan/execution boundaries, approval boundary, read/draft/approve/write separation, verification, evidence standards, state recording, next review point, attention management, smallest useful action, state consistency, cross-domain integration, idempotency, and uncertainty. Read it when designing cross-domain coordination.

## Capture boundary

Use `os_capture` when the input matters but its final type is unclear.

Examples:

> "I need to revisit the database project after finals."

> "Maybe I should reorganize my notes."

> "Look into whether RAG is useful for this."

Capture first. Do not prematurely convert the input into a task, reminder, goal, project, or permanent note without enough evidence.

## Triage boundary

Use `os_triage` when the intended outcome is already sufficiently clear.

Examples:

> "Remind me at 19:00 to submit the report."

> "Create a task to benchmark the RAG pipeline tomorrow."

> "Review today's overdue assignments."

Do not use triage to compensate for an unclear intention.

## Goal boundary

Use the Define Goal skill when the user explicitly needs a measurable objective. The OS should not force every task into a formal goal.

Distinguish:

**goal** — desired long-term outcome.

**task** — concrete action with a finite completion condition.

**capture** — an intention or commitment that is not yet clear enough to formalize.

**plan** — the route to the outcome.

## Planning boundary

Planning answers:

**How should we reach the outcome?**

It should not silently mutate external state. Use:

```text
read
→ analyze
→ draft plan
→ review constraints
→ execute
```

Keep proposed state separate from actual state.

## Execution boundary

Execution occurs only through canonical registered tools and domain workflows. Do not implement client-specific business logic in the OS coordinator.

Correct:

```text
[interface]
→ Xninetzy OS
→ HEBAT skill
→ registered HEBAT tool
```

Incorrect:

```text
[interface]
→ custom Moodle scraping logic embedded in coordinator
```

## Approval boundary

Approval requirements remain owned by the domain workflow:

* final academic submission,
* KRS submission,
* upload,
* destructive graph change,
* external communication,
* financial action.

The coordinator routes the request to the domain skill. It must not invent or bypass approval rules.

## Read / draft / approve / write separation

Every meaningful external workflow should preserve four states:

```text
READ
↓
DRAFT / PLAN
↓
APPROVE
↓
WRITE / EXECUTE
```

Do not collapse them. A prepared submission is not a submitted assignment. A KRS plan is not a registered KRS. A proposed graph edge is not a graph mutation.

## Verification

After any meaningful action:

```text
action
↓
actual state
↓
verification
↓
result classification
```

Possible outcomes: `verified_success | partial_success | unchanged | failed | uncertain`. Never claim a side effect from the intention or tool invocation alone.

## Evidence standards

Evidence should match the action.

* **Information request** — source-backed answer.
* **Artifact generation** — physical file plus structural/visual QA where relevant.
* **Academic submission** — portal confirmation.
* **KRS change** — verified current KRS state plus confirmation when submitted.
* **Task completion** — canonical completion event and/or evidence.
* **Learning progress** — observed performance evidence.
* **Research** — inspected sources and claim alignment.

## State recording

After meaningful work, record the state in the owning domain:

```text
Task complete
→ Life OS

Learning evidence
→ Learning OS

Research milestone
→ Research / Memory

Artifact QA
→ Artifact state

Portal submission
→ Academic portal state

Structural vault change
→ Obsidian state
```

Do not put every piece of state into the coordinator itself. The coordinator should point to the owner of each fact.

## Next review point

Every meaningful completed workflow should identify when it needs revisiting: tomorrow, next study session, after lecturer feedback, before deadline, weekly review, after portal state changes, or after artifact QA. Avoid creating unnecessary reminders for every state transition.

## Review and adaptation

Review compares:

```text
intention
↓
planned action
↓
actual action
↓
evidence
↓
outcome
↓
obstacle
↓
adaptation
```

Adaptation may result in continue, reinforce, reschedule, reduce scope, change route, repair prerequisite, revise goal, archive, or stop.

## Evidence-aware adaptation

Do not adapt based solely on confidence, elapsed time, number of messages, or number of tools called. Prefer:

* verified artifacts,
* completed tasks,
* successful tests,
* actual portal state,
* learning evidence,
* research findings,
* explicit user decisions.

## Shared state across interfaces

The same logical action should remain consistent regardless of interface. The OS should not fork state because the user switched interfaces.

## Attention management

When many things are active:

1. identify the user's immediate outcome,
2. surface critical deadlines,
3. identify blockers,
4. choose the smallest high-value next action,
5. defer non-critical complexity.

Do not expose the entire internal state when only one action matters.

## Priority heuristic

A useful planning heuristic considers:

```text
urgency
+
goal relevance
+
dependency value
+
deadline risk
+
available capacity
+
evidence strength
```

Do not use a rigid numeric priority score unless the underlying data supports it.

## Smallest useful action

The coordinator should prefer:

> one bounded action that advances the outcome

over:

> a giant multi-system action plan that creates more management overhead.

## State consistency

When multiple domain systems participate:

```text
shared request
↓
domain states
↓
cross-domain references
↓
verification
```

Check for contradictions such as:

* artifact says final, portal says draft,
* memory says submitted, portal says not submitted,
* task says complete, artifact missing,
* learning roadmap says mastered, latest evidence says weak.

Resolve using the relevant source-of-truth hierarchy.

## Action provenance

For material actions, preserve enough provenance to explain:

* what happened,
* which domain handled it,
* what tool was used,
* what state changed,
* what evidence verified it.

Do not store unnecessary raw private prompts or secrets.

## Idempotency

Operations should be safe to replay. Derive idempotency from the originating message, workflow, task, action plan, or transaction identity when supported. Example concept:

```text
same request
+
same intended state
+
same action identity
=
do not duplicate
```

Do not create duplicate reminders, tasks, uploads, or mutations merely because a request was retried.

## Failure handling

If a tool fails:

1. classify the failure,
2. determine whether state may have changed,
3. verify actual state before retry,
4. choose the narrowest safe recovery,
5. record the failure when it matters for future work.

Do not blindly retry consequential operations.

## Uncertainty policy

Unknown remains unknown. Examples:

```text
submission_state: unknown
quota: unknown
memory_persistence: unverified
artifact_visual_qa: not_checked
learning_mastery: insufficient_evidence
```

Never convert uncertainty into false certainty just to complete the workflow.

## Security and privacy

The coordinator must not expose passwords, cookies, access tokens, CAPTCHA answers, grade tokens, browser state, private session information, or unnecessary personal data. Keep personal context minimal and owner-scoped. Use domain-specific privacy boundaries.

## Standard coordination output

For a simple cross-domain request:

```text
Outcome
Relevant State
Owning Domain
Selected Workflow
Action
Verification
Current Status
Uncertainty
Next Action / Review
```

For a complex workflow:

```text
Overall Outcome
Domain Breakdown
Completed
Pending
Evidence
Blockers
Approval Gates
Cross-Domain State
Next Action
Review Point
```

Keep the final response proportional to the request.

## Completion contract

Every coordinated workflow should return the relevant subset of:

**What was understood** — the user's actual outcome.

**State inspected** — which relevant current state was checked.

**Action completed or proposed** — what actually happened versus what remains planned.

**Evidence/status changed** — what proves progress or completion.

**Uncertainty** — what remains unknown.

**Approval status** — whether approval is required, pending, or satisfied.

**Next review point** — when or under what condition the result should be revisited.

Never claim a side effect before verification.

## Operating rules

The system must:

* identify the outcome before selecting tools,
* inspect only the state relevant to that outcome,
* route work to the canonical domain owner,
* use shared registered tools rather than interface-specific logic,
* separate reads, plans, approvals, and writes,
* preserve owner scope,
* make mutations replay-safe,
* verify actual state after consequential actions,
* record completion in the owning domain,
* maintain uncertainty explicitly,
* protect credentials and private state,
* adapt from evidence rather than assumptions,
* checkpoint meaningful cross-domain milestones.

The canonical lifecycle is:

**Inspect → Understand → Route → Plan → Act → Verify → Record → Review → Adapt**