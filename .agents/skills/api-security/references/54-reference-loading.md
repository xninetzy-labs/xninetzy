# api-security — §54

## 54. Reference Loading

When this skill is invoked:

```text
IF installation/tool availability is required
    -> read ../xninetzy-security-testing/references/install.md

IF live scanner orchestration is required
    -> read ../xninetzy-security-testing/references/workflow.md

IF scope/authorization/evidence policy is required
    -> read ../xninetzy-security-testing/SKILL.md

IF all are required
    -> read all three
```

Precedence:

```text
SKILL.md security policy
    >
this api-security skill
    >
workflow reference
    >
generic assumptions
```

This skill must never override the security domain's authorization and scope policy.

---
