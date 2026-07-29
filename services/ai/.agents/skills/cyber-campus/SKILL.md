---
name: cyber-campus
description: Read and safely operate the owner's Cyber Campus academic portal for session status, navigation, profile, academic status, schedule, grades, course offerings, and KRS planning. Use for nilai, jadwal, semester, KRS, portal login, or navigation; keep CAPTCHA and grade-token input private and require staged approval for KRS writes and final submission.
---

# Cyber Campus workflow

Use deterministic portal adapters and typed readers. Do not let the model invent selectors or execute arbitrary page JavaScript.

For read-only requests:

1. Check session status.
2. Start the owner-bound WhatsApp verification workflow when login or a grade token is required.
3. Follow the portal's required field order.
4. Select the requested semester only after the token step permits it.
5. Parse tables into typed values and store only approved minimal snapshots.

For KRS:

1. Read offerings, prerequisites, quota, current selections, schedule, and academic constraints.
2. Build a plan without changing the portal.
3. Detect conflicts and provide alternatives.
4. Bind approval to the plan, action hash, owner, and current portal snapshot.
5. Revalidate before applying selections.
6. Require a separate final approval before submission.
7. Store confirmation evidence.

Never solve CAPTCHA automatically. Never expose credentials, session state, or verified tokens to the model, MCP caller, logs, or final answer.
