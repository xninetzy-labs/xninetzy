# AGENTS.md — §4–10

Part of the AGENTS.md policy; binds equally.

Contents: 4. Autonomous Execution Loop; 5. Long-Running Autonomy; 6. Autonomous Task Graph; 7. Dynamic Planning; 8. Web Intelligence; 9. Browser-First Web Analysis; 10. Authenticated Browser Sessions

## 4. Autonomous Execution Loop

Canonical loop:

```text
USER OBJECTIVE
    ↓
INTERPRET
    ↓
SCOPE
    ↓
DISCOVER
    ↓
PLAN
    ↓
ACQUIRE
    ↓
EXECUTE
    ↓
OBSERVE
    ↓
VERIFY
    ↓
RECOVER
    ↓
CONTINUE
    ↓
CHECKPOINT
    ↓
EVALUATE
    ↓
ADAPT
    ↓
COMPLETE
```

The loop may execute hundreds or thousands of internal operations without asking the owner.

---

## 5. Long-Running Autonomy

Long-running tasks must not stop merely because an intermediate operation fails.

The agent should:

```text
detect failure
→ classify failure
→ retry if safe
→ use fallback if available
→ checkpoint
→ continue independent tasks
→ reconcile state
→ resume failed task
```

A single source failure must not automatically terminate the entire workflow.

---

## 6. Autonomous Task Graph

Every complex workflow should be represented internally as a DAG.

```text
                    ROOT
                      │
             ┌────────┼────────┐
             ↓        ↓        ↓
          SOURCE A SOURCE B SOURCE C
             │        │        │
             └────────┼────────┘
                      ↓
                  NORMALIZE
                      ↓
                  ANALYZE
                      ↓
             ┌────────┴────────┐
             ↓                 ↓
          VERIFY            CRITIQUE
             └────────┬────────┘
                      ↓
                   OUTPUT
```

Independent nodes should execute concurrently.

Dependent nodes wait for their prerequisites.

---

## 7. Dynamic Planning

The initial plan is not immutable.

The agent may revise the execution plan when new information appears.

```text
PLAN
→ EXECUTE
→ OBSERVE
→ UPDATE PLAN
→ EXECUTE
→ OBSERVE
→ UPDATE PLAN
```

The agent may autonomously:

- add subtasks
- remove unnecessary subtasks
- change source priority
- select better tools
- change extraction strategy
- retry with a different method
- switch to fallback sources
- increase evidence collection
- reduce redundant work.

The agent must preserve the original objective.

---

## 8. Web Intelligence

Web analysis is a first-class Xninetzy capability.

Given:

```text
https://example.com
```

the agent may autonomously perform:

```text
DISCOVER
→ FETCH
→ RENDER
→ INSPECT DOM
→ INSPECT ACCESSIBILITY TREE
→ IDENTIFY ROUTES
→ IDENTIFY COMPONENTS
→ IDENTIFY FORMS
→ IDENTIFY APIs
→ IDENTIFY ASSETS
→ IDENTIFY TECHNOLOGIES
→ EXTRACT DATA
→ ANALYZE BEHAVIOR
→ BUILD SITE MODEL
→ REPORT
```

The agent should not limit itself to the landing page.

When permitted by the target and workflow, it may recursively inspect relevant public pages.

---

## 9. Browser-First Web Analysis

For dynamic websites:

```text
HTTP FETCH
```

should not automatically be considered sufficient.

Use:

```text
HTTP
+
DOM
+
Accessibility
+
Rendered Browser
+
Structured Data
```

when required.

The browser is an observation and execution capability.

---

## 10. Authenticated Browser Sessions

An existing owner-authorized browser session may be used autonomously.

Example:

```text
OWNER
↓
LOGIN / OAUTH
↓
SESSION ESTABLISHED
↓
Xninetzy BROWSER GATEWAY
↓
AUTONOMOUS WORK
```

The agent may continue using the authorized session without asking for confirmation on every page.

The agent must never expose:

```text
password
cookie
session token
refresh token
MFA secret
private key
```

---
