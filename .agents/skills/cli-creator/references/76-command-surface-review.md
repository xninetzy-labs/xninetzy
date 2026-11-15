# cli-creator — §76

## 76. Command Surface Review

Before implementation, emit:

```text
Binary:
tool-name

Discovery:
tool-name projects list

Resolve:
tool-name projects resolve <name>

Read:
tool-name projects get <id>

Write:
tool-name deployments create --dry-run

Verify:
tool-name deployments status <id>

Raw:
tool-name request GET /...

Auth:
tool-name init

Diagnostics:
tool-name --json doctor
```

The user should be able to understand the main workflow immediately.

---
