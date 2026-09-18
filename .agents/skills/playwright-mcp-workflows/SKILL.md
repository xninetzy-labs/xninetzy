---
name: playwright-mcp-workflows
description: Procedural guardrails for Playwright MCP browser automation, UI QA, screenshot inspection, and end-to-end testing against authorized targets. Pairs Playwright MCP with Xninetzy's `web_analysis` and `vision` capability families so the harness can drive the browser, capture visual evidence, compare before/after, and verify business rules. Use when the operator asks to test a web flow, take a screenshot for review, scrape data from a permitted site, or verify a feature gate.
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: domain
  priority: P1
  required_tools:
    - web_discover
    - web_fetch
    - web_analysis_refresh
    - image_inspect
    - image_preprocess
    - image_ocr
    - image_compare
    - web_source_ledger
  optional_tools:
    - security_scope
    - hitl_request_approval
    - knowledge_ingest
    - os_inbox
  trigger_conditions:
    - the operator asks to test or QA a web flow
    - the operator asks for a screenshot review or visual diff
    - Playwright MCP is available
  prerequisites:
    - explicit authorized target (use `security_scope`)
    - Playwright MCP server reachable
    - output directory writable
---

# playwright-mcp-workflows

Playwright is fast and Playwright is dangerous. This skill exists so
the harness can drive the browser with measurable guardrails and
visual evidence — without crossing into unauthorized scope.

## Operating procedure

```
SCOPE
   ↓
DISCOVER
   ↓
INSPECT
   ↓
ACT
   ↓
OBSERVE
   ↓
VERIFY
```

### 1. SCOPE

Before any browser action:

- call `security_scope(targets=[...])` to confirm the target host is
  authorized
- record the scope token in the Lightning trace
- if scope is denied: stop, route to owner via HITL

Refuse to drive a browser against any host not in scope. No exceptions.

### 2. DISCOVER

Run `web_discover(source_url=target, depth=1, max_pages=10,
ingest_to_knowledge=False, capture_visual=False)` to get a bounded
site map. Discovery is GET/HEAD-only and pauses when it sees a
human-verification wall.

Store the discovery output in the project state spine.

### 3. INSPECT

For each route the intent targets:

- capture a screenshot via the Playwright MCP screenshot tool
- run `image_inspect(path=screenshot)` to load pixels into the vision
  pipeline
- if the screenshot contains text, run `image_ocr(path=screenshot,
  regions=...)` to extract structured text
- record region bounding boxes for visual diffing

Refuse to act on a route whose inspect step returns "human
verification required" — escalate to owner via HITL.

### 4. ACT

Drive the browser through Playwright MCP tool calls. The MCP server
enforces the canonical action set; this skill enforces the harness
side:

- only declared scope URLs
- only declared form interactions
- readonly-by-default (no POST/PUT/PATCH unless explicitly declared
  in the intent)
- idempotent: a retry replays the same action and gets the same
  server response shape

Act only after the inspect step has produced evidence the page is in
the expected state.

### 5. OBSERVE

After every action:

- capture before/after screenshots
- run `image_compare(before, after, regions=...)` to detect drift
- if expected vs actual differs, mark the action `UNVERIFIED` and
  rotate to recovery

Observation is mandatory. An action without before/after evidence is
not accepted as done.

### 6. VERIFY

Run the verification step that matches the intent:

- business rule assertion (text on the page matches the expected output)
- visual diff assertion (`image_compare` similarity above threshold)
- error-state assertion (no 4xx/5xx except expected)
- auth assertion (post-action, expected user is logged in)

Persist verification evidence to the Lightning episode and to
`web_source_ledger` if the source was an external site.

## Output contract

A playwright-mcp-workflows invocation returns:

```
playwright-mcp-workflows record
scope_token: <uuid>
actions: [{ tool, args, screenshot_before, screenshot_after, evidence }, ...]
verifications: [{ assertion, expected, actual, pass: bool }, ...]
verdict: VERIFIED | UNVERIFIED | BLOCKED
```

## Failure classification

| Class                          | Cause                              | Action                                |
|--------------------------------|------------------------------------|---------------------------------------|
| `SCOPE_DENIED`                 | target not in `security_scope`      | stop; HITL escalation                 |
| `HUMAN_VERIFICATION_REQUIRED`  | CAPTCHA / challenge detected        | stop; do not bypass                    |
| `UNVERIFIED_ACTION`            | no before/after evidence collected  | retry once with explicit evidence      |
| `IMAGE_DIFF_THRESHOLD_FAILED` | visual change exceeds tolerance     | rollback; report to owner              |
| `NETWORK_SCOPE_BREACH`         | redirect off the authorized host   | halt; alert                            |

## Recovery

- human verification wall → stop, route to owner
- unexpected redirect → halt, alert
- visual diff fails → retry once; second failure → escalate
- timeout → split into smaller pages, retry

## See also

- `security-review` — application-level counterpart
- `web-analysis` MCP capability family — backs the discover/fetch steps
- `vision` MCP capability family — backs the inspect/compare steps
- `tdd-workflow` — for verifying durable UI behavior changes
- `structured-project-execution` — durable spine for multi-step UI work
