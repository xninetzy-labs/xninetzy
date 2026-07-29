# Cyber Campus KRS Workflow Analysis

Date: 2026-07-29
Mode: authenticated, read-only, local single-owner

## Verified surface

The encrypted owner session was inspected through GET/HEAD only. The audit did
not fill controls, click navigation actions, invoke portal POST handlers, or
persist visible academic values.

The live runtime inventory found 29 navigation entries. Twenty-seven unique safe
routes were reachable with zero failures; Logout was inventoried but deliberately
not visited. Academic routes include:

- `/modul/mhs/akademik-krs.php`
- `/modul/mhs/akademik-kprs.php`
- `/modul/mhs/akademik-khs.php`
- `/modul/mhs/akademik-transkrip.php`
- `/modul/mhs/akademik-jadwal.php`
- `/modul/mhs/akademik-draft.php`

The KRS page exposes four conceptual tabs:

1. Penawaran MK
2. MK Lintas Rumpun
3. MK Terambil
4. Cetak KRS

The current closed-period page contains no active selection form, checkbox, or
submit control. The runtime manifest therefore reports no write capability
instead of guessing stale selectors.

## Runtime adaptation contract

`portal_navigation` inventories same-origin anchors and handler targets in all
frames. `portal_krs_capabilities` inspects current form/control structure,
extracts only sanitized `.php` targets from inline scripts, and calculates a
structure hash. Raw JavaScript is never placed in the model prompt or executed
from model output.

Future KRS execution can adapt without client-specific selector updates only
through bounded browser primitives and a fresh capability manifest. Any DOM,
handler, course, class, quota, or schedule change invalidates the prior snapshot
and approval.

## Target safe workflow

```text
Read status and offerings
  -> normalize courses, classes, credits, schedules, prerequisites, and capacity
  -> build immutable KRS plan without mutation
  -> validate conflicts and personal rules
  -> request bound WhatsApp approval for selection changes
  -> reopen portal and validate a fresh capability snapshot
  -> apply only approved selections through bounded primitives
  -> reread and compare applied state
  -> request a distinct final WhatsApp approval
  -> submit once and capture redacted receipt evidence
```

Deterministic value parsers, immutable plan persistence, snapshot-bound approval,
and the bounded executor remain required before KRS write can be enabled.

Runtime account details, NIM, course rows, grades, cookies, tokens, and browser
storage are intentionally excluded from this tracked document.
