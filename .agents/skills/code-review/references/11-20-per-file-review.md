# code-review — §11–20

Contents: 11. Per-File Review; 12. Diff Anchoring; 13. Deleted-Code Analysis; 14. Added-Code Analysis; 15. Modified-Code Analysis; 16. Naming; 17. Naming Semantics; 18. No-Comment Rules; 19. Error Propagation; 20. Error Contract

## 11. Per-File Review

Every changed source file receives a review record.

```yaml
file_review:
  file:
  change_type:
  changed_lines:
  affected_symbols:
  applicable_rules:
  findings:
  test_evidence:
  risk:
```

Every actionable finding must point to:

```text
file:line
```

or:

```text
file:symbol
```

and include supporting repository evidence when the issue depends on broader context.

---

## 12. Diff Anchoring

Required anchor:

```text
file_path:line_number
```

Preferred:

```text
file_path:line_number
symbol_name
```

For deleted code:

```text
file_path:old_line_number
```

For cross-file findings:

```text
changed_file:line
+
related_file:line
```

Never produce:

```text
"This part seems wrong."
```

without a location.

---

## 13. Deleted-Code Analysis

Deletion deserves independent analysis.

Check whether deleted code represented:

```text
validation
authorization
logging
cleanup
retry
timeout
transaction boundary
security header
test coverage
error handling
```

A removal can be a regression even when the replacement code is clean.

---

## 14. Added-Code Analysis

Added code is checked for:

```text
new state
new dependency
new side effect
new public surface
new external call
new permission
new config
new persistence
new concurrency
```

---

## 15. Modified-Code Analysis

For modified symbols compare:

```text
precondition
postcondition
invariants
error behavior
side effects
call graph
```

Do not assume the function's old behavior remains unchanged merely because
the signature did not change.

---

## 16. Naming

Check repository naming conventions for:

```text
variables
functions
classes
types
files
modules
commands
routes
constants
environment variables
tests
```

Do not flag naming merely because it differs from generic language conventions.

The project convention is authoritative.

---

## 17. Naming Semantics

Check whether names accurately describe behavior.

Potential issue:

```text
getUser()
```

actually:

```text
updates user
```

or:

```text
validate()
```

actually:

```text
normalizes + persists
```

Misleading names are especially important for:

```text
side effects
security
writes
network operations
transactions
```

---

## 18. No-Comment Rules

If the project forbids source comments:

```text
flag newly introduced comments
```

including:

```text
inline comments
block comments
temporary comments
TODO comments
debug comments
```

Do not flag:

```text
LICENSE headers
required generated-code headers
configuration where the project explicitly permits them
```

unless the rulebook says otherwise.

Finding should cite the exact project rule.

---

## 19. Error Propagation

Trace:

```text
error source
   ↓
catch
   ↓
transform
   ↓
return
```

Check for:

```text
swallowed errors
empty catch blocks
incorrect fallback
generic error replacement
lost context
incorrect status mapping
partial failure hidden as success
```

Potential anti-pattern:

```text
try:
   operation()
catch:
   return []
```

if callers interpret:

```text
[]
```

as:

```text
successful empty result
```

---

## 20. Error Contract

For each changed public operation identify:

```text
success state
failure states
retryable errors
non-retryable errors
user-visible errors
internal errors
```

Verify that the patch preserves the contract.

---
