---
layout: ../../layouts/DocsLayout.astro
title: Cyber Campus and grade tokens
description: UNAIR Cyber Campus MCP tools for academic profile, KRS, and grade-token flow.
section: Integrations
---

Cyber Campus is an academic adapter separate from HEBAT. HEBAT handles
Moodle courses and materials; Cyber Campus handles academic profile,
status, grades, schedule, and KRS planning.

In v2.2.0 the adapter is reachable only as MCP tools — no WhatsApp
mediation, no chat slash commands.

## MCP tools

| Tool | Purpose |
|---|---|
| `portal_login_start` | Start headless Chromium login, fills credentials, captures CAPTCHA challenge |
| `portal_login_submit_captcha` | Submit owner CAPTCHA answer |
| `portal_login_cancel` | Cancel an in-flight login |
| `portal_session_status` | Check current session state |
| `portal_logout` | Tear down session |
| `portal_info` | Read portal metadata |
| `portal_profile` | Read name, student id, faculty, program |
| `portal_academic_status` | Academic status by semester |
| `portal_schedule` | Current schedule (deterministic reader) |
| `portal_grades` | KHS reader (waits for portal's official token) |
| `portal_grade_changes` | Diff of grade changes |
| `portal_krs_capabilities` | KRS module capabilities |
| `portal_krs_watcher_status` / `..._start` / `..._stop` | KRS change watcher |
| `portal_krs_war_status` / `..._arm` / `..._disarm` / `..._plan` / `..._dry_run` | KRS final-submit guard |
| `portal_grade_token_submit` | Owner submits the grade token once |
| `uacc_login_*` | Same flow for UACC subdomain |
| `qa_list_kuesioner` / `qa_fill_kuesioner` | QA portal survey reader / filler |

Credentials come from `HEBAT_USERNAME` and `HEBAT_PASSWORD` in memory only.
Browser sessions and downloaded files are ignored by Git.

## CAPTCHA / OTP

CAPTCHA handling is opt-in via `XNINETZY_CAPTCHA_OCR_ENABLED`. Default is
manual owner solve. The lockout guard
(`xninetzy/os/security/captcha/lockout.py`) auto-disables OCR after the
configured threshold of failures within the window.

## Grade tokens

Grade tokens travel through deterministic owner-only routes. They never
enter prompts, MCP persistence, snapshots, or logs and are discarded after
one attempt. Use `portal_grade_token_submit` once per session.

## Final submission guard

`portal_krs_war_*` enforces a precondition gate before any KRS final
submission. The `_arm` / `_disarm` / `_plan` / `_dry_run` / `_status`
cycle ensures operators can review a plan before owner-approved
execution. The actual `portal_krs_final_submit` is FINAL-class and
requires HITL approval.
