---
name: memory-chat
description: Persist milestone summaries, step processes, and used skills into Xninetzy memory so any future session can resume with full context. Use at every key process, milestone, before long generations, after external actions, and before session end. Also use when a user asks to remember process steps or skills across sessions.
metadata:
  triggers: "checkpoint milestone summarize steps remember skill resume session continuity"
  lifecycle: "summarize-persist-verify-resume"
  version: "1.0"
---

# Memory Chat: cross-session process memory

Every key process must be summarized and persisted so another session can
understand what was done, why, and how to continue. This skill defines the
exact procedure.

## When to use

- after any key process milestone (download, extraction, research, artifact,
  integration, ingest);
- before a long generation or before context becomes large;
- after any external action (upload, submit, portal change);
- when a user says "simpulkan ke memory", "ingatkan", "lanjutkan", or asks
  another session to remember;
- at session end.

## Procedure

1. Summarize the process in compact form:
   - goal and scope;
   - completed steps with concrete counts/paths;
   - decisions and corrections (including superseded assumptions);
   - current state (files, records, IDs);
   - skills and tools actually used;
   - next actions and resume hint.
2. Persist via `memory_add` (content only; provenance is server-injected).
   Keep each entry self-contained: a future session reads only this entry.
3. Include exact paths, IDs, and commands needed to resume (e.g. manifest
   paths, vault paths, course_id mapping, test commands).
4. Verify persistence by noting the returned memory id.
5. When resuming: retrieve scoped context with `memory_get_context` or
   `memory_search`, verify stale external facts, reopen local files, and
   continue from `next_actions` without repeating completed work.

## Entry format

```yaml
CHECKPOINT <project> <date>:
goal:
scope:
completed:
decisions:
corrections:
state:
skills_used:
next_actions:
resume_hint:
```

Use plain text with clear labels; do not fabricate memory ids or outcomes.

## Completion contract

Report: what was persisted (memory id), what was verified, and the exact next
action a future session should take. Never claim a memory entry exists without
the server response.
