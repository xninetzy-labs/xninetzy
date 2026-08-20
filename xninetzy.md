# Xninetzy — Personal Learning OS & Life OS

> Dokumen ini menjelaskan **apa itu Xninetzy, skill & kemampuannya, dan cara kerjanya**.
> Informasi diambil langsung dari server Xninetzy (skill list, capability map, tool catalog)
> per **2026-08-08**. Katalog bersifat dinamis — owner dapat memasang skill baru kapan saja
> (`skill_validate` → `skill_install`) tanpa mengubah kode client.

---

## 1. Apa itu Xninetzy

Xninetzy adalah **Personal Learning OS dan Life OS** milik owner, yang:

- menjaga konteks personal dan project **lintas sesi** (memory durable + retrieval-based);
- membantu memahami dan mengerjakan **tugas akademik** (HEBAT/Moodle, Cyber Campus, KRS, UACC);
- melakukan **riset berbasis sumber** (multi-round, multi-source, evidence audit);
- membangun **pembelajaran aktif dan adaptif** (roadmap, active recall, mastery evidence);
- menghasilkan **dokumen & presentasi bertahap** (DOCX/PDF/PPTX/XLSX);
- mengelola **Life OS** (goal, task, habit, money, workout, reminder, daily review);
- menyimpan keputusan, progress, evidence, artifact, dan next action.

### Interface utama

| Interface | Peran |
|---|---|
| **WhatsApp** | Front utama: slash commands (`/helper`, `/today`, `/goals`, `/tasks`, `/money`, `/workout`, `/hebat`, `/jadwal`, `/portalinfo`, `/review`, `/capture`, `/inbox`, `/triage`, `/llm`, `/agent`, `/code`), CAPTCHA/OTP manual, notifikasi |
| **OpenCode / Codex / Claude Code** | Execution interface: coding, riset, dokumen, orkestrasi subagent |
| **MCP (server Xninetzy)** | Sumber utama personal state: Obsidian, knowledge, learning, HEBAT, life OS, task, reminder, research, workflow |
| **Obsidian vault** | Knowledge permanen, daily note, project note |
| **AI Runtime** | Pilih provider/model chat dan coding agent (Codex, Claude Code, OpenCode) |

---

## 2. Cara kerja (arsitektur & pola operasi)

```text
Owner (WhatsApp / OpenCode / Codex / Claude Code)
        │
        ▼
Xninetzy Server (MCP) ────┬── memory (durable, scoped, supersession)
                          ├── knowledge (vector store + Graph RAG)
                          ├── Obsidian vault
                          ├── Learning OS (roadmap, mastery, recall)
                          ├── Life OS (goal, task, habit, money, workout)
                          ├── HEBAT / Cyber Campus / UACC / QA portal (session aman)
                          ├── Research (deep research session, subplan)
                          ├── Workflow (draft/status/resume/cancel)
                          ├── Lightning (evaluasi & perbaikan diri)
                          └── HITL approval (gate untuk aksi berdampak besar)
        │
        ▼
Agent (primary) ── skill-first ── subagent (research/writing/QA)
```

### Prinsip kerja utama

1. **Xninetzy first** — untuk tugas/deadline, HEBAT, Cyber Campus, KRS, notes Obsidian,
   goals/tasks/habits/learning progress, checkpoint: tanya Xninetzy dulu, bukan mengarang.
2. **Skill-first policy** — sebelum workflow penting, agent memuat skill paling spesifik
   (mis. `xninetzy-memory`, `xninetzy-deep-research`, `xninetzy-hebat`). Skill mendefinisikan
   **prosedur**; MCP menyediakan **capability**; subagent menyediakan **isolated context**.
3. **Memory durable & scoped** — hanya informasi yang berguna lintas sesi yang disimpan,
   masing-masing dengan `scope, type, content, provenance, confidence, timestamp, supersedes`.
   Checkpoint (YAML) dibuat saat milestone, sebelum context membesar, setelah external action,
   dan sebelum sesi berakhir.
4. **Evidence-based** — tidak mengarang tool result, URL, DOI, citation, deadline, grade.
   Akses sumber dicatat statusnya (full text / abstract / metadata / snippet).
5. **Human-in-the-loop** — CAPTCHA/OTP dijawab **manual oleh owner**; aksi consequential
   (submit tugas, commit KRS, kirim pesan) butuh preview eksak + konfirmasi eksplisit.
6. **Completion contract** — sebelum menyatakan selesai: apa yang selesai, tool/skill/subagent
   yang benar-benar dipakai, file yang berubah, yang terverifikasi, yang belum pasti,
   external action, artifact path, checkpoint.

### Safety tiers

| Tier | Level | Contoh |
|---|---|---|
| 0 | Read only | search, retrieve, analisis, download materi, simulasi jadwal, draft |
| 1 | Reversible local write | note lokal, checkpoint, draft, research manifest |
| 2 | External reversible | upload draft tanpa final submission |
| 3 | Consequential external | submit assignment, commit KRS, send message, delete data — butuh preview + konfirmasi |
| 4 | Prohibited | bypass CAPTCHA/OTP, graded quiz/exam otomatis, fabrikasi evidence, impersonasi, ubah grade |

---

## 3. Skills

Ada dua kelompok: **skills agent lokal** (di `~/.config/opencode/skills/`) dan **skills katalog server** (ditemukan dinamis via `skill_list`).

### 3.1 Skills agent lokal (prosedur untuk agent)

| Skill | Fungsi |
|---|---|
| `xninetzy-memory` | Retrieve, tulis, konsolidasi, checkpoint, dan resume memory durable lintas sesi |
| `xninetzy-deep-research` | Deep research multi-round, multi-agent, berbasis sumber + evidence auditing |
| `xninetzy-research-memory` | Persist & resume research manifest, sources, claims, worker results, synthesis, gaps |
| `xninetzy-learning-coach` | Pembelajaran adaptif: prior knowledge, prerequisite, active recall, practice, mastery evidence, spaced review |
| `xninetzy-assignment-orchestrator` | Retrieve, pahami, dekomposisi, riset, bangun, validasi, siapkan tugas akademik dengan aman |
| `xninetzy-artifact-orchestrator` | Bangun artifact panjang (DOCX/PDF/PPTX/XLSX) lewat staged research → writing → integration → QA |
| `xninetzy-hebat` | Akses aman HEBAT/Moodle: course, tugas, deadline, materi, status submission, siapkan submit yang dikonfirmasi |
| `xninetzy-cyber-campus` | Akses aman status akademik Cyber Campus: jadwal, nilai, KRS — CAPTCHA/OTP manual |
| `xninetzy-krs` | Rencana, validasi, siapkan, commit KRS: kurikulum, roster, prerequisite, konflik, limit SKS, konfirmasi eksplisit |
| `xninetzy-uacc` | Akses aman SSO UNAIR UACC/UnairSatu dengan CAPTCHA manual, sesi terpisah dari Cyber Campus |
| `xninetzy-academic-safety` | Aturan authorization, confirmation, idempotency, revalidasi state, dan receipt untuk workflow akademik |

### 3.2 Skills katalog server (capability Xninetzy)

| Skill | Sumber | Fungsi |
|---|---|---|
| `xninetzy-os` | trusted-builtin | Koordinasi Xninetzy sebagai Learning OS & Life OS single-owner lintas interface (capture → understanding → planning → execution → review → adaptation) |
| `it-learning` | trusted-builtin | Roadmap & evidence-backed learning plan: programming, backend, DB, Docker, system design, AI agents, RAG, data analytics, ML |
| `hebat-academic` | trusted-builtin | Course HEBAT/Moodle, aktivitas, deadline, materi, PDF, persiapan submission (approval sebelum upload) |
| `academic-assignment` | owner-installed | Mengerjakan assignment end-to-end: instruksi → riset brief → dokumen (PDF/DOCX) → siap upload HEBAT |
| `cyber-campus` | trusted-builtin | Portal akademik: session, navigasi, profile, status, jadwal, nilai, penawaran MK, KRS planning |
| `krs-war` | owner-installed | Operasi KRS War (auto-commit) mahasiswa.unair.ac.id: plan Obsidian, ambil MK, upgrade kelas goal, verifikasi |
| `life-management` | trusted-builtin | Goal, task, reminder, habit, workout, money log, daily check-in, weekly review |
| `memory-chat` | trusted-builtin | Persist milestone summary, proses langkah, dan skill yang dipakai ke memory agar sesi berikutnya bisa resume |
| `obsidian-knowledge` | trusted-builtin | Baca/cari/organisasi/tulis vault Obsidian: notes, daily note, tags, frontmatter, backlinks, MOC, document ingestion |
| `graph-rag` | trusted-builtin | Model & query relasi berbasis evidence: concept maps, prerequisite reasoning, research-to-roadmap links |
| `research` | trusted-builtin | Riset evidence-first multi-source: scoping → verifikasi sumber → claim-evidence map → synthesis → adversarial review |
| `define-goal` | trusted-builtin | Membantu mendefinisikan goal yang konkret & terukur sebelum mulai kerja |
| `cli-creator` | trusted-builtin | Bangun CLI composable dari API docs/OpenAPI/curl/SDK/web app/admin tool |
| `pdf` | trusted-builtin | Baca/buat/review PDF dengan render visual (Poppler) + reportlab/pdfplumber/pypdf |
| `jupyter-notebook` | trusted-builtin | Scaffold/edit `.ipynb` dengan template & helper script |
| `transcribe` | trusted-builtin | Transkripsi audio/video ke teks, opsi diarization & known-speaker hints |
| `screenshot` | trusted-builtin | Screenshot desktop/app/window/region |
| `playwright` | trusted-builtin | Automasi browser via terminal: navigasi, form, snapshot, screenshot, UI-flow debugging |
| `playwright-interactive` | trusted-builtin | Interaksi browser/Electron persisten via `js_repl` |
| `gh-fix-ci` | trusted-builtin | Debug/fix GitHub PR checks (GitHub Actions) via `gh` |
| `security-best-practices` | trusted-builtin | Security review per bahasa (python/js/ts/go) — hanya saat diminta eksplisit |
| `security-threat-model` | trusted-builtin | Threat modeling berbasis repo: trust boundaries, assets, abuse paths, mitigations |
| `security-ownership-map` | trusted-builtin | Topologi kepemilikan kode (people-to-file), bus factor, export CSV/JSON |
| `xninetzy-tdd-impl` | owner-installed | Implementasi kode dari plan yang disetujui: inline TDD, per-task ledger, baseline-vs-delta, commit gate (umum, lintas bahasa) |
| `xninetzy-inmemory-db-test` | owner-installed | Pola test dengan in-memory DB (SQLite) di belakang ORM; fix error tipe-scan `time.Time` |
| `xninetzy-go-tdd-impl` | owner-installed | **DEPRECATED** → pakai `xninetzy-tdd-impl` |
| `xninetzy-go-sqlite-test` | owner-installed | **DEPRECATED** → pakai `xninetzy-inmemory-db-test` |
| `test-mcp` | owner-installed | Skill uji coba MCP session testing — hapus jika tidak diperlukan |

---

## 4. Kemampuan (capability map)

### 4.1 Xninetzy OS Kernel
Universal capture, inbox, triage, dan attention queue lintas interface
(`os_capture`, `os_inbox`, `os_triage`, `os_today`, `os_job_status`, `action_policy_evaluate`).

### 4.2 Learning OS
- Roadmap belajar otomatis (`learning_create_roadmap`, `learning_generate_today_plan`)
- Konsep + prerequisite + milestone + task (`learning_define_concept`, `learning_get_concept_map`)
- Sesi belajar aktif + mastery evidence (`learning_start_study_session`, `learning_complete_study_session`, `learning_record_concept_evidence`)
- Active recall / spaced review (`learning_create_recall_card`, `learning_due_recall`, `learning_submit_recall_answer`)
- Progress & review (`learning_get_study_progress`, `learning_review_week`, `learning_list_study_sessions`)
- Materi HEBAT → ringkas → simpan ke knowledge
- Tanya jawab dari knowledge base (RAG), cari video YouTube & artikel web

### 4.3 HEBAT / E-Learning UNAIR
- Login dengan kredensial terkonfigurasi (`hebat_start_login`, status sesi)
- Sync course & aktivitas (`hebat_sync_courses`, `hebat_sync_course_activities`)
- Cek tugas & deadline (`hebat_sync_assignments`, `hebat_get_assignment_detail`, `hebat_academic_digest`)
- Download & ringkas PDF materi (`hebat_download_material`, `hebat_read_pdf`)
- Upload tugas dengan konfirmasi token (`hebat_prepare_submission_from_whatsapp_file` → `hebat_upload_submission`)

### 4.4 Knowledge OS
- Ingest teks/file ke vector store (`knowledge_ingest_text`, `knowledge_ingest_file`, `document_ingest`)
- Cari semantik + jawaban tersitasi (`knowledge_search`, `knowledge_answer`)
- Evaluasi retrieval (`knowledge_evaluate_retrieval`, `knowledge_rebuild_index`)
- Document router structure-aware (`document_analyze`, `document_overview`, `document_tables`, `document_catalog`)
- Unified search lintas sumber (`unified_search`: knowledge + Obsidian + Graph RAG + memory)
- Graph RAG (`graph_search`, `graph_get_context`, `graph_explain_topic_map`, `graph_v3_*`)

### 4.5 Life OS
- Goal: buat, track, review (`goal_create`, `goal_list`, `goal_update_progress`, `goal_review`)
- Task: catat, lihat due, centang selesai (`task_capture`, `task_list`, `task_today`, `task_complete`, `task_breakdown`)
- Reminder dari natural language (`reminder_create`, `reminder_list`, `reminder_cancel`)
- Habit & workout (`habit_log`, `habit_today`, `workout_log`, `workout_summary`)
- Money (`money_add_transaction`, `money_summary`)
- Daily check-in & review (`daily_checkin`, `daily_review_generate`, `life_dashboard`)

### 4.6 Obsidian Vault
Daily note, learning note, project note; `obsidian_create/read/search/append/update_section`,
tags, frontmatter, backlinks, headings, MOC, folder canonical + verify/organize.

### 4.7 Research
- `web_search`, `youtube_search` (+ ranker, playlist finder)
- `research_light`, `research_web_collect`, `research_youtube_collect`, `research_rank_sources`
- `research_generate_brief`, `research_save_brief` (butuh approval), `research_create_subplans`
- `deep_research_topic` (admin-only, session, tanpa auto-save), `deep_research_get/list`
- `web_discover` (bounded GET/HEAD), `web_fetch`, `web_analysis_*` (allowlisted sites)
- PixelRAG: visual retrieval (`pixelrag_capture/search_public/search_local/health`)

### 4.8 Portal Akademik (Cyber Campus & UACC)
- **Cyber Campus**: `portal_login_start/submit_captcha/cancel`, `portal_session_status`,
  `portal_profile`, `portal_academic_status`, `portal_schedule`, `portal_grades` (token KHS sekali pakai),
  `portal_current_krs`, `portal_navigation`, `portal_krs_capabilities`
- **KRS War**: watcher read-only (`portal_krs_watcher_start/stop/status`),
  war auto-commit (`portal_krs_war_arm` **approval wajib** / `disarm` / `plan` / `dry_run` / `status`)
- **UACC/UnairSatu SSO**: `uacc_login_*`, `uacc_session_status`, `uacc_info`, `uacc_logout` (sesi terpisah dari Cyber Campus)
- **QA**: `qa_list_kuesioner`, `qa_fill_kuesioner` (**approval wajib**)

### 4.9 WhatsApp
`wa_send_text/image/document/audio/ptt/video/sticker`, `wa_pin_message`, `wa_set_announce`,
`wa_send_admin_verification`, `wa_forward_media_to_admin`, `media_read_document/image/audio`,
`media_ingest_to_knowledge`, `wa_send_*` via URL/base64.

### 4.10 AI Runtime & Tools
- `ai_provider_list/status/use` — pilih provider/model chat dari allowlist
- `coding_agent_list/status/use/run` — jalankan Codex, Claude Code, atau OpenCode (terbatas workspace, timeout, allowlist, kebijakan admin)
- `external_mcp_*` — daftarkan/panggil MCP stdio eksternal (secret dari env lokal)
- `workflow_*` — draft, status, resume, cancel workflow automation
- `lightning_*` — episode evaluasi, feedback, proposal perbaikan, strategy rank (self-improvement system)
- `draft_workflow`, `idea_analysis`, `generate_plan`, `task_breakdown`, `calculate`, `datetime_now`

---

## 5. Katalog tool (ringkasan risk level)

Dari `tool_catalog` server, setiap tool punya metadata:

```yaml
feature_pack: core | academic-unair | research
risk:         read | draft | write | final
requires_approval: true | false
requires_idempotency: true | false
stability:    stable
```

Contoh tool dengan `risk: final` + `requires_approval: true`:

- `hebat_upload_submission` — upload tugas ke HEBAT
- `portal_krs_war_arm` — aktifkan KRS War auto-commit
- `qa_fill_kuesioner` — isi kuesioner QA

Tool `risk: read` (contoh): `portal_*` read-only, `uacc_info`, `os_job_status`, `web_analysis_status`,
`obsidian_folder_status`. Semua tool write bersifat idempotent (`requires_idempotency: true`).

---

## 6. Memory & checkpoint (prosedur)

### 6.1 Retrieve (start sesi)
1. Ambil scoped context: request + workspace + project + artifact + goal aktif
   (`memory_get_context`, `memory_search`, `unified_search`)
2. Ambil checkpoint terbaru yang kompatibel
3. Ambil keputusan stabil, constraint, deadline, artifact, pending action
4. Verifikasi fakta eksternal yang mungkin berubah — **jangan muat seluruh history**

### 6.2 Write (durable only)
Hanya informasi berguna lintas sesi: keputusan disetujui user, requirement resmi, constraint stabil,
progress + evidence, source terpilih, artifact, blocker, next action.

```yaml
scope:        # project / course / goal
type:         # project_context | goal | decision | constraint | preference | learning_profile
content:      # isi
provenance:   # dari mana
confidence:   # tinggi/sedang/rendah
timestamp:    # ISO date
supersedes:   # id memory yang digantikan (jika ada)
```

### 6.3 Checkpoint (YAML)
```yaml
goal:
scope:
completed:
decisions:
constraints:
sources:
artifacts:
failed_attempts:
open_questions:
next_actions:
resume_hint:
```
Dibuat: setelah milestone · sebelum context membesar · sebelum generasi panjang ·
setelah external action · sebelum sesi berakhir.

### 6.4 Conflict handling
Preserve provenance · prefer approval eksplisit user · prefer data portal resmi terbaru ·
tandai record lama `superseded` · tidak pernah merge fakta yang bertentangan secara diam-diam.

---

## 7. Aturan keamanan & approval

1. **CAPTCHA & OTP** (HEBAT, Cyber Campus, UACC): dijawab **manual oleh owner** — tidak pernah di-bypass.
2. **Graded quiz/exam** tidak dikerjakan otonom.
3. **Submit tugas / commit KRS / kirim pesan / hapus data**: preview eksak + konfirmasi eksplisit, lalu
   eksekusi sekali → re-read → verifikasi → receipt.
4. **Token KHS** (nilai): sekali pakai, tidak disimpan, dikirim via WhatsApp admin.
5. **HITL approval** (`hitl_request_approval` / `hitl_approve` / `hitl_reject` / `hitl_list_pending`):
   gerbang untuk aksi berdampak besar; approval hanya dari admin/owner.
6. Prompt bukan security boundary — authorization diperiksa server Xninetzy.
7. **Tidak mengarang**: tool result, URL, DOI, citation, deadline, grade, memory, file content, status portal.

---

## 8. Cara agent memakai Xninetzy (routing rules)

Dari AGENTS.md (aturan operasi OpenCode untuk Xninetzy):

| Kebutuhan | Sumber pertama |
|---|---|
| Tugas/deadline, HEBAT/Moodle, Cyber Campus, KRS, notes Obsidian, goals/tasks/habits, progress, checkpoint | **Xninetzy (MCP)** |
| Coding, dataset, notebook, report, template di workspace | **File lokal** |
| Paper/jurnal/DOI/literature review | `paper_research` |
| Fakta eksternal, dokumentasi resmi, versi software, regulasi | `web_search` |
| Dokumentasi library versi spesifik | `context7` |
| Video lecture/tutorial (supplementary) | `youtube_search` — bukan primary evidence |
| PDF/DOCX/PPTX/XLSX → teks | `markitdown` |
| Testing web | Playwright CLI + skills (MCP hanya jika perlu state persisten) |
| GitHub | `github-operator` |

Multi-agent orchestration: deep research (`research-coordinator` → `topic-researcher` x3–6 →
`evidence-auditor` → synthesis), dokumen panjang (`assignment-analyst` → research → `section-writer` →
`evidence-auditor` → `document_generator` → `artifact-qa`), academic action (prepare → preview →
confirm → execute once → re-read → verify → receipt).

---

## 9. Slash commands (WhatsApp)

```
/helper /today /goals /tasks /money /workout /hebat /jadwal /portalinfo /review
/capture /inbox /triage /llm /agent /code
```

Contoh pemakaian: `"buat goal belajar React 2 minggu"`, `"cek tugas hebat"`, `/today`.

---

## 10. Catatan & sumber

- **Katalog skill & tool bersifat dinamis** — jalankan `xninetzy_skill_list`, `xninetzy_skill_discovery`,
  `xninetzy_helper_get <kategori>`, atau `xninetzy_tool_catalog` untuk versi terkini.
- Dokumen ini disusun dari: `skill_list`, `skill_discovery`, `helper_get`, `tool_catalog` (server Xninetzy),
  AGENTS.md (aturan operasi), dan skill lokal `~/.config/opencode/skills/xninetzy-*`.
- Tidak ada klaim yang tidak didukung sumber; perbarui dokumen ini bila katalog berubah.
