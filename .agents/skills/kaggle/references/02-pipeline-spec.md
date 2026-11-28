# kaggle — Pipeline spec

## Plan

```text
kaggle_pipeline_plan(
  name="pdf-scan",
  limits={"cpu": 4, "gpu": 1},
  jobs=[
    {"slug": "pdf-download-01", "source_path": "pdf/download.py",
     "params": {"root": "folder-1"}, "max_attempts": 8, "summary_required": true},
    {"slug": "pdf-extract-01", "source_path": "pdf/extract.py",
     "depends_on": ["pdf-download-01"], "accelerator": "gpu_or_cpu",
     "max_attempts": 8, "summary_required": true},
    {"slug": "pdf-merge", "source_path": "pdf/merge.py", "depends_on": ["pdf-extract-01"]}
  ])
```

`source_path` is relative to the Kaggle workspace (`~/.local/share/xninetzy/kaggle`) or absolute inside it or inside a root listed in `KAGGLE_SOURCE_ROOTS`. A job may pass inline `source` instead; it is stored under the workspace.

## Job fields

| Field | Default | Meaning |
| --- | --- | --- |
| `slug` | required | Lowercase letters, digits and hyphens, 5 to 45 characters, unique in the plan. |
| `source_path` or `source` | exactly one | The worker script. |
| `params` | `{}` | Merged into `JOB`. JSON types only. |
| `depends_on` | `[]` | Job slugs that must be `complete` first. |
| `mount_dependencies` | `true` | Mount each dependency's latest run as a kernel source. |
| `adopt_run` | unset | Verify and adopt an existing kernel in the authenticated account without submitting it again. |
| `adopt_gpu` | `false` | GPU allocation of the existing run, for concurrency accounting during adoption. |
| `adopt_run` | unset | Verify and adopt an existing kernel in the authenticated account without submitting it again. |
| `adopt_gpu` | `false` | GPU allocation of the existing run, for concurrency accounting during adoption. |
| `kernel_sources`, `dataset_sources` | `[]` | Extra inputs (`owner/slug`; bare kernel slugs resolve to your account). |
| `accelerator` | `none` | `gpu` waits for GPU capacity; `gpu_or_cpu` falls back to CPU; `none` stays on CPU. |
| `internet` | `true` | Kernel internet access. |
| `time_budget_seconds` | `3600` | 60 to 43200. |
| `max_attempts` | `1` | Total runs including continuations (1 to 32). |
| `summary_required` | `false` | Treat a missing `summary.json` as `partial`. |

Unknown keys are rejected so typos fail at plan time. `limits.cpu` is 1 to 5 (default 4); `limits.gpu` is 0 to 2 (default 1).

Adoption explicitly reads the existing run's status and completed `summary.json`.
Running jobs become `submitted`, complete outputs are reused, and partial outputs
become continuations with their existing attempt number and previous output.
Missing or unverified runs reject the plan without pushing a replacement;
cancelled or errored runs remain terminal. Planning without adoption stays local.

Adoption explicitly reads the existing run's status and completed `summary.json`.
Running jobs become `submitted`, complete outputs are reused, and partial outputs
become continuations with their existing attempt number and previous output.
Missing or unverified runs reject the plan without pushing a replacement;
cancelled or errored runs remain terminal. Planning without adoption stays local.

## Plan lifecycle

- Planning the same spec again returns `unchanged`.
- A different spec under an existing name needs `replace=true`, and only while no job has been submitted.
- Once any job was submitted, plan a new pipeline name for changed work.

## Tick loop

1. `kaggle_pipeline_tick(name, idempotency_key="<name>-<timestamp>")`.
2. Read `submitted`, `finished`, `needs_attention`, `done`, `blocked`, `next_tick_seconds`.
3. If `done` or `blocked`, stop. Otherwise schedule the next tick after `next_tick_seconds`.

A tick is safe to repeat. It never pushes a job twice: each push goes through the kernel ledger with the key `pipeline:<name>:<run slug>`. Rejections caused by Kaggle's batch or quota limits keep the job `pending` and back off 60 seconds (CPU) or 300 seconds (GPU). Other rejections mark the job `failed`.

## State meanings

| State | Meaning | Next action |
| --- | --- | --- |
| `pending` | Waiting for dependencies, capacity or a backoff. | Tick again. |
| `submitting` | Push issued, outcome not yet confirmed. | The next tick confirms it. |
| `submitted` | Kernel exists on Kaggle (`remote_status` shows queued or running). | Tick again. |
| `complete` | Finished and `summary.json` (if any) says complete. | None. |
| `partial` | Finished but incomplete, with no progress or out of attempts. | Inspect the output, fix, plan a new name. |
| `failed` | Kaggle errored or cancelled the kernel, or refused the push. | Read `failure`, fix, plan a new name. |
| `unknown_delivery` | A push may have landed but no kernel was found. | Check Kaggle by hand; never replay. |
