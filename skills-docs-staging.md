---

layout: ../../layouts/DocsLayout.astro

title: Shared Agent Skills

description: Shared, auditable Agent Skills used across LangGraph, MCP, Codex, Claude Code, and OpenCode.

## section: AI & developer tools

# Shared Agent Skills

Xninetzy uses the standard Agent Skills `SKILL.md` contract.

A skill is **workflow guidance**, not factual evidence and not an authorization mechanism.

Facts must come from:

* Xninetzy OS tools;
* validated portal state;
* local repository or artifact inspection;
* evidence bundles;
* grounded knowledge retrieval;
* authoritative external sources when required.

```text
LangGraph / WhatsApp / MCP / Codex / Claude Code / OpenCode
                            ↓
                 Shared Skill Registry
                            ↓
                 services/ai/.agents/skills
```

All supported interfaces use the same skill catalog. Client-specific skill registries and duplicated business logic are not allowed.

---

## Built-in Xninetzy Skills

The built-in catalog currently covers the primary Xninetzy domains:

| Skill                | Purpose                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `xninetzy-os`        | OS principles, lifecycle, boundaries, and shared operating rules                            |
| `it-learning`        | Roadmaps, concepts, sessions, prerequisites, mastery, and active recall                     |
| `research`           | Research planning, evidence collection, source management, and citations                    |
| `obsidian-knowledge` | Vault operations, durable notes, and knowledge grounding                                    |
| `graph-rag`          | Knowledge graphs, nodes, edges, prerequisites, and topic relationships                      |
| `hebat-academic`     | HEBAT/Moodle courses, materials, deadlines, requirements, and submission safety             |
| `cyber-campus`       | Authorized academic portal access, session handling, CAPTCHA/OTP boundaries, and KRS safety |
| `life-management`    | Goals, tasks, habits, money, workouts, reviews, and Personal Context                        |
| `academic-safety`    | Academic-integrity, authorization, confirmation, and consequential-action boundaries        |

Additional domain skills may be installed through the shared registry without creating a separate client-specific catalog.

---

## Open-Source Skills

Xninetzy can also install validated skills from approved open-source catalogs.

Examples include:

| Skill                     | Purpose                                                      |
| ------------------------- | ------------------------------------------------------------ |
| `define-goal`             | Define outcomes, priorities, and measurable milestones       |
| `jupyter-notebook`        | Data analysis, ML, visualization, and reproducible notebooks |
| `pdf`                     | Read, render, and inspect PDF materials                      |
| `playwright`              | Structured browser automation and testing                    |
| `playwright-interactive`  | Interactive locator inspection and browser debugging         |
| `screenshot`              | Visual evidence and UI verification                          |
| `transcribe`              | Audio and voice transcription workflows                      |
| `security-best-practices` | Application and dependency security review                   |
| `security-ownership-map`  | Security ownership mapping                                   |
| `security-threat-model`   | Threat boundaries and mitigations                            |
| `cli-creator`             | Consistent developer CLI design                              |
| `gh-fix-ci`               | GitHub Actions failure analysis                              |

Open-source skills retain their upstream `LICENSE` and `NOTICE` files.

Installing an external skill:

* does not create a new domain tool automatically;
* does not override Xninetzy safety policy;
* does not become factual evidence;
* does not grant additional authorization.

---

## Skill Lifecycle

The runtime resolves skills progressively rather than injecting the entire catalog into context.

```text
request
  ↓
skill metadata discovery
  ↓
state / relevance check
  ↓
skill selection
  ↓
skill body
  ↓
optional resources
  ↓
tool selection
  ↓
plan
  ↓
act
  ↓
verify
  ↓
adapt / checkpoint
```

This keeps context small while preserving deterministic workflow behavior.

---

## Discovery

For direct client interaction:

```text
/skills
/skills-health
/skill research
```

For natural-language requests:

```text
skill_suggest_for_request
        ↓
skill_get
        ↓
skill_resource_list
        ↓
skill_resource_read
```

Load additional resources only when they are relevant.

Do not inject the complete skill catalog into every request.

---

## Skill Metadata and Trust

The runtime distinguishes at least:

```text
trusted-builtin
owner-installed
```

User-installed skills are **not automatically injected**.

Enable:

```text
XNINETZY_SKILL_AUTO_INJECT_USER=true
```

only after an explicit audit and when the deployment policy permits it.

The healthcheck should expose, where available:

* validity;
* provenance;
* resource count;
* line count;
* quality warnings;
* installation source;
* integrity information.

---

## Shared Skill Tools

The canonical skill-management interface is:

```text
skill_list
skill_get
skill_suggest_for_request
skill_validate
skill_install
skill_resource_list
skill_resource_read
skill_healthcheck
```

The same interface is exposed through the shared Xninetzy runtime rather than maintained independently by each client.

---

## Installing a Skill

From an MCP client:

```text
Use MCP xninetzy to list available skills.

Validate the skill named security-threat-model.

Install the validated skill.

List its installed resources.
```

A skill installation consists of:

```text
SKILL.md
+
optional references/
+
optional scripts/
+
optional assets/
+
optional agents/
```

The installer should:

* validate frontmatter;
* require matching folder and skill names;
* enforce owner scope;
* remain idempotent;
* reject credentials;
* reject unsafe path traversal;
* reject symlinks where prohibited;
* verify resource integrity;
* write atomically;
* preserve upstream license/notice requirements.

An installation that passes validation becomes available through the shared registry.

---

## Skill Security Contract

A skill must never:

* lower the action policy;
* bypass approval requirements;
* bypass CAPTCHA or OTP;
* authorize an external action;
* contain credentials;
* redefine server-side identity;
* convert untrusted retrieved text into trusted instructions;
* present workflow guidance as factual evidence.

Skill instructions are subordinate to:

```text
system / platform safety
→ repository / deployment policy
→ explicit authorization
→ domain safety policy
→ skill procedure
```

---

## Evidence Boundary

Skill text is not evidence.

For factual claims, use the appropriate evidence layer:

```text
personal state
→ Xninetzy

code
→ repository / codebase tools

academic portal state
→ current portal

scientific evidence
→ papers / authoritative datasets

current public facts
→ authoritative web sources

knowledge-base claims
→ grounded knowledge retrieval
```

A skill may tell an agent **how to perform a research workflow**.

It cannot prove **what the world or the user's data currently says**.

---

## Progressive Disclosure

Prefer small skill bodies with structured resources.

A large procedure should be decomposed into:

```text
SKILL.md
  ↓
references/
scripts/
assets/
agents/
```

Load resources only when the current task needs them.

Long skill files should be periodically reviewed and split when excessive length harms discoverability or context efficiency.

---

## Skill Selection

Selection should be deterministic where practical.

Examples:

```text
learning request
→ it-learning

research request
→ research

assignment request
→ hebat-academic / assignment workflow

knowledge request
→ obsidian-knowledge / graph-rag

security review
→ security-best-practices / security-threat-model

browser testing
→ playwright

PDF inspection
→ pdf
```

When multiple skills apply, the runtime may compose them, but the primary agent remains responsible for:

* ordering;
* scope;
* conflicts;
* safety;
* final verification.

---

## Domain Skill vs Tool

Do not confuse:

```text
Skill
= procedure

Tool / MCP
= capability

Subagent
= bounded execution context
```

For example:

```text
research skill
→ tells the agent how to research

paper_research
→ provides paper retrieval capability

topic-researcher
→ performs one bounded research subquestion
```

The primary agent coordinates these layers rather than duplicating their responsibilities.

---

## Skill Quality Gate

A skill should be considered healthy only when:

* frontmatter is valid;
* name and folder match;
* required structure exists;
* prohibited content is absent;
* resources resolve;
* installation is reproducible;
* provenance is known;
* no credential is embedded;
* action policy cannot be weakened;
* instructions are understandable within the intended context.

Recommended health states:

```text
VALID
VALID_WITH_WARNINGS
INVALID
UNVERIFIED
```

Warnings should be tracked separately from blocking validation failures.

---

## Current Catalog Hygiene

The catalog should periodically audit:

### Provenance

Verify external URLs and upstream origin.

### Size

Split oversized `SKILL.md` files into progressive resources when necessary.

### Duplication

Remove overlapping skills that perform substantially the same workflow.

### Staleness

Review skills whose procedures no longer match current tools or repository architecture.

### Ownership

Remove obsolete owner-installed skills when they are no longer needed.

### Integrity

Continue validating hashes and installation state.

---

## Recommended Composition

A productive Xninetzy workflow may combine:

```text
define-goal
→ it-learning
→ jupyter-notebook
→ research
→ obsidian-knowledge
→ security-threat-model
→ artifact verification
```

Use only the skills required by the actual request.

Do not invoke a skill merely because it exists.

---

## Integration With Xninetzy

The shared skill system participates in the overall Xninetzy loop:

```text
Capture
  ↓
Understand
  ↓
Plan
  ↓
Execute
  ↓
Review
  ↓
Adapt
```

The skill layer should remain reusable across:

* LangGraph;
* WhatsApp;
* MCP;
* Codex;
* Claude Code;
* OpenCode.

Business logic belongs in shared domain/tool layers, not inside individual client skills.

---

## Operating Contract

Every skill-enabled workflow should satisfy:

```text
trigger
→ inspect context
→ select relevant skill
→ retrieve only needed guidance
→ choose tools
→ plan
→ act within authorization
→ verify
→ checkpoint when appropriate
```

Never allow a skill to silently expand the task scope.

Never allow skill instructions to override:

* authorization;
* approval gates;
* repository policy;
* academic integrity;
* security controls;
* authoritative state.

---

## Final Principle

The shared skill catalog is a **workflow layer**, not a second application architecture.

Its purpose is to provide consistent procedures across Xninetzy interfaces while keeping:

```text
Skills
    ↓
shared tools
    ↓
shared domains
    ↓
shared state / policy
```

as the canonical architecture.

The desired outcome is not "more skills".

The desired outcome is:

**fewer duplicated workflows, better reuse, stronger safety, smaller context, clearer provenance, deterministic orchestration, and a continuously verifiable Xninetzy operating system.**
