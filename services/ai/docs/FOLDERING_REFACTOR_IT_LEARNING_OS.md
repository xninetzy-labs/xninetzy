# Foldering Refactor — Xninetzy as an IT Learning OS

This document describes the namespace refactor that reorganized the codebase
around a single primary domain: **IT Learning OS**. No business behavior was
changed; this is a structural move plus backward-compat adapters.

## 1. Problem with the old structure

- Product domains and technical layers were mixed at the same level.
- `learning`, `research`, `knowledge`, `graph_rag`, `obsidian`, `life`, `hebat`
  all sat side-by-side under `app/`, so the product read as a *bag of features*
  rather than one Learning OS.
- Workflow lived inside `app/agent/` (`workflow_*.py`), blurring the line between
  the agent and the orchestration layer.
- HEBAT/Moodle looked like a core domain instead of an academic connector.
- There was no dedicated home for the first MVP domain (`it_learning`).
- No clear boundary between core / interface / domain / OS service / connector /
  infrastructure.

## 2. Target structure

Everything now lives under the `app/xninetzy/` namespace:

```txt
app/
  main.py                     # entrypoint (unchanged location)
  xninetzy/
    core/                     # config, llm, logging
    db/                       # sqlite, migrations
    agent/                    # graph, executor, orchestrator, prompts, response, state
    workflow/                 # actions, executor, models, notifier, plan, store, tools
    context/                  # NEW skeleton: packet, normalizer, classifiers, mode_router, builder
    interfaces/
      api/                    # FastAPI routes + deps
      whatsapp/               # wa client + messaging
      media/                  # document parser, media store/tools
    domains/
      it_learning/            # ACTIVE MVP domain (roadmap, progress, study, skill_tree)
      future/                 # placeholders: biology, neuroscience, it_biology
    os/                       # support OS services
      knowledge/  research/  graph/  notes/  life/  reminders/
      memory/  rules/  style/  hitl/  notifications/  lightning/
      academic/hebat/         # HEBAT/Moodle connector (demoted from top level)
    tools/                    # registry + internal/ + ecosystem/
    schemas/  skills/  ecosystem/  helper/
```

## 3. Why IT Learning OS first

The Xninetzy roadmap targets month one as the **IT Domain Learning MVP**. Rather
than building every domain at once, the product is anchored to one domain
(`it_learning`) with the supporting OS services (Knowledge, Research, Graph,
Notes, Academic, Life, Reminder) positioned as *support*, and Biology /
IT+Biology / Neuroscience deferred to `domains/future/` placeholders.

## 4. Migration map (old → new)

| Old path | New path |
|---|---|
| `app/core/*` | `app/xninetzy/core/*` |
| `app/db/*` | `app/xninetzy/db/*` |
| `app/api/*` | `app/xninetzy/interfaces/api/*` |
| `app/agent/{executor,graph,orchestrator,prompts,response,state}.py` | `app/xninetzy/agent/*` |
| `app/agent/workflow_actions.py` | `app/xninetzy/workflow/actions.py` |
| `app/agent/workflow_executor.py` | `app/xninetzy/workflow/executor.py` |
| `app/agent/workflow_models.py` | `app/xninetzy/workflow/models.py` |
| `app/agent/workflow_notifier.py` | `app/xninetzy/workflow/notifier.py` |
| `app/agent/workflow_plan.py` | `app/xninetzy/workflow/plan.py` |
| `app/agent/workflow_store.py` | `app/xninetzy/workflow/store.py` |
| `app/agent/workflow_tools.py` | `app/xninetzy/workflow/tools.py` |
| `app/learning/*` | `app/xninetzy/domains/it_learning/*` |
| `app/knowledge/*` | `app/xninetzy/os/knowledge/*` |
| `app/research/*` | `app/xninetzy/os/research/*` |
| `app/graph_rag/*` | `app/xninetzy/os/graph/*` |
| `app/obsidian/*` | `app/xninetzy/os/notes/*` (`config.py` → `obsidian_config.py`) |
| `app/life/*` | `app/xninetzy/os/life/*` |
| `app/planning/{goal_manager,task_manager}.py` | `app/xninetzy/os/life/*` |
| `app/reminders/*` | `app/xninetzy/os/reminders/*` |
| `app/memory/*` | `app/xninetzy/os/memory/*` |
| `app/rules/*` | `app/xninetzy/os/rules/*` |
| `app/style/*` | `app/xninetzy/os/style/*` |
| `app/hitl/*` | `app/xninetzy/os/hitl/*` |
| `app/notifications/*` | `app/xninetzy/os/notifications/*` |
| `app/lightning/*` | `app/xninetzy/os/lightning/*` |
| `app/tools/hebat/*` | `app/xninetzy/os/academic/hebat/*` |
| `app/media/*` | `app/xninetzy/interfaces/media/*` |
| `app/wa_tools/*` | `app/xninetzy/interfaces/whatsapp/*` |
| `app/tools/whatsapp/*` | `app/xninetzy/interfaces/whatsapp/*` |
| `app/tools/{registry,internal,ecosystem}` | `app/xninetzy/tools/*` |
| `app/schemas/*` | `app/xninetzy/schemas/*` |
| `app/skills/*` | `app/xninetzy/skills/*` |
| `app/ecosystem/*` | `app/xninetzy/ecosystem/*` |
| `app/helper/*` | `app/xninetzy/helper/*` |

Notes:
- `app/ecosystem/` and `app/helper/` were not in the original target sketch but
  were preserved 1:1 under the namespace to avoid behavior changes.
- `app/planning/` was merged into `os/life/` (its `__init__.py` was empty).
- The two WhatsApp sources (`wa_tools/` + `tools/whatsapp/`) merged into
  `interfaces/whatsapp/`.

## 5. Compatibility adapters

Every old module path still imports, via a thin adapter generated at the old
location. Two patterns are used:

- **Package `__init__.py`** re-exports the new package so the old package keeps
  its own path alive (submodule adapters stay reachable):

  ```py
  # Backward compatibility adapter. New code should import from app.xninetzy.os.knowledge
  from app.xninetzy.os.knowledge import *  # noqa: F401,F403
  ```

- **Modules** alias themselves to the new module in `sys.modules`, preserving the
  full public + private surface (and handling renames/splits):

  ```py
  # Backward compatibility adapter. New code should import from app.xninetzy.os.knowledge.rag
  import sys as _sys
  import app.xninetzy.os.knowledge.rag as _mod
  _sys.modules[__name__] = _mod
  ```

These adapters are **temporary**. New code must import from `app.xninetzy.*`.

## 6. How to import (new code)

```py
from app.xninetzy.core.config import get_settings
from app.xninetzy.os.knowledge.rag import RAGService          # example
from app.xninetzy.os.academic.hebat.tools import hebat_login_status
from app.xninetzy.domains.it_learning.roadmap_planner import ...
from app.xninetzy.workflow.executor import ...
```

## 7. How to test

```bash
uv run python -m pytest -q
```

`tests/test_foldering_refactor.py` asserts both the new namespace imports and the
legacy adapters resolve to the same modules.

## 8. Deferred domains

`domains/future/{biology,neuroscience,it_biology}/` are README-only placeholders.
Do not add logic there until those domains are planned. Only `it_learning` is
active.

## 9. Future cleanup

Once all callers (including any external services / scripts) import from
`app.xninetzy.*`, delete the adapter files at the old paths
(`app/core`, `app/agent`, `app/tools`, `app/learning`, `app/knowledge`, …) and
remove this compatibility layer.
