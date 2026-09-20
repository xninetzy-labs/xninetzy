---
layout: ../../layouts/DocsLayout.astro
title: Data intelligence & dashboards
description: Data ingestion, profiling, quality, table artifacts, and provider-independent dashboard generation.
section: Operations
badge: Reference
difficulty: intermediate
readingTime: 10 min
---

The data subsystem turns CSV/XLSX inputs into **profiled, quality-
audited, reproducible artifacts** and **provider-independent
dashboards**. The architecture favors capability-level abstractions
over low-level dataframe primitives.

```text
USER
  ↓
INTENT
  ↓
DATA SUBSYSTEM
  ├── ingestion      (format detection + checksum)
  ├── profiling      (per-column type, null, uniqueness, semantic hint)
  ├── quality        (4-dimension scoring + severity-ranked issues)
  ├── analysis       (deterministic computation)
  ├── artifact       (XLSX TableArtifact with reopen-validation)
  └── dashboard
        ├── DashboardSpec   (provider-independent)
        └── ProviderRouter
              ├── NativeEChartsProvider  (default, no external dep)
              ├── Superset (future, opt-in)
              ├── Metabase (future, opt-in)
              └── Evidence / Grafana (future, opt-in)
```

## 1. Ingestion

`xninetzy/context/data_analysis/dataset.py::detect_format` inspects
file signatures, not only suffixes. Supported today: `csv`, `tsv`,
`xlsx`, `xls`, `json`, `jsonl`, `parquet`, `sqlite`. Profiling +
quality audit currently cover `csv` and `xlsx`; other formats raise
`ValueError("unsupported format for profiling: ...")` until their
adapter lands.

Every dataset gets a `dataset_id = "ds-<12-hex>"` and a `sha256`
checksum on ingest.

## 2. Profiling

`profile_dataset(path)` returns `DatasetSummary`:

- `row_count`, `column_count`, `checksum`
- `ColumnProfile` per column: `physical_type`, `semantic_type`
  (identifier / measure / temporal / categorical / boolean),
  `nullable`, `unique_count`, `null_count`, `example_values`.

Semantic type inference is heuristic (`id`/`uuid`→identifier, `date`/
`time`/`created`→temporal, `amount`/`price`/`revenue`→measure). It
is **not** authoritative — the column is marked with a confidence
free-text in `provenance` if you need to override it later.

## 3. Quality

`audit_quality(summary)` returns `QualityReport` with four scores:

| Dimension | What it measures | Default if missing |
|---|---|---|
| `completeness` | null fraction across columns | `1.0` |
| `validity` | nullability + type adherence | `1.0` |
| `uniqueness` | unique / total ratio | `1.0` |
| `consistency` | reserved for schema-drift detection | `1.0` |

`passed == True` iff no issue has `severity == "high"`. Issues are
tuples of `QualityIssue(dimension, column, severity, description,
affected_rows)`.

## 4. TableArtifact

`xninetzy/context/data_analysis/table_artifact.py`:

- `generate_xlsx_artifact(path, name, rows, source, transformation)`
  writes a real `.xlsx` via `openpyxl` and returns a `TableArtifact`
  with `artifact_id`, `schema`, `row_count`, `checksum`.
- `validate_xlsx_artifact(artifact)` reopens the file with `openpyxl`,
  compares the header row to `artifact.schema`, the row count to
  `artifact.row_count`, and reports `validation_status` ∈
  `{valid, missing, corrupt, empty, schema_mismatch, row_count_mismatch}`.

Never declare success without `validation_status == "valid"`.

## 5. DashboardSpec

`DashboardSpec` is a frozen dataclass containing `dashboard_id`,
`title`, `description`, `dataset_id`, and a tuple of `Widget`s. Each
`Widget` declares:

- `type` ∈ `kpi, bar, line, table, pie, scatter, heatmap`
- `dimensions` (group-by), `measures` (aggregation targets)
- `aggregation` ∈ `sum, avg, count, count_distinct, min, max, median`
- `filters`, `limit`, `position`

The spec is **provider-independent**. Rendering is the provider's job.

## 6. Provider abstraction

`DashboardProvider` ABC requires `render(spec, dataset_payload) -> str`
and `write(spec, payload, path) -> DashboardArtifact`, plus
`validate(artifact)` which checks the file exists, is non-empty,
and carries the matching `data-dashboard-id` attribute.

`DashboardProviderRegistry` is a tiny dict-backed registry. The default
registry ships with one provider:

### NativeEChartsProvider (default)

- Renders standalone HTML using the Apache ECharts CDN (5.5.0).
- Each widget gets a `<section class="xninetzy-widget">` with a chart
  div + a JSON option block.
- Renders the dashboard even with zero rows (renders an empty-state
  message).
- Does NOT install any Python deps beyond what the repo already ships
  (no `pyecharts`, no `plotly`).
- No authentication, no remote calls.

`supported_formats = ("html",)`,
`supported_capabilities = ("dashboard_as_html", "interactive_chart", "standalone")`.

### Future providers

`Superset`, `Metabase`, `Evidence`, `Grafana` are **opt-in**. They
must satisfy the `DashboardProvider` contract before registration.
No provider-specific metadata leaks into the spec.

## 7. MCP tools

| Tool | Use |
|---|---|
| `data_profile` | Profile a CSV or XLSX |
| `data_quality_audit` | Run 4-dim audit |
| `data_generate_xlsx` | Write a TableArtifact |
| `data_validate_xlsx` | Reopen + verify XLSX |
| `dashboard_generate` | Render spec → HTML artifact |
| `dashboard_validate` | Reopen + verify HTML |
| `dashboard_list_providers` | List registered providers |

Total registered tools: **392** (audit-script-verified).

## 8. Skill

`.agents/skills/data-analysis/SKILL.md` is the workflow contract:

1. profile first
2. audit quality second
3. stop on `severity == "high"`
4. only then generate artifact / dashboard
5. always validate before declaring done

## 9. Configuration

| Env var | Default | Purpose |
|---|---|---|
| `XNINETZY_DASHBOARD_DEFAULT_PROVIDER` | `native_echarts` | Provider ID for `dashboard_generate` when not specified |
| `XNINETZY_DASHBOARD_OUTPUT_DIR` | `~/Documents/xninetzy/generated/dashboards` | Where dashboards are written by default |

(These envs are read by future routing. The default registry ships
with `native_echarts` only.)

## 10. Tests

| File | Covers |
|---|---|
| `tests/data_analysis/test_profiling.py` | CSV + XLSX profile, format detect |
| `tests/data_analysis/test_quality.py` | 4-dim scoring + severity |
| `tests/data_analysis/test_table_artifact.py` | XLSX round-trip + corrupt detect |
| `tests/data_analysis/test_dashboard.py` | DashboardSpec, NativeEChartsProvider, registry, validation |

## 11. Out of scope today

- DuckDB / Polars / PyArrow engines (not yet installed; will land via
  the `pyproject.toml` extras group when the provider router demands
  them).
- Superset / Metabase / Evidence / Grafana providers (intentionally not
  installed; each requires its own dependency + license review before
  registration).
- Streaming for > RAM datasets (Phase-1 assumes ≤ 100k rows per profile).
- ML layer (descriptive analytics only for now).

## 12. Failure containment

| Failure | Behavior |
|---|---|
| Unknown format | `ValueError` raised, surfaced via tool error |
| Empty file | `validation_status = "empty"` |
| Corrupt XLSX | `validation_status = "corrupt"` |
| Schema drift | `validation_status = "schema_mismatch"` |
| Row-count drift | `validation_status = "row_count_mismatch"` |
| Missing artifact file | `validation_status = "missing"` |
| Missing dashboard provider | tool returns `{error, available}` |
