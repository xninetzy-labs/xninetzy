# Kaggle biodiversity implementation verification

Verified on 2026-11-15 at 13:34 UTC. This is an implementation receipt,
not a claim that processing all source files has finished.

## Scope and current execution

- The public Drive inventory contains 4,377 unique files from 59 supplied roots.
- All downloads, PDF parsing, OCR, Hugging Face inference, scoring, text
  checkpoints and Excel creation execute in private Kaggle jobs.
- Local code only controls jobs and reads bounded execution metadata. The
  controller refuses report, extracted-text and workbook downloads.
- The detached supervisor was confirmed running with an exclusive lock.
  `campaign_state.json` is the authoritative live state; `supervisor.log`
  records transitions. These runtime files are intentionally ignored by Git.
- At verification, 495 files had verified download records; two extraction
  jobs were running, one GPU extraction was queued, and two acquisition jobs
  were running. A zero-page source PDF was marked for review after bounded
  retries. Remaining jobs have dependencies and wait for available capacity.
- The final collection workbook is pending. Failed or incomplete PDFs retain
  a blank score and diagnostics. They are never converted to score 0.

## Scoring and extraction

The score is 1 when the total number of occurrences across the supplied
English keyword groups is at least 2. Two occurrences of the same word count.
The workbook begins with `nama perusahaan`, `tahun`, `keyword`, `value score`.
Separate detail and method sheets retain provenance and coverage.

Version 5 uses the native Docling pipeline through LangChain only for clean
text pages without bitmap images or vector drawings. Complex pages retain
local layout/table models, RapidOCR and the local Granite Docling fallback.
The version-4 spatial scoring is unchanged and its verified checkpoints are
compatible. The exact submitted worker SHA-256 is:

```
0792ea75f95bf243df616d4b1db321626f127924b12a3367711e8d65b605c2b6
```

## Verification evidence

- Cancellation regression: `CANCEL_ACKNOWLEDGED` incorrectly remained submitted
  before the fix; the regression now passes and cancelled jobs are not replayed.
- Local control/security regressions: 63 passed; affected Ruff checks passed.
  These tests do not download or process the user's PDFs locally.
- Kaggle native-path regression version 1 failed at the expected routing
  assertion before the fast path was added.
- Kaggle CPU smoke version 7 completed successfully for the exact SHA above:
  raster OCR, mixed native/image occurrence counts, native routing, vector
  routing, and three resumed pages. Runtime: 77 seconds.
- Earlier full-document validation version 2 completed all 53 pages and
  reopened its generated workbook successfully. Version 3 benchmarks the new
  routing on the same source and was still running at this receipt time.
- The controller confirmed the current smoke SHA before allowing subsequent
  extraction submissions. It started another acquisition shard automatically.

Private account links:

- [Drive inventory](https://www.kaggle.com/code/misbahulmuttaqin/biodiversity-drive-inventory)
- [Current CPU smoke](https://www.kaggle.com/code/misbahulmuttaqin/biodiversity-pipeline-cpu-smoke)
- [Full-document validation and example Excel](https://www.kaggle.com/code/misbahulmuttaqin/biodiversity-full-pdf-validation)

Next action: let the supervisor reconcile remote completions, resume partial
jobs from their Kaggle outputs, and build sector/final workbooks when their
dependencies are ready. Revalidate live state before any recovery; do not
repeat an uncertain submission or start a second supervisor.

## Progress check, 2026-11-15 around 13:50 UTC

The supervisor remained active. Verified download records increased to 758
of 4,377 files (17.32%, approximately 9.97 GB). Energy: 575/576; Basic
Materials: 129/778; Industrials: 54/447. Other sectors were still pending.
One Energy source remained a zero-page PDF requiring review.

Full-document validation version 3 completed all 53 pages with no failures
in 733 seconds, for the exact version-5 SHA recorded above. Its summary
confirmed one complete PDF, 52 standard-model pages and one local Granite
OCR page. The example Excel is available in that private Kaggle output.

Production logs showed one 298-page PDF fully read in extraction shard 02;
its next PDF reached 184/543 pages. Shard 03 reached 416/551 pages on its
first PDF. Shard 06 remained queued for GPU, while acquisition shard 09
was running. The collection-wide Excel remained pending.

## PDF filename audit

[Private Kaggle file-type audit](https://www.kaggle.com/code/misbahulmuttaqin/biodiversity-file-type-count)
version 1 completed successfully. Of the 4,377 inventoried files, 4,351 have
the `.pdf` extension. The remaining 26 comprise 17 `.xlsx`, 6 `.zip`, 1 `.htm`,
1 `.7z`, and 1 filename without an extension. These are filename-based counts;
PDFs nested inside archives and the true format of the extensionless file are
not included in the 4,351 direct-PDF count. Full binary/readability validation
continues in the download and extraction jobs.

## Characteristics profile

[Private Kaggle profile](https://www.kaggle.com/code/misbahulmuttaqin/biodiversity-pdf-characteristics)
version 1 completed successfully with aggregate metadata only returned locally.
Across 339 validated PDFs in four attached download outputs, page counts had
median 240 and range 31–884; 318 reports had at least 100 pages.

A reproducible sample selected 32 PDFs (16 Energy, 8 Basic Materials,
8 Industrials), checking five spread pages each. Of 160 sampled pages, 122
(76.25%) had at least 80 nonspace native-text characters, 21 had fewer than 80,
and 17 had no native text. 94 pages (58.75%) contained bitmap images, including
57 with substantial native text. 37 image pages had less than 80 native-text
characters. Those may include photos, scans or sparse covers; this does not
establish that they are scanned text. Native text can also be an existing OCR
layer. These subset statistics must not be described as a full-corpus profile.

## Live progress, 2026-11-15 around 22:40 WIB

The controller was active. Saved download summaries accounted for 824 files.
Live logs in new shards 10 and 11 confirmed a further 38 and 35 successful
downloads respectively: at least 897 unique files (20.49% of 4,377) at the
observed timestamps. The new jobs were still running; adding their complete
future summaries to these same live counts would double-count them.

Extraction logs confirmed five production PDFs fully read (three in shard 02,
two in shard 03), with current PDFs at 72/522 and 264/504 pages. The two jobs
had observed 2,536 pages in total, with no extraction-failure events in the
bounded history. GPU extraction shard 06 remained queued. The final combined
Excel was still pending. Two earlier download shards remained partial after
Drive verification/rate/quota responses.

## Live progress, 2026-11-16 around 01:27 WIB

Saved summaries confirmed 1,174 successful file downloads (26.82% of 4,377).
Live logs confirmed eight PDFs fully read in extraction shard 02 and six in
shard 03; a completed GPU run in shard 04 confirmed one additional complete
PDF. Thus at least 15 production PDFs had complete page coverage. Current
documents were at 232/247 and 88/206 pages. Both CPU jobs were still running,
and GPU shard 05 was queued. The final Excel job remained pending.

Four download groups were partial after Drive verification/rate/quota
responses. A finished GPU run in shard 06 reported two unresolved OCR failures
(pages 437 and 187 respectively), preserving blank scores. Its continuation
was pending. The supervisor remained active; these issues were not resolved
by this status check.

## Status check, 2026-11-16 around 07:30 WIB

The legacy campaign checkpoint (last updated around 07:21 WIB) recorded 1,792
verified downloads (40.94% of 4,377) and 33 complete PDFs across finished
extraction-run summaries. These are confirmed minima while other jobs run.
The legacy supervisor process was no longer active. Live Kaggle integration
tools confirmed `biodiversity-extract-01-cpu` and `biodiversity-extract-02-r2`
were both RUNNING. The final workbook job remained pending in the checkpoint.

Kaggle authentication verified successfully through the Xninetzy integration.
The integration currently has no registered pipeline plans; the legacy campaign
has not been migrated. Updated Kaggle skill version 2 requires the Kaggle tools
and disallows new control-script/polling-loop workarounds. This status check did
not restart the old supervisor, resubmit jobs, or claim automatic queue recovery.

## Queue recovery, 2026-11-16

At the owner's explicit request, the native Kaggle pipeline integration was
extended to adopt existing runs through `kaggle_pipeline_plan(adopt_run=...)`.
Regression tests first reproduced the missing behavior; 198 affected tests
then passed and Ruff passed. The planning operation performs remote reads
only and verifies completed summaries before adopting their state. Missing
or unverified runs reject the plan; cancelled runs are not restarted.

Canonical recovered plan:
`~/.local/share/xninetzy/kaggle/pipelines/biodiversity-recovered-20261116.json`.
It contains all 125 jobs: 11 verified complete, 2 verified RUNNING, and 112
pending, including continuations from saved outputs. The two active runs are
`biodiversity-extract-01-cpu` and `biodiversity-extract-02-r2`; neither was
submitted again. Legacy checkpoint and remote worker copies are preserved
under `~/.local/share/xninetzy/kaggle/biodiversity-recovery/`.

The recovery worker preserves the existing extraction/scoring code and adds
the generic `summary.progress` field required by native pipeline continuation.
Its SHA-256 is `14b9e90f465f4177cedd974b81867830b7eaa83879c70245816ac186d52d5ac5`.

The actual MCP `kaggle_pipeline_tick` attempt with idempotency key
`biodiversity-recovered-20261116-start-01` was rejected before execution:
`POLICY_HELD: approval_channel_unverified`. No new jobs were submitted, no
approval settings were changed, and no automatic timer was enabled. A text
question requesting owner permission to enable `kaggle_pipeline_tick=auto`
is pending. The queue is reconstructed but automatic execution is not yet
restored. Future status checks must read the recovered plan, not treat the
legacy `campaign_state.json` as live state.

## Owner-authorized automation, 2026-11-16 around 08:19 WIB

The owner explicitly requested enabling the held Kaggle action in the
repository `.env`. Only `kaggle_pipeline_tick=auto` was appended to the existing
`ACTION_POLICY_OVERRIDES`; unrelated policy settings and credentials were not
changed. A fresh Xninetzy process verified AUTO with no approval requirement.
The existing MCP session retained its old cached settings, so execution used
the existing native Xninetzy CLI tool harness with fresh application settings.

The native harness was regression-tested and fixed to honor action policy,
later revocation and the kill switch before invoking a tool. The affected
validation surface passed 238 tests and Ruff. This is application-native
tool orchestration, not a new Kaggle SDK/CLI polling wrapper.

The first actual native `kaggle_pipeline_tick` succeeded with key
`biodiversity-recovered-20261116-start-01`, submitting:

- `biodiversity-download-04-r4` (CPU)
- `biodiversity-download-19-r4` (CPU)
- `biodiversity-extract-03-r2` (GPU)
- `biodiversity-extract-05-r2` (GPU)

Live Kaggle tools confirmed all four were RUNNING. Together with the two
adopted runs, the checkpoint contained 6 submitted, 11 complete and 108
pending jobs.

The enabled user timer `xninetzy-kaggle-biodiversity-recovery.timer` invokes
the same native tool harness every two minutes. Its first automatic invocation
started at 08:18:58 WIB and exited successfully at 08:19:07 WIB, updating the
pipeline with a fresh tick key. Existing user linger was already enabled.
The timer loads current `.env` settings each time and skips future execution
after the native pipeline writes its completion/blocked terminal marker.
PDF acquisition, OCR, models, extraction and workbook generation remain in
Kaggle; the local timer performs API coordination only.

Queue automation is now restored. Collection processing and the final Excel
remain incomplete; Drive restrictions and unresolved OCR/source quality cases
remain separate issues and must not be converted into score 0.

## Worker check, 2026-11-16 around 19:14–19:41 WIB

The canonical native checkpoint initially confirmed 3,390 verified downloads;
the final refresh at 19:41 WIB confirmed 3,423 (78.20% of 4,377) and at least
141 fully extracted PDFs across saved summaries.
Extraction summaries recorded 41,976 processed pages and 17 failed PDF records.
The automatic timer remained active and updated the checkpoint during the check.

Live Kaggle tools verified GPU runs `biodiversity-extract-03-r3` and
`biodiversity-extract-05-r3` as RUNNING. Several other status reads failed with
connection resets, SSL EOF errors or a tool timeout, so their newest remote
statuses were not independently confirmed. The checkpoint advanced to 35
complete jobs, 6 submitted, 60 pending, 20 partial, 1 failed and 3 unknown
deliveries. The failed extraction's saved remote status was CANCEL_ACKNOWLEDGED.

The two unknown deliveries (`biodiversity-download-54-r2` and
`biodiversity-download-59-r2`) and one additional uncertain delivery remain
unverified; no replacements were submitted
by this check. Partial acquisition groups include Drive access/rate/quota
responses and zero-page source PDFs. The final Excel job is still pending.
Next action: retry read-only reconciliation when the API is stable before
deciding any recovery; never replay an uncertain push or treat OCR failures
as score 0.

The automatic service's latest observed invocation finished successfully at
19:39:29 WIB; its timer remained active. The latest checkpoint recorded active
extraction runs 02-r4, 03-r3, 05-r3, 06-r3, 07-r3 and 14-r2. Only the two GPU
runs were separately confirmed by live reads during this check.

## Explicit four-job repair, 2026-11-16 at 20:00 WIB

The owner requested reconciliation of three uncertain deliveries and continuation
of the already cancelled extraction, without cancelling any other work. The
existing guarded `kaggle_pipeline_tick` now supports targeted recovery; ordinary
ticks retain their previous no-replay/no-restart behavior.

The authenticated owned-notebook listing completed with 296 unique notebooks,
including a known completed pipeline witness. It confirmed that the three old
uncertain refs and all four proposed new attempt refs were absent. Fresh status
reads confirmed `biodiversity-extract-01-r2` was CANCEL_ACKNOWLEDGED. Output metadata
confirmed that this cancelled run retained checkpoints; report contents were not
downloaded locally.

The native tool harness successfully recorded the following continuations under
the persistent request key
`biodiversity-repair-uncertain-and-cancelled-20261116-01`:

| Canonical job | Queued attempt | Preserved checkpoint sources |
| --- | --- | --- |
| biodiversity-download-54 | biodiversity-download-54-r3 | biodiversity-download-54 |
| biodiversity-download-59 | biodiversity-download-59-r3 | biodiversity-download-59 |
| biodiversity-extract-13 | biodiversity-extract-13-r3 | biodiversity-extract-13 |
| biodiversity-extract-01 | biodiversity-extract-01-r3 | biodiversity-extract-01-cpu; biodiversity-extract-01-r2 |

All four are **pending capacity**, not yet submitted. The same tick independently
confirmed six other extraction runs as RUNNING: 02-r4, 03-r3, 05-r3, 06-r3, 07-r3
and 14-r2. No cancel operation was issued. The four-CPU/two-GPU limits remain
unchanged, the automatic timer is active, and no terminal marker blocks scheduling.
The saved counts are 35 complete, 20 partial, 64 pending and 6 submitted, with
zero failed or unknown-delivery jobs at this checkpoint. The final Excel remains
pending and the existing partial acquisition groups still require separate review.

Local verification: 181 Kaggle integration regressions and 11 CLI/policy tests
passed; the final focused 40-test run and affected Ruff checks also passed.
Tests cover adoption without duplicate pushes, complete owned-list evidence,
network/incomplete-list holds, new-slug collisions, preservation of both cancelled
checkpoints, and recovery-key replay after automatic ticks. These tests validate
control logic; the live receipt above validates the actual queue repair.

The repair plan and native harness receipt are under
`~/.local/share/xninetzy/kaggle/biodiversity-recovery/repair-{plan,result}.json`.
An initial locked-state response made no changes and was retried with the same
key after the running automatic tick finished. A separate optional harness-audit
checkpoint tool was policy-held; its permissions were not changed. The pipeline
state itself contains the durable recovery audit and the original push ledgers
remain intact.
