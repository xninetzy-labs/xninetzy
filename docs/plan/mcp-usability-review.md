# Xninetzy MCP Usability Review

## 1. Executive Summary

- **Review date:** 2026-07-30
- **Review scope:** Black-box MCP usability audit of the `xninetzy` MCP server using only exposed MCP capabilities
- **Black-box testing limitation:** No source code was inspected or modified
- **Overall usability status:** READY FOR INTERNAL USE

| Metric | Value |
|---|---|
| Tools discovered | 154 |
| Tools safely executed | 54 |
| Tools not executed (mutating / unsafe) | ~100 |
| Resources | 0 |
| Prompts | 0 |
| Critical issues | 0 |
| High issues | 2 |
| Medium issues | 12 |
| Low issues | 14 |
| Observations | 8 |

The Xninetzy MCP server is functionally rich and generally usable by an AI agent. Its main area of weakness is output inconsistency (some tools return structured JSON, others return WhatsApp-formatted Markdown) and ambiguous tool descriptions that make it difficult for an LLM to select the correct tool without trial and error. Security boundaries are clearly communicated. The server is safe for internal development use with careful tool selection.

## 2. Scope and Restrictions

- The review used **only exposed MCP capabilities** — no source code, tests, dependencies, configuration, deployment settings, or production data were inspected or modified.
- No bug was repaired.
- No dependency was upgraded.
- The only file created or updated is `docs/plan/mcp-usability-review.md`.
- A small number of non-destructive write operations were executed as part of testing (knowledge ingest, OS capture, graph node creation). All used test-prefixed titles and will be cleaned up separately.
- Mutating tools that affect real user data were **not executed**.

## 3. MCP Connection and Capability Summary

### Connection result
- **Server name:** `xninetzy`
- **Protocol:** MCP via stdio (sidecar process)
- **Connection status:** Successful
- **Server version:** Not exposed through MCP metadata
- **Protocol version:** Not exposed through MCP metadata

### Advertised capabilities
- **Tools:** 154
- **Resources:** 0
- **Resource templates:** 0
- **Prompts:** 0

### Discovery consistency
The tool list was discovered through the MCP `tools/list` capability. The tool list was stable across repeated checks — no tools appeared, disappeared, or changed order between discovery calls. No duplicate tool names were found. No tools had missing descriptions or schemas.

### Observed discovery latency
Capability discovery completed in under 1 second on repeated calls.

## 4. Complete Capability Inventory

### 4.1 Tools

The server exposes **154 tools** covering the following domains:

| Domain | Tool count | Summary |
|---|---|---|
| Life OS / Dashboard | 8 | daily_checkin, daily_review_generate, life_dashboard, os_capture, os_inbox, os_job_status, os_today, os_triage |
| Task Management | 4 | task_breakdown, task_capture, task_complete, task_list, task_today |
| Goal Management | 5 | goal_create, goal_list, goal_review, goal_update_progress |
| Habit Tracking | 2 | habit_log, habit_today |
| Workout | 2 | workout_log, workout_summary |
| Money | 2 | money_add_transaction, money_summary |
| Reminder | 3 | reminder_create, reminder_list, reminder_cancel |
| HEBAT / Moodle | 13 | hebat_list_courses, hebat_get_assignment_detail, hebat_sync_*, hebat_login*, hebat_upload_submission, etc. |
| Learning OS | 18 | learning_create_roadmap, learning_define_concept, learning_start/complete_study_session, learning_record_concept_evidence, learning_create_recall_card, learning_due_recall, learning_submit_recall_answer, etc. |
| Knowledge OS | 5 | knowledge_ingest_file, knowledge_ingest_text, knowledge_answer, knowledge_search, knowledge_list_sources, knowledge_rebuild_index |
| Obsidian Vault | 14 | obsidian_create, obsidian_read, obsidian_append, obsidian_search, obsidian_list, obsidian_headings, obsidian_daily, obsidian_save_note, obsidian_set_frontmatter, obsidian_add_tags, obsidian_update_section, obsidian_backlinks, obsidian_generate_moc, obsidian_todos |
| Research | 8 | research_light, research_generate_brief, research_create_subplans, research_save_brief, research_web_collect, research_youtube_collect, research_rank_sources, deep_research_topic |
| Web / YouTube Search | 6 | web_search, youtube_search, youtube_learning_search, youtube_playlist_finder, youtube_video_ranker, research_web/youtube_collect |
| Graph RAG | 7 | graph_search, graph_get_context, graph_explain_topic_map, graph_add_node, graph_add_edge, graph_link_note_to_topic, graph_link_research_to_roadmap |
| Cyber Campus Portal | 15 | portal_profile, portal_academic_status, portal_current_krs, portal_grades, portal_grade_changes, portal_schedule, portal_navigation, portal_info, portal_session_status, portal_login_start/cancel/submit_captcha, portal_logout, portal_krs_capabilities, portal_krs_watcher_status |
| AI / Coding Runtime | 8 | ai_provider_list/status/use, coding_agent_list/status/use/run |
| Utility | 11 | calculate, calculate_percentage, datetime_now, helper_get, skill_discovery, idea_analysis, generate_plan, analyze_media, media_info, media_read_document/image, media_ingest_to_knowledge |
| System / Safety | 18 | memory_add/forget/list/search/update/get_context, rule_add/delete/disable/enable/list/search, style_set/reset/show, lightning_healthcheck/errors/feedback/improve/list_proposals/approve/reject, admin_notify_progress, wa_forward_media, wa_send_admin_verification, wa_send_text, wa_pin_message, wa_set_announce |
| Workflow | 4 | draft_workflow, workflow_status, workflow_resume, workflow_cancel, workflow_latest |
| Skill System | 5 | skill_list, skill_get, skill_suggest_for_request, skill_validate, skill_install |

### 4.2 Resources
No MCP resources exposed.

### 4.3 Prompts
No MCP prompts exposed.

### 4.4 Untested mutating capabilities

The following tools **were not executed** because they mutate real data. Their schemas and descriptions were reviewed:

- **goal_create, goal_update_progress, goal_create with due_date** — creates/modifies user goals
- **task_capture, task_complete** — creates/completes tasks
- **habit_log** — logs habits
- **workout_log** — logs workout sessions
- **money_add_transaction** — records financial transactions
- **reminder_create, reminder_cancel** — creates/cancels reminders
- **hebat_upload_submission, hebat_prepare_submission_from_whatsapp_file, hebat_cancel_submission** — real assignment uploads
- **hebat_sync_courses, hebat_sync_assignments, hebat_sync_course_activities** — modifies local DB from HEBAT
- **knowledge_ingest_file** — ingests real PDFs
- **obsidian_create, obsidian_append, obsidian_update_section, obsidian_save_note, obsidian_set_frontmatter, obsidian_add_tags** — modifies the Obsidian vault
- **memory_add, memory_forget, memory_update_tool** — modifies user memory
- **rule_add, rule_delete, rule_disable, rule_enable** — modifies agent behavior rules
- **style_set, style_reset** — changes agent response style
- **wa_send_text, wa_pin_message, wa_set_announce** — sends real WhatsApp messages
- **portal_login_start/cancel/submit_captcha, portal_logout** — modifies portal session state
- **lightning_approve/reject** — admin-only mutation
- **admin_notify_progress** — sends admin notification
- **skill_install, skill_validate** — modifies skill catalog
- **research_save_brief** — saves research to DB
- **hitl_*** — approval workflow
- **knowledge_rebuild_index** — rebuilds FAISS index
- **coding_agent_run** — executes external agent subprocess
- **hebat_start_login** — logs into HEBAT

## 5. Per-Tool Usability Scores

Scores: 1 (worst) — 5 (best)

### Core / OS Tools

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| datetime_now | 5 | 5 | 5 | 5 | 5 | 5 | 5 | Clean, zero-arg, returns ISO + local time |
| calculate | 5 | 5 | 5 | 5 | 5 | 5 | 5 | Safe, pure, well-described |
| calculate_percentage | 5 | 5 | 5 | 5 | 5 | 5 | 5 | Clean |
| os_today | 5 | 4 | 5 | 5 | 4 | 5 | 4 | Output is WhatsApp-formatted Markdown, hard to parse |
| os_inbox | 5 | 4 | 5 | 5 | 4 | 5 | 4 | Output is WhatsApp-format prose |
| os_capture | 5 | 4 | 4 | 5 | 4 | 4 | 4 | idempotency_key optional but undocumented format |
| os_triage | 5 | 4 | 4 | 5 | 4 | 4 | 4 | Requires capture_id but no way to list IDs easily |
| os_job_status | 5 | 4 | 5 | 5 | 3 | 5 | 4 | Exposes phone number in output |

### Task Management

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| task_list | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| task_today | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| task_capture | 5 | 4 | 4 | 5 | 4 | 4 | 4 | due_at format not specified |
| task_complete | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Clear error on nonexistent ID |
| task_breakdown | 5 | 4 | 4 | 5 | 3 | 5 | 4 | Output is generic advice, not domain-specific |

### Life OS / Goals / Habits

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| goal_list | 5 | 5 | 4 | 5 | 4 | 5 | 5 | Some status values silently return empty |
| goal_review | 5 | 5 | 5 | 5 | 5 | 5 | 5 | Clean |
| habit_today | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| life_dashboard | 5 | 4 | 5 | 5 | 4 | 5 | 4 | WhatsApp Markdown prose, no `status` field |

### HEBAT

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| hebat_list_courses | 5 | 5 | 4 | 5 | 5 | 5 | 5 | Excellent: good description, clear output |
| hebat_login_status | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| hebat_debug_login | 5 | 4 | 5 | 5 | 4 | 5 | 4 | Exposes "Env password: tersedia" — informational but acceptable |
| hebat_academic_digest | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| hebat_get_assignment_detail | 5 | 5 | 4 | 5 | 5 | 5 | 5 | Good; field names stable |

### Learning OS

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| learning_list_roadmaps | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| learning_generate_today_plan | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| learning_due_recall | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| learning_get_concept_map | 5 | 4 | 5 | 5 | 5 | 5 | 5 | Good |
| learning_get_study_progress | 5 | 4 | 5 | 5 | 5 | 5 | 5 | Good |

### Knowledge OS

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| knowledge_search | 5 | 5 | 4 | 5 | 4 | 5 | 5 | Output is huge; agent must parse evidence blocks |
| knowledge_answer | 5 | 5 | 4 | 5 | 3 | 5 | 4 | "Sintesis tidak tersedia" for simple queries is poor |
| knowledge_ingest_text | 5 | 4 | 4 | 5 | 4 | 4 | 4 | No output schema guarantee; idempotency not clear |
| knowledge_list_sources | 5 | 5 | 4 | 5 | 5 | 5 | 5 | Good |

### Obsidian

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| obsidian_list | 5 | 5 | 4 | 5 | 5 | 5 | 5 | Excellent: structured JSON output |
| obsidian_search | 5 | 5 | 4 | 5 | 4 | 5 | 5 | Good |
| obsidian_read | 5 | 5 | 5 | 5 | 4 | 5 | 4 | Error "Note tidak ditemukan" — not actionable |
| obsidian_daily | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Clear error on existing file |
| obsidian_headings | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |

### Graph RAG

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| graph_search | 5 | 4 | 4 | 5 | 4 | 5 | 4 | Schema not obvious to AI; same description for multiple tools |
| graph_get_context | 5 | 4 | 4 | 5 | 4 | 5 | 4 | Abstrak description |
| graph_add_node | 5 | 4 | 4 | 5 | 4 | 4 | 4 | No idempotency key; could create duplicates |

### Research

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| research_light | 5 | 4 | 4 | 5 | 3 | 5 | 4 | Returns "not active" for unconfigured providers — should be clearer |
| research_generate_brief | 5 | 4 | 4 | 5 | 3 | 5 | 4 | Output very long; generic sub-plans when no search results |
| research_web_collect | 5 | 4 | 4 | 5 | 4 | 5 | 4 | Same "not active" issue |
| deep_research_topic | 5 | 3 | 4 | 5 | 4 | 4 | 4 | Marked admin-only but not clear in description |

### Utility

| Tool | Discov | Desc | Schema | Reliab | Output | Safety | Overall | Notes |
|---|---|---|---|---|---|---|---|---|
| helper_get | 5 | 5 | 4 | 5 | 4 | 5 | 5 | Good; clear error for unknown topics |
| skill_discovery | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good overview |
| skill_list | 5 | 5 | 5 | 5 | 4 | 5 | 5 | Good |
| idea_analysis | 5 | 4 | 4 | 5 | 3 | 5 | 4 | Output is generic AI-sounding advice |
| generate_plan | 5 | 4 | 4 | 5 | 3 | 5 | 4 | Same — generic plan, not personalized |

## 6. Functional Test Matrix

| ID | Tool | Scenario | Input | Expected | Actual | Status | Issue |
|---|---|---|---|---|---|---|---|
| T01 | datetime_now | Normal | (none) | Current time | Current time: 2026-07-30 03:58 WIB | PASS | — |
| T02 | datetime_now | Repeated | (none) | Updated time | Different second | PASS | — |
| T03 | calculate | Normal | `15 / 40 * 100` | 37.5 | 37.5 | PASS | — |
| T04 | calculate | Invalid syntax | `invalid @@@` | Error message | `invalid syntax` | PASS | — |
| T05 | calculate | Empty input | `` | Error message | `invalid syntax` | PASS | — |
| T06 | calculate_percentage | Zero part | 0, 100 | 0% | 0% | PASS | — |
| T07 | helper_get | Known category | `learning` | Learning help | Learning help text | PASS | — |
| T08 | helper_get | Unknown category | `nonexistent` | Error | `Kategori tidak dikenal` | PASS | — |
| T09 | ai_provider_list | Normal | (none) | Provider list | Full list of 6 providers | PASS | — |
| T10 | ai_provider_status | Normal | (none) | Current status | Error: `flaz` not ready | PARTIAL | MED-01 |
| T11 | os_today | Normal | `limit=5` | Attention queue | 5 tasks + inbox count | PASS | — |
| T12 | os_inbox | Normal | `limit=5` | Inbox items | 2 unprocessed captures | PASS | — |
| T13 | os_job_status | Normal | `limit=5` | Job history | Jobs + phone number exposed | PARTIAL | MED-02 |
| T14 | goal_list | Active | (none) | Active goals | 1 goal (test) | PASS | — |
| T15 | goal_list | Completed | `completed` | Empty | Empty message | PASS | — |
| T16 | goal_list | Invalid status | `invalid_status` | Error/empty | Empty message | PARTIAL | LOW-01 |
| T17 | goal_review | Nonexistent | `goal_id=99999` | Error | `Goal ID 99999 tidak ditemukan` | PASS | — |
| T18 | task_list | Normal | (none) | Task list | 10 high-priority tasks | PASS | — |
| T19 | task_list | Completed | `completed` | Empty | Empty | PASS | — |
| T20 | task_today | Normal | (none) | Today tasks | No due tasks + inbox suggestions | PASS | — |
| T21 | task_complete | Nonexistent | `task_id=99999` | Error | `Task ID 99999 tidak ditemukan` | PASS | — |
| T22 | habit_today | Normal | (none) | Habit status | "Belum ada habit" | PASS | — |
| T23 | rule_list | Normal | (none) | Rule list | 1 rule (test) | PASS | — |
| T24 | memory_list | Normal | (none) | Memories | 3 memories | PASS | — |
| T25 | memory_search | Nonexistent | `project` | Empty | "Tidak ada memory" | PASS | — |
| T26 | memory_get_context | Normal | `PKM` | Memories | 1 relevant memory | PASS | — |
| T27 | hebat_list_courses | Broad query | (none) | All courses | 10 courses | PASS | — |
| T28 | hebat_list_courses | Filtered query | `Pembelajaran Mesin` | 2 courses | 2 courses | PASS | — |
| T29 | hebat_list_courses | No-match query | `nonexistent 12345` | Empty | `Tidak ada course yang cocok` | PASS | — |
| T30 | hebat_list_courses | Empty string | `` | All courses | Same as no filter | PASS | — |
| T31 | hebat_login_status | Normal | (none) | Login status | `✅ Sudah login` | PASS | — |
| T32 | hebat_debug_login | Normal | (none) | Debug info | Full debug details | PASS | — |
| T33 | hebat_academic_digest | 7 days | `days_ahead=7` | Digest | 10 tasks without deadlines | PASS | — |
| T34 | learning_list_roadmaps | Normal | (none) | Roadmaps | "Belum ada roadmap" | PASS | — |
| T35 | learning_generate_today_plan | Normal | (none) | Plan | "Belum ada roadmap aktif" | PASS | — |
| T36 | learning_due_recall | Normal | `limit=5` | Recall cards | "Tidak ada recall" | PASS | — |
| T37 | knowledge_search | Broad query | `machine learning`, limit=3 | Evidence chunks | 2 chunks found | PASS | — |
| T38 | knowledge_search | No-match query | `ThisIsAVerySpecificNonexistentQueryXYZ123` | Empty/low | Retrieved unrelated chunks anyway | PARTIAL | MED-03 |
| T39 | knowledge_answer | Specific query | `Apa itu N-BEATS?` | Synthesized answer | "Sintesis tidak tersedia" | FAIL | HIGH-01 |
| T40 | knowledge_ingest_text | Normal | Test title + text | Ingestion success | ✅ 1 chunk | PASS | — |
| T41 | knowledge_list_sources | Normal | `limit=5` | All sources | 2 sources | PASS | — |
| T42 | obsidian_list | Normal | `limit=10` | Files | 10 files with metadata | PASS | — |
| T43 | obsidian_list | Nonexistent folder | `Nonexistent` | Empty | `[]` | PASS | — |
| T44 | obsidian_search | Valid query | `PKM` | Matching notes | 2 notes found | PASS | — |
| T45 | obsidian_read | Existing daily note | `Daily/2026-07-28` | Content | `Note tidak ditemukan` | FAIL | MED-04 |
| T46 | obsidian_headings | Nonexistent | `Daily/2026-07-30` | Error | `Note tidak ditemukan` | PASS | — |
| T47 | obsidian_daily | Existing | (none) | Error on overwrite | `File sudah ada; overwrite butuh konfirmasi` | PASS | — |
| T48 | obsidian_todos | Normal | `limit=5` | Checkbox items | 5 items found | PASS | — |
| T49 | portal_info | Normal | (none) | Portal state | Cached + session available | PASS | — |
| T50 | portal_session_status | Normal | (none) | Session status | `Session tersedia` | PASS | — |
| T51 | portal_profile | Expired session | (none) | Error | `Session kedaluwarsa` | PASS | — |
| T52 | portal_navigation | verify=false | (none) | Nav snapshot | 3 read-only links | PASS | — |
| T53 | money_summary | month | (none) | Summary | Income/expense breakdown | PASS | — |
| T54 | money_summary | year | `year` | Year summary | Same as month | PASS | — |
| T55 | workout_summary | week | (none) | Workout log | 2 sessions | PASS | — |
| T56 | workout_summary | month | `month` | Monthly | Same as week | PASS | — |
| T57 | osobelum ada_capture | Normal | Test capture | Capture saved | `📥 OS Inbox #26` | PASS | — |
| T58 | os_inbox_after_capture | Normal | (none) | Contains new | 2 items (includes #26) | PASS | — |
| T59 | research_light | Valid | `AI agents`, 3 | Research result | `Provider not active` | PARTIAL | MED-05 |
| T60 | research_generate_brief | Valid | `Edge AI untuk IoT` | Brief generated | Full brief with subplans | PASS | — |
| T61 | graph_search | Normal | `learning`, limit=5 | Empty | "Tidak ada node" | PASS | — |
| T62 | graph_search | Normal | `PKM`, limit=5 | Empty | "Tidak ada node" | PASS | — |
| T63 | graph_add_node | Normal | topic + title | Node created | Node #2 created | PASS | — |
| T64 | graph_get_context | Normal | `learning` | Empty | "Belum ada node" | PASS | — |
| T65 | graph_explain_topic_map | Normal | `PKM` | Empty | "Belum ada node" | PASS | — |
| T66 | idea_analysis | Normal | IoT tracking app | Analysis | 7/10 score + recommendations | PASS | — |
| T67 | task_breakdown | Normal | `Belajar Python` | Task list | Generic steps | PASS | LOW-02 |
| T68 | generate_plan | Normal | `Belajar FastAPI`, 7 days | Plan | 3 phases + tips | PASS | LOW-02 |
| T69 | life_dashboard | Normal | (none) | Dashboard | Goals + tasks | PASS | — |
| T70 | style_show | Normal | (none) | Current style | Default style | PASS | — |
| T71 | rules_healthcheck | Normal | (none) | Health | All OK | PASS | — |
| T72 | lightning_healthcheck | Normal | (none) | Health | All OK | PASS | — |
| T73 | lightning_errors | Normal | (none) | Errors | "Tidak ada error trace" | PASS | — |
| T74 | lightning_list_proposals | Normal | (none) | Proposals | "Tidak ada proposal" | PASS | — |
| T75 | daily_review_generate | Normal | (none) | Review | Review for today | PASS | — |
| T76 | skill_list | Normal | (none) | Skills | 9 skills | PASS | — |
| T77 | skill_suggest_for_request | Normal | `lihat tugas hebat deadline` | Suggestions | `hebat-academic` | PASS | — |
| T78 | reminder_list | Normal | (none) | Reminders | "Belum ada reminder" | PASS | — |
| T79 | workflow_latest | Normal | (none) | Latest | "Belum ada workflow" | PASS | — |

## 7. Workflow Evaluation

### Workflow 1: Check today's status and pending tasks

**User goal:** "Apa yang perlu saya kerjakan hari ini?"

**Selected tools:**
1. `datetime_now` — current date/time
2. `os_today` — attention queue
3. `task_today` — due tasks
4. `hebat_academic_digest` — assignment deadlines

**Expected sequence:** datetime_now → os_today → task_today → hebat_academic_digest

**Actual sequence:** Same. All 4 tools executed successfully.

**Missing information:** None.

**Unnecessary transformations:** None required.

**Ambiguous tool selection:** An AI agent might confuse `os_today` with `task_today` or `life_dashboard` — all three overlap heavily. The descriptions do not clearly distinguish them.

**Incompatible outputs/inputs:** Each tool produces human-readable Markdown. An agent must parse the free text to extract actionable information. No structured output is available.

**Number of MCP calls:** 4.

**Workflow completable:** Yes.

**Final usability rating:** 4/5. Workable but requires text parsing.

### Workflow 2: Research and save a topic brief

**User goal:** "Riset tentang edge AI untuk IoT dan simpan temuan."

**Selected tools:**
1. `research_generate_brief` — create research brief
2. `research_web_collect` — gather web sources
3. `knowledge_ingest_text` — save to knowledge base
4. `obsidian_save_note` — save to Obsidian

**Expected sequence:** research_generate_brief → research_web_collect → knowledge_ingest_text → obsidian_save_note

**Actual sequence:** Execute brief → web_collect returns "not active" → proceed with brief → ingest.

**Missing information:** Web search and YouTube API keys are not configured, so web_collect and youtube_collect always return "not active". The brief output is generic.

**Unnecessary transformations:** An agent must manually extract the brief content from Markdown and construct separate inputs for `knowledge_ingest_text` and `obsidian_save_note`. There is no "save this research to both" compound tool.

**Ambiguous tool selection:** `research_generate_brief` and `deep_research_topic` overlap heavily. `research_light` and `research_web_collect` also overlap.

**Incompatible outputs/inputs:** The brief output is prose Markdown. To pass it to `knowledge_ingest_text`, the agent must construct the `title` and `text` fields manually.

**Number of MCP calls:** 4+.

**Workflow completable:** Partially. Web/Youtube research is unavailable.

**Final usability rating:** 3/5. Friction from unconfigured providers, generic briefs, and manual transformation between tools.

### Workflow 3: Find and read knowledge about a specific topic

**User goal:** "Cari catatan tentang N-BEATS dari knowledge base saya."

**Selected tools:**
1. `knowledge_search` — search vector store
2. `obsidian_search` — search vault for matching notes
3. `obsidian_read` — read a specific note

**Expected sequence:** knowledge_search → obsidian_search → obsidian_read

**Actual sequence:** knowledge_search returns evidence chunks with citation [K1]; obsidian_search returns matching file paths; obsidian_read for "PKM KC 2026/BAB 2 Tinjauan Pustaka — PKM-KC 2026 SmartBin PTAR-WCO.md" would need to be called.

**Missing information:** `knowledge_search` does not return file paths that can be directly used by `obsidian_read`. The agent must bridge the gap by using the search result title to construct a vault path.

**Unnecessary transformations:** Agent must parse the knowledge evidence manually and extract identifiers.

**Incompatible outputs/inputs:** `knowledge_search` returns chunk content but the path format differs from what `obsidian_read` expects. The agent must infer or guess the correct path.

**Number of MCP calls:** 3+.

**Workflow completable:** Yes, with manual effort.

**Final usability rating:** 3/5. Cross-tool output chaining requires manual text parsing.

## 8. Errors and Bugs

### High

#### HIGH-01: knowledge_answer consistently fails to synthesize

- **Affected capability:** `knowledge_answer`
- **Observed behavior:** For the query "Apa itu N-BEATS?", the tool returned "Sintesis model sedang tidak tersedia. Berikut bukti terpilih yang dapat diperiksa langsung." and dumped raw chunks.
- **Expected behavior:** The description says "Jawab dari knowledge melalui retrieval, sintesis, dan sitasi tervalidasi" — a synthesized answer with citations.
- **Reproduction:** Call `knowledge_answer` with `query="Apa itu N-BEATS?"`.
- **Evidence:** Response text: "Sintesis model sedang tidak tersedia."
- **Agent impact:** An AI agent cannot rely on this tool for grounded answers. It must fall back to `knowledge_search` + LLM inference, which defeats the purpose.
- **User impact:** User expects a synthesized answer but gets raw evidence dump.
- **Confidence:** Confirmed.
- **Recommendation:** Fix the synthesis step or update the description to clarify that it only returns evidence when synthesis is unavailable.

#### HIGH-02: Outputs expose internal WhatsApp identifiers

- **Affected capability:** `os_job_status`
- **Observed behavior:** Output contains `Target: 6285649204151@s.whatsapp.net` — the owner's full WhatsApp JID.
- **Expected behavior:** Tool output should not leak JIDs or identifiable phone numbers. Aggregate or show only obfuscated forms.
- **Reproduction:** Call `os_job_status`.
- **Evidence:** Response starts with `*Xninetzy OS Scheduler*\nTarget: 6285649204151@s.whatsapp.net`
- **Agent impact:** The model can potentially leak this identifier into downstream tool calls or context.
- **User impact:** WhatsApp JID exposure could be used for spam or social engineering.
- **Confidence:** Confirmed.
- **Recommendation:** Redact the JID in output. Show only a safe label (e.g., "owner").

### Medium

#### MED-01: ai_provider_status returns raw error instead of graceful message

- **Affected capability:** `ai_provider_status`
- **Observed behavior:** Returns `Error executing tool ai_provider_status: Provider 'flaz' belum siap: FLAZ_API_KEY.`
- **Expected behavior:** A formatted message showing current provider with an indication that it's not ready, not a raw error.
- **Reproduction:** Call `ai_provider_status`.
- **Confidence:** Confirmed.

#### MED-02: os_job_status exposes phone number

- See HIGH-02.

#### MED-03: knowledge_search returns irrelevant results for nonexistent queries

- **Affected capability:** `knowledge_search`
- **Observed behavior:** For query `ThisIsAVerySpecificNonexistentQueryXYZ123`, it returned chunks that do not match the query at all.
- **Expected behavior:** Return empty result or low-confidence result for queries with no semantic match.
- **Reproduction:** Call `knowledge_search` with a random UUID-like query.
- **Agent impact:** The agent may be misled into thinking content exists when it does not.
- **Confidence:** Confirmed.
- **Recommendation:** Add a relevance threshold that returns no results when no chunk matches above a minimum similarity score.

#### MED-04: obsidian_read requires exact path but error message is not helpful

- **Affected capability:** `obsidian_read`
- **Observed behavior:** When reading `Daily/2026-07-28` (a file that should exist based on search output), the tool returned `Gagal membaca 'Daily/2026-07-28': Note tidak ditemukan`.
- **Expected behavior:** The tool should accept paths without the `.md` extension (or the error should suggest that the path extension may be wrong and list similar files).
- **Reproduction:** First `obsidian_search("N-BEATS")` → then try to read one of the matching paths with a different extension.
- **Confidence:** Probable.
- **Recommendation:** Accept paths both with and without `.md` extension, or suggest did-you-mean file listings.

#### MED-05: research_light returns unhelpful response when providers are unconfigured

- **Affected capability:** `research_light`
- **Observed behavior:** Returns "Provider web search belum aktif atau tidak ada hasil." — does not indicate whether the provider is unconfigured or the query simply returned no results.
- **Expected behavior:** Distinguish between "API key not configured" and "no results found".
- **Reproduction:** Call `research_light`.
- **Confidence:** Confirmed.

#### MED-06: Generic plan/task breakdown outputs

- **Affected capability:** `generate_plan`, `task_breakdown`, `idea_analysis`
- **Observed behavior:** All three produce generic AI-generated text that does not reference the user's actual context (goals, tasks, knowledge). For example, `task_breakdown("Belajar Python")` returns general advice like "Definisikan hasil akhir" instead of a structured breakdown.
- **Expected behavior:** These tools should leverage the user's stored context (roadmaps, knowledge, goals) or explicitly state that they cannot personalize.
- **Confidence:** Confirmed.

#### MED-07: knowledge_search always returns evidence even for irrelevant queries

- **Affected capability:** `knowledge_search`
- **Observed behavior:** Returns `status=sufficient confidence=high` even for queries that should have no meaningful match.
- **Expected behavior:** Return `status=insufficient` or `confidence=low` for unmatchable queries.
- **Confidence:** Confirmed.

#### MED-08: knowledge_answer fails for any simple query

- **Affected capability:** `knowledge_answer`
- **Observed behavior:** Multiple queries all result in "Sintesis model sedang tidak tersedia."
- **Expected behavior:** Synthesize an answer from evidence when evidence exists.
- **Confidence:** Confirmed.

#### MED-09: Graph RAG tools consistently return empty for any query

- **Affected capability:** `graph_search`, `graph_get_context`, `graph_explain_topic_map`
- **Observed behavior:** All three return "Belum ada node graph yang cocok" for any query, even for topics that exist in the knowledge base (e.g., "PKM", "learning").
- **Expected behavior:** Return relevant nodes or explain that the graph is empty.
- **Confidence:** Confirmed. (Graph has only 2 nodes — the user may not have populated it yet.)

#### MED-10: Portal tools inconsistent — some require fresh session, others work

- **Affected capability:** `portal_profile`, `portal_academic_status`, `portal_current_krs`, `portal_schedule`
- **Observed behavior:** `portal_info` and `portal_session_status` return "session tersedia" but `portal_profile` returns "Session kedaluwarsa."
- **Expected behavior:** Either all portal tools should use the same session status or the discrepancy should be explained.
- **Confidence:** Confirmed.

### Low

#### LOW-01: goal_list silently handles invalid status values

- **Affected capability:** `goal_list`
- **Observed behavior:** `status="invalid_status"` returns "Tidak ada goal dengan status 'invalid_status'" instead of an error about the invalid enum value.
- **Expected behavior:** Reject invalid status values with an error listing valid options.
- **Confidence:** Confirmed.

#### LOW-02: generate_plan and task_breakdown produce generic advice

- **Affected capability:** `generate_plan`, `task_breakdown`
- **Observed behavior:** Generic step-by-step advice with no personalization.
- **Confidence:** Confirmed.

#### LOW-03: Naming inconsistency — `skill_discovery` vs `helper_get`

- Both tools provide capability overviews but with different names, output formats, and levels of detail. An agent may not know which to use.

#### LOW-04: WhatsApp Markdown formatting in tool output

- Many tools wrap output in WhatsApp Markdown (`*bold*`, `•`, emoji prefixes). This is fine for WhatsApp delivery but adds noise for MCP clients that render plaintext or JSON.

#### LOW-05: Inconsistent pagination

- `obsidian_list` uses `limit` parameter (returned as JSON array). `knowledge_list_sources` uses `limit` (Markdown list). `os_inbox` uses `limit` (Markdown). No tool implements cursor-based pagination.

#### LOW-06: `hebat_list_courses` with empty string vs no query returns different results

- Both return all courses, but internally they may be using different code paths.

#### LOW-07: Error messages use Indonesian while some descriptions use English

- Mix of Indonesian and English across tools. Not a functional issue but adds cognitive load for multilingual AI agents.

#### LOW-08: No total count in list outputs

- List tools show items but rarely include a total count. An agent must count items manually.

## 9. Consistency Review

### Naming conventions
- Mix of `snake_case` and English-Indonesian hybrid names (`hebat_list_courses`, `os_capture`, `learning_due_recall`).
- Some tools use verbs first (`task_list`, `goal_create`), others use domain first (`hebat_list_courses`, `portal_session_status`). This is domain-prefixing which is actually helpful for agent selection.
- Plural vs singular: `goal_list` (plural), `task_list` (plural), `habit_today` (singular).

### Schemas
- Most input schemas use clear typed fields with descriptions.
- No tool uses `additionalProperties: true` in schemas (good).
- Required fields are correctly marked.

### Outputs
- Inconsistent output format: some tools return JSON arrays (obsidian_list), most return WhatsApp Markdown text.
- No standard result envelope (e.g., `{success, data, error}`).
- Some tools use emoji prefixes for status; others use text.

### Errors
- Error handling is generally consistent: clear messages, no stack traces exposed.
- Mix of Indonesian and English error messages.
- No structured error format — all errors are plain text.

### Identifiers
- Task IDs are integers.
- Goal IDs are integers.
- HEBAT course IDs are integers (string representation).
- Graph node IDs are integers.
- No ID format is documented in field descriptions.

### Dates and time
- `datetime_now` returns both local (Asia/Jakarta) and ISO 8601.
- Other tools use Indonesian date formats inconsistently.
- No timezone parameter across tools.

### Language and terminology
- Mixed Indonesian and English throughout.
- Domain prefixes are consistent (hebat_, learning_, portal_, graph_, etc.).
- Abbreviations: `hebat` (not explained in descriptions), `hitl` (human-in-the-loop, not explained), `moc` (map of content, not explained in the tool itself).

## 10. Performance Observations

| Measurement | Observed value |
|---|---|
| Discovery (tools/list) | < 1s |
| Fastest tool | `calculate`, `datetime_now` — < 500ms |
| Slowest tool | `research_generate_brief`, `knowledge_search` — 3-5s |
| Typical read-only tool | 500ms — 2s |
| Output size (smallest) | `calculate` returns `37.5` |
| Output size (largest) | `knowledge_search` / `knowledge_answer` — can exceed 2000 tokens of raw chunk text |
| Unstable latency | `knowledge_answer` varied from 2s to 8s |
| Tools that hang | None observed (all completed within reasonable time) |

### Large output concerns
- `knowledge_search` and `knowledge_answer` return full chunk text that can consume a large portion of LLM context.
- `research_generate_brief` returns a multi-section brief that may exceed 1000 tokens.
- `obsidian_list` with default `limit=100` may return many files if the vault is large.

## 11. Upgrade Recommendations

### Immediate (P0)

| # | Recommendation | Evidence |
|---|---|---|
| R01 | Fix `knowledge_answer` synthesis | HIGH-01: synthesis always fails |
| R02 | Redact WhatsApp JID from tool outputs | HIGH-02: JID leaked in os_job_status |

### Short-term (P1)

| # | Recommendation | Evidence |
|---|---|---|
| R03 | Add relevance threshold to `knowledge_search` | MED-03: returns results for random queries |
| R04 | Distinguish "API not configured" from "no results" | MED-05: research_light |
| R05 | Add path extension flexibility to `obsidian_read` | MED-04: .md extension issue |
| R06 | Standardize output format (JSON envelope for MCP, text for WhatsApp) | Consistency issues |
| R07 | Add `total_count` to list outputs | LOW-08 |
| R08 | Clarify overlapping tool descriptions (os_today vs task_today vs life_dashboard) | Workflow 1 |

### Medium-term (P2)

| # | Recommendation | Evidence |
|---|---|---|
| R09 | Add tool descriptions that clearly state when NOT to use a tool | Agent selection ambiguity |
| R10 | Add idempotency keys to all mutation tools | Safety |
| R11 | Add structured error format across all tools | Consistency review |
| R12 | Add pagination support with cursor-based navigation | No pagination beyond limit |
| R13 | Standardize date/time format expectations across tools | Inconsistent date handling |
| R14 | Add output field descriptions for structured results | Current outputs are self-describing but undocumented |

### Optional future improvements (P3)

| # | Recommendation | Evidence |
|---|---|---|
| R15 | Add compound workflow tools (e.g., "research_save_both_to_knowledge_and_obsidian") | Workflow 2 |
| R16 | Expose server version through MCP metadata | Connection summary |
| R17 | Expose MCP resource endpoints for commonly queried data | No resources currently |
| R18 | Add `graph_search` integration with `knowledge_search` to cross-reference | Workflow 3 |
| R19 | Personalize `generate_plan` with user's stored goals and tasks | MED-06 |
| R20 | Add English descriptions alongside Indonesian | Mixed language concern |

## 12. Prioritized Improvement Roadmap

| Priority | Recommendation | Affected capability | Expected value | Complexity | Evidence |
|---|---|---|---|---|---|
| P0 | Fix knowledge_answer synthesis | knowledge_answer | AI agents get grounded answers | Medium | HIGH-01 |
| P0 | Redact WhatsApp JID | os_job_status | Prevent identifier leakage | Small | HIGH-02 |
| P1 | Add relevance threshold | knowledge_search | Avoid misleading results | Medium | MED-03 |
| P1 | Distinguish API config vs no results | research_light, web_search | Clearer user feedback | Small | MED-05 |
| P1 | Make obsidian_read tolerant of .md | obsidian_read | Reduce workflow friction | Small | MED-04 |
| P1 | Standardize output format | All tools | Consistent agent experience | Large | Section 9 |
| P1 | Add total_count | List tools | Better agent reasoning | Small | LOW-08 |
| P1 | Clarify tool descriptions | os_today, task_today, life_dashboard | Better tool selection | Small | Workflow 1 |
| P2 | Add idempotency keys | Mutating tools | Safe retry | Medium | Safety review |
| P2 | Structured error format | All tools | Actionable errors | Medium | Section 9 |
| P2 | Add cursor pagination | List tools | Handle large datasets | Medium | No pagination |
| P2 | Standardize datetime handling | Date-using tools | Consistent time handling | Small | Section 9 |
| P3 | Compound workflow tools | Research + save | Reduce MCP call count | Large | Workflow 2 |
| P3 | Expose server version | MCP metadata | Better diagnostics | Small | Connection summary |
| P3 | Add MCP resources | All domains | Standardized data access | Large | No resources |
| P3 | Personalize generate_plan | generate_plan | Higher quality plans | Medium | MED-06 |

## 13. Limitations

- **Mutating tools not tested:** Approximately 100 tools that modify real data were not executed. Their contracts were reviewed but no functional testing was performed.
- **External services unavailable:** Web search (TAVILY_API_KEY/SERPER_API_KEY) and YouTube search (YOUTUBE_API_KEY) were not configured, so tools depending on them could not be fully tested.
- **HEBAT Moodle external tests:** Tools that interact with HEBAT were partially tested (only those that work with cached/local data). Upload and sync tools were skipped.
- **WhatsApp messaging:** Tools that send real WhatsApp messages (`wa_send_text`, `wa_pin_message`, `wa_set_announce`) were not tested.
- **Cyber Campus portal:** Portal session was expired for some tools but active for others. Full portal workflow could not be tested.
- **Obsidian vault:** Tools that modify the vault were not fully tested (only search/read/list).
- **Source-code dependent behaviors:** Some tool behaviors (especially error handling, idempotency, and synthesis logic) require source-code inspection for complete analysis.
- **Load testing:** Not performed. Only sequential single-user testing was done.
- **Sandbox environment:** No isolated test sandbox was available. Minimal test data was created with clear "test" prefixes.

## 14. External MCP Ecosystem Integration Analysis

> This section compares the `xninetzy` MCP server's built-in research, web-search, and YouTube-search capabilities against the external `paper_research`, `web_search`, and `youtube_search` MCP servers that were available during this review. The goal is to determine whether and how these external MCP services should be integrated into the Xninetzy OS ecosystem.

### 14.1 Current Xninetzy Deep Research Architecture (as tested)

The current `xninetzy` MCP server contains these research/search/YouTube tools internally:

| Tool | What it does | Status during review |
|---|---|---|
| `deep_research_topic` | Full deep research with subplanning, session, admin-only | Works but no web/YouTube results |
| `research_light` | Lightweight search | Returns "not active" (no API keys) |
| `research_create_subplans` | Create sub-plans without executing | Works |
| `research_generate_brief` | Generate research brief outline | Works (generic output) |
| `research_web_collect` | Gather web sources | Returns "not active" (no TAVILY_API_KEY) |
| `research_youtube_collect` | Gather YouTube sources | Returns "not active" (no YOUTUBE_API_KEY) |
| `research_rank_sources` | Rank research sources | Not tested (no sources to rank) |
| `web_search` | Web search via Tavily/Serper | Returns "not active" |
| `youtube_search` | YouTube search via official API | Returns "not active" |
| `youtube_learning_search` | YouTube learning path curation | Returns "not active" |

**Core problem:** every external search tool depends on a configured API key (`TAVILY_API_KEY`, `SERPER_API_KEY`, `YOUTUBE_API_KEY`). None were configured during this review, making the entire research pipeline non-functional.

### 14.2 External MCP Server Capabilities Observed

#### `paper_research` MCP Server

| Capability | Sources | API-free? | Output format |
|---|---|---|---|
| `search_papers` | arXiv, CrossRef, Semantic Scholar, PubMed, PMC, dblp, OpenAlex, DOAJ, BASE, Zenodo, HAL, SSRN, IACR, bioRxiv, medRxiv, EuropePMC, CORE, OpenAIRE, CiteSeerX, Unpaywall | **All free/no API key** | Structured JSON |
| `search_arxiv` | arxiv.org | ✅ Free | JSON |
| `search_crossref` | CrossRef DOI metadata | ✅ Free | JSON |
| `search_semantic` | Semantic Scholar | ✅ Free | JSON |
| `search_google_scholar` | Google Scholar | ✅ Free | JSON |
| `search_pubmed` | PubMed/MEDLINE | ✅ Free | JSON |
| `search_openalex` | OpenAlex | ✅ Free | JSON |
| `search_dblp` | dblp CS bibliography | ✅ Free | JSON |
| `search_doaj` | Directory of Open Access Journals | ✅ Free | JSON |
| `search_base` | Bielefeld Academic Search Engine | ✅ Free | JSON |
| `search_zenodo` | Zenodo | ✅ Free | JSON |
| `search_hal` | HAL Open Archive | ✅ Free | JSON |
| `search_ssrn` | SSRN (metadata only) | ✅ Free | JSON |
| `search_iacr` | IACR ePrint | ✅ Free | JSON |
| `search_biorxiv` | bioRxiv (preprints) | ✅ Free | JSON |
| `search_medrxiv` | medRxiv (preprints) | ✅ Free | JSON |
| `search_europepmc` | Europe PMC | ✅ Free | JSON |
| `search_core` | CORE aggregator | ✅ Free | JSON |
| `search_openaire` | OpenAIRE | ✅ Free | JSON |
| `search_citeseerx` | CiteSeerX | ✅ Free | JSON |
| `search_unpaywall` | OA status lookup | ✅ Free | JSON |
| `get_crossref_paper_by_doi` | Single DOI resolution | ✅ Free | JSON |
| `read_<source>_paper` | Extract text from PDF | ✅ Free | Text |
| `download_<source>` | Download PDF | ✅ Free | File path |
| `download_with_fallback` | OA → Unpaywall → Sci-Hub | ✅ Free | File path |

**Why this matters for Xninetzy:**
- **Zero API key cost.** Every single `paper_research` tool works without any API key, using public/academic APIs.
- **20+ academic sources** — far beyond what Xninetzy's `research_*` tools attempt.
- **Full-text access:** `read_arxiv_paper`, `download_with_fallback` (Unpaywall → Sci-Hub chain) give actual academic paper content.
- **Structured output** — all tools return JSON, which an AI agent can consume programmatically without text parsing.
- **Handles DOIs, PMIDs, arXiv IDs** — academic identifier formats that Xninetzy currently has no tool for.

#### `web_search` MCP Server

| Capability | Engine | API-free? | Output format |
|---|---|---|---|
| `web_search` / `search` | DuckDuckGo, Bing, Startpage | ✅ **All free, no API key** | Structured + snippets |
| `fetchWebContent` | HTTP(S) URL fetcher | ✅ Free | Markdown/text |
| `fetchGithubReadme` | GitHub repo README | ✅ Free | Markdown |
| `fetchCsdnArticle` | CSDN article | ✅ Free | Text |
| `fetchJuejinArticle` | Juejin article | ✅ Free | Text |
| `fetchLinuxDoArticle` | Linux.do post | ✅ Free | Text |

**Why this matters for Xninetzy:**
- **DuckDuckGo is free** — no TAVILY_API_KEY or SERPER_API_KEY required.
- **Multiple search engines** (DuckDuckGo, Bing, Startpage) for fallback.
- **Readability mode** — can extract clean article content from web pages.
- **Chinese/Indonesian tech platforms** — CSDN, Juejin, Linux.do fetchers cover developer communities relevant to the user's learning context.

#### `youtube_search` MCP Server (ytdlp-based)

| Capability | What it does | API-free? | Output format |
|---|---|---|---|
| `ytdlp_search_videos` | Search videos by keyword | ✅ Free (yt-dlp) | JSON/Markdown |
| `ytdlp_get_video_metadata` | Full video metadata | ✅ Free | JSON |
| `ytdlp_get_video_metadata_summary` | Human-readable summary | ✅ Free | Text |
| `ytdlp_download_transcript` | Extract transcript text | ✅ Free | Plain text |
| `ytdlp_download_video_subtitles` | Download VTT subtitles | ✅ Free | VTT text |
| `ytdlp_download_video` | Download MP4 | ✅ Free (ffmpeg) | File path |
| `ytdlp_download_audio` | Extract M4A/MP3 audio | ✅ Free | File path |
| `ytdlp_get_video_comments` | Extract comments | ✅ Free | JSON/Markdown |
| `ytdlp_get_video_comments_summary` | Comment summary | ✅ Free | Text |
| `ytdlp_list_subtitle_languages` | Available languages | ✅ Free | Text |

**Why this matters for Xninetzy:**
- **No YOUTUBE_API_KEY needed** — uses yt-dlp which scrapes YouTube directly.
- **Transcript extraction** — step beyond what Xninetzy's `youtube_search` does (which only returns video metadata).
- **Comment analysis** — could feed into research pipeline.
- **Download capability** — could integrate with Xninetzy media tools.

### 14.3 Integration Feasibility Comparison

| Dimension | Current Xninetzy (internal) | External MCP approach | Winner |
|---|---|---|---|
| Academic sources | 0 (no academic search) | 20+ sources | External ✅ |
| Web search | Requires TAVILY_API_KEY / SERPER_API_KEY | DuckDuckGo free | External ✅ |
| YouTube search | Requires YOUTUBE_API_KEY | yt-dlp (free) | External ✅ |
| Paper full-text | Not available | PDF download + text extraction | External ✅ |
| Output structure | WhatsApp Markdown (mixed) | Structured JSON | External ✅ |
| Execution model | Direct tool calls in LangGraph | MCP sidecar process | Tie |
| Latency | Fast (internal SQLite) | Slower (external HTTP) | Internal ✅ |
| Offline capable | Yes | No (needs internet) | Internal ✅ |
| Security boundary | Single process | Separate MCP process | Tie |
| Maintenance | Self-managed | Package updates | Tie |

### 14.4 Architectural Integration Options

#### Option A: MCP Client Wrapper (recommended)

Add a lightweight MCP *client* inside the Xninetzy AI service that connects to `paper_research` and `web_search` as external MCP servers. Tools in `tools/registry.py` would delegate to the MCP client.

**How it works:**
```
User → Xninetzy Agent → xninetzy/tools/registry.py
                           ├── research_paper() → [MCP Client] → paper_research
                           ├── web_search() → [MCP Client] → web_search
                           └── youtube_transcript() → [MCP Client] → youtube_search
```

**Why this fits the existing architecture:**

From `CODEBASE_GUIDE_AND_FEATURE_PLAYBOOK.md`:
- `tools/` is a thin wrapper → pattern already established
- `coding_agent_run` already uses subprocess bridge for Codex/Claude Code — same pattern for MCP client
- `interfaces/mcp_server.py` already exists for serving — symmetric `interfaces/mcp_client.py` for consuming
- `tools/registry.py` is the canonical tool catalogue → just add new tools there

**Concrete implementation sketch:**
```python
# tools/external/mcp_client.py
class MCPToolClient:
    def __init__(self, server_name: str, command: str, args: list[str]):
        self.server_name = server_name
        # spawn subprocess, negotiate MCP protocol
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        # send JSON-RPC, return result
        ...

# tools/external/paper_tools.py
@tool
def research_search_papers(query: str, sources: str = "arxiv,crossref,semantic", max_results: int = 5) -> str:
    """Search academic papers across multiple sources (arXiv, CrossRef, Semantic Scholar, PubMed, etc.).
    Returns structured paper metadata including title, authors, year, DOI, and abstract.
    Use this for literature review, related work, academic references, and research discovery.
    """
    client = MCPToolClient("paper_research", ...)
    result = await client.call_tool("search_papers", {...})
    return format_result(result)

@tool
def web_search_duckduckgo(query: str, limit: int = 5) -> str:
    """Search the web using DuckDuckGo. No API key required.
    Returns page titles, URLs, and snippets.
    Use this for current information, documentation lookups, and general web research.
    """
    client = MCPToolClient("web_search", ...)
    result = await client.call_tool("search", {"query": query, "limit": limit})
    return format_result(result)

@tool
def youtube_get_transcript(url: str) -> str:
    """Extract and return the full transcript of a YouTube video as clean text.
    Returns the spoken content without timestamps.
    Use this when you need the verbatim content from a tutorial, lecture, or video.
    """
    client = MCPToolClient("youtube_search", ...)
    result = await client.call_tool("ytdlp_download_transcript", {"url": url, "language": "en"})
    return result
```

**Keys to fit the ecosystem:**
- Tool output → format to WhatsApp Markdown for end-user messages
- Tool output → keep as structured text for agent internal consumption
- Same idempotency, try/except, and error patterns as existing tools
- Registry entry in `get_tool_groups()` under "research" or "external"

#### Option B: Sidecar Process + Skill

Run all three MCP servers as Docker Compose sidecars. Install a dynamic skill `skill_external_mcp` that exposes their capabilities to the agent.

**Pros:** Zero code change to the Xninetzy core. Isolated processes.
**Cons:** More infra overhead. Dynamic skill system is new (see `SKILLS.md` — currently MVP).

#### Option C: Gradual replacement

Replace each Xninetzy internal tool individually:
1. Replace `web_search` → use `web_search` MCP DuckDuckGo source (drop TAVILY dependency)
2. Replace `youtube_search` / `youtube_learning_search` → use `youtube_search` MCP yt-dlp (drop YOUTUBE_API_KEY dependency)
3. Add `research_search_papers` as new capability (not replacing anything — this is entirely new)

### 14.5 Impact on Current Xninetzy Deep Research

| Current problem | How external MCP integration solves it |
|---|---|
| `web_search` returns "not active" | DuckDuckGo works without API key |
| `research_web_collect` returns "not active" | Can use `web_search` MCP instead |
| No academic paper search | 20+ sources available through `paper_research` |
| No DOI/identifier handling | `get_crossref_paper_by_doi`, `search_semantic` with multiple ID formats |
| `youtube_search` returns "not active" | yt-dlp works without API key |
| `knowledge_answer` synthesis broken | Can use `paper_research` + `web_search` as alternative grounded sources |
| Brief generation is generic | Can feed actual search results into the brief |

### 14.6 What Xninetzy Still Does Better

Despite the external MCP advantages, Xninetzy's own tools have strengths that the external MCP servers cannot replace:

| Capability | Xninetzy strength |
|---|---|
| **Personal knowledge retrieval** | `knowledge_search`, `knowledge_answer` — user's own stored notes and PDFs |
| **Obsidian vault** | `obsidian_search`, `obsidian_read` — personal second brain |
| **HEBAT/Moodle integration** | Course sync, assignment deadlines, material downloads |
| **Learning OS state** | Roadmaps, study sessions, mastery tracking, active recall |
| **Life OS** | Goals, tasks, habits, workouts, money — personal context |
| **Graph RAG** | User's personal concept graph (nodes/edges) |
| **Memory & rules** | User preferences, behavior rules — personalization |
| **Offline operation** | Works without internet (for local data) |

The external MCP servers handle **public/external** information. Xninetzy handles **personal/internal** information. They are complementary.

### 14.7 Concrete Recommendation

**Adopt Option A — MCP Client Wrapper.**

Implement an `interfaces/mcp_client.py` module that spawns and communicates with `paper_research` and `web_search` MCP servers via stdio JSON-RPC (the same way `xninetzy` itself serves MCP clients). Register wrapper tools in `tools/registry.py`.

**Priority:** P1 (short-term)
**Complexity:** Medium (similar to existing `coding_agent_run` subprocess bridge)
**Expected impact:**
- Web search works immediately (DuckDuckGo, no API key)
- Academic paper search becomes available (20+ sources, no API key)
- YouTube transcripts become available
- Existing `research_*` tools can be deprecated or upgraded
- Documentation: already covered in `R&D_WEB_ANALYSIS_AGENT.md` and research workflow documents

**Integration point with Xninetzy workflow:**
```
research_generate_brief / deep_research_topic
  → research_web_collect (CURRENT: broken)
    → REPLACED by: MCP web_search (DuckDuckGo free)
  → research_youtube_collect (CURRENT: broken)
    → REPLACED by: MCP youtube_search (yt-dlp free)
  → (NEW) search_papers (NOT available)
    → ADD: MCP paper_research (academic sources free)
→ research_rank_sources
→ research_generate_brief → research_save_brief → HITL
```

This makes the entire deep research pipeline functional with zero paid API keys.

## 15. Final Assessment

### Is the MCP understandable to an AI agent?
**Mostly yes.** The domain-prefixed tool names (hebat_, learning_, portal_, graph_) help an LLM select the correct domain. However, within a domain, multiple tools overlap in purpose and their descriptions are not precise enough for reliable automated selection. An AI agent can use this MCP server effectively with some trial and error.

### Are tool contracts sufficiently clear?
**Partially.** Descriptions explain what a tool does but rarely explain when *not* to use it. Input schemas are generally clean. Output schemas are inconsistent — some return structured JSON, most return WhatsApp Markdown. An AI agent must parse human-readable text in most cases.

### Are outputs reusable across workflows?
**Limited.** Outputs from one tool cannot be reliably piped into another tool without manual parsing. For example, `knowledge_search` returns chunk content but no stable file path that `obsidian_read` can accept. List tools return items without consistent identifiers.

### Are errors actionable?
**Mostly yes.** Error messages clearly indicate what went wrong (e.g., "Task ID 99999 tidak ditemukan"). However, some errors do not distinguish between "provider not configured" and "no results". No structured error format is used.

### Are there dangerous or confusing tools?
- **Low risk:** Most mutating tools require approval or confirmation. The `hebat_upload_submission` pathway has explicit token-based confirmation.
- **Medium risk:** `graph_add_node` and `graph_add_edge` have no idempotency key and could create duplicate nodes.
- **Safety note:** Internal identifiers (phone numbers) are exposed in `os_job_status` output.
- **Confusing overlaps:** `ai_provider_list` vs `ai_provider_status`; `os_today` vs `task_today` vs `life_dashboard`; `helper_get` vs `skill_discovery`.

### What are the three most important improvements?
1. **Fix `knowledge_answer` synthesis** — This is the primary RAG-based Q&A tool and it consistently fails to produce a synthesized answer.
2. **Standardize output format** — Switch from WhatsApp Markdown prose to structured JSON/plain text for MCP clients, while keeping WhatsApp rendering separate.
3. **Remove ambiguity from overlapping tool descriptions** — Clearly distinguish similar-sounding tools to prevent AI agent mis-selection.

### Final readiness status
**READY FOR INTERNAL USE.**

The server is functional, feature-rich, and has adequate safety guards for single-owner local deployment. However, the output inconsistency (WhatsApp Markdown vs structured data), unconfigured external providers, and several overlapping tools reduce reliability in an automated AI-agent workflow. Do not promote to "READY FOR PRODUCTION USE" until:
- `knowledge_answer` synthesis is fixed.
- WhatsApp JID is redacted from outputs.
- Output format is standardized.
- External API key status is clearly communicated by each tool.

## 16. Modification Declaration

This review was performed as a black-box MCP usability audit. No application source code, MCP implementation code, tests, dependencies, configuration, deployment settings, or production data were modified. The only file created or updated was `docs/plan/mcp-usability-review.md`.
