# Gap Analysis: Current State → Xninetzy Engineering Vision

**Basis:** MCP usability review (30 Juli 2026, 154 tools tested, 54 executed)
**Sumber visi:** `PROJECT_LEARNING_LIFE_OS_ANALYSIS.md`, arsitektur Next Phase, dan dokumentasi internal.
**Metode:** Black-box MCP testing + review seluruh dokumentasi `docs/plan/*.md`.

---

## Ringkasan

| Dimensi | Status | Coverage |
|---|---|---|
| Xninetzy Engineering | 🟡 Partial | ~60% dari target |
| Loop Engineering | 🟡 Partial | ~40% dari target |
| Contextual Engineering | 🟡 Partial | ~50% dari target |
| RL + Lightning Self-Upgrade | 🔴 Early | ~10% dari target |

---

## 1. Xninetzy Engineering

### Visi
Platform engineering terintegrasi yang menghubungkan WhatsApp, AI agent, scheduler, database, Obsidian, HEBAT, portal, knowledge, graph, research, dan learning OS menjadi satu sistem yang kohesif.

### Sudah Ada (Confirmed via MCP testing)

| Komponen | Tool/System | Status |
|---|---|---|
| WhatsApp bridge | wa-enggine (Baileys) | ✅ Berfungsi |
| AI core | FastAPI + LangGraph + ReAct | ✅ Berfungsi |
| Tool registry | `tools/registry.py` (154 tools) | ✅ Berfungsi |
| SQLite database | `db/sqlite.py` + migrations | ✅ Berfungsi |
| Obsidian vault | `obsidian_*` (14 tools) | ✅ Berfungsi |
| HEBAT/Moodle | `hebat_*` (13 tools) | ✅ Berfungsi |
| Portal Cyber Campus | `portal_*` (15 tools) | ✅ Berfungsi (session-dependent) |
| Knowledge RAG | FAISS + FTS5 + ingestion | ✅ Berfungsi (synthesis broken) |
| Learning OS | roadmap, study, recall, mastery | ✅ Berfungsi |
| Life OS | goals, tasks, habits, money, workout | ✅ Berfungsi |
| Graph RAG | SQLite MVP (node + edge) | 🟡 Berfungsi (kosong) |
| Memory system | semantic memory & rules | ✅ Berfungsi |
| Media ingestion | document parser, OCR | ✅ Tools terekspos |
| Skills system | skill registry & lookup | ✅ Berfungsi |
| Research tools | brief, subplan, web/youtube collect | 🟡 Web/YouTube tidak aktif |
| Workflow engine | multi-action DAG + scheduler | ✅ Berfungsi |
| Coding agents | Codex, Claude Code, OpenCode bridge | ✅ Berfungsi |
| HITL approval | approval request + approve/reject | ✅ Berfungsi |

### Kurang / Belum Terbangun

#### 1A. Event System & Event-Driven Architecture

**Visi Next Phase:**
```
Event → ambil konteks → tentukan urgensi → pilih workflow → jalankan tool → verifikasi hasil → simpan outcome
```

**Kondisi sekarang:**
- Tidak ada event table atau event bus.
- `os_job_status` menunjukkan scheduler job, tapi hanya morning_briefing + evening_checkin (2 job, terbatas).
- Tidak ada sistem publish/subscribe untuk event seperti `HEBAT_DEADLINE_FOUND`, `TASK_OVERDUE`, `HABIT_MISSED`, dll.

**Yang perlu dibangun:**
- `events` table di SQLite
- Event producer untuk setiap perubahan state (HEBAT sync selesai, task due, habit missed, dll)
- Event consumer / handler registry
- Urgensi kalkulator berdasarkan deadline + priority + dependency

**Prioritas:** P0 — ini fondasi automation loop.

#### 1B. Scheduler & Proactive Automation

**Visi:**
```
07.00 Morning Briefing
13.00 Midday Replan
21.30 Evening Review
Minggu Weekly Review
```

**Kondisi sekarang:**
- `daily_review_generate` ada dan berfungsi (manual, via command)
- Reminder system ada (via `reminder_create`)
- Tidak ada scheduling untuk briefing otomatis
- Tidak ada midday replan
- Tidak ada weekly review otomatis

**Yang perlu dibangun:**
- Scheduler job registry (APScheduler sudah available di stack)
- Morning briefing pipeline: os_today → hebat_academic_digest → format → wa_send_text
- Evening review pipeline: daily_review_generate → task_complete check → habit summary → format → wa_send_text
- Weekly review pipeline: learning_review_week → goal_review → money_summary → workout_summary → format
- Policy untuk menentukan kapan dan apa yang dikirim otomatis

**Prioritas:** P1

#### 1C. Scheduling & Dependency Graph

**Visi:**
```
Life Mission → Annual Goal → Quarterly Outcome
→ Project → Milestone → Task → Daily Action → Evidence of Progress
```

**Kondisi sekarang:**
- Goals terisolasi (tidak terhubung ke tasks)
- Tasks tidak terhubung ke goal_id
- Tidak ada hierarchy mission → goal → project → task
- Tidak ada dependency detection

**Yang perlu dibangun:**
- `goal_id` foreign key di tasks table (saat ini tidak ada)
- Hierarchy table: `goal_hierarchy(parent_goal_id, child_goal_id)`
- Project entity (level antara goal dan task)
- Dependency graph untuk task (task A harus selesai sebelum task B)
- Impact analysis: "goal X tidak akan tercapai karena task Y terlambat"

**Prioritas:** P1

#### 1D. Verification & Self-Healing

**Visi:**
```
action_id, status, attempt_count, expected_result,
actual_result, error, rollback_action, verified_at
```

**Kondisi sekarang:**
- `lightning_errors` ada untuk error tracing
- `lightning_healthcheck` untuk sistem health
- Tidak ada action log dengan verification step
- Tidak ada rollback mechanism
- Tidak ada retry dengan backoff

**Yang perlu dibangun:**
- Action log table (`action_log`)
- Verification step di setiap workflow (compare expected vs actual)
- Automatic retry untuk transient failures
- Rollback/handling untuk partial failures
- Health check endpoint sistematis

**Prioritas:** P2

#### 1E. Observability Dashboard

**Visi:**
Pantau tokens per workflow, tool calls, duplicate searches, retrieval hit rate, cost per research.

**Kondisi sekarang:**
- Tidak ada dashboard MCP tool
- Tidak ada tool untuk metrics agregat
- `os_job_status` hanya menunjukkan recent jobs, tanpa analytics

**Yang perlu dibangun:**
- Tool metrics collector (call count, latency, error rate, token usage)
- Cost tracking per LLM call
- Duplicate search detection (query normalization + hash comparison)
- Retrieval hit rate per knowledge search

**Prioritas:** P2

---

## 2. Loop Engineering

### Visi
Closed-loop learning dan life management:

```
Capture → Understand → Plan → Execute → Review → Adapt
```

Serta learning loop spesifik:

```
Research selesai
→ Simpan source registry
→ Buat concept notes di Obsidian
→ Hubungkan knowledge graph
→ Buat learning roadmap
→ Buat task membaca
→ Generate active-recall questions
→ Jadwalkan spaced repetition
→ Tes pemahaman
→ Update mastery score
→ Cari ulang bagian yang belum dikuasai
```

### Sudah Ada (Confirmed)

| Langkah | Tool/System | Status |
|---|---|---|
| Capture | `os_capture`, task_capture | ✅ |
| Understand | `knowledge_answer`, `knowledge_search` | 🟡 synthesis broken |
| Plan | `generate_plan`, `learning_create_roadmap` | ✅ generic |
| Execute | task_complete, study_session | ✅ |
| Review | `daily_review_generate`, `learning_review_week` | ✅ |
| Adapt | N/A | ❌ |
| Active recall | `learning_create_recall_card`, `learning_due_recall` | ✅ |
| Spaced repetition | `learning_submit_recall_answer` (scheduling update) | ✅ |
| Mastery update | `learning_record_concept_evidence` | ✅ |

### Kurang / Belum Terbangun

#### 2A. Closed-Loop Orchestrator

**Visi:** Satu workflow yang menghubungkan research → obsidian → graph → roadmap → task → recall → quiz → mastery.

**Kondisi sekarang:** Setiap tool berdiri sendiri. Tidak ada orchestrator yang menjalankan pipeline lengkap.

**Yang perlu dibangun:**
- `learning_closed_loop_run(topic)` — satu tool yang menjalankan seluruh pipeline
- State machine untuk tracking progress loop
- Conditional branching (jika mastery sudah tinggi, skip recall)

**Prioritas:** P1

#### 2B. Assignment Intelligence Pipeline

**Visi:**
```
Tugas baru di HEBAT → download instruksi & material
→ ekstrak requirement → identifikasi deliverable
→ estimasi kesulitan & durasi → periksa kalender & task aktif
→ pecah jadi subtugas → cari referensi
→ pantau progres → review sebelum deadline
→ siapkan file untuk diperiksa user
```

**Kondisi sekarang:**
- `hebat_get_assignment_detail` ada — menampilkan detail tugas
- `hebat_download_material` ada — download PDF materi
- Tidak ada pipeline otomatis setelah tugas baru terdeteksi

**Yang perlu dibangun:**
- Assignment parser yang ekstrak requirement dari deskripsi tugas
- Difficulty estimator berdasarkan historical data
- Subtask generator
- Deadline-aware scheduler untuk subtask
- Pre-deadline review reminder

**Prioritas:** P1

#### 2C. Mastery Graph & Progress Visualization

**Visi:**
```json
{
  "concept": "Reward Prediction Error",
  "mastery": 0.68,
  "evidence": {
    "papers_read": 3,
    "quiz_accuracy": 0.72,
    "explanation_score": 0.63
  },
  "weak_points": ["distributional reinforcement learning"]
}
```

**Kondisi sekarang:**
- `learning_get_concept_map` menampilkan konsep + prerequisite + mastery
- `learning_get_study_progress` menampilkan total sesi, menit, mastery
- Tidak ada weak point analysis
- Tidak ada evidence aggregation per konsep
- Tidak ada visualization-ready output

**Yang perlu dibangun:**
- Weak point detector (bandingkan quiz accuracy per subtopic)
- Evidence aggregator (gabung papers_read + quiz_accuracy + explanation)
- Mastery trend over time
- Visualization-ready output (JSON struktur untuk frontend)

**Prioritas:** P2

#### 2D. Capacity & Energy-Aware Planning

**Visi:**
Pertimbangan deadline, priority, estimated effort, calendar, energy level, task dependencies, historical completion rate.

**Kondisi sekarang:**
- Tidak ada energy tracking di planning
- `daily_checkin` mencatat mood/energy/fokus tapi tidak dipakai planning
- Task tidak punya field estimated_effort
- Tidak ada historical completion rate

**Yang perlu dibangun:**
- `task.estimated_minutes` field
- Energy-based task scheduling (task berat di jam energi tinggi)
- Historical completion rate per user
- Overload detection (total estimated effort > available time)

**Prioritas:** P2

#### 2E. Evidence Registry Permanen

**Visi:**
```json
{
  "claim": "Phasic dopamine activity can encode reward prediction error.",
  "sources": [{"doi": "10.1126/science.275.5306.1593", "support": "strong"}],
  "confidence": "high"
}
```

**Kondisi sekarang:**
- Knowledge base menyimpan chunks, bukan claims
- Tidak ada claim → evidence mapping
- Tidak ada confidence scoring
- Tidak ada re-verification scheduling

**Yang perlu dibangun:**
- Claims table (claim_id, claim_text, confidence, last_verified_at)
- Evidence junction table (claim_id, source_id, support_level)
- Claim extraction tool (dari paper/teks → claims)
- Re-verification scheduler (claim yang sudah lama → cek ulang)

**Prioritas:** P2

---

## 3. Contextual Engineering

### Visi
Sistem yang memahami konteks penuh kehidupan user sebelum mengambil keputusan:

```
Pesan → ambil konteks → tentukan urgensi → pilih workflow → jalankan tool → verifikasi hasil
```

Dengan 4 tingkat memory:
1. Working Memory — percakapan & tugas aktif
2. Episodic Memory — ringkasan sesi, keputusan, outcome
3. Semantic Memory — konsep stabil, paper, knowledge graph
4. Procedural Memory — workflow, preferensi, rules, skill

### Sudah Ada (Confirmed)

| Komponen | Tool/System | Status |
|---|---|---|
| Working Memory | Chat history + context packet | ✅ |
| Semantic Memory | Knowledge FAISS + Graph RAG | ✅ (partial) |
| Procedural Memory | Rules, style, skills | ✅ |
| Personal Context | `os_today`, `memory_get_context` | ✅ |
| Domain classifier | `context/builder.py` rule-based | ✅ |

### Kurang / Belum Terbangun

#### 3A. Episodic Memory System

**Visi:** Ringkasan sesi belajar, keputusan penting, error berulang, outcome — disimpan sebagai episodic memory yang bisa direcall.

**Kondisi sekarang:**
- `memory_*` tools ada (add, list, search, get_context) — ini semantic/procedural
- Tidak ada episodic memory yang terstruktur (sesi → outcome → reflection)
- Tidak ada session-level summarization

**Yang perlu dibangun:**
- Episodic memory table (session_id, type, summary, outcome, reflection, timestamp)
- Auto-summarization setelah study session selesai
- Pattern detection (error berulang, topik yang selalu ditunda)

**Prioritas:** P1

#### 3B. Multi-Modal Context Fusion

**Visi:** Satu ContextPacket yang menggabungkan:
- Pesan saat ini + quoted message
- Media content (dokumen/gambar yg dilampirkan)
- Memory relevan
- Knowledge releven
- Graph context
- Personal context (goals, tasks, deadlines)

**Kondisi sekarang:**
- `context/builder.py` ada dengan rule-based domain/intent/mode
- `memory_get_context` bisa diakses terpisah
- `os_today` bisa diakses terpisah
- Tidak ada fusion tool yang menggabungkan semuanya dalam satu panggilan

**Yang perlu dibangun:**
- `context_fuse(query)` — tool yang mengembalikan ContextPacket lengkap
- Weighted relevance scoring untuk tiap sumber konteks
- Context budget management (limit total konteks untuk LLM)

**Prioritas:** P1

#### 3C. Memory Compression Pipeline

**Visi:**
4 tingkat memory dengan kompresi otomatis:
```
Working → Episodic → Semantic → Procedural
```

**Kondisi sekarang:**
- Tidak ada kompresi
- Working memory = chat history penuh (raw)
- Tidak ada summarization otomatis

**Yang perlu dibangun:**
- Working memory summarizer (ringkas percakapan lama)
- Episodic extractor (ambil keputusan penting dari percakapan)
- Semantic consolidation (pattern detection → rule generation)
- Procedural skill extraction (workflow yang sering dipakai → skill)

**Prioritas:** P2

#### 3D. Proactive Context Push

**Visi:** Sistem mengirim konteks ke user tanpa diminta (deadline mendekat, task overdue, dll).

**Kondisi sekarang:**
- Hanya reaktif (menjawab pesan user)
- Tidak ada proactive notification selain reminder

**Yang perlu dibangun:**
- Urgency detector (deadline < 24 jam → push notification)
- Contextual suggestion engine (habit missed → suggest catch-up)
- Proactive interruption policy (kapan boleh ganggu, kapan tidak)

**Prioritas:** P1

---

## 4. RL + Lightning Self-Upgrade

### Visi
Self-improvement loop yang berjalan otomatis:

```
Mining error berulang
→ Analisis pola kegagalan
→ Generate improvement proposal
→ Approve/reject (admin)
→ Apply improvement
→ Monitor hasil
→ Learn dari outcome
```

Dengan Reinforcement Learning:
```
Action → Outcome → Reward → Policy update
```

### Sudah Ada (Confirmed)

| Komponen | Tool/System | Status |
|---|---|---|
| Error tracing | `lightning_errors` | ✅ |
| Error mining | `lightning_improve` | ✅ Berfungsi |
| Proposal system | `lightning_list_proposals` | ✅ Berfungsi |
| Approval flow | `lightning_approve` / `lightning_reject` | ✅ Berfungsi |
| Feedback capture | `lightning_feedback` | ✅ Berfungsi |
| Healthcheck | `lightning_healthcheck` | ✅ Berfungsi |

### Kurang / Belum Terbangun

#### 4A. RL Foundation — Action → Outcome → Reward

**Visi:** Setiap keputusan/tool call dicatat sebagai (state, action, reward, next_state) untuk RL training.

**Kondisi sekarang:**
- Tidak ada reward signal
- Tidak ada state recording
- Tidak ada policy update mechanism

**Yang perlu dibangun:**
- RL episode recorder (state → action → outcome → reward)
- Reward function: user_feedback (+1/-1), task_completion_rate, query_success, error_rate
- Policy update: weight adjustment berdasarkan reward history
- Exploration vs exploitation strategy

**Prioritas:** P1 (foundational)

#### 4B. Automated Improvement Loop

**Visi:**
```
Lightning improve → detect error pattern → generate proposal
→ if confidence > threshold, apply automatically
→ else request admin approval
→ monitor for regression
```

**Kondisi sekarang:**
- Manual: user harus menjalankan `/lightning-improve`
- Proposal selalu butuh admin approval
- Tidak ada automatic application
- Tidak ada post-apply monitoring

**Yang perlu dibangun:**
- Confidence threshold untuk auto-apply
- Automatic trigger (setelah N error atau tiap M jam)
- A/B testing framework (before/after comparison)
- Regression detector (apakah improvement bikin masalah baru)

**Prioritas:** P2

#### 4C. Code-Level Self-Improvement

**Visi:** Sistem bisa mengusulkan dan menerapkan perubahan kode sendiri berdasarkan error pattern dan usage data.

**Kondisi sekarang:**
- Sudah ada `coding_agent_run` — bisa menjalankan Codex/Claude Code/OpenCode
- `lightning_improve` bisa mining error dan generate proposal
- Tidak ada yang menghubungkan keduanya

**Yang perlu dibangun:**
- Code change proposal generator (error pattern → fix suggestion → diff)
- Safe code execution sandbox (sudah ada sebagian di `coding_agent_run`)
- Change verification (test dulu sebelum apply)
- Rollback mechanism if test fails

**Prioritas:** P2

#### 4D. User Behavior Learning

**Visi:** Sistem belajar dari pola interaksi user:
- Waktu produktif user → jadwalkan task berat di jam itu
- Topik yang sering di-ignore → turunkan prioritas
- Format respon yang disukai → sesuaikan style

**Kondisi sekarang:**
- `style_set` memungkinkan user atur gaya manual
- `rule_add` memungkinkan user atur aturan manual
- Tidak ada automatic behavior learning

**Yang perlu dibangun:**
- Interaction pattern analyzer (kapan user aktif, topik apa yang direspon cepat)
- Preference estimator (format apa yang paling efektif)
- Automatic style adjustment
- Automatic rule suggestion ("saya perhatikan kamu sering tanya X di jam Y, mau saya ingatkan otomatis?")

**Prioritas:** P3

#### 4E. Energy-Aware Adaptation

**Visi:** Sistem menyesuaikan interaksi berdasarkan energi user (dari daily check-in).

**Kondisi sekarang:**
- `daily_checkin` mencatat energy (1-5)
- Tidak digunakan untuk adaptation

**Yang perlu dibangun:**
- Energy-aware response length (energi rendah → jawab lebih singkat)
- Energy-aware task suggestion (energi rendah → suggest task ringan)
- Energy-aware notification frequency
- Energy trend analysis

**Prioritas:** P3

---

## 5. Ringkasan Prioritas

### P0 — Fondasi (harus ada sebelum yang lain)

| # | Gap | Kompleksitas | Dampak |
|---|---|---|---|
| 1 | Event system + event table | Medium | Automation loop foundation |
| 2 | Goal-Task dependency (goal_id di tasks) | Small | Hierarki kehidupan |
| 3 | Fix `knowledge_answer` synthesis | Medium | RAG yang bisa diandalkan |
| 4 | Integrasi `paper_research` + `web_search` (DuckDuckGo gratis) MCP | Medium | Research pipeline hidup |
| 5 | Redact JID di output tool | Small | Security |

### P1 — Core Loop Engineering

| # | Gap | Kompleksitas | Dampak |
|---|---|---|---|
| 6 | Closed-loop orchestrator (research→obsidian→graph→roadmap→task→recall) | Large | Learning loop otomatis |
| 7 | Assignment intelligence pipeline | Large | HEBAT tugas auto-processing |
| 8 | Morning briefing + evening review scheduler | Medium | Proactive engagement |
| 9 | Episodic memory system | Medium | Long-term context |
| 10 | Multi-modal context fusion (context_fuse) | Medium | Satu panggilan = semua konteks |
| 11 | RL episode recorder + reward function | Large | Self-improvement data |
| 12 | Proactive context push (urgensi detector) | Medium | Timing yang tepat |

### P2 — Advanced Engineering

| # | Gap | Kompleksitas | Dampak |
|---|---|---|---|
| 13 | Automated improvement loop (auto-apply proposal) | Large | Self-upgrade |
| 14 | Mastery graph + weak point analysis | Medium | Belajar adaptif |
| 15 | Evidence registry (claim→source→confidence) | Medium | Knowledge permanen |
| 16 | Capacity-aware planning (energy + effort) | Medium | Planning realistis |
| 17 | Memory compression pipeline (4 tingkat) | Medium | Context efficiency |
| 18 | Observability dashboard tool | Medium | Monitoring |
| 19 | Verification & self-healing | Large | Reliability |
| 20 | Code-level self-improvement (coding_agent_run + proposal) | Large | Otomatis fix bug |

### P3 — Visionary

| # | Gap | Kompleksitas | Dampak |
|---|---|---|---|
| 21 | User behavior learning | Large | Personalisasi dalam |
| 22 | Energy-aware adaptation | Medium | Interaksi humanis |
| 23 | Proactive intelligence (detect overload, forgotten deadline) | Large | Life orchestrator penuh |

---

## 6. Dependency Map

```
Event System (P0)
  ├── Scheduler & Proactive Loops (P1)
  │     ├── Morning Briefing
  │     ├── Evening Review
  │     └── Weekly Review
  │
  ├── Assignment Pipeline (P1)
  │     └── HEBAT task auto-processing
  │
  └── RL Episode Recorder (P1)
        ├── Automated Improvement Loop (P2)
        │     └── Code-Level Self-Improvement (P2)
        └── User Behavior Learning (P3)

Goal-Task Dependency (P0)
  └── Capacity-Aware Planning (P2)
        └── Energy-Aware Adaptation (P3)

knowledge_answer fix (P0)
  └── Closed-Loop Orchestrator (P1)
        ├── Mastery Graph (P2)
        └── Evidence Registry (P2)

External MCP Integration (P0)
  └── Research Pipeline penuh (P1)

Context Fusion (P1)
  └── Memory Compression (P2)

Proactive Context Push (P1)
  └── Proactive Intelligence (P3)
```

---

## 7. Quick Wins (Bisa dikerjakan dalam 1-2 hari)

| # | Gap | Existing tool yang bisa dipakai ulang |
|---|---|---|
| 1 | Redact JID di output | `os_job_status` — tambah masking |
| 2 | Goal-Task dependency | `goal_list` + `task_list` — tambah foreign key |
| 3 | Integrasi DuckDuckGo web search | `research_web_collect` → ganti backend pakai `web_search` MCP |
| 4 | Morning Briefing MVP | `os_today` + `hebat_academic_digest` + `wa_send_text` via workflow |
| 5 | Evening Review MVP | `daily_review_generate` + `habit_today` via workflow |

---

## 8. Catatan dari MCP Review

Temuan dari black-box testing yang relevan dengan engineering vision:

1. **Output format inconsistency** — Tool return WhatsApp Markdown, bukan JSON terstruktur. Ini masalah besar untuk loop engineering karena agent harus parse text manual. **Solusi:** dual output (JSON untuk agent consumption + Markdown untuk user display).

2. **Web search tidak aktif** — `research_web_collect`, `web_search`, `research_youtube_collect` semua return "not active". Ini blokir total untuk closed-loop learning yang butuh riset. **Solusi:** integrasi DuckDuckGo (free, tanpa API key) via `web_search` MCP.

3. **knowledge_answer synthesis broken** — RAG synthesis gagal total. Ini kritis untuk fase "Understand" di loop. **Solusi:** fix synthesis pipeline.

4. **Graph RAG kosong** — walau tools ada, data tidak ada. Closed-loop yang membutuhkan graph traversal tidak akan berfungsi. **Solusi:** populate graph otomatis saat knowledge ingest + research complete.

5. **Mutasi tanpa idempotency key** — `graph_add_node`, `knowledge_ingest_text`, `os_capture` tidak punya idempotency key. RL loop yang memanggil tool berulang bisa bikin data duplikat.

6. **Tidak ada Resource/Prompt MCP** — server hanya expose tools. Untuk observability dashboard, resource endpoints akan lebih cocok daripada tool calls.

---

## 9. Kesimpulan

**Xninetzy saat ini adalah platform reaktif yang sangat capable (154 tools) tetapi belum memiliki automation loop untuk menjadi proactive OS yang mandiri.**

Untuk mencapai **Xninetzy Engineering** yang utuh, diperlukan:
1. Event-driven architecture (P0)
2. Scheduler untuk proactive loops (P1)
3. Goal-Task dependency graph (P0)

Untuk mencapai **Loop Engineering**:
1. Closed-loop orchestrator yang menghubungkan research → obsidian → graph → roadmap → task → recall (P1)
2. Assignment intelligence pipeline (P1)
3. Mastery graph + weak point analysis (P2)

Untuk mencapai **Contextual Engineering**:
1. Episodic memory system (P1)
2. Multi-modal context fusion (P1)
3. Memory compression 4 tingkat (P2)

Untuk mencapai **RL + Lightning Self-Upgrade**:
1. RL episode recorder dengan reward function (P1)
2. Automated improvement loop dengan auto-apply (P2)
3. Code-level self-improvement (P2)

**Estimasi:** 3-4 bulan untuk P0-P1, +3-4 bulan untuk P2, +2-3 bulan untuk P3.
**Total:** ~9-11 bulan untuk mencapai full vision.

---

## 10. Referensi

- `docs/plan/mcp-usability-review.md` — hasil black-box testing 154 tools
- `PROJECT_LEARNING_LIFE_OS_ANALYSIS.md` — visi sistem
- Arsitektur Next Phase — automation & loop engineering
- `CODEBASE_GUIDE_AND_FEATURE_PLAYBOOK.md` — pola engineering yang sudah ada
- `WA_AI_SECOND_BRAIN_AUDIT.md` — audit state Juni 2026
