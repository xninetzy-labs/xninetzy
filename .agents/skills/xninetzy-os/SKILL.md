---

...

...
name: "xninetzy-os"
description: "Top-level coordination layer for the Xninetzy operating system. Routes incoming requests to the appropriate domain skill, inspects relevant current state, separates reads from plans from approvals from writes, preserves verification, and integrates results across canonical subsystems."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "2.0.0"
  lifecycle: "inspect -> understand -> route -> plan -> act -> verify -> record -> review -> adapt"
...

# Xninetzy OS

This skill is the **top-level coordination layer** for the Xninetzy operating system. It does not replace specialized skills. It determines:

* what the user is trying to accomplish,
* which domain owns the work,
* what existing state matters,
* which canonical workflow should be used,
* whether the action is safe to execute,
* what evidence proves completion,
* what should happen next.

The central principle is:

> **One owner, one shared state, many interfaces, domain-owned workflows, verified outcomes.**

The canonical lifecycle is:

**Inspect → Understand → Route → Plan → Act → Verify → Record → Review → Adapt**

## Operating model

Xninetzy should behave as one coherent operating system when accessed through any registered interface. The interface is not the source of truth. The shared state and domain systems are.

## When to use

* the request spans multiple domains and the orchestrator must route between them;
* the request needs lifecycle classification (capture, goal, plan, task, execute) before any specific skill can act;
* the user asks for a cross-domain dashboard, attention queue, briefing, or review.

## When NOT to use

* the request clearly belongs to one specialized skill — route directly;
* for domain-specific deep execution — defer to the owning skill;
* for academic action authorization — defer to `xninetzy-academic-safety` and the domain workflow.

## Source-of-truth hierarchy

Use the strongest current evidence available:

```text
Current verified external state
        ↓
Canonical domain tools / persisted state
        ↓
Verified local artifacts
        ↓
Approved decisions
        ↓
Durable memory
        ↓
Conversation context
        ↓
General assumptions
```

Examples:

* Current HEBAT activity beats remembered assignment metadata.
* Current Cyber Campus KRS beats an old memory checkpoint.
* Actual PDF contents beat an earlier draft summary.
* Canonical task state beats a conversational statement that a task is complete.

Do not silently replace authoritative current state with memory.

## Owner scope

All coordination should remain owner-scoped. Owner scope covers goals, tasks, learning state, academic state, projects, artifacts, memory, connected tools, and external actions. A chat identifier alone is not proof of authorization. Do not infer permission simply because a request arrived through a familiar interface.

## Request understanding

Before routing, identify the desired outcome, urgency, risk, domain, and the evidence required to call the task complete.

### Urgency

Immediate, time-sensitive, scheduled, routine, or exploratory.

### Risk

Informational, local/reversible, externally visible, consequential, or destructive.

## Attention inspection

Before changing state, inspect relevant current attention: current date/time, active goals, due tasks, overdue commitments, reminders, learning roadmap, active assignments, deadlines, project blockers, and current captures. Use the minimum state required to make a good decision.

## Routing principle

Use the **smallest canonical domain workflow** that can achieve the outcome. Examples:

```text
Assignment requirements
→ hebat-academic

Assignment coordination
→ xninetzy-assignment-orchestrator

Artifact production
→ xninetzy-artifact-orchestrator

Deep research
→ xninetzy-deep-research

Learning
→ xninetzy-learning-coach / it-learning

Graph relationships
→ graph-rag

Goal definition
→ define-goal

Obsidian structure
→ xninetzy-obsidian-orchestra

Cyber Campus
→ xninetzy-cyber-campus

Personal commitments
→ life-management

Cross-session continuity
→ xninetzy-memory
```

Use supporting skills only when they materially improve the task.

## Multi-domain requests

When a request spans multiple domains:

1. identify the primary outcome,
2. identify dependencies,
3. route each component to its owning skill,
4. preserve shared state,
5. integrate results,
6. verify the overall outcome.

Do not create a new duplicate workflow merely because the request crosses domains.

## Capture, triage, goal, and plan boundaries

* Use `os_capture` when the input matters but its final type is unclear.
* Use `os_triage` when the intended outcome is already sufficiently clear.
* Use **Define Goal** when the user explicitly needs a measurable objective.
* Planning answers **how** to reach the outcome and should not silently mutate external state.
* Execution occurs only through canonical registered tools and domain workflows.

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

Evidence should match the action:

* **Information request** — source-backed answer.
* **Artifact generation** — physical file plus structural/visual QA where relevant.
* **Academic submission** — portal confirmation.
* **KRS change** — verified current KRS state plus confirmation when submitted.
* **Task completion** — canonical completion event and/or evidence.
* **Learning progress** — observed performance evidence.
* **Research** — inspected sources and claim alignment.

## State recording

After meaningful work, record the state in the owning domain. The coordinator should point to the owner of each fact rather than absorb every piece of state.

## Next review point

Every meaningful completed workflow should identify when it needs revisiting: tomorrow, next study session, after lecturer feedback, before deadline, weekly review, after portal state changes, or after artifact QA. Avoid creating unnecessary reminders for every state transition.

## Review and adaptation

Review compares intention → planned action → actual action → evidence → outcome → obstacle → adaptation. Adaptation may result in continue, reinforce, reschedule, reduce scope, change route, repair prerequisite, revise goal, archive, or stop.

## Evidence-aware adaptation

Do not adapt based solely on confidence, elapsed time, number of messages, or number of tools called. Prefer verified artifacts, completed tasks, successful tests, actual portal state, learning evidence, research findings, and explicit user decisions.

## Interface-neutral business logic

Domain logic belongs to domain skills, canonical tools, persisted state, and verified external systems — not to client-specific code in the coordinator.

## Knowledge routing

For evidence-based knowledge workflows: `knowledge_search → inspect relevant evidence → knowledge_answer → final cited synthesis`. Do not substitute a generic answer when the user's task depends on stored knowledge. When source evidence is unavailable, state the limitation.

## Academic, learning, life, research, artifact, Obsidian, graph, and memory routing

Route each domain to its owner:

* **HEBAT** for course state.
* **Assignment Orchestrator** for requirement decomposition.
* **Deep Research** for evidence.
* **Learning Coach / Learning OS** for competence development.
* **Artifact Orchestrator** for deliverable generation.
* **Cyber Campus** for academic portal state.
* **Obsidian Orchestra** for vault structure.
* **Graph RAG** for relationship reasoning.
* **Memory** for cross-session continuity.

Maintain clear boundaries between these states.

## Cross-domain example

A request such as:

> "I need to finish my HEBAT assignment by Friday, learn the missing concepts, produce the report, and submit it."

should become:

```text
Xninetzy OS
│
├── HEBAT Academic
│   └── retrieve brief + deadline + materials
│
├── Assignment Orchestrator
│   └── requirement matrix + work breakdown
│
├── Learning Coach
│   └── prerequisite repair + practice
│
├── Deep Research
│   └── evidence collection
│
├── Artifact Orchestrator
│   └── report generation + QA
│
├── HEBAT
│   └── submission preparation + approval
│
└── Memory
    └── checkpoint + resume state
```

The coordinator integrates these results rather than duplicating their workflows.

## Attention management

When many things are active:

1. identify the user's immediate outcome,
2. surface critical deadlines,
3. identify blockers,
4. choose the smallest high-value next action,
5. defer non-critical complexity.

Do not expose the entire internal state when only one action matters.

## Priority heuristic

A useful planning heuristic considers urgency, goal relevance, dependency value, deadline risk, available capacity, and evidence strength. Do not use a rigid numeric priority score unless the underlying data supports it.

## Smallest useful action

The coordinator should prefer **one bounded action that advances the outcome** over a giant multi-system action plan that creates more management overhead.

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

## Checkpoint integration

At meaningful milestones, use the memory/checkpoint system. A useful checkpoint records `goal`, `scope`, `completed`, `decisions`, `constraints`, `sources`, `artifacts`, `failed_attempts`, `open_questions`, `next_actions`, and `resume_hint`. Do not duplicate entire domain state inside the checkpoint. Reference the canonical owner state when possible.

## Security and privacy

The coordinator must not expose passwords, cookies, access tokens, CAPTCHA answers, grade tokens, browser state, private session information, or unnecessary personal data. Keep personal context minimal and owner-scoped. Use domain-specific privacy boundaries.

## Routing

* Domain selection → the appropriate specialized skill.
* Academic safety → `xninetzy-academic-safety`.
* Tool/strategy decisions → `xninetzy-mcp-lightning`.
* Memory → `xninetzy-memory`.

## Reference map

* `references/routing-and-workflows.md` — capture, triage, goal, plan, and execution boundaries; approval boundary; read/draft/approve/write separation; verification; evidence standards; state recording; next review point; review and adaptation; attention management; priority heuristic; smallest useful action; state consistency; cross-domain integration; interface-neutral business logic; action provenance; idempotency; failure handling; uncertainty policy; security and privacy; academic, learning, life, research, artifact, Obsidian, graph, and memory routing.

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

The central operating principle is:

> **Xninetzy should feel like one coherent system even when many tools and interfaces are involved: one owner, shared state, clear domain ownership, explicit approval boundaries, evidence-backed completion, and no invented side effects.**