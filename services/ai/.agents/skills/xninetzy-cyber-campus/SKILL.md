---
name: xninetzy-cyber-campus
description: Safely retrieve and analyze authorized Cyber Campus status, schedules, grades, and KRS using manual CAPTCHA and OTP challenges.
metadata:
  owner: xninetzy
  version: "1.1.0"
---

# Cyber Campus

## Authentication

* use authorized credentials only;
* never expose credentials in logs;
* CAPTCHA and OTP remain manual;
* use short-lived challenge;
* invalidate expired challenge;
* do not bypass institutional controls.

## Fast-path login pipeline & session watchdog

* `/cyber-login` is one-shot: credentials are auto-filled from server config,
  the CAPTCHA is delivered to WhatsApp automatically, and a wrong answer
  triggers an automatic retry with a fresh CAPTCHA image up to
  `CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS`;
* `portal_session_status` validates the stored session against the portal;
  `portal_info` reports its local age;
* the shared session watchdog notifies the owner on WhatsApp when this
  portal's session is missing or older than `ACADEMIC_SESSION_STALE_HOURS`;
* the owner still reads and answers every CAPTCHA manually; OCR, auto-solving,
  and unattended submission remain prohibited.

## Read operations

May retrieve:

* academic status;
* course history;
* grades;
* roster;
* schedule;
* KRS state;
* academic notice.

Store only minimum durable information.

## Write operations

Use:

```text
current state
-> proposed exact diff
-> confirmation
-> execute once
-> re-read
-> verify
-> receipt
```

Stop when portal response is ambiguous.
