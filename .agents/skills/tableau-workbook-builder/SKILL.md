---
name: tableau-workbook-builder
description: Build Tableau .twb / .twbx workbooks declaratively from CSV inputs via the xninetzy Tableau integration. Use when the user asks for a Tableau dashboard, .twb generation, Tableau storyboard, or wants to compile KPIs / maps / heatmaps without opening Tableau Desktop.
metadata:
  domain: tableau
  inputs: csv_paths, visualization_specs, optional template
  outputs: twb_file_in_workspace, optional twbx_archive
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
  "top_n": 15,
  "color": "review_score"
}
```

Aggregation defaults to `SUM`. Pass `measure_aggregation: "AVG"` for ratios.

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
        {"type": "kpi",   "name": "01_KPI_Orders",    "measure": "order_id",        "measure_aggregation": "CountDistinct"},
        {"type": "kpi",   "name": "02_KPI_Revenue",   "measure": "price"},
        {"type": "kpi",   "name": "03_KPI_LateRate",  "measure": "is_late",         "measure_aggregation": "Avg"},
        {"type": "kpi",   "name": "04_KPI_Review",    "measure": "review_score",    "measure_aggregation": "Avg"},
        {"type": "map",   "name": "05_Map_Brazil",    "rows": ["customer_state"],  "measure": "price", "color": "price"},
        {"type": "line",  "name": "06_Trend_Monthly", "rows": ["purchase_yearmonth"], "measure": "price"},
        {"type": "bar",   "name": "07_Top_Categories","rows": ["product_category_en"], "measure": "price", "top_n": 15},
        {"type": "scatter","name": "08_Scatter_Price_Freight", "measure": "freight_value", "color": "is_late"},
        {"type": "heatmap","name": "09_Heatmap_Late", "rows": ["customer_state"], "cols": ["purchase_yearmonth"], "measure": "is_late", "measure_aggregation": "Avg"},
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
- Top-N filter uses the `measure_aggregation` you supply.
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
declarations, dashboard-to-worksheet references, and round-trip
serialization. It also flags stale `C:\` Windows paths.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `TableauIntegrationError: VIZ_TYPE_ERROR` | Unsupported viz type | Pick from `tableau_capabilities` → `supported_visualizations` |
| `TableauIntegrationError: WORKSHEET_CONFLICT` | Duplicate worksheet name | Pass unique `name` per visualization or suffix `_2` |
| Errors include `TWB_DANGLING_DASHBOARD_REF` | Dashboard references missing worksheet | Run after `tableau_worksheet_create` |
| Warnings include `TWB_WINDOWS_PATH` | Repo template has `C:\` paths | Switch to `template_name="Progres1ya.twb"` or strip before load |
| `idempotency_key` collision warning | Re-ran with same content | Already idempotent — emit is informational |

## Reference

- Reference workbook shipped under
  `xninetzy/templates/tableau/Progres1ya.twb` (compiled by this skill
  itself — round-trips through the same pipeline).
- Integration tests live at `tests/integrations/tableau/`; they pin the
  current behaviour of the parser, compiler, validator, packager, and
  registry wiring.
