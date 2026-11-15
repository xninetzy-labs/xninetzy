# cli-creator — §14–19

Contents: 14. Command Naming; 15. Discovery Commands; 16. Resolve Commands; 17. Resolve Ambiguity; 18. Read Commands; 19. Pagination

## 14. Command Naming

Prefer:

```text
resource action
```

Examples:

```text
projects list
projects get
projects resolve
jobs list
jobs logs
members list
deployments create
deployments status
```

Avoid vague commands:

```text
fix
manage
process
run-all
debug
do-it
auto
```

The command name should reveal:

```text
resource
action
risk
```

---

## 15. Discovery Commands

Discovery commands locate top-level resources.

Examples:

```text
projects list
workspaces list
teams list
channels list
queues list
repositories list
dashboards list
```

Discovery should support:

```text
--limit
--cursor
--offset
--query
--search
--json
```

Pagination must be bounded.

Default limits must be documented.

---

## 16. Resolve Commands

A resolve command converts human input into stable IDs.

Examples:

```text
projects resolve "My Project"
repos resolve github.com/org/repo
jobs resolve "latest failed build"
```

Resolution inputs may include:

```text
name
slug
URL
permalink
external ID
human identifier
```

Output:

```json
{
  "id": "proj_123",
  "name": "My Project",
  "matched_by": "name",
  "confidence": "exact"
}
```

A future command should consume the stable ID rather than repeatedly performing broad searches.

---

## 17. Resolve Ambiguity

Never silently choose among multiple matches.

Example:

```text
My Project
  ├── proj_123
  └── proj_981
```

Return:

```text
AMBIGUOUS_RESOLUTION
```

with candidates.

Allow:

```text
--id
--slug
--workspace
```

to disambiguate.

---

## 18. Read Commands

Every major resource should support precise reads where practical:

```text
get
show
list
search
logs
history
status
```

A read command should request only the data required for the command.

Prefer:

```text
tool jobs get job_123
```

over:

```text
tool request GET /everything
```

---

## 19. Pagination

Pagination must be explicit and bounded.

Support whichever API model provides:

```text
cursor
offset
page
next_token
link
```

CLI contract:

```text
--limit N
--cursor VALUE
--page N
```

Never silently fetch unlimited pages.

For aggregation commands:

```text
max_items
max_pages
max_runtime
```

must be enforced.

---
