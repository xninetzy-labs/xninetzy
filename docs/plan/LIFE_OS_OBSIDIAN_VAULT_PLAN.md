# Life OS — Obsidian Vault Integration Plan

**Tujuan:** Transformasi vault Obsidian Xninetzy dari learning-centric vault menjadi Life OS + Learning OS yang terintegrasi penuh: daily → weekly → monthly → quarterly reviews, life areas (PARA), habits/routines tracking, goals MOC, dan otomatisasi lewat Xninetzy tools.

**Basis riset:** PARA Method (Tiago Forte 2017/2023, Building a Second Brain), GTD Weekly Review (David Allen), Life OS vault templates (thejourneyofbabo, cotemaxime/obsidian-para-starter), Obsidian PKM framework (Nick Milo LYT/ACE), analisis gap Xninetzy (MCP usability review 30 Juli 2026), dan pengalaman langsung menggunakan 54 tools Xninetzy.

---

## Arsitektur Target

```
Daily Notes (template upgrade)
    ↓ setiap hari
Weekly Review (minggu)
    ↓ setiap minggu
Monthly Review (bulan)
    ↓ setiap bulan
Quarterly / Annual Review
```

Siklus hidup:

```
Capture (inbox/WhatsApp/obsidian)
    → Process (daily note → task/habit/note)
    → Review (weekly: check all areas)
    → Plan (monthly: adjust goals)
    → Reflect (quarterly: life audit)
```

---

## 1. Current State vs Target

| Dimensi | Saat Ini | Target |
|---|---|---|
| Daily Note Template | 179 bytes, 5 section minimal | Template lengkap dengan habits, money, learning, refleksi |
| Weekly Review | ❌ Tidak ada | Mingguan: GTD 3 fase + refleksi + planning |
| Monthly Review | ❌ Tidak ada | Bulanan: goal progress, financial review, habit trends |
| Life Areas (PARA) | ❌ Tidak ada | 5-8 area hidup (Health, Finance, Education, Spiritual, Relationships, Career) |
| Goals MOC | Hanya `## Notes` kosong | Active goals per area, progress tracker, completed |
| Routines | ❌ Tidak ada | Pagi & malam checklist |
| Journal | ❌ Tidak ada | Catatan refleksi bebas |
| Habits | Ada di Xninetzy tools, **tidak di vault** | Habits direfleksikan di daily + weekly |
| Money | Ada di Xninetzy tools, **tidak di vault** | Summary pengeluaran di weekly/monthly |
| Workout | Ada di Xninetzy tools, **tidak di vault** | Ringkasan workout di weekly |
| _INDEX.md | Cuma punya Goals, Learning, Projects | Tambah Life section |

---

## 2. Folder Structure Target

```
Life/
├── Areas/
│   ├── 💰 Finance.md
│   ├── 🧠 Education & Career.md
│   ├── ⚕️ Health & Fitness.md
│   ├── 🤝 Relationships.md
│   ├── 🧘 Spiritual.md
│   └── 🏠 Home & Environment.md
├── Reviews/
│   ├── Weekly/
│   │   └── 2026-W31.md
│   ├── Monthly/
│   │   └── 2026-07.md
│   └── Quarterly/
│       └── 2026-Q3.md
├── Routines.md
└── 🧭 Life — MOC.md

Journal/
├── 2026-07.md
└── (per bulan atau per topik)

Templates/
├── Daily Note Template.md     ← UPGRADE
├── Weekly Review Template.md   ← NEW
├── Monthly Review Template.md  ← NEW
└── Life Area Note.md           ← NEW
```

---

## 3. Daily Note Template — Desain Baru

Template sekarang terlalu simpel (179 bytes). Yang baru harus mencakup:

### Frontmatter
```yaml
---
created: {{date}}
tags: [daily]
mood: 
energy: 
focus: 
---
```

### Sections
1. **🎯 Fokus Hari Ini** — maksimal 3 prioritas
2. **✅ Tasks** — checklist, bisa link ke task Xninetzy
3. **📊 Habits** — checklist rutinitas (bangun, sholat, olahraga, baca)
4. **💰 Pengeluaran** — catatan belanja (map ke money_add_transaction)
5. **📖 Learning** — apa yang dipelajari hari ini
6. **🤔 Refleksi Malam** — 3 prompt: wins, challenges, gratitude
7. **🎯 Goals Check-in** — progress ke active goals
8. **📝 Catatan Bebas** — capture inbox

### Integrasi Xninetzy
- `xninetzy_daily_checkin` → mood/energy/focus di frontmatter
- `xninetzy_habit_today` → habits checklist
- `xninetzy_task_today` → task list
- `xninetzy_money_summary` → pengeluaran (manual entry)
- `xninetzy_daily_review_generate` → refleksi malam

---

## 4. Weekly Review — Desain

Terinspirasi GTD Weekly Review (David Allen) 3 fase:

### Fase 1: Get Clear (10 menit)
- [ ] Proses semua inbox (os_inbox → triage)
- [ ] Catat wins & challenges minggu ini
- [ ] Empty head: catat ide/loop yang belum tertangkap

### Fase 2: Get Current (15 menit)
- [ ] Review tasks: apa yang selesai vs pending
- [ ] Review goals: progres per area
- [ ] Review habits: streak minggu ini
- [ ] Review money: total pengeluaran mingguan
- [ ] Review workout: sesi latihan
- [ ] Review learning: apa yang dipelajari

### Fase 3: Get Creative (10 menit)
- [ ] Adjust priorities minggu depan
- [ ] Catat insight/pattern dari minggu ini
- [ ] Satu hal yang mau berbeda minggu depan

### Integrasi Xninetzy
- `xninetzy_task_list` + `task_today` → task review
- `xninetzy_goal_list` + `goal_review` → goal progress
- `xninetzy_habit_today` → habits streak
- `xninetzy_money_summary(period="week")` → financial
- `xninetzy_workout_summary(period="week")` → workout
- `xninetzy_learning_review_week` → learning reflection

---

## 5. Life Areas (PARA) — Desain

Mengadopsi konsep **Areas** dari PARA Method (Tiago Forte): ongoing responsibilities with standards to maintain.

### Area 1: 💰 Finance
- Monthly budget tracking
- Pengeluaran vs pemasukan
- Target nabung
- Linked tools: `money_add_transaction`, `money_summary`

### Area 2: 🧠 Education & Career
- Progress kuliah (HEBAT)
- Skill development
- PKM / research progress
- Linked tools: `hebat_*`, `learning_*`, `research_*`

### Area 3: ⚕️ Health & Fitness
- Workout consistency
- Sleep & energy tracking (dari daily check-in)
- Medical checkup
- Linked tools: `workout_log`, `daily_checkin`, `habit_log`

### Area 4: 🤝 Relationships
- Keluarga dan teman
- Social events
- Linked tools: (manual — future: contact system?)

### Area 5: 🧘 Spiritual
- Ibadah consistency (sholat, puasa, ngaji)
- Refleksi spiritual
- Linked tools: `habit_log`

### Area 6: 🏠 Home & Environment
- Chores, maintenance
- Lingkungan belajar/kerja
- Linked tools: (manual — future: task?)

---

## 6. Goals MOC — Desain

```markdown
# 🎯 Goals — MOC

## Active Goals

### 💰 Finance
- [ ] Goal: ...  [target: ...]  [progress: ...%]

### 🧠 Education
- [ ] Goal: ...  [target: ...]  [progress: ...%]

### ⚕️ Health
- [ ] Goal: ...  [target: ...]  [progress: ...%]

## Completed
- [x] Goal (selesai tanggal ...)

## Per Area — Maps
- [[Life/Areas/💰 Finance|💰 Finance]]
- [[Life/Areas/🧠 Education & Career|🧠 Education & Career]]
- [[Life/Areas/⚕️ Health & Fitness|⚕️ Health & Fitness]]
```

---

## 7. Codebase Integration — Yang Perlu Dibangun di Xninetzy

### Jangka Pendek (Vault First — Bisa Langsung)
| Item | Status | Notes |
|---|---|---|
| Folder `Life/` + `Life/Areas/` + `Life/Reviews/` | Perlu dibuat | Bisa manual via `obsidian_create_folder` |
| Template upgrade | Perlu ditulis | Tulis markdown template |
| Life Areas notes | Perlu ditulis | Satu note per area |
| Weekly Review template | Perlu ditulis | Template + contoh review |
| Goals MOC | Perlu diupdate | Dari kosong jadi proper |
| _INDEX.md update | Perlu ditambah | Life section |
| Journal/ folder | Perlu dibuat | Folder + contoh |

### Jangka Menengah (Codebase — Perlu Development)
| Item | Priority | Referensi Gap Analysis |
|---|---|---|
| goal_id foreign key di tasks | P1 | Gap 1C — Goal-Task hierarchy |
| Weekly review auto-generate tool | P1 | Gap 1B — Scheduler enhancement |
| Monthly review template + tool | P2 | Gap 1B |
| Life dashboard di Obsidian (dataview-compatible query) | P2 | Gap — integration layer |
| Periodic notes system (weekly/monthly auto-create) | P2 | Gap 1B — Scheduler |
| Unified search: vault + knowledge + graph + life | P3 | Bug B9 dari bug report |

### Jangka Panjang
| Item | Notes |
|---|---|
| Event-driven: habit_missed → notification | Gap 1A — Event system |
| Goal → Project → Task hierarchy | Gap 1C — Dependency graph |
| Life areas linked ke goals & tasks otomatis | Gap — Data model |
| Auto weekly review dari aggregated data | Gap 1B — Scheduler |

---

## 8. Prioritas Implementasi

| Phase | Item | Waktu | Dampak |
|---|---|---|---|
| 🏃 **Phase 1 (sekarang)** | Daily template upgrade | 10 menit | Dipakai tiap hari |
| 🏃 **Phase 1 (sekarang)** | Life/ folder + Areas | 15 menit | Struktur jangka panjang |
| 🏃 **Phase 1 (sekarang)** | Weekly review template | 10 menit | Siklus mingguan |
| 🏃 **Phase 1 (sekarang)** | Goals MOC update | 5 menit | Visibilitas goals |
| 🏃 **Phase 1 (sekarang)** | Routines note | 5 menit | Struktur harian |
| 🏃 **Phase 1 (sekarang)** | _INDEX.md update | 5 menit | Navigasi |
| 🚀 **Phase 2 (dev)** | goal_id foreign key | 4-8 jam | Foundational |
| 🚀 **Phase 2 (dev)** | Weekly review auto tool | 4-8 jam | Otomatisasi |
| 🚀 **Phase 2 (dev)** | Monthly review template | 2-4 jam | Siklus bulanan |
| 🌟 **Phase 3 (future)** | Event-driven life management | weeks | Full automation |

---

## Sumber Riset

- Tiago Forte, *Building a Second Brain* (2022) dan *The PARA Method* (2023)
- David Allen, *Getting Things Done* (2001/2015)
- Tiago Forte, "The PARA Method: The Simple System for Organizing Your Digital Life in Seconds" — fortelabs.com (2017/2023)
- thejourneyofbabo, "Life OS Vault" — github.com (Obsidian template)
- cotemaxime, "PARA Starter Kit" — github.com/obsidian-para-starter
- PKM Wiki, "PARA Method" — pkm-wiki.knowii.net
- Dan Holloran, "The PARA Method in Obsidian: A Practical Guide" (2026)
- Iwo Szapar, "The PARA Method: A Complete Guide" (2026)
- Fabric, "The PARA Method: A Complete Guide" (2026)
- Obsibrain, "The Obsidian Weekly Review System" (2026)
- loggd.life, "The GTD Weekly Review: A 20-Minute Template" (2026)
- Todoist, "The PARA Method: How to Organize Your Life in 4 Categories"
- Gap Analysis Engineering Vision — docs/plan/GAP_ANALYSIS_ENGINEERING_VISION.md
- MCP Usability Review — docs/plan/mcp-usability-review.md
- Tool Bug Report — docs/plan/TOOL_BUG_REPORT_SESI_20260730.md

---

*Ditulis berdasarkan deep research (web: 15+ sumber), existing vault analysis, Xninetzy source code audit, dan gap analysis. 30 Juli 2026.*
