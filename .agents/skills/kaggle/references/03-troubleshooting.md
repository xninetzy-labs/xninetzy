# kaggle — Troubleshooting

| Code or status | Meaning | Action |
| --- | --- | --- |
| `KAGGLE_AUTH_REQUIRED` / `auth_required` | No Kaggle credentials found. | Ask the owner to run `kaggle auth login`, set `KAGGLE_API_TOKEN`, or start `auth_session_create(provider='kaggle')`. |
| `KAGGLE_SDK_MISSING` | No interpreter with the `kaggle` package. | Ask the owner to run `python3 -m pip install --user kaggle`, or set `KAGGLE_PYTHON` to an interpreter that has it. |
| `KAGGLE_RUNNER_TIMEOUT` | The Kaggle call exceeded `KAGGLE_RUNNER_TIMEOUT_SECONDS`. For a push the result is unknown. | Check `kaggle_kernel_status`; do not repeat the push blindly. |
| `KAGGLE_RUNNER_PROTOCOL` | The runner returned malformed output. | Treat a push as unknown; retry reads. |
| `POLICY_HELD` | The tool is a write and the owner has not enabled it. | Report it; the owner approves or sets `ACTION_POLICY_OVERRIDES`. |
| `idempotency_key_required` | A write tool was called without a key. | Add a non-empty key. |
| `not_accessible` | Dataset or kernel is missing or private (Kaggle returns 403 or 404). | Check the ref and the account; do not claim non-existence. |
| `KAGGLE_DATASET_TOO_LARGE` | Dataset exceeds `max_bytes`. | Process it inside a kernel, or raise `max_bytes` on purpose. |
| `KAGGLE_IDEMPOTENCY_KEY_REUSED` | Same key, different payload. | Use a new key for the new action. |
| `KAGGLE_DELIVERY_UNKNOWN` | An earlier attempt with this key has no confirmed outcome. | Check `kaggle_kernel_status` and Kaggle itself first. |
| `KAGGLE_PUSH_REJECTED` | Kaggle refused the push (limits, invalid sources). | Read `message` and `invalid`; Kaggle's batch limit clears when running sessions finish. |
| `KAGGLE_SOURCE_OUTSIDE_ROOTS` | `source_path` is outside the allowed roots. | Move the file into the Kaggle workspace or add a root to `KAGGLE_SOURCE_ROOTS`. |
| `KAGGLE_STATE_LOCKED` | Another operation holds the state file. | Retry shortly. |
| `KAGGLE_PIPELINE_EXISTS` / `KAGGLE_PIPELINE_ACTIVE` | Name already planned or already started. | Use `replace=true` before any submission, otherwise a new name. |

Kernel status values: `NEW_SCRIPT`, `QUEUED`, `RUNNING` (active), `COMPLETE` (success), `ERROR`, `CANCEL_ACKNOWLEDGED` (final), `CANCEL_REQUESTED` (a cancel is in flight). Unknown values are treated as still running.

Settings: `KAGGLE_PYTHON`, `KAGGLE_WORKSPACE_DIR` (default `~/.local/share/xninetzy/kaggle`), `KAGGLE_SOURCE_ROOTS` (comma-separated extra source roots), `KAGGLE_RUNNER_TIMEOUT_SECONDS` (default 180).

State on disk (all under the workspace): `ledger/pushes.json` (push receipts by key), `pipelines/<name>.json` (plan and live state), `registry/datasets.json` (registered capabilities), `datasets/<owner>/<slug>/` (downloads).
