# cli-creator — §58–64

Contents: 58. Test Matrix; 59. Repository Layout; 60. Documentation Contract; 61. Command Documentation; 62. Companion Skill; 63. Companion Skill Example; 64. Skill Reference Loading

## 58. Test Matrix

Every durable CLI should test:

| Area       | Test                   |
| ---------- | ---------------------- |
| CLI        | help/version           |
| Config     | missing config         |
| Auth       | no credential          |
| Auth       | invalid credential     |
| HTTP       | request builder        |
| HTTP       | timeout                |
| HTTP       | retry                  |
| HTTP       | rate limit             |
| Read       | single object          |
| Read       | list                   |
| Pagination | cursor/offset          |
| Resolve    | exact match            |
| Resolve    | ambiguous match        |
| JSON       | success                |
| JSON       | error                  |
| Write      | dry-run                |
| Write      | confirmation gate      |
| Async      | polling timeout        |
| Fixture    | offline                |
| Install    | execution outside repo |

---

## 59. Repository Layout

Preferred durable layout:

```text
~/code/clis/<tool-name>/
```

when the user does not specify an existing repository.

Example Rust:

```text
tool-name/
├── Cargo.toml
├── README.md
├── Makefile
├── src/
│   ├── main.rs
│   ├── cli.rs
│   ├── config.rs
│   ├── auth.rs
│   ├── client/
│   ├── commands/
│   ├── output.rs
│   └── error.rs
├── tests/
└── references/
```

---

## 60. Documentation Contract

README must contain:

```text
installation
authentication
doctor
command overview
resource discovery
resolve
read
write
dry-run
JSON output
errors
pagination
raw request
examples
exit codes
limitations
```

Do not hide important operational information in source code only.

---

## 61. Command Documentation

Every major command should answer:

```text
What does it do?
What inputs does it need?
Is it read-only?
Can it modify state?
What JSON does it return?
What errors can occur?
```

Example:

```text
tool deploy create

ACTION:
Creates a deployment.

MUTATION:
Yes.

SAFE PREVIEW:
--dry-run

REQUIRES:
project_id
artifact_id

RETURNS:
deployment ID

FOLLOW-UP:
deployments status <id>
```

---

## 62. Companion Skill

After the CLI works, create/update:

```text
$CODEX_HOME/skills/<tool-name>/SKILL.md
```

unless the user specifies another location.

The companion skill should explain:

```text
verify binary
doctor
auth
first discovery
resolve
safe read
write path
raw escape hatch
approval boundaries
```

Do not duplicate the entire API reference.

---

## 63. Companion Skill Example

Future agent sequence:

```text
1. command -v tool-name
2. tool-name --json doctor
3. tool-name <resource> list --json
4. tool-name <resource> resolve "<name>" --json
5. tool-name <resource> get <id> --json
6. use narrow write command only when explicitly requested
```

Include three practical examples.

---

## 64. Skill Reference Loading

When this skill is invoked:

```text
IF command-surface design is required
    -> read references/agent-cli-patterns.md

IF security-sensitive service interaction exists
    -> read ../xninetzy-security-testing/SKILL.md

IF both apply
    -> read both
```

Do not invent conventions that the reference already defines.

---
