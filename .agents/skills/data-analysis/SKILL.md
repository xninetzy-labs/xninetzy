---
name: data-analysis
description: Use when the user provides tabular data (CSV/XLSX) and wants profiling,
  quality audit, table generation, or dashboard generation. Forces data-first workflow
  profile → quality → analyze → artifact rather than ad-hoc Excel manipulation.
metadata:
  type: workflow
  domain: data_intelligence
  capabilities: '["data_profile","data_quality_audit","data_generate_xlsx","data_validate_xlsx","dashboard_generate","dashboard_validate","dashboard_list_providers"]'
  version: 1.0.0
---


# Data Intelligence Workflow

Use this skill when the request maps to any of these:

- profile a CSV/XLSX file
- audit data quality
- generate a table artifact (XLSX)
- generate a dashboard

Do NOT call individual cell-level Excel APIs. The data subsystem
exposes capabilities, not low-level primitives.

## Decision tree

```text
user request
   ├── has a file → data_profile → data_quality_audit
   ├── needs table → data_generate_xlsx → data_validate_xlsx
   └── needs dashboard → dashboard_generate → dashboard_validate
```

## Step 1. Profile

Call `data_profile` first. Do not skip profiling even when the file
"looks fine" — quality issues are often invisible until measured.

If profiling reports `row_count = 0` or `column_count = 0`, stop and
ask the user for a different file.

## Step 2. Quality

Call `data_quality_audit` after profiling. Read every issue. If any
issue has `severity == "high"`, surface it to the user BEFORE
proceeding to analysis. Do not silently accept bad data.

## Step 3. Analysis vs artifact vs dashboard

| User intent | Capability |
|---|---|
| "show me what's in this file" | profile + quality only |
| "give me a spreadsheet" | `data_generate_xlsx` |
| "give me a dashboard" | `dashboard_generate` |

## Step 4. Dashboard

When generating a dashboard:

1. List providers with `dashboard_list_providers` if user is unsure.
2. Default provider is `native_echarts`. Do NOT recommend Superset /
   Metabase / Grafana unless the user explicitly asks for external BI.
3. Always pass `dataset_id` matching the profiled dataset id.
4. Each widget must declare: `dimensions`, `measures`, `aggregation`.
   Do not invent columns not in the profile.
5. Validate the artifact with `dashboard_validate` before declaring
   success.

## Step 5. Reporting

Always report:

- row count
- column count
- quality scores
- chosen provider
- artifact path
- validation status

Do not claim "done" without validation status == "valid".

## Non-negotiable rules

- Never claim an artifact exists without validation.
- Never silently coerce bad data.
- Never choose a provider the user did not opt into for external BI.
- Never bypass the profile → quality → generate → validate chain.
