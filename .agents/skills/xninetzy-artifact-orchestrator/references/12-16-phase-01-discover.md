# xninetzy-artifact-orchestrator — §12–16

Contents: 12. Phase 01 — DISCOVER; 13. Phase 02 — BIND; 14. Phase 03 — SPECIFY; 15. Phase 04 — INSPECT TEMPLATE; 16. Template Preservation

## 12. Phase 01 — DISCOVER

Identify:

```text
artifact type
purpose
audience
target
delivery format
constraints
existing template
required references
required companion artifacts
```

Determine whether:

```text
single-unit production
```

is sufficient or:

```text
bounded multi-unit production
```

is required.

---

## 13. Phase 02 — BIND

Bind the work to:

```text
target
version
environment
source material
template
artifact type
```

Example:

```yaml
binding:
  source:
  target:
  environment:
  template:
  source_version:
```

This prevents accidentally producing an artifact for a stale target.

---

## 14. Phase 03 — SPECIFY

Create the artifact specification:

```text
type
purpose
audience
scope
required sections
required evidence
required visuals
format
dimensions
length constraints
citation requirements
filename
delivery package
```

Do not begin styling until the specification is stable enough.

---

## 15. Phase 04 — INSPECT TEMPLATE

When reproducing or extending a template, inspect:

```text
page/slide dimensions
margins
grid
typography
master layouts
headers/footers
repeated components
branding
placeholders
locked elements
section patterns
```

Also identify:

```text
DO_NOT_CHANGE
MUST_PRESERVE
MAY_CHANGE
```

Do not blindly reproduce a template whose semantics are not understood.

---

## 16. Template Preservation

When a template is authoritative:

```text
template constraints
>
generic design defaults
```

Preserve:

```text
required branding
required dimensions
required placeholders
required identity fields
required layout conventions
```

Only change elements allowed by the assignment or template policy.

---
