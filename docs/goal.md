Saya sudah menyusun **master prompt implementasi V1 Tier 3** yang dapat langsung diberikan ke OpenCode, Codex, atau Claude Code.

[Download XNINETZY Tier 3 V1 Master Prompt](sandbox:/mnt/data/XNINETZY_TIER3_V1_MASTER_PROMPT.md)

## Arah V1 yang ditetapkan

Prompt tersebut sengaja **tidak langsung membangun ML Lab, RL, self-upgrade, atau autonomous event-driven system**. Dalam roadmap repository, kemampuan tersebut memang ditempatkan sebagai V2 dan mensyaratkan V1 sudah stabil terlebih dahulu. 

V1 difokuskan untuk mengubah kondisi sekarang dari:

> **READY FOR INTERNAL USE**

menjadi:

> **Production-ready local single-owner Integrated Personal Learning OS.**

Audit MCP menemukan 154 tool dengan masalah utama berupa output tidak konsisten dan deskripsi tool yang masih ambigu bagi agent.  Roadmap V1 juga menetapkan fondasi seperti structured errors, idempotency, output redaction, grounded knowledge synthesis, search gratis, dokumentasi, coverage, dan CI sebagai syarat rilis. 

## Isi prompt lengkap

Master prompt tersebut memaksa coding agent menjalankan pekerjaan dalam urutan:

```text
Truth Audit
→ Stable Tool Contract
→ Output Redaction
→ Mutation Idempotency
→ Grounded Knowledge Reliability
→ Free Research Providers
→ Shared Tier 3 Loop
→ Interface Parity
→ Operational Reliability
→ Test Coverage dan CI
→ Open-Source Developer Experience
→ V1 Release Audit
```

### Batch yang akan dikerjakan

| Batch   | Fokus                                                           |
| ------- | --------------------------------------------------------------- |
| Batch 0 | Audit fakta antara kode, test, progress tracker, dan roadmap    |
| Batch 1 | Kontrak output/error MCP yang stabil dan aman                   |
| Batch 2 | Idempotency dan replay safety seluruh mutasi penting            |
| Batch 3 | Perbaikan penuh `knowledge_answer` dan validasi citation        |
| Batch 4 | DuckDuckGo, `yt-dlp`, arXiv, dan CrossRef tanpa paid search key |
| Batch 5 | Integrasi loop Capture → Review dan interface parity            |
| Batch 6 | Backup, recovery, health, worker, dan Docker hardening          |
| Batch 7 | Coverage domain kritis minimal 80% dan CI                       |
| Batch 8 | Installer, README, contribution guide, dan dokumentasi OSS      |
| Batch 9 | Audit release candidate Tier 3 V1                               |

## Tier 3 yang ingin dicapai

Prompt menetapkan enam journey yang wajib bekerja end-to-end:

```text
Capture
→ Inbox
→ Triage
→ Task
→ Today
→ Complete
→ Review
```

```text
Source
→ Knowledge ingest
→ Hybrid retrieval
→ Grounded answer
→ Valid citations
→ Learning note
```

```text
Roadmap draft
→ Approval
→ Activation
→ Shared tasks
→ Task completion
→ Roadmap progress
→ Weekly review
```

```text
Research
→ Source registry
→ Research brief
→ Approval
→ Obsidian / Knowledge / Graph
→ Roadmap / Task
```

```text
HEBAT atau Cyber Campus read
→ Deadline / Material / Schedule
→ Attention queue
→ Task / Reminder
```

```text
WhatsApp attachment
→ Durable media
→ Parsing / OCR
→ Knowledge ingestion
→ Grounded answer
```

Semua journey wajib menggunakan:

```text
WhatsApp / CLI / LangGraph / MCP
                ↓
       Central Tool Registry
                ↓
   Shared Domain, Policy, dan State
```

Ini mengikuti aturan arsitektur repository bahwa interface hanya menjadi pintu masuk, business logic berada di `domains/` atau `os/`, dan tool menjadi adapter tipis. 

## Scope yang sengaja dibekukan

Prompt melarang coding agent memperluas pekerjaan ke:

* RL dan reward optimization;
* automatic code self-modification;
* autonomous Lightning auto-apply;
* ML training dan Colab/Kaggle orchestration;
* multi-user atau SaaS;
* domain Biology/Neuroscience;
* full episodic-memory compression;
* KRS mutation dan final submission;
* CAPTCHA atau OTP automation;
* Tier 4 proactive intelligence.

Fitur Tier 4 yang sudah terlanjur ada tidak dihapus, tetapi hanya distabilkan bila dibutuhkan V1.

## Cara menggunakannya

Letakkan file tersebut di repository:

```bash
cp XNINETZY_TIER3_V1_MASTER_PROMPT.md \
  docs/plan/XNINETZY_TIER3_V1_MASTER_PROMPT.md
```

Lalu berikan ke OpenCode:

```text
Baca AGENTS.md dan
docs/plan/XNINETZY_TIER3_V1_MASTER_PROMPT.md.

Jalankan instruksi tersebut mulai dari Batch 0.
Jangan langsung mengimplementasikan semua roadmap lama.
Audit kode dan test sebagai sumber kebenaran, buat
docs/plan/XNINETZY_TIER3_V1_FOUNDATION_PLAN.md,
kemudian kerjakan batch secara berurutan sampai V1 release audit.
```

Prompt juga sudah mengharuskan agent menjaga perubahan user, tidak melakukan `git reset`, tidak membuat commit/tag/release tanpa izin, menjalankan full test, dan tidak mengklaim “production ready” sebelum seluruh release gate benar-benar terpenuhi.
