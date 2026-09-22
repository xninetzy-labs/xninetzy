---
name: mcp-development
description: 'Engineering discipline for Xninetzy''s MCP tool surface. Enforces the
  canonical rules: strict Pydantic input/output schemas, FastMCP-compatible metadata
  (`annotations`, `meta`), explicit risk class via `manifest_for`, principal propagation
  via `MCPPrincipal`, idempotency on mutations, bounded output size, deterministic
  error contracts, unit + integration tests, registration through the canonical registry.
  Use whenever the operator asks to add, modify, or remove an MCP tool, change a tool
  signature, or audit the registry.'
metadata:
  author: xninetzy
  version: 1.0.0
  scope: domain
  priority: P1
  required_tools: '["tool_catalog","skill_list","grep_search","read_file","write_file","bash_run","pytest_run","manifest_for","meta_for"]'
  optional_tools: '["action_policy_evaluate","lightning_record_action","hitl_request_approval","skill_creator","skill_security_review"]'
  trigger_conditions: '["the operator asks to add or modify an MCP tool","the operator
    asks to audit the registry","the operator reports a tool signature change"]'
  prerequisites: '["target tool name (or \"all\")","explicit git branch"]'
---


# mcp-development

Every MCP tool is part of Xninetzy's published capability surface. This
skill enforces the engineering rules that keep that surface
deterministic, auditable, and aligned with FastMCP client expectations.

## Rules every tool MUST satisfy

### Input / output

- strict Pydantic schema on inputs (no `dict`, no `Any` leakage)
- declared `output_schema` when the tool returns structured data
- bounded output size (default cap 50 KB, configurable per tool)
- deterministic error contract (no bare exceptions leaking stack traces)

### Metadata

- `manifest_for(name)` returns a valid `ToolManifest` with explicit
  `risk` (read | draft | write | final)
- `meta_for(name)` returns tags + annotations + meta for FastMCP
- `requires_approval: True` for risk=`final`
- `requires_idempotency: True` for risk=`write | final`
- `requires_evidence: True` when the tool produces research claims

### Identity

- primary tool functions accept `chat_id`, `sender_id` as keyword-only
  parameters with `""` defaults
- tools never accept `sender_id` as authorization evidence
- `MCPPrincipal` is injected server-side by the FastMCP adapter; never
  by the client

### Idempotency

- every mutation exposes `idempotency_key: str = ""`
- the wrapper `xninetzy.db.idempotency.idempotent_call` handles dedupe
- final-risk tools additionally require `approval_id` from HITL

### Concurrency

- sync tools that perform IO must use `xninetzy.runtime.cpu_guard` to
  stay within owner-controlled CPU envelope
- async tools that hit network must declare a timeout

### Tests

- unit tests under `tests/` cover the contract
- integration tests cover wire shape (for HTTP-bound or MCP-bound tools)
- regression tests accompany every bug fix
- tests never use `@pytest.mark.skip` to silence a failure

### Documentation

- skill body stays under `XNINETZY_SKILL_MAX_BODY_LINES`
- long bodies decompose to `references/<topic>.md`
- `description` matches the actual capability; no over-promising

## Operating procedure

```
PROPOSE
   ↓
NAMESPACE
   ↓
SCHEMA
   ↓
RISK
   ↓
METADATA
   ↓
TEST
   ↓
DOCUMENT
   ↓
REGISTER
   ↓
VERIFY
   ↓
SHIP
```

### 1. PROPOSE

State the new tool's intent in measurable terms:

- what capability it adds
- which existing tool (if any) it replaces or extends
- which existing skill it pairs with
- which trigger condition uses it

If the proposal duplicates an existing capability, refuse and route
to `skill-creator` for consolidation.

### 2. NAMESPACE

Pick the tool name by these rules:

- snake_case, lowercase, no whitespace
- under 64 characters
- verb-led when it's a mutation (`task_capture`, `reminder_create`,
  `knowledge_ingest_text`)
- noun-led when it's a query (`task_list`, `reminder_search`,
  `knowledge_answer`)
- prefix with the layer (e.g., `harness_plan`, `security_sast`)

If the name collides with an existing tool, refuse and propose a
different name.

### 3. SCHEMA

Define the input Pydantic model:

- required vs optional parameters
- defaults that match the harness's injection rules
- explicit `idempotency_key`, `sender_id`, `chat_id` when relevant
- declared bounds (`max_length`, `limit`, `min`, `max`)

Define the output model:

- either `str` (markdown-like) or a Pydantic class with `output_schema`
- never `dict`, `Any`, or a union of both

### 4. RISK

Use `manifest_for` with the tool name to assign risk class:

- `read` for pure queries
- `draft` for planning / proposal generation
- `write` for local mutators (DB, vault, file)
- `final` for external / irreversible actions

`final` always requires `approval_id`. `write` always requires
`idempotency_key`.

### 5. METADATA

Add tags via `meta_for`:

- pick a tag from `TAG_BY_GROUP` or a name-prefix fallback
- keep `tags` short (≤ 4 items)
- set `annotations.idempotentHint: true` unless risk == `final`
- set `annotations.readOnlyHint: true` only for `read`
- set `annotations.openWorldHint: true` for tools that hit external
  hosts

### 6. TEST

Write tests first, per `tdd-workflow`:

- one unit test per behavior class
- one integration test for the registration surface
- one regression test if the tool replaces a buggy predecessor

### 7. DOCUMENT

Update or create a skill `references/mcp-tools.md` if the tool surface
grew. Update the user's documentation site via Astro if the tool is
in a public category.

### 8. REGISTER

Add the tool to:

- the importing module's `@tool` decorator
- `xninetzy/tools/registry.py` import + `_ALL_TOOLS` list
- the appropriate `get_tool_groups()` category

### 9. VERIFY

Run:

```
ruff check xninetzy/ tests/
pytest tests/
git diff --stat HEAD~1
python scripts/install_skills.py --dry-run
python scripts/verify_cpu_only.py
```

Verify the registry now contains the tool with the expected
metadata.

### 10. SHIP

Only ship when:

- all tests pass
- ruff is clean
- the registry shows the tool with the expected metadata
- the dry-run skills installer does not regress
- the operator has approved via HITL if `risk == final`

## Output contract

A mcp-development invocation returns:

```
mcp-development record
tool_name: <name>
risk: <read|draft|write|final>
tags: [...]
annotations: {...}
tests_added: [<path>, ...]
registry_ok: bool
verdict: SHIPPED | BLOCKED
```

## Failure classification

| Class                          | Cause                              | Action                                |
|--------------------------------|------------------------------------|---------------------------------------|
| `DUPLICATE_TOOL`              | name collides                       | refuse; propose alternative          |
| `NO_FINAL_RISK`                | final-risk tool missing approval    | refuse; require approval_id          |
| `UNBOUNDED_OUTPUT`             | output > 50 KB                      | cap + log                             |
| `MISSING_TEST`                 | no test for new behavior           | refuse; require test                  |
| `METADATA_MISSING`             | `manifest_for` returns default risk | require explicit classification      |

## Recovery

- registry breaks → revert; isolate registration change
- test fails → revert; re-derive schema
- metadata incomplete → stop; require annotation

## See also

- `tdd-workflow` — discipline for the test step
- `skill-security-review` — gate that any new skill (which is the
  description layer over MCP tools) must pass
- `skill-creator` — companion for evolving the tool descriptions
- `security-review` — for any tool touching authn/z or secrets
