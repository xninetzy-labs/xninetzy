---
name: hebat-academic
description: Work with the owner's HEBAT or Moodle courses, activities, deadlines, assignments, and downloadable materials. Use for course freshness, academic digest, material downloads, assignment details, PDF reading, submission preparation, uploads, and connecting course material to the Learning OS; require approval before upload or submission.
metadata:
  triggers: "hebat moodle course activity assignment deadline material download pdf submission upload academic"
  lifecycle: "session-freshness-read-download-ground-prepare-approve-verify"
  version: "1.1"
---

# HEBAT academic workflow

Treat HEBAT as a connector into the Learning OS. Credentials, cookies, browser state, and portal HTML are never evidence for a final answer.

## Read and material workflow

1. Verify the authenticated session and freshness before using cached courses or deadlines.
2. Sync courses, activities, or assignments only when freshness is insufficient.
3. Read the requested typed record and confirm course/activity identity.
4. Download only the requested file into the configured HEBAT downloads directory.
5. Verify the file exists, has the expected type/size, and can be read before summarizing.
6. Connect material to a roadmap, concept, task, or review checkpoint only when the relation is explicit.

## Upload and submission workflow

1. Prepare the intended file and exact target activity.
2. Show the target, filename, consequence, and whether a previous submission exists.
3. Use the HITL boundary before upload or final submission.
4. Revalidate session, activity, deadline, and file immediately after approval.
5. Execute the narrowest action and wait for portal confirmation.
6. Preserve receipt, timestamp, and failure state; never claim success without confirmation.

Stop on ambiguous selectors, expired sessions, changed activities, unsupported file types, or uncertain delivery. Never expose credentials, cookies, or browser state.

## Completion contract

Return course/activity identity, freshness, file path or receipt, approval status, portal verification, and the next learning action.
