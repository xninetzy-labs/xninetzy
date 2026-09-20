---
name: "process-engineering-providers"
description: "Provider-agnostic process_engineering capability. Selects between native_xninetzy, bpmn-js, PM4Py (AGPL-3.0 opt-in), Flowable (REST opt-in), SimPy, Bizagi/Camunda interop based on capability + license posture."
metadata:
  type: "meta"
  layer: "process-engineering"
  consumes:
    - tool: process_list_providers
    - tool: process_select_provider
    - tool: process_capability_providers
    - tool: process_is_provider_enabled
    - tool: process_discover_from_event_log
    - tool: process_simulate
    - tool: process_plan_execution
  produces:
    - provider_decision
    - discovery_report
    - simulation_result
    - execution_plan
  tier: "0"
---

# process-engineering-providers

Capability layer that lets XNINETZY do process work without binding to
any single vendor.

Capabilities and providers:

| capability | native | bpmn-js | PM4Py | Flowable | SimPy | Bizagi/Camunda |
|---|---|---|---|---|---|---|
| process_modeling | yes | yes (visual) | — | — | — | yes (interop) |
| process_mining | (opt-in) | — | yes (AGPL) | — | — | — |
| process_execution | — | — | — | yes (REST) | — | — |
| process_simulation | — | — | — | — | yes | — |
| process_validation | yes | — | — | — | — | — |
| process_interop | — | — | — | — | — | yes |

## License posture

- PM4Py is AGPL-3.0. Bundling AGPL into XNINETZY core triggers copyleft.
  Therefore PM4Py is opt-in via env var `XNINETZY_ENABLE_PM4PY=1`.
- Flowable is Apache-2.0 but requires a Java runtime reachable via REST.
  Opt-in via `XNINETZY_FLOWABLE_BASE_URL`.
- Bizagi Modeler Free is Freeware (manual import only, no runtime link).
  Always available as interop artifact target.
- Camunda Modeler is Apache-2.0 (manual import only).
- bpmn-js + SimPy + native_xninetzy ship under permissive licenses.

## When to invoke

- User asks for BPMN modeling, simulation, mining, or execution
- User wants to compare providers for a task
- Lightning needs to record which provider worked best for a context

## Inputs

```yaml
capability: process_modeling | process_mining | process_execution |
            process_simulation | process_validation | process_interop
preferred: <provider_id> # optional
```

## Outputs

```yaml
chosen: <provider_id>
candidates: [<provider_id>]
license_warnings: [<string>]
```

## Workflow

1. `process_select_provider(capability)` — returns decision
2. Inspect `license_warnings`; escalate to owner if AGPL chosen
3. Dispatch to provider-specific tool (`process_discover_from_event_log`,
   `process_simulate`, `process_plan_execution`)
4. Record outcome to Lightning

## Anti-pattern

Do NOT install PM4Py unconditionally.
Do NOT auto-register AGPL providers as defaults.
Do NOT link against Bizagi Freeware EULA at runtime.
