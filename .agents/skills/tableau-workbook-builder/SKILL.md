---
name: tableau-workbook-builder
description: Build Tableau .twb / .twbx workbooks declaratively from CSV inputs via the xninetzy Tableau integration. Use when the user asks for a Tableau dashboard, .twb generation, Tableau storyboard, or wants to compile KPIs / maps / heatmaps without opening Tableau Desktop.
metadata:
  domain: "tableau"
  inputs: "csv_paths, visualization_specs, optional template"
  outputs: "twb_file_in_workspace, optional twbx_archive"
  tier: "2"
---

# tableau-workbook-builder

End-to-end pipeline that takes CSV inputs + visualization specs and produces a
Tableau-compatible `.twb` XML document, validates it, and (optionally) packages
the workbook plus resources into a `.twbx` archive. Built on the
`xninetzy.integrations.tableau` package and exposed through the MCP tools
`tableau_*`.

## When to use

- User wants a Tableau workbook built from data they already have on disk.
- User wants KPI cards, a country/state map, monthly trend, top-N bar,
  scatter, or state-by-month heatmap layout that matches the reference
  workbook shipped with this skill.
- User wants to package a `.twb` plus extra CSV resources into a `.twbx`
  distribution archive.
- AVD-praktikum style "Analisis dan Visualisasi Data" deliverables.

## Pipeline

```
CSV inputs  ─►  tableau_workbook_generate  ─►  /.../workbooks/<name>/<name>.twb
                                              │
                                              ├─► tableau_workbook_validate  (smoke check)
                                              ├─► tableau_worksheet_*       (mutations)
                                              ├─► tableau_dashboard_*       (layout)
                                              └─► tableau_twbx_package      (distribution)
```

All tools are STABLE except the write tools (WRITE tier, require
`idempotency_key`). See `manifest_for(name)` for the exact stability class.

## Supported visualization types

`bar`, `line`, `area`, `circle`, `square`, `map`, `kpi`, `pie`, `scatter`,
`heatmap`, `table`.

Each spec is a dict:

```json
{
  "type": "bar",
  "name": "top_categories",
  "rows": ["product_category_en"],
  "measure": "price",
  "measure_aggregation": "SUM",
  "color": "review_score"
}
```

Aggregation defaults to `SUM`. Valid values: `SUM`, `AVG` (`AVERAGE`, `MEAN`),
`COUNT`, `COUNTD`, `MIN`, `MAX`, `MEDIAN`. Use `COUNTD` for distinct counts;
`CountDistinct` is rejected. On a text field only `COUNT`, `COUNTD`, `MIN`
and `MAX` apply; anything else falls back to `COUNT`.

Orientation: put the dimension in `cols` for vertical bars and in `rows` for
horizontal bars. For `line` and `area` a dimension given in `rows` is moved to
the columns shelf so time runs on the x axis.

Dates: a `date` field defaults to `YEAR` (discrete) and to `MONTH` truncation on
`line`/`area`. Set `date_level` (`year`, `quarter`, `month`, `week`, `day`) to
force continuous truncation at that level, for example `day` for a daily series.
Values such as `2018-03` are text, not dates, and are never given a date
derivation.

`top_n` is not supported by the generator and raises `VIZ_OPTION_UNSUPPORTED`.
Pre-bucket the category in the CSV (keep the top N, label the rest) or add the
Top N filter in Tableau Desktop.

## Reference deliverable: AVD-praktikum "Olist" workbook

The canonical reference build drops nine worksheets into one dashboard and
captures four story points. Use this template when the user asks for an
"Olist-style" or "AVD-praktikum" workbook.

```python
from xninetzy.tools.ecosystem.tableau_tools import (
    tableau_workbook_generate,
    tableau_dashboard_create,
    tableau_story_create,
    tableau_twbx_package,
)

result = tableau_workbook_generate.invoke({
    "csv_paths": ["~/Documents/.../olist_merged.csv"],
    "name": "olist_avd_praktikum",
    "dashboard_title": "Olist E-Commerce Dashboard",
    "story_points": [
        "Brazilian E-Commerce grew 3x in 2 years",
        "North/Northeast states have 15-25% late delivery rate",
        "Top 15 categories = 60% of total revenue",
        "Action: prioritize SP/RJ sellers for north region",
    ],
    "visualizations": [
        {"type": "kpi",   "name": "01_KPI_Orders",    "measure": "order_id",        "measure_aggregation": "COUNTD"},
        {"type": "kpi",   "name": "02_KPI_Revenue",   "measure": "price"},
        {"type": "kpi",   "name": "03_KPI_LateRate",  "measure": "is_late",         "measure_aggregation": "AVG"},
        {"type": "kpi",   "name": "04_KPI_Review",    "measure": "review_score",    "measure_aggregation": "AVG"},
        {"type": "map",   "name": "05_Map_Brazil",    "rows": ["customer_state"],  "measure": "price", "color": "price"},
        {"type": "line",  "name": "06_Trend_Monthly", "rows": ["purchase_yearmonth"], "measure": "price"},
        {"type": "bar",   "name": "07_Top_Categories","rows": ["product_category_en"], "measure": "price"},
        {"type": "scatter","name": "08_Scatter_Price_Freight", "measure": "freight_value", "color": "is_late"},
        {"type": "heatmap","name": "09_Heatmap_Late", "rows": ["customer_state"], "cols": ["purchase_yearmonth"], "measure": "is_late", "measure_aggregation": "AVG"},
    ],
})

tableau_dashboard_create.invoke({
    "workbook_path": result["path"],
    "dashboard_name": "Olist E-Commerce Dashboard",
    "worksheets": [v["name"] for v in visualizations],
})

tableau_story_create.invoke({
    "workbook_path": result["path"],
    "story_name": "Olist Story",
    "points": [s for s in [
        "Brazilian E-Commerce grew 3x in 2 years",
        "North/Northeast states have 15-25% late delivery rate",
        "Top 15 categories = 60% of total revenue",
        "Action: prioritize SP/RJ sellers for north region",
    ]],
})

tableau_twbx_package.invoke({"workbook_path": result["path"]})
```

## Constraints

- CSV header row required; columns map 1:1 to Tableau fields.
- Field names are tokenized — `My Field!` becomes `[My_Field]`.
- Output follows the Tableau 2026.2 document format: `version='18.1'`, the full
  `document-format-change-manifest` feature list, worksheets identified by
  `simple-id`, and an object-model datasource (`object-graph`,
  `metadata-records`). Tableau Desktop builds its runtime schema from that
  manifest, so an empty or invented manifest makes it load the legacy schema
  and reject every worksheet.
- `tableau_version` selects which vendored official XSD (`26.1` or `26.2`) the
  output is validated against; the document `version` attribute is always
  `18.1`.
- Map worksheet requires a column with geographic role; use
  `state-name` or `city` semantic role (added automatically when the
  column name matches `customer_state` / `seller_state` / `customer_city`).
- `.twbx` packaging uses `zipfile.ZIP_DEFLATED`; resource basenames
  must be unique within the archive.

## Verification

After generation, always run:

```python
from xninetzy.tools.ecosystem.tableau_tools import tableau_workbook_validate
report = tableau_workbook_validate.invoke({"workbook_path": result["path"]})
assert report["valid"], report["errors"]
```

The validator checks: XML well-formedness, namespace, datasource
declarations, dashboard-to-worksheet references, the manifest
(`TWB_MANIFEST_INVALID`, `TWB_MANIFEST_INCOMPLETE`), the official XSD, and
round-trip serialization. It also flags stale `C:\` Windows paths.

The XSD cannot see manifest problems, and it cannot see whether the requested
aggregation reached the XML. After generating, read the worksheet XML back
(`column-instance` derivation per worksheet) and recompute each one from the
CSV before claiming the dashboard matches another source.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `TableauIntegrationError: VIZ_TYPE_ERROR` | Unsupported viz type | Pick from `tableau_capabilities` → `supported_visualizations` |
| `TableauIntegrationError: WORKSHEET_CONFLICT` | Duplicate worksheet name | Pass unique `name` per visualization or suffix `_2` |
| Errors include `TWB_DANGLING_DASHBOARD_REF` | Dashboard references missing worksheet | Run after `tableau_worksheet_create` |
| Tableau Desktop reports `group 'Sort-G' must contain all, choice, or sequence compositor` or `missing required attribute 'number'` | Manifest empty or invented, `version` not `18.1` | Regenerate with the current generator; run `tableau_workbook_validate` and expect `checks.manifest: true` |
| KPI shows a row count instead of a distinct count | `CountDistinct` or another unsupported spelling, or an older generator that forced `Count` on text | Use `COUNTD`; regenerate |
| Daily or monthly chart collapses to years or months | Field typed `date`/`datetime` without `date_level`, or a text label mistyped as a date | Set `date_level`; make sure label columns are not date-shaped |
| Warnings include `TWB_WINDOWS_PATH` | Repo template has `C:\` paths | Switch to `template_name="Progres1ya.twb"` or strip before load |
| `idempotency_key` collision warning | Re-ran with same content | Already idempotent — emit is informational |

## Reference

- Reference workbook shipped under
  `xninetzy/templates/tableau/Progres1ya.twb` (compiled by this skill
  itself — round-trips through the same pipeline).
- Integration tests live at `tests/integrations/tableau/`; they pin the
  current behaviour of the parser, compiler, validator, packager, and
  registry wiring.

## Hyper extract + publish pipeline (Phase 9-23)

When the user wants real `.hyper` columnar extracts (instead of CSV-bound
textscan datasources) or to ship a workbook to a live Tableau server, the
following extras are available. They depend on `tableauhyperapi` and
`tableauserverclient` — install via `pip install 'xninetzy-mcp[tableau]'`.

```python
from xninetzy.tools.ecosystem.tableau_tools import (
    tableau_infer_schema,    # READ tier 0
    tableau_profile_dataset, # READ tier 0
    tableau_hyper_create,    # WRITE tier 1
    tableau_validate_hyper,  # READ tier 0
    tableau_publish_workbook,# FINAL tier 3, HITL required
    tableau_refresh_workbook,# WRITE tier 1, idempotent
    tableau_list_workbooks,  # READ tier 0
)
```

Schema inference + typed Hyper extract:

```python
schema = tableau_infer_schema.invoke({"csv_path": "/data/orders.csv"})
profile = tableau_profile_dataset.invoke({"csv_path": "/data/orders.csv"})
extract = tableau_hyper_create.invoke({
    "csv_path": "/data/orders.csv",
    "name": "orders",
})
info = tableau_validate_hyper.invoke({"extract_path": extract["path"]})
```

Publish to a Tableau Server (requires owner approval):

```python
tableau_publish_workbook.invoke({
    "workbook_path": result["path"],
    "target": {
        "server_url": "https://tableau.example.com",
        "site_id": "mysite",
        "project": "default",
        "token_name": "<PAT_NAME>",
        "token_secret": "<PAT_SECRET>",
    },
    "mode": "Append",
})
```

Refresh + inventory are tier-1 / tier-0 and do not require HITL.

## Failure modes (Hyper + Server)

| Symptom | Cause | Fix |
|---|---|---|
| `TABLEAU_DEPENDENCY_MISSING` | `tableauhyperapi` or `tableauserverclient` not installed | `pip install 'xninetzy-mcp[tableau]'` |
| `PUBLISH_AUTH_REQUIRED` | empty `token_name` or `token_secret` | supply Personal Access Token credentials |
| `PUBLISH_PERMISSION_DENIED` | site role lacks publish right on target project | raise role or pick another project |
| `PUBLISH_RATE_LIMITED` / `PUBLISH_TIMEOUT` | transient | tool retries up to 3x with exponential backoff |
| `REFRESH_FAILED` | workbook id missing on server | run `tableau_list_workbooks` to resolve id |
| `ARTIFACT_NOT_FOUND` | workbook path or Hyper path does not exist | verify path before invoking |

Token secrets never appear in tool outputs — `_REDACT_KEYS` covers
`token_secret`, `password`, `credentials`, and
`personal_access_token_secret` recursively.
