---
name: cyber-campus
description: Read and safely operate the owner's Cyber Campus academic portal for session status, navigation, profile, academic status, schedule, grades, course offerings, and KRS planning. Use for nilai, jadwal, semester, portal login, navigation, KRS analysis, staged writes, or final submission; keep CAPTCHA and grade-token input private and require separate approval gates.
metadata:
  triggers: "cyber campus nilai grade jadwal semester krs portal login captcha token navigation offering quota"
  lifecycle: "session-login-read-plan-hash-approve-revalidate-execute-evidence"
  version: "1.1"
---

# Cyber Campus workflow

Use deterministic portal adapters and typed readers. The model chooses a domain tool; it never invents selectors, arbitrary JavaScript, credentials, CAPTCHA answers, or grade tokens.

## Login and read workflow

1. Check session status before opening a new login challenge.
2. Start the owner-bound WhatsApp verification workflow when login or a grade token is required.
3. Follow the portal's required field order and wait for asynchronous CAPTCHA/reCAPTCHA settlement.
4. Read navigation or the requested page through the adapter and parse typed values.
5. For grades, complete the token step before selecting the semester and disclose the exact period read.
6. Store only approved minimal snapshots; never store credentials, token values, or browser state in prompts or logs.

## KRS workflow

1. Read offerings, prerequisites, quota, current selections, schedules, academic constraints, and window metadata.
2. Build a dry-run plan without changing the portal; calculate total credits and conflicts.
3. Bind approval to owner, plan ID, action hash, selected classes, total credits, and portal snapshot hash.
4. Revalidate the session, snapshot, quota, and plan after approval and before every write phase.
5. Apply selections only after the first approval; verify the staged KRS.
6. Require a separate final approval before submission.
7. Save confirmation evidence, receipt, screenshots, and audit status; stop on any portal change.

Never solve CAPTCHA automatically. Never expose credentials, session state, verified tokens, or portal HTML as final evidence.

## Completion contract

Return the period/page read, structured result, freshness/session status, conflicts or uncertainty, approval phase, and verification evidence.
