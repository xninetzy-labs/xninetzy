# api-security — §10–17

Contents: 10. Phase 3 — Authorization Map; 11. Authorization Dimensions; 12. IDOR / BOLA; 13. Property-Level Authorization; 14. Function-Level Authorization; 15. Tenant Isolation; 16. GraphQL Security; 17. WebSocket Security

## 10. Phase 3 — Authorization Map

Build:

```yaml
authorization:
  actors:
    - anonymous
    - user
    - manager
    - admin

  resources:
    - user
    - project
    - document
    - invoice

  actions:
    - read
    - create
    - update
    - delete
```

Then derive expected policy.

---

## 11. Authorization Dimensions

Test:

```text
same-user
other-user
same-tenant
other-tenant
lower privilege
higher privilege
anonymous
expired identity
wrong scope
```

Also distinguish:

```text
object-level
property-level
function-level
tenant-level
field-level
workflow-level
```

---

## 12. IDOR / BOLA

A finding requires more than:

```text
object ID appears in URL
```

Required evidence:

```text
authorized principal
target object
authorization expectation
request
observed result
```

Example:

```text
User A
  ↓
GET /api/projects/123

Project 123 belongs to User B

Observed:
HTTP 200
resource returned

Expected:
HTTP 403
```

Finding:

```text
BROKEN_OBJECT_AUTHORIZATION
```

Never expose unrelated user's sensitive data in the report.

Use the smallest necessary proof.

---

## 13. Property-Level Authorization

Check whether clients can modify fields they are not authorized to control.

Example:

```json
{
  "name": "Project",
  "role": "admin",
  "ownerId": "..."
}
```

Ask:

```text
Which properties are client-controlled?
Which properties are server-controlled?
Which role may modify each field?
```

Test only safe fields/environment.

Potential class:

```text
MASS_ASSIGNMENT
BROKEN_PROPERTY_AUTHORIZATION
OVERPOSTING
```

---

## 14. Function-Level Authorization

Verify:

```text
ordinary user
    ->
admin function
```

and:

```text
anonymous
    ->
protected function
```

Examples:

```text
/admin/*
/manage/*
/internal/*
/billing/*
/users/:id/role
```

Do not confuse hidden frontend navigation with authorization.

The server must enforce authorization independently.

---

## 15. Tenant Isolation

For multi-tenant systems model:

```text
principal
    ↓
tenant
    ↓
resource
```

Test:

```text
tenant A -> tenant A resource
tenant A -> tenant B resource
tenant B -> tenant A resource
```

Check:

```text
read
write
list
search
export
aggregation
background jobs
file references
webhooks
```

Tenant isolation is a first-class control.

---

## 16. GraphQL Security

Inspect:

```text
schema
query
mutation
subscription
resolver
field
object
```

Check:

```text
field authorization
resolver authorization
nested object authorization
introspection policy
query depth
query complexity
alias abuse
batching
resource exhaustion
sensitive mutation access
```

A field hidden from documentation is not secure unless resolver enforcement exists.

---

## 17. WebSocket Security

Model:

```text
connection
  ↓
authentication
  ↓
channel
  ↓
message
  ↓
action
```

Check:

```text
authentication on connection
authorization per channel
authorization per message
origin policy
session expiration
reconnect behavior
tenant isolation
message validation
resource limits
subscription access
```

Do not assume connection authentication automatically authorizes every channel.

---
