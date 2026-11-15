# dependency-audit — §6–10

Contents: 6. Phase 01 — INVENTORY; 7. Manifest vs Lockfile; 8. Dependency Normalization; 9. Phase 02 — BASELINE; 10. Dependency Diff

## 6. Phase 01 — INVENTORY

Inventory direct and transitive dependencies.

Canonical fields:

```yaml id="x4p7n2"
dependency:
  ecosystem:
  package:
  resolved_version:
  requested_range:
  dependency_type:
  direct:
  parent_chain:
  lockfile:
  manifest:
```

Possible `dependency_type`:

```text id="y9c3m1"
runtime
development
optional
peer
build
test
tooling
```

Do not collapse development-only dependencies into runtime exposure.

---

## 7. Manifest vs Lockfile

Compare:

```text id="c6v2j8"
DECLARED
vs
RESOLVED
```

Example:

```text id="m8x1q5"
Manifest:
foo ^4.2

Lockfile:
foo 4.2.7
```

The advisory match must use the resolved version when assessing actual installed
exposure.

A broad manifest range is not itself proof of a vulnerable installed version.

---

## 8. Dependency Normalization

Normalize package identity using:

```text id="q7n2w5"
ecosystem
canonical package name
resolved version
package manager
source registry
lockfile identity
```

Account for ecosystem-specific aliases and package naming semantics when supported.

Do not treat:

```text id="f1r8m4"
same text
```

as:

```text id="p3w9k7"
same package
```

without ecosystem context.

---

## 9. Phase 02 — BASELINE

Establish the comparison point.

Possible baselines:

```text id="d8q2f6"
current branch
merge base
release tag
previous lockfile
previous audit snapshot
operator-specified version
```

Preferred order:

```text id="w1m5c9"
explicit operator baseline
→ repository merge base
→ previous known-good audit
→ previous lockfile
```

Record the baseline identity.

---

## 10. Dependency Diff

Summarize:

```yaml id="u6k9r2"
dependency_diff:
  added: []
  removed: []
  upgraded: []
  downgraded: []
  unchanged: []
  source_changed: []
```

For each changed package capture:

```text id="b5r7x1"
old version
new version
direct/transitive
parent chain
lockfile location
reason when available
```

Do not state that a dependency upgrade caused a regression merely because the
upgrade appears in the diff.

---
