---
layout: ../../layouts/DocsLayout.astro
title: Tableau workbook generator
description: TWB parsing, IR, template engine, visualization compiler, validator, and TWBX packaging.
section: Integrations
badge: new
difficulty: intermediate
readingTime: 8 min
---

Xninetzy ships a Tableau workbook generator that produces real `.twb`
and `.twbx` artifacts. The pipeline:

```text
TWB parser
  ↓
TableauWorkbookIR
  ↓
Template transformer (Progres1ya.twb reference)
  ↓
Visualization compiler
  ↓
TWB serializer
  ↓
Validator (XML + reference + Windows-path strip)
  ↓
TWBX packager
```

The pipeline never overwrites the source template.

## Tools

| Tool | Class | Purpose |
|---|---|---|
| `tableau_capabilities` | read | Per-operation support matrix |
| `tableau_template_list` | read | Available `.twb` templates |
| `tableau_template_inspect` | read | Structural summary of a template |
| `tableau_workbook_inspect` | read | Inspect any `.twb` workbook |
| `tableau_workbook_validate` | read | XML + reference + local-resource validation |
| `tableau_workbook_generate` | write | Produce a new `.twb` from a template + CSV |
| `tableau_datasource_replace` | write | Swap the source CSV inside an existing workbook |
| `tableau_worksheet_create` | write | Append a worksheet with a visualization |
| `tableau_worksheet_modify` | write | Replace an existing worksheet's visualization |
| `tableau_dashboard_create` | write | Populate dashboard zones |
| `tableau_dashboard_layout` | write | Adjust zone positions |
| `tableau_story_create` | write | Assign story-point captions to a storyboard |
| `tableau_twb_export` | write | Round-trip parse → serialize |
| `tableau_twbx_package` | write | Build a `.twbx` archive (TWB + resources) |
| `tableau_hyper_create` | write | Probe Hyper capability (currently `not_implemented`) |

Supported visualization types: `bar`, `line`, `area`, `pie`, `scatter`,
`table`, `map`, `kpi`, `histogram`.

## Authentication

None required. The generator operates on local files only. Hyper
extracts require the optional `tableauhyperapi` package; otherwise
extracts return `TABLEAU_NOT_IMPLEMENTED`.

## Workspace

```text
~/.local/share/xninetzy/tableau/
├── templates/      # Progres1ya.twb + custom templates
├── workbooks/      # generated .twb outputs
├── twbx/           # packaged .twbx archives
├── hyper/          # future extract workspace
├── metadata/       # cached inspection snapshots
├── staging/        # intermediate serializer scratch
└── temp/           # throwaway
```

Path traversal in any `output` / `destination` argument is rejected
with `TABLEAU_INVALID_PATH`.

## Example workflow

```text
1. tableau_template_list                    → choose Progres1ya.twb
2. tableau_workbook_inspect(template)        → confirm structure
3. tableau_workbook_generate(
     template="Progres1ya.twb",
     datasource_path="predictions.csv",
     worksheets=[
       {"name": "Forecast", "visualization": {"type": "bar", "rows": ["category"], "measure": "value"}}
     ],
     dashboard_name="Forecast",
     dashboard_layout=[
       {"worksheet": "Forecast", "x": 0, "y": 0, "width": 10000, "height": 10000}
     ]
   )
4. tableau_workbook_validate(workbook)      → confirm references resolve
5. tableau_twbx_package(workbook=...)        → produce final .twbx
```

## Limitations

- Hyper extracts are not implemented on Linux unless
  `tableauhyperapi` is installed AND `hyperd` is on `$PATH`.
- Generated workbooks have not been opened in Tableau Desktop in CI;
  XML and reference validity are verified by `tableau_workbook_validate`.
- Stale Windows-style paths from the reference template are stripped
  automatically by the compiler.

## See also

- [MCP system reference](/docs/mcp-system/) — risk class for each tool
- [Configuration](/docs/configuration/) — `ARTIFACT_ALLOWLIST` and workspace paths
