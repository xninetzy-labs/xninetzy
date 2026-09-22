---
name: repo-context-packaging
description: Compact a code repository into a layered context bundle for the harness.
  Avoids the "model reads 1000 files" antipattern. Produces L0-L4 layers from the
  architecture down to the relevant symbols, with hard caps on each layer so the bundle
  stays inside the harness's prompt budget. Use whenever the operator asks for a "deep
  dive" into a codebase, or whenever a non-trivial code modification will exceed the
  model's context window.
metadata:
  author: xninetzy
  version: 1.0.0
  scope: domain
  priority: P1
  required_tools: '["read_file","grep_search","glob_files","repo_search","repo_symbol","repo_dependency","repo_architecture","repo_test"]'
  optional_tools: '["knowledge_search","memory_search","lightning_record_action"]'
  trigger_conditions: '["the operator asks \"explain this codebase\"","a structured-project-execution
    milestone starts","verification of a cross-file change requires architectural
    confirmation"]'
  prerequisites: '["repository root","target intent"]'
---


# repo-context-packaging

A repository is not a list of files; it is a structured graph with
binding contracts between modules. This skill compresses a repo into
the smallest set of layers that still lets the harness reason correctly
about changes.

## Layered output

| Layer | Content                                          | Hard cap    |
|-------|--------------------------------------------------|-------------|
| L0    | intent (one sentence)                            | 1 item      |
| L1    | architecture overview: top-level dirs, key files  | ≤ 80 lines  |
| L2    | dependency graph (modules + key imports)         | ≤ 200 lines |
| L3    | relevant symbols (functions/classes) with paths   | ≤ 200 lines |
| L4    | relevant file excerpts (≤ 50 lines per file)      | ≤ 5 files   |
| L5    | constraint surface: lint, tests, CI, governance  | ≤ 100 lines |
| L6    | risk surface: secrets, network scope, authn/z    | ≤ 60 lines  |

Total bundle target: ≤ 1500 lines, ≤ 12 KB serialized.

## Operating procedure

```
INTENT
   ↓
SURFACE
   ↓
ARCHITECTURE
   ↓
SYMBOLS
   ↓
EXCERPTS
   ↓
CONSTRAINTS
   ↓
EMIT
```

### 1. INTENT

State the question the bundle must answer. Without a measurable
question, refuse to proceed.

Example: "I need to add `idempotency_key` to every mutation tool and
ensure no test breaks." That intent determines which symbols, which
dependencies, and which test files matter.

### 2. SURFACE

Run:

- `glob_files("**/AGENTS.md" | "**/CLAUDE.md" | "**/README.md")` for
  governance
- `read_file("AGENTS.md")` for the binding contract
- `repo_architecture(root)` if available
- `grep_search("^\\s*def [a-z_]+\\(", "**/*.py")` for a function index
- `repo_search(intent, root, limit=50)` for relevant files

Output: a tree of relevant paths + a short list of "files to open
L4".

### 3. ARCHITECTURE (L1)

Read the top-level layout. Target: ≤ 80 lines summarizing:

- top-level directories and their purpose
- the public surface (entry points, modules exposed to MCP)
- the binding contracts (`AGENTS.md`, lint, tests)
- the contract surface (interfaces, abstractions, domain boundaries)

Skip files that don't inform the intent. The skill is allowed to
output "irrelevant" once for every dropped subtree.

### 4. DEPENDENCY GRAPH (L2)

Run `repo_dependency(root)` and emit a directed graph of imports
between modules relevant to the intent. Cap at 200 lines.

If a module has more than 30 external imports and is irrelevant to the
intent, summarize it as one line and move on.

### 5. SYMBOLS (L3)

Use `repo_symbol(name)` for each candidate symbol relevant to the
intent. Cap at 200 lines; prefer higher-priority symbols first:

- public surface functions/classes used by the intent
- internal helpers called by those surfaces
- constants, types, and exceptions tied to the surface

Drop everything else.

### 6. EXCERPTS (L4)

Use `read_file(path, offset=N, limit=50)` to pull only the relevant
range of each file in the L3 list. Cap at 5 files; reject the task
silently growing beyond that.

Each excerpt must begin with a one-line statement of why this file
is in the bundle.

### 7. CONSTRAINTS (L5 + L6)

Run `repo_test(root)` for the test surface, `bash lint` for current
state, and a security read for secrets/network/authn/z relevant to the
intent. Emit as a structured constraints block.

### 8. EMIT

Serialize the layered bundle as JSON:

```
{
    "L0": "<intent>",
    "L1": "<arch overview lines>",
    "L2": "<dep graph>",
    "L3": "<symbol excerpts>",
    "L4": "<file excerpts>",
    "L5": "<constraints>",
    "L6": "<risk surface>",
    "total_lines": <int>,
    "budget_ok": true | false
}
```

## Failure classification

| Class                          | Cause                              | Action                                |
|--------------------------------|------------------------------------|---------------------------------------|
| `INTENT_TOO_VAGUE`             | no measurable intent               | refuse; require intent                |
| `BUDGET_OVERFLOW`              | any layer exceeds its cap          | truncate + log in Lightning           |
| `MISSING_TOOL`                 | `repo_search` or `repo_architecture` unavailable | fall back to direct file tools |
| `STALE_DOCS`                   | `AGENTS.md` or `README.md` out of date | mark stale; surface to owner       |

## Recovery

- bundle too large → drop L4 first, then L3, never L5/L6
- missing files → escalate via `os_inbox`; do not invent content
- budget overflow → re-derive the intent more narrowly; do not silently
  shrink

## See also

- `context-engineering` — consumes this bundle as the L4 layer
- `multi-agent-orchestration` — distributes per-symbol work across
  sub-agents
- `structured-project-execution` — uses the bundle as its task spine
- `tdd-workflow` — uses the bundle's L5 layer for test discovery
