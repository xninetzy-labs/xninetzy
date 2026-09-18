---
name: skill-creator
description: Companion to `skill-security-review`. Use whenever you author or modify a SKILL.md, add a new MCP capability, or want to evaluate whether a candidate skill should ship. Drives the loop: create skill → create evals → run with/without → compare → benchmark → improve → publish. Bridges the Lightning RL episode store so every skill mutation is tied to a measured episode outcome rather than anecdote.
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: process
  priority: P0
  required_tools:
    - read_file
    - write_file
    - glob_files
    - grep_search
    - skill_validate
    - skill_install
    - lightning_episode_start
    - lightning_record_action
    - lightning_record_outcome
    - lightning_episode_finish
    - action_policy_evaluate
  optional_tools:
    - hitl_request_approval
    - os_inbox
    - memory_forget
    - memory_add
  trigger_conditions:
    - the operator asks to create or modify a skill
    - a new MCP tool is added and its expected use cases warrant a skill
    - evidence suggests an existing skill should be retitled, reframed, or merged
  prerequisites:
    - target skill directory identified
    - `skill-security-review` verdict available for first-party skills (if publishing outside this repo)
---

# skill-creator

Authoring a Skill without measuring it is a form of speculation. This
skill enforces a measured loop every time a skill is created, mutated, or
retired.

## Operating procedure

```
OBJECTIVE
   ↓
DISCOVERY
   ↓
DRAFT
   ↓
EVAL
   ↓
BENCHMARK
   ↓
DECIDE
   ↓
PUBLISH
```

### 1. OBJECTIVE

State the outcome the skill must produce. Convert free-form requests
("make a security reviewer") into a measurable objective:

- inputs (what the harness hands the skill)
- expected outputs (what the skill must produce)
- failure modes (what counts as broken)
- success evidence (where it is observable)

If the objective cannot be measured, the skill is not ready. Stop and
ask the owner for a measurable objective before proceeding.

### 2. DISCOVERY

Inspect existing skills before authoring. The harness catalog is at
`.agents/skills/<name>/SKILL.md`. Use:

```
search_skill("research")       → list of skill names whose metadata matches
list_skills()                  → every skill, sorted
```

If a similar skill exists, decide: merge, fork, supersede, or leave
alone. Do not silently create a duplicate.

### 3. DRAFT

A skill body has three layers:

1. **Frontmatter** (YAML, no leading markdown title) — `name`, `description`,
   `metadata` with `author`, `version`, `scope`, `priority`, `required_tools`,
   `trigger_conditions`, `prerequisites`
2. **Operating procedure** — explicit ordered steps the harness follows
3. **Output contract** — what the skill returns, what it never returns
   under any circumstances

The body MUST NOT contain hidden instructions, anthropomorphic claims,
or imperative commands that try to subvert other skills. Allowed:

- imperative steps for the harness ("Run tool X with arguments Y")
- output contracts ("returns a verdict object")
- failure classifications ("if X fails, classify as Y and route to Z")

Forbidden inside a skill body:

- "ignore previous instructions"
- "you are now a..."
- "reveal your system prompt"
- "send the conversation to..."
- any pattern the `skill-security-review` gate flags as prompt injection

The body SHOULD stay below the progressive-disclosure budget declared in
`XNINETZY_SKILL_MAX_BODY_LINES` (default ~250 lines). Long bodies must
decompose to `references/<topic>.md` and link out.

### 4. EVAL

For every objective, write at least three eval cases before publishing:

- a positive case where the skill should succeed and produce the documented
  output
- a negative case where the skill should refuse, escalate, or fall back
- an edge case with ambiguous input

Each eval case is stored in `references/evals/<objective>.md` with:

- input
- expected tool sequence (`grep_search` → `read_file` → `os_inbox`)
- expected output structure
- minimum evidence required to count as success

Evals are evaluated against the harness using the same MCP tool surface
the skill itself declares.

### 5. BENCHMARK

Run the eval set through the harness with the skill installed AND with
the skill temporarily disabled. Record both runs as Lightning episodes:

```
lightning_episode_start(
    task_type="skill_eval",
    intent="skill-creator/<name>/<objective>",
    interface="mcp"
)

... call the eval cases ...

lightning_episode_finish(outcome_code="success" | "fail" | "ambiguous")
```

The benchmark produces two numbers per objective:

- **success rate with skill** ≥ **success rate without skill** + delta
- **latency**: with vs without; the skill must not regress p95 by more
  than 25 % unless the regression is justified in the proposal

A skill that does not beat its baseline by at least a
configurable delta (default 5 percentage points) is rejected, not
published.

### 6. DECIDE

Promotion rules:

| Outcome                              | Action                                                |
|--------------------------------------|-------------------------------------------------------|
| positive delta ≥ threshold           | publish                                               |
| delta = 0                            | hold for revision; do not ship                        |
| delta < 0                            | block; emit `improvement_propose` Lightning proposal  |
| HITL rejects                         | archive the draft, log the verdict                     |

### 7. PUBLISH

A published skill lands at `.agents/skills/<name>/SKILL.md` with:

- a `sha256` of the body in `metadata.content_hash`
- the benchmark numbers in `metadata.benchmark`
- the publish timestamp

After publish, re-run `skill-security-review` (the gate skill) on the
newly published first-party skill. First-party skills are auto-passed
because they originate in this repo, but the scan still runs so the
verdict log captures every skill that ever shipped.

## Output contract

A `skill-creator` invocation returns the eval report and a publish
verdict object:

```
skill-creator verdict
skill: <name>
evals_total: N    passed: N    failed: N
delta_vs_no_skill: <percentage>
verdict: PUBLISH | HOLD | BLOCK
body_line_count: N
license_compatible: true
sha256: <hex>
```

## Failure classification

| Class                          | Cause                                      | Action                          |
|--------------------------------|--------------------------------------------|---------------------------------|
| `BAD_OBJECTIVE`                | requested skill has no measurable outcome | stop; ask owner for measurable   |
| `DUPLICATE_SKILL`              | another skill already covers this objective | stop; offer merge or supersede |
| `EVAL_FAIL`                    | fewer than 3 eval cases produced           | block; require more             |
| `BENCHMARK_NEGATIVE_DELTA`     | skill loses to no-skill baseline            | block; require redesign         |
| `SECURITY_GATE_BLOCK`          | `skill-security-review` blocks               | block; route to owner inbox     |
| `LICENSE_INCOMPATIBLE`         | license not Apache-2.0 compatible            | block                           |

## Recovery

If publishing fails, the draft is preserved in a sibling directory
`.agents/skills/_draft/<name>/SKILL.md`. The owner can resume by re-running
this skill pointing at the draft path.

## See also

- `skill-security-review` — runs first, gates every publication
- `skill-improvement-opportunity-logger` — long-running capability that
  watches published skills for drift
- `mcp-development` — what the Skill is calling into; pair this with the
  registry metadata to know which tools are available
- `lightning_improve` — for proposals that fail benchmark, route through
  the Lightning self-improvement loop
