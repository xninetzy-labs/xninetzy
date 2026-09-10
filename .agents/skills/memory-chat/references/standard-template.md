# Memory Chat — Standard Template and Completion Contract

This reference expands the standard checkpoint template and the completion contract. Read it when finalizing a checkpoint or producing the closing report of a memory operation.

## Goal

State the actual objective.

Weak: `Work on HEBAT.`

Better: `Prepare the HEBAT assignment report from the current brief and verified course materials, ending with a submission-ready PDF.`

Do not replace the user's actual goal with an invented interpretation.

## Scope

Record boundaries.

Example: `Scope: SII209 I4 assignment, current project report, HEBAT material and lecturer instructions only; no portal submission performed.`

Scope protects future sessions from accidentally expanding the task.

## Completed

Record concrete completed work.

Prefer:

* Downloaded `Minggu_03_Tema_Proyek.pdf`
* Extracted assignment requirements
* Built report outline
* Generated DOCX
* Rendered PDF and verified one-page cover

over: `Made good progress.`

Use counts where meaningful: number of files, records, tests, milestones, or sources. Do not fabricate counts.

## Decisions

Record decisions that change future execution.

Examples:

* Use Times New Roman 12 pt, 1.5 spacing.
* Keep cover to exactly one page.
* Use current lecturer instructions as the authoritative requirement.
* Do not upload until explicit approval.

Include rationale only when it prevents future confusion.

## Corrections

Corrections are especially valuable because they prevent old assumptions from resurfacing.

Example: `Superseded assumption: deadline was believed to be Friday. Verified correction: portal shows Monday, August 24, 2026 at 23:59 WIB.`

Or: `Initial filename was incorrect; final artifact is kelompok4_ecotrack.pdf.`

Never preserve an outdated assumption as if it remains valid.

## State

State should describe the current world, not only the conversation. Possible content:

```text
Files:
IDs:
Portal status:
Artifact status:
Approval status:
Projection status:
Review status:
```

Example: `State: DOCX and PDF exist at /mnt/data/...; PDF QA completed; HEBAT upload not performed; approval still pending.`

## Skills used

Record only skills or tools actually used.

Example:

```yaml
skills_used:
  - hebat-academic
  - hebat-assignment
  - pdf-reading
```

Do not list skills merely because they could have been relevant. This prevents future sessions from assuming work was performed through a capability that was never actually used.

## Next actions

Next actions must be executable and bounded.

Prefer:

1. Reopen the generated PDF.
2. Verify the final references section.
3. Prepare the upload package for approval.

Avoid: `Continue working on it.`

The first future action should be obvious.

## Resume hint

The resume hint is the most important continuation instruction. It should tell the future session:

* where to start,
* what not to repeat,
* what to inspect,
* what must happen next.

Example: `Resume from PDF QA. Do not regenerate the DOCX unless the PDF check reveals a defect. After QA, prepare the HEBAT upload package but stop before submission approval.`

## Standard checkpoint template

```yaml
CHECKPOINT <project> <date>:

goal:
<concrete objective>

scope:
<boundaries>

completed:
- <verified milestone>
- <verified milestone>

decisions:
- <important decision>

corrections:
- <superseded assumption or correction>

state:
- <files / IDs / portal / artifact state>

skills_used:
- <skill actually used>

next_actions:
- <smallest next action>
- <following action, if necessary>

resume_hint:
<exact instruction for the next session>
```

Keep the content compact enough to retrieve efficiently.

## Completion contract

When a checkpoint is persisted, report:

**What was persisted** — a concise description of the saved state.

**Memory ID** — only the ID returned by the memory service.

**What was verified** — persistence status and any relevant state verification.

**Exact next action** — the first action a future session should take.

If persistence was not confirmed: `Memory status: unverified.`

Never claim that cross-session memory exists without a server-confirmed response.

## Operating rules

The system must:

* checkpoint meaningful state transitions,
* write self-contained summaries,
* store exact paths and identifiers when they are necessary to resume,
* record corrections and superseded assumptions,
* separate verified state from proposals,
* revalidate stale external facts during resume,
* reopen referenced artifacts before continuing,
* avoid duplicate memory entries,
* keep secrets out of memory,
* record only skills and tools actually used,
* never fabricate memory IDs or persistence results.

The canonical lifecycle is:

**Detect → Summarize → Persist → Verify → Scope → Resume → Revalidate → Continue**