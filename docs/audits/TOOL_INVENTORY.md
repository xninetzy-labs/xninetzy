# Tool inventory and audit contract

Recorded 2026-11-10 against checkout `2d0f13f` plus this local audit change.
Evidence labels follow `CURRENT_SYSTEM_TRUTH.md`.

The complete generated inventory is [tool_inventory.json](tool_inventory.json).
It contains one record per registered canonical name with registry groups,
implementation module, description, input schema, inferred output schema,
manifest, and explicit `UNKNOWN` values for metadata not established by this
inspection. No tool handlers or external providers were invoked to generate it.

## Observed surface

| Metric | Value | Evidence |
|---|---:|---|
| Registered tools | 571 | `VERIFIED_RUNTIME`: `get_all_tools()` |
| READ / DRAFT / WRITE / FINAL | 43 / 23 / 501 / 4 | `VERIFIED_RUNTIME`: manifest declarations |
| Registry groups | 34 | `VERIFIED_RUNTIME`: `get_tool_groups()` |
| Tools without a group membership | 244 | `VERIFIED_RUNTIME`: inventory comparison |
| Tools labelled stable | 571 | `VERIFIED_CODE`: manifest default; not a readiness assessment |
| Inferred output schemas with a top-level `type` | 0 / 571 | `VERIFIED_RUNTIME`: LangChain schema inspection |
| Declared WRITE/FINAL tools without an `idempotency_key` input field | 430 / 505 | `VERIFIED_RUNTIME`: input schema comparison |
| Declared FINAL tools without an `approval_id` input field | 1 / 4 | `VERIFIED_RUNTIME`: `tableau_publish_workbook` schema |
| Live provider availability, cost, coverage, consumer ownership | UNKNOWN | Not measured by registry inspection |

Input fields do not establish enforcement. A tool can enforce idempotency or
approval in a shared service or use another parameter; absence of these names
does not demonstrate a bypass. Conversely, manifest `requires_idempotency=true`
does not prove reservation or replay protection. Risk and stability metadata
remain partly name-derived (`manifest_for` → `classify_risk`). No tool was
removed or reclassified in this batch.

The input schemas here are registry schemas. The MCP adapter removes trusted
identity fields from its public callable signatures and injects server context.
The output schemas are LangChain inference, not verified MCP `outputSchema`
contracts or evidence that runtime results are validated.

## Strict audit correction

`VERIFIED_RUNTIME`: before this change, `scripts/mcp_audit.py --strict --json`
exited 1 solely because `tableau_publish_workbook` was a fourth FINAL tool while
the script expected exactly three historical names. The actual registry was
otherwise accepted by its metadata checks.

The strict gate now requires these consequential tools to remain FINAL:

- `hebat_upload_submission`
- `portal_krs_war_arm`
- `qa_fill_kuesioner`
- `tableau_publish_workbook`

Additional FINAL tools are allowed. All FINAL declarations must require
approval, all WRITE/FINAL declarations must require idempotency, and duplicate
canonical names fail the audit. This is a metadata integrity gate; successful
execution does not certify independent enforcement inside every tool.

The existing human-readable and `--json` output shapes retain their prior
fields; `missing_approval` and `duplicate_names` are additive. `--inventory`
adds the full inventory and emits JSON to stdout. There is no install or
configuration mutation command.

## Reproduction and verification

Executed in the existing `.venv` with Python 3.14.5, MCP SDK 1.30.0,
LangChain Core 1.6.3, and pytest 9.1.1. The runner set `MCP_RUNTIME_MODE=container`,
pointed SQLite and writable data paths at a fresh temporary directory, disabled
automatic memory/graph/improvement, and set `Settings.model_config['env_file']`
to `None` before accessing settings. Production configuration and databases
were not edited. These are local registry checks, not a clean installation.

Commands within that isolated process:

```text
pytest -q tests/tools/test_mcp_audit.py --tb=short
pytest -q tests/tools/test_mcp_audit.py tests/tools/test_tool_manifest.py tests/tools/test_registry_contract.py --tb=short
python scripts/mcp_audit.py --strict --inventory
ruff check scripts/mcp_audit.py tests/tools/test_mcp_audit.py
```

| Check | Before | After |
|---|---|---|
| New audit regression tests | 6 failed | 6 passed |
| Focused audit + manifest + registry suite | NOT_MEASURED as combined pre-change suite | 25 passed in 6.00s |
| Live registry strict audit | Exit 1: stale FINAL list | Exit 0 |
| Inventory completeness | No schema inventory option | 571 unique names, 571 records |
| Scoped Ruff | NOT_MEASURED before | All checks passed |
| Provider execution / mutation safety | NOT_MEASURED | NOT_MEASURED |
| Latency improvement | NOT_MEASURED | NOT_MEASURED |

The tests explicitly cover an added FINAL tool, a missing/downgraded required
tool, a FINAL declaration missing approval, duplicate names, non-executing
schema inspection, and JSON CLI output. Test expectations were written and
observed failing before implementation. No skips or xfails were added.

## Rationalization backlog

1. P1: reconcile the 244 registered tools outside current domain groups against
   existing capability routing before adding another registry.
2. P1: trace approval/idempotency enforcement through representative real
   mutation paths; fix independently proven gaps with domain regression tests.
3. P1: establish meaningful typed output contracts incrementally on critical
   tools; avoid applying a broad schema rewrite to all 571 tools.
4. P2: record tested aliases, dependencies, stability ownership, provider
   availability, and consumer workflows in existing canonical metadata.

All recommendations retain MCP-first, CPU-only, local-first operation and use
the current registry. No new database, provider, agent runtime, or tool was
introduced.

## Rollback and limitations

Files changed in this batch: `scripts/mcp_audit.py`,
`tests/tools/test_mcp_audit.py`, this report, and `tool_inventory.json`.
There are no migrations or public tool signature changes. Rollback consists
of reverting only those reviewable file changes; retain unrelated preexisting
workspace changes. Reverting the script restores the historical strict false
positive. The JSON is a dated snapshot and must be regenerated after registry
changes. No release readiness or end-to-end user success is inferred from it.
