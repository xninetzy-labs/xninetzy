# kaggle — Worker contract

A worker is a plain Python script that runs inside a private Kaggle kernel. `kaggle_kernel_push` and `kaggle_pipeline_tick` prepend one line to it, after any `from __future__` imports:

```python
JOB = {"time_budget_seconds": 3600, "source_sha256": "<hash of your source>", ...your job parameters...}
```

The pipeline engine adds `_pipeline`, `_slug`, `_attempt` and `_previous` (the run slugs whose outputs are mounted for a continuation). Your own `job` or `params` keys are passed through unchanged. Values must be JSON types: strings, numbers, booleans, null, lists and objects.

## Paths inside Kaggle

| Path | Meaning |
| --- | --- |
| `/kaggle/working/` | Output directory. Everything written here becomes the kernel output. |
| `/kaggle/input/<dataset-slug>/` | A dataset passed in `dataset_sources`. |
| `/kaggle/input/<kernel-slug>/` | Output of a kernel passed in `kernel_sources`, or of a pipeline dependency, or of the previous attempt. |

## summary.json

Write `/kaggle/working/summary.json` last. `kaggle_pipeline_tick` reads it (at most 64 KiB) when the kernel completes.

```json
{"complete": true}
{"complete": false, "progress": 120, "deferred": {"retry_after_seconds": 1800}}
```

| Field | Meaning |
| --- | --- |
| `complete` | `true` ends the job as `complete`. `false` means more work remains. If the key is absent the job is complete unless the job sets `summary_required: true`. |
| `progress` | A number that grows as work advances (pages, files, rows). Two consecutive attempts without growth end the job as `partial`, which prevents endless continuations. |
| `deferred.retry_after_seconds` | Hold the next continuation for this long, for example after a rate limit. |

Any other keys are kept (bounded to about 6 KB) and shown in `kaggle_pipeline_status`.

## Resumable workers

Set `max_attempts` above 1 and `summary_required: true`. On a continuation the previous attempt's output is mounted at `/kaggle/input/<previous run slug>/` (the slug is in `JOB["_previous"]`). Copy finished results forward instead of redoing them, and checkpoint at stable boundaries so a kernel that hits its time budget leaves usable state.

## Budget

`time_budget_seconds` is the time your worker should plan for (60 to 43200). Kaggle receives that value plus 240 seconds as the hard timeout. A GPU job's budget is capped by the remaining GPU quota minus 300 seconds.

## Keep outputs small to read, large to keep

Leave reports, models and spreadsheets in the kernel output. Read back only status and small JSON through `kaggle_kernel_output(read=[...])`. A single call returns at most about 24 KB of file content.
