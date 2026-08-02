---
layout: ../../layouts/DocsLayout.astro
title: Shared Agent Skills
description: An open skill catalog shared by LangGraph, MCP, Codex, Claude Code, and OpenCode.
section: AI & developer tools
---

Xninetzy follows the Agent Skills `SKILL.md` contract. A skill is workflow
guidance, not factual evidence. Facts must come from OS tools, validated portal
data, evidence bundles, or grounded knowledge retrieval.

```text
LangGraph / WhatsApp / MCP / Codex / Claude Code / OpenCode
                         ↓
              services/ai/.agents/skills
```

## Built-in Xninetzy skills

- `xninetzy-os`: OS principles and boundaries;
- `it-learning`: roadmaps, concepts, sessions, mastery, and recall;
- `research`: research plans, sources, and citations;
- `obsidian-knowledge`: vault workflow and knowledge grounding;
- `graph-rag`: nodes, edges, prerequisites, and topic maps;
- `hebat-academic`: courses, materials, deadlines, and submission policy;
- `cyber-campus`: read-only portal access, tokens, CAPTCHA, and KRS safety;
- `life-management`: goals, tasks, habits, money, workouts, and reviews.

## Additional open-source skills

These skills come from the open `openai/skills` catalog and pass the Xninetzy
validator:

| Skill | Purpose |
|---|---|
| `define-goal` | Define outcomes, priorities, and measurable milestones |
| `jupyter-notebook` | Data analytics, ML, visualization, and reproducible notebooks |
| `pdf` | Read, render, and inspect PDF materials |
| `playwright` | Structured browser automation and testing |
| `playwright-interactive` | Interactive locator inspection and browser debugging |
| `screenshot` | Visual evidence and UI verification |
| `transcribe` | Audio and voice transcription workflows |
| `security-best-practices` | Application and dependency security review |
| `security-ownership-map` | Security ownership mapping |
| `security-threat-model` | Threat boundaries and mitigations |
| `cli-creator` | Consistent developer CLI design |
| `gh-fix-ci` | GitHub Actions failure analysis |

Open-source skills retain their upstream LICENSE and NOTICE files. Installing a
skill does not add a new domain tool or override a built-in Xninetzy skill.

## Discovery and use

The runtime scans the catalog on demand:

```text
/skills
/skills-health
/skill research
```

For a natural request, call `skill_suggest_for_request`, then load
`skill_get` only when the procedure is relevant. Load additional files
progressively with `skill_resource_list` and `skill_resource_read`; never
inject the entire catalog into context.

`skill_healthcheck` reports validity, provenance, resource count, line count,
and quality warnings. Built-ins are `trusted-builtin`; owner installs are
`owner-installed`. User skills are not injected automatically. Enable
`XNINETZY_SKILL_AUTO_INJECT_USER=true` only after an audit.

The lifecycle is:

```text
trigger metadata → inspect state → choose tool → plan → act → verify → adapt
```

Skill text cannot become evidence, reduce action policy, or bypass approval.

## Install a shared skill

All interfaces use one installation. Do not create a separate client registry.

From an MCP client:

```text
Use MCP xninetzy to list available skills.
Validate and install the skill named security-threat-model.
List the installed skill resources.
```

Shared tools are:

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

`skill_install` accepts a `SKILL.md` body plus an optional `resources`
mapping under `references/`, `scripts/`, `assets/`, or `agents/`.
Resources are size-limited, hash-verified, written atomically, and rejected for
path traversal or symlinks.

Installation rules:

- frontmatter must validate;
- folder and skill name must match;
- installation is owner-scoped and idempotent;
- credentials are forbidden;
- skills cannot lower action policy;
- factual claims still require evidence;
- a valid skill is immediately available to LangGraph and MCP clients.

Custom skills live under `XNINETZY_SKILLS_DIR` or the runtime data catalog.
Repository built-ins remain in `services/ai/.agents/skills`.

A productive sequence is to use `define-goal` for the outcome,
`it-learning` for the roadmap, `jupyter-notebook` for experiments,
`research` for sources, `obsidian-knowledge` for durable notes, and
`security-threat-model` before exposing a connector or browser action.

The detailed design audit is available in
[Skill Agentic Best Practices](https://github.com/misbahul45/xninetzy/blob/main/docs/research/XNINETZY_SKILL_AGENTIC_BEST_PRACTICES.md).
