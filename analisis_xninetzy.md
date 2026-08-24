# Xninetzy MCP Analysis & Test Report

**Date:** 8 August 2026, approximately 04:03–04:06 WIB
**Method:** source-code inspection, live MCP testing, and client configuration verification
**Coverage:** 40+ read-only and dry-run tool calls
**Safety boundary:** final/submit operations, user-data writes, CAPTCHA/OTP, destructive operations, and configuration mutations were not executed without approval/manual interaction.

---

# 1. Executive Summary

| Area                 | Status                 | Assessment                                       |
| -------------------- | ---------------------- | ------------------------------------------------ |
| MCP server           | ✅ Healthy              | Tested read/dry-run tools operated correctly     |
| Skill catalog        | ✅ Healthy              | 29 valid, 0 invalid, 4 non-blocking warnings     |
| Risk/approval policy | ✅ Verified             | `FINAL` tools require approval and idempotency   |
| External MCP         | ✅ Available            | Management exists; no external server configured |
| GraphRAG V3          | ⚠️ Degraded            | Neo4j offline; SQLite fallback active            |
| HEBAT                | ⚠️ Session inactive    | Login required                                   |
| UACC                 | ⚠️ Human verification  | Manual verification required                     |
| Cyber Campus         | ✅ Cached/authenticated | Session state available                          |
| Memory               | ⚠️ Needs maintenance   | 45+ records; consolidation recommended           |

### Verdict

**Xninetzy MCP is healthy and suitable for normal use.**

No functional bug was identified during the tested scope. Remaining observations are **environmental degradation, inactive sessions, or low-priority maintenance items**, not demonstrated MCP defects.

---

# 2. Architecture

## 2.1 MCP Entry Point

Client configuration:

```jsonc
{
  "xninetzy": {
    "type": "local",
    "command": [
      "uv",
      "run",
      "--directory",
      "/home/misbahul45/code/xninetzy/services/ai",
      "python",
      "-m",
      "app.xninetzy.interfaces.mcp_server"
    ],
    "enabled": true,
    "timeout": 120000
  }
}
```

Runtime:

```text
OpenCode
  ↓
stdio MCP
  ↓
FastMCP server: xninetzy
  ↓
principal / policy
  ↓
shared registry
  ↓
domain + OS services
```

Startup sequence:

```text
init_db
→ migrations
→ tool registration
→ stdio server
```

The runtime applies host-safe path overrides before other modules load.

The principal context is injected server-side, including `chat_id`, preventing caller-supplied prompt fields from becoming authorization evidence.

---

# 3. Tool Architecture

## 3.1 Explicit MCP Wrappers

`mcp_server.py` exposes thin wrappers over shared `BaseTool.invoke()`.

Domains tested include:

* Obsidian
* Knowledge
* Tasks
* Reminders

## 3.2 Dynamic Tool Exposure

The adapter:

```text
expose_xninetzy_tools(...)
```

exposes tools from the central registry:

```text
get_all_tools()
get_tool_names()
get_tool_descriptions()
get_tool_groups()
```

This supports the desired architecture:

```text
new shared tool
→ registry / manifest
→ MCP adapter
→ all compatible clients
```

Client-specific tool catalog duplication is therefore unnecessary.

---

# 4. Risk and Approval Policy

Tool metadata is defined through `ToolManifest`, including:

* risk class,
* approval requirement,
* idempotency requirement,
* feature pack,
* stability.

Policy rule:

```text
FINAL
→ requires_approval = true
→ requires_idempotency = true

WRITE
→ requires_idempotency = true
```

### Live verification

The following `FINAL` tools were confirmed to expose the expected policy:

* `hebat_upload_submission`
* `portal_krs_war_arm`
* `qa_fill_kuesioner`

All returned:

```text
requires_approval = true
requires_idempotency = true
```

**Assessment: PASS**

---

# 5. Live Tool Testing

## 5.1 Core Runtime

| Tool                   | Result                               |
| ---------------------- | ------------------------------------ |
| `datetime_now`         | ✅ `2026-08-08T04:03:51+07:00`        |
| `calculate`            | ✅ `(100-25)/3 = 25`                  |
| `calculate_percentage` | ✅ `37.5%`                            |
| `ai_provider_status`   | ✅ Active: `flaz / deepseek-v4-flash` |
| `coding_agent_status`  | ✅ `opencode`                         |
| `skill_discovery`      | ✅ 9-category map + slash commands    |

## 5.2 Memory and Knowledge

| Tool                     | Result                                                            |
| ------------------------ | ----------------------------------------------------------------- |
| `memory_get_context`     | ✅ Scoped relevant memory returned                                 |
| `memory_list`            | ✅ 45+ records                                                     |
| `knowledge_list_sources` | ✅ HEBAT sources 118–122                                           |
| `knowledge_search`       | ✅ Evidence bundle + honest `insufficient` status where applicable |
| `graph_v3_stats`         | ⚠️ SQLite degraded mode: 61 nodes / 30 edges; Neo4j offline       |
| `unified_search`         | ✅ Knowledge + vault + graph + memory                              |

Important positive finding:

`knowledge_search` does not fabricate evidence when the available knowledge base is insufficient.

---

# 6. Life OS and OS Kernel

| Tool                | Result                                 |
| ------------------- | -------------------------------------- |
| `life_dashboard`    | ✅ Goals/tasks/habits                   |
| `task_today`        | ✅ No due tasks; 3 HEBAT tasks in inbox |
| `goal_list`         | ✅ Full-Stack Agentic AI Engineer       |
| `habit_today`       | ✅ 3 habits                             |
| `os_today`          | ✅ HEBAT task #19 marked high priority  |
| `os_inbox`          | ✅ 0 pending / 17 archived              |
| `reminder_list`     | ✅ Empty                                |
| `rules_healthcheck` | ✅ 4 active rules                       |
| `style_show`        | ✅ Default profile                      |

---

# 7. Academic Subsystems

| Tool                         | Result                                                             |
| ---------------------------- | ------------------------------------------------------------------ |
| `portal_info`                | ✅ Cached structure + encrypted session                             |
| `uacc_info`                  | ⚠️ `human_verification_required`                                   |
| `hebat_login_status`         | ⚠️ Not logged in                                                   |
| `web_analysis_status(hebat)` | ✅ `auth_required`; cache not stale                                 |
| `lightning_healthcheck`      | ✅ 1,029 episodes; 98.9% reported success; owner-only approval flow |
| `workflow_latest`            | ✅ No workflow                                                      |
| `deep_research_list`         | ✅ 2 research sessions                                              |
| `obsidian_folder_status`     | ✅ 120 notes; healthy; 0 duplicates                                 |

---

# 8. Intentionally Unexecuted Operations

The following were **not executed** because they are consequential, destructive, or require manual authentication:

### Final / consequential

* `hebat_upload_submission`
* `portal_krs_war_arm`
* `qa_fill_kuesioner`
* WhatsApp send operations
* user-data write operations

### Authentication

* HEBAT CAPTCHA/OTP
* Cyber Campus CAPTCHA/OTP
* UACC human verification

### Destructive

* `graph_v3_rebuild`

### Configuration

* `external_mcp_add`
* `external_mcp_remove`

This preserves the established approval/HITL boundary.

---

# 9. Skill System

| Check                             | Result                                    |
| --------------------------------- | ----------------------------------------- |
| `skill_list`                      | ✅ 29 skills                               |
| Trusted built-ins                 | ✅ 24                                      |
| Owner-installed                   | ✅ 5                                       |
| Invalid skills                    | ✅ 0                                       |
| Warnings                          | ⚠️ 4                                      |
| `skill_suggest_for_request`       | ✅ Deterministic ranking                   |
| `skill_get("research")`           | ✅ Progressive disclosure                  |
| `skill_resource_list("research")` | ✅ 8 resources                             |
| `skill_resource_read(...)`        | ✅ Successful                              |
| `skill_validate`                  | ✅ Valid; SHA-256 generated; not persisted |

## Catalog warnings

1. `gh-fix-ci`, `playwright`, `academic-assignment`

   * external URLs should have provenance verified.

2. `playwright-interactive`

   * 693-line `SKILL.md`; above the preferred progressive-disclosure target.

3. `test-mcp`

   * owner-installed; remove if no longer needed.

### Assessment

**Non-blocking.**

---

# 10. External MCP Management

Current state:

```yaml
external_mcp:
  enabled: false
  servers: []
```

Capabilities exist for:

* listing,
* adding,
* removing,
* accessing external MCP tools.

No external server is currently configured.

This is consistent with an available-but-inactive integration layer.

---

# 11. GraphRAG Status

Current state:

```text
Neo4j
→ OFFLINE

SQLite fallback
→ ACTIVE
→ 61 nodes
→ 30 edges
→ outbox 0
```

### Impact

Normal Xninetzy functionality remains available.

Graph-based retrieval is degraded because the Neo4j projection is unavailable.

### Classification

**Environmental degradation, not demonstrated MCP failure.**

### Recommended action

Investigate Neo4j connectivity/projection health before relying on full GraphRAG V3 capabilities.

---

# 12. Memory Status

The memory system currently contains **45+ records**, including multiple historical checkpoints.

This is functional but creates an increasingly large retrieval surface.

Recommended maintenance:

```text
identify stale checkpoints
→ compare supersession
→ consolidate redundant state
→ preserve active decisions
→ retain provenance
```

This is a **maintenance optimization**, not a correctness defect.

---

# 13. Security Findings

The test evidence supports the following:

### Owner-scoped principal

Authorization context is injected server-side rather than accepted from caller-provided identity fields.

### Final approval gate

`FINAL` tools require approval.

### Idempotency metadata

`WRITE` and `FINAL` tools are marked as requiring idempotency.

### CAPTCHA/OTP boundary

Authentication challenges were not bypassed or automated.

### Read honesty

Knowledge retrieval reports insufficient evidence rather than fabricating an answer.

### Overall

**No security-control bypass was identified in the tested scope.**

---

# 14. Findings by Severity

## Blocking

**None identified.**

## Medium

1. Neo4j projection is offline.
2. HEBAT session is inactive.
3. UACC requires human verification.
4. Memory requires eventual consolidation.

## Low

1. Skill URL provenance warnings.
2. Long `playwright-interactive` skill body.
3. Potentially unused `test-mcp`.
4. External MCP remains inactive.

---

# 15. Recommended Actions

| Priority | Recommendation                       | Reason                                 |
| -------- | ------------------------------------ | -------------------------------------- |
| Medium   | Restore/check Neo4j projection       | Restore full GraphRAG V3 capability    |
| Medium   | Consolidate stale memory/checkpoints | Reduce retrieval noise                 |
| Low      | Verify skill URL provenance          | Improve catalog hygiene                |
| Low      | Split `playwright-interactive` skill | Improve progressive disclosure         |
| Low      | Remove `test-mcp` if unused          | Reduce catalog clutter                 |
| Optional | Configure external MCP               | Only when a real integration is needed |
| Manual   | Re-test authenticated academic flows | Requires CAPTCHA/OTP/HITL              |

Do not prioritize external MCP activation merely because the capability exists. It should be driven by an actual product requirement.

---

# 16. Technical Evidence

### MCP server

```text
services/ai/app/xninetzy/interfaces/mcp_server.py
```

### Adapter

```text
services/ai/app/xninetzy/interfaces/mcp_tool_adapter.py
```

### Runtime

```text
services/ai/app/xninetzy/interfaces/mcp_runtime.py
```

### Registry

```text
services/ai/app/xninetzy/tools/registry.py
```

### Manifest

```text
services/ai/app/xninetzy/tools/manifest.py
```

### Policy

```text
services/ai/app/xninetzy/os/policy/action_policy.py
```

### Client configuration

```text
~/.config/opencode/opencode.jsonc
```

Configured characteristics:

```text
local MCP
timeout: 120s
default agent: xninetzy
modes: xn-research / xn-assignment / xn-learn
```

---

# 17. Final Assessment

### Overall Status

**✅ HEALTHY / READY FOR NORMAL USE**

### Confidence

**High within the tested scope.**

The testing establishes that:

* the MCP server starts and responds,
* shared tool registration works,
* risk metadata is exposed consistently,
* final approval gates work,
* read-only workflows operate,
* knowledge retrieval reports insufficient evidence honestly,
* skill discovery and progressive loading work,
* owner-scoped identity is preserved,
* no tested operation bypassed safety controls.

The remaining issues are primarily:

**Neo4j availability + session state + maintenance hygiene**, not a demonstrated MCP implementation failure.

### Important scope qualification

This verdict covers the **read-only/dry-run test surface described above**. It does **not** certify untested final-write, CAPTCHA/OTP, destructive, or external-configuration workflows.

---

# 18. Recommended Next Checkpoint

```yaml
checkpoint:
  goal: "Maintain healthy Xninetzy MCP platform"
  status: "healthy_with_environmental_warnings"

  verified:
    - MCP server startup and tool routing
    - shared registry exposure
    - risk / approval metadata
    - skill catalog
    - knowledge retrieval honesty
    - owner-scoped principal
    - read-only academic subsystem behavior

  known_environment:
    neo4j: offline
    hebat_session: unauthenticated
    uacc: human_verification_required
    external_mcp: inactive
    memory_records: 45+

  pending:
    - investigate Neo4j projection
    - consolidate stale memory
    - optional skill catalog cleanup
    - manual authenticated workflow testing

  prohibited_without_confirmation:
    - final submissions
    - KRS commit
    - WhatsApp sends
    - destructive rebuild
    - external MCP configuration
    - CAPTCHA/OTP automation
```

**Conclusion: no blocking MCP defect was identified; the system is fit for normal read-oriented and preparation workflows, with the stated environmental limitations.**
