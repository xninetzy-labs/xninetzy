# code-review — §49–53

Contents: 49. Caching; 50. External Integrations; 51. Scope Creep; 52. Generated Files; 53. Dependency Lockfile Integrity

## 49. Caching

Changes involving cache must evaluate:

```text
key
TTL
invalidation
scope
tenant
authorization
stale data
race
```

Potential security issue:

```text
tenant A
  ↓
cache key
  ↓
tenant B receives cached response
```

Cache correctness is part of authorization correctness when responses are
tenant-sensitive.

---

## 50. External Integrations

For new/changed calls to external services inspect:

```text
timeout
retry
rate limit
authentication
request size
response validation
error mapping
idempotency
failure mode
```

Do not assume the external API is always available or correct.

---

## 51. Scope Creep

Detect modifications unrelated to the stated change.

Example:

```text
feature:
add login endpoint

diff:
+ login endpoint
+ database migration
+ UI redesign
+ dependency replacement
+ unrelated formatter changes
```

Classify:

```text
SCOPE_EXPANSION
```

The finding should explain why the extra changes increase review uncertainty.

---

## 52. Generated Files

Classify generated files:

```text
generated
derived
manual
unknown
```

Do not repeatedly flag generated content when the repository expects generated
artifacts to be committed.

Instead review:

```text
generator source
```

when available.

---

## 53. Dependency Lockfile Integrity

When package manifest and lockfile both change:

```text
verify they represent the same dependency intent
```

Potential issue:

```text
package version:
A

lockfile:
B
```

or unexpected transitive changes.

---
