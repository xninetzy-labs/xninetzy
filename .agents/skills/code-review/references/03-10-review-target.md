# code-review — §3–10

Contents: 3. Review Target; 4. Diff Integrity; 5. Rulebook Loading; 6. Rule Scope; 7. Rule Conflict; 8. Change Classification; 9. Change Surface; 10. Behavior Delta

## 3. Review Target

Accept:

```text
PR
branch
commit
commit range
git diff
patch file
```

Normalize to:

```yaml
review_target:
  repository:
  base:
  head:
  merge_base:
  changed_files:
  changed_lines:
  generated_files:
```

Always establish the exact comparison:

```text
base...head
```

Do not accidentally review:

```text
working tree
```

when the user intended:

```text
branch vs main
```

---

## 4. Diff Integrity

Before review verify:

```text
base exists
head exists
merge base exists
diff is non-empty or explicitly expected
renames detected
deleted files detected
binary files detected
generated files classified
submodules classified
```

If the target diff is ambiguous:

```text
REVIEW_BLOCKED
```

Do not invent a comparison.

---

## 5. Rulebook Loading

Load applicable project rules before judging code.

Possible sources:

```text
AGENTS.md
CLAUDE.md
CONTRIBUTING.md
README.md
workspace rules
package-level rules
directory-local rules
CI rules
lint configuration
formatter configuration
architecture contracts
security policies
API contracts
```

Rule precedence:

```text
explicit local project rule
    >
parent project rule
    >
architecture contract
    >
CI/tool configuration
    >
repository conventions
    >
general engineering best practice
```

Where a higher-level repository rule explicitly establishes a stronger requirement,
apply it.

---

## 6. Rule Scope

Rules may be:

```text
repository-wide
workspace-wide
package-specific
directory-specific
file-specific
language-specific
generated-code-specific
test-specific
```

A rule must only apply where its scope is valid.

Do not flag a file using a rule from an unrelated package.

---

## 7. Rule Conflict

If two rules conflict:

```text
identify both
identify scope
identify precedence
report conflict
```

Do not silently choose.

Example:

```text
workspace:
  no comments

generated package:
  generated files may contain comments
```

The more specific applicable rule wins when project policy says so.

---

## 8. Change Classification

Classify the diff:

```text
FEATURE
BUGFIX
REFACTOR
PERFORMANCE
SECURITY
API_CHANGE
CONFIG_CHANGE
DEPENDENCY_CHANGE
DATABASE_CHANGE
INFRASTRUCTURE_CHANGE
TEST_ONLY
DOCUMENTATION
GENERATED_CODE
MIXED
```

A patch may have multiple classifications.

Example:

```text
FEATURE
+
API_CHANGE
+
AUTHORIZATION_CHANGE
```

---

## 9. Change Surface

Determine:

```text
changed files
changed symbols
changed modules
changed packages
changed public APIs
changed dependencies
changed configuration
changed persistence
changed network behavior
changed authentication
changed authorization
```

Output:

```yaml
change_surface:
  files:
  symbols:
  modules:
  packages:
  public_api:
  persistence:
  network:
  security:
  dependencies:
```

---

## 10. Behavior Delta

Do not review only syntax.

Determine:

```text
before
vs
after
```

for:

```text
inputs
outputs
side effects
state transitions
errors
retries
timeouts
authorization
dependencies
resource usage
```

Example:

```text
before:
POST /orders
  -> create one order

after:
POST /orders
  -> create order
  -> enqueue notification
  -> update analytics
```

This is a behavior expansion even if only ten lines changed.

---
