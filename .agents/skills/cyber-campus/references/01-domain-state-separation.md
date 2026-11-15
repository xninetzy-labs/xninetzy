# cyber-campus — §1

## 1. Domain State Separation

Never collapse these states into one object.

```text
IDENTITY STATE
    ↓
SESSION STATE
    ↓
PORTAL CONTEXT
    ↓
ACADEMIC READ STATE
    ↓
PLANNING STATE
    ↓
APPROVAL STATE
    ↓
EXECUTION STATE
    ↓
VERIFICATION STATE
    ↓
AUDIT STATE
```

### Identity State

Who is authenticated.

### Session State

Whether the authenticated session is currently valid.

### Portal Context

Which:

```text
institution
semester
page
module
record type
```

is currently being inspected.

### Academic Read State

What the portal currently reports.

### Planning State

What the learner proposes to do.

### Approval State

Whether the learner explicitly approved that exact action.

### Execution State

What the system actually attempted.

### Verification State

What the portal confirms afterward.

### Audit State

What evidence and state transitions were recorded.

---
