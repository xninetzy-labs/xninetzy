---
name: kaggle
description: Runs Kaggle work through Xninetzy tools instead of new scripts. Searches and downloads datasets, pushes and monitors CPU/GPU kernels, reads outputs and runs dependent job pipelines. Use for any Kaggle dataset, notebook or remote-compute task.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: 2.0.0
  lifecycle: auth-check -> search -> inspect -> download | push -> status -> output -> pipeline-tick
  triggers: kaggle dataset notebook kernel gpu tpu quota pipeline remote compute push status output download olistbr
  keywords: accelerator campaign continuation dependency idempotency job summary worker workspace
---

## Rule

Kaggle work is done with the `kaggle_*` tools. Do not write `control.py`, supervisors, polling loops or `kaggle` CLI wrappers. The only code you author for a task is the remote worker that runs inside Kaggle. If a Kaggle operation the task needs has no tool, extend `xninetzy/integrations/kaggle/` and register a tool; do not script around the gap.

Credentials come from the Kaggle CLI configuration (`~/.kaggle/access_token`, `kaggle.json`), `KAGGLE_API_TOKEN`, `KAGGLE_USERNAME` with `KAGGLE_KEY`, or an Xninetzy auth session. Never accept or print credentials, and never put secrets in worker source, `job` parameters or logs.

## Tool map

| Need | Tool | Risk |
| --- | --- | --- |
| Is Kaggle usable, who am I, GPU quota | `kaggle_auth_status(verify=true)`, `kaggle_capabilities(include_quota=true)` | read |
| Find datasets | `kaggle_dataset_search` | read |
| Metadata and file list | `kaggle_dataset_get` | read |
| Pre-flight checks (accessible, has files, size limit) | `kaggle_dataset_validate` | read |
| Local copy for small data | `kaggle_dataset_download` | write |
| Remember a dataset for a capability | `kaggle_dataset_register` | write |
| Run code on Kaggle | `kaggle_kernel_push` | write |
| Kernel state | `kaggle_kernel_status` | read |
| Kernel files, small file contents, log tail | `kaggle_kernel_output` | read |
| Several dependent jobs | `kaggle_pipeline_plan`, `kaggle_pipeline_status`, `kaggle_pipeline_tick` | draft, read, write |

Reads and `kaggle_pipeline_plan` run without approval. Write tools need a non-empty `idempotency_key`, and under the default `ACTION_POLICY_DEFAULT_MODE=approval` they are held (`POLICY_HELD`) until the owner approves or sets `ACTION_POLICY_OVERRIDES=kaggle_kernel_push=auto,kaggle_pipeline_tick=auto`. That setting is the owner's decision; report the hold and ask, never edit settings yourself.

## Dataset workflow

1. `kaggle_auth_status(verify=true)`. On `KAGGLE_AUTH_REQUIRED` stop and relay `next_steps`.
2. `kaggle_dataset_search`, then `kaggle_dataset_get` on the chosen ref.
3. `kaggle_dataset_validate`. `not_accessible` means missing or private; Kaggle answers 403 for both, so never claim a dataset does not exist.
4. Small data you must inspect locally: `kaggle_dataset_download` (default limit 2 GiB, raise `max_bytes` only deliberately), then `data_profile` and `data_quality_audit`. Large data: process it inside a kernel with `dataset_sources`, not locally.

## Run code on Kaggle

1. Write the worker to `~/.local/share/xninetzy/kaggle/<task>/worker.py` (or pass `source` inline when under about 48 KB). A worker reads its parameters from the injected `JOB` dict and, when it can be resumed or checked, writes `/kaggle/working/summary.json`. See `references/01-worker-contract.md`.
2. `kaggle_kernel_push(slug, source_path, job, gpu, dataset_sources, kernel_sources, time_budget_seconds, idempotency_key)`. Kernels are private scripts. Choose the `idempotency_key` for the intended action once and reuse it on retries of that same action.
3. Poll `kaggle_kernel_status`. Wait with the harness scheduler (Claude Code: `ScheduleWakeup` or `/loop`); do not busy-poll.
4. `kaggle_kernel_output(read=["summary.json"], log_tail_chars=2000)`. Add `live_log_seconds` (up to 60) to sample the live log of a running kernel. Fetch only small files; leave reports, models and spreadsheets in Kaggle.

Push outcomes: `submitted` (receipt with `url`, `version`), `rejected` (Kaggle refused; fix the cause, same key may be retried), `unknown_delivery` (the call may have landed; check `kaggle_kernel_status`, then use a new key only after confirming no kernel was created), `error` (nothing was sent), `auth_required`, `invalid_input`.

## Pipelines (several jobs, dependencies, resumable work)

1. `kaggle_pipeline_plan(name, jobs, limits)` validates the DAG, the sources and the limits and stores the plan locally. It never touches Kaggle. Job fields and a full example are in `references/02-pipeline-spec.md`.
2. `kaggle_pipeline_tick(name, idempotency_key)` reconciles running kernels, reads each finished kernel's `summary.json`, schedules continuations, and submits ready jobs within the CPU/GPU limits and the live GPU quota. Use a fresh key per tick (for example `<name>-<UTC timestamp>`); the same key replays the stored result without new calls.
3. Repeat the tick after `next_tick_seconds` using the harness scheduler. Stop when `done` is true or `blocked` is true.
4. `kaggle_pipeline_status` reads the stored state without any Kaggle call, including `needs_attention`.

Job states: `pending`, `submitting`, `submitted`, `complete`, `partial`, `failed`, `unknown_delivery`. `failed`, `partial` and `unknown_delivery` need a decision: inspect with `kaggle_kernel_output`, fix the worker or inputs, and plan a new pipeline name. A cancelled or errored kernel is final and is never restarted automatically; `unknown_delivery` is never replayed.

## Invariants

- Replay safety: every push is recorded in a local ledger keyed by `idempotency_key` plus payload hash. A repeated key replays the stored receipt; the same key with a different payload is rejected.
- Quota: an unknown GPU quota never authorizes a GPU job. `gpu_or_cpu` jobs fall back to CPU; `gpu` jobs wait.
- Never make a kernel public, never run graded exams, and never bypass Kaggle limits or Drive and site access controls.
- Report what was verified. A fake-backend test proves tool logic, not a live Kaggle run; say which one you observed.

## Detailed references

- `references/01-worker-contract.md`: `JOB`, `summary.json`, resumable workers, input and output paths.
- `references/02-pipeline-spec.md`: job fields, limits, example plan, tick loop, state meanings.
- `references/03-troubleshooting.md`: error codes and what to do.
