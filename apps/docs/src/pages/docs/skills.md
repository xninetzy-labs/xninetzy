---
layout: ../../layouts/DocsLayout.astro
title: Shared Agent Skills
description: Katalog skill terbuka yang dipakai bersama oleh LangGraph, MCP, Codex, Claude Code, dan OpenCode.
section: Operasional
---

Xninetzy memakai kontrak Agent Skills SKILL.md. Skill adalah prosedur kerja,
bukan sumber fakta. Fakta tetap harus berasal dari tool OS, evidence bundle,
portal, atau knowledge retrieval yang tervalidasi.

Semua interface membaca katalog yang sama:

~~~text
LangGraph / WhatsApp / MCP / Codex / Claude Code / OpenCode
                         ↓
              services/ai/.agents/skills
~~~

## Skill bawaan Xninetzy

- xninetzy-os — prinsip dan batas OS;
- it-learning — roadmap, konsep, sesi, mastery, recall;
- research — research plan, sumber, citation;
- obsidian-knowledge — vault dan knowledge grounding;
- graph-rag — node, edge, prerequisite, dan topic map;
- hebat-academic — course, material, deadline, dan submission policy;
- cyber-campus — portal read, token, CAPTCHA, dan KRS safety;
- life-management — goal, task, habit, money, workout, dan review.

## Skill open-source tambahan

Skill berikut diambil dari katalog terbuka openai/skills dan divalidasi oleh
parser Xninetzy:

| Skill | Kegunaan |
|---|---|
| define-goal | Menentukan outcome, prioritas, dan milestone yang bisa dievaluasi |
| jupyter-notebook | Eksperimen data analytics, ML, visualisasi, dan reproducible notebook |
| pdf | Membaca, merender, dan memeriksa dokumen PDF materi |
| playwright | Browser automation terstruktur untuk portal dan testing |
| playwright-interactive | Inspeksi locator dan debugging browser secara interaktif |
| screenshot | Bukti visual dan verifikasi tampilan |
| transcribe | Alur transkripsi audio/voice |
| security-best-practices | Review keamanan aplikasi dan dependency |
| security-ownership-map | Pemetaan area kode dan ownership keamanan |
| security-threat-model | Threat model, trust boundary, dan mitigasi |
| cli-creator | Merancang CLI developer yang konsisten |
| gh-fix-ci | Menganalisis kegagalan workflow CI GitHub |

Skill open-source menyertakan LICENSE/NOTICE dari sumbernya. Skill ini tidak
menambah tool baru dan tidak boleh menimpa skill bawaan Xninetzy.

## Discovery dan penggunaan

Katalog dipindai saat runtime:

~~~text
/skills
/skills-health
/skill research
~~~

Untuk request natural language, gunakan `skill_suggest_for_request`, lalu muat
body dengan `skill_get` hanya ketika prosedurnya relevan. Resource tambahan dimuat
bertahap melalui `skill_resource_list` dan `skill_resource_read`; agent tidak
menyuntik seluruh katalog atau seluruh resource ke context. Body skill hanya memberi
langkah kerja; agent tetap wajib memanggil tool domain yang benar dan mematuhi
approval policy.

## Quality dan trust

`skill_healthcheck` melaporkan skill valid/invalid, provenance, jumlah resource,
line count, dan quality warnings. Builtin diberi trust `trusted-builtin`; skill
yang dipasang owner diberi `owner-installed`. User skill tidak di-auto-inject
secara default; aktifkan `XNINETZY_SKILL_AUTO_INJECT_USER=true` hanya setelah audit.
Validator juga memeriksa pola credential, referensi file, ukuran, dan path traversal.

Lifecycle skill mengikuti:

~~~text
trigger metadata → inspect state → choose tool → plan → act → verify → adapt
~~~

Skill tidak boleh menjadi evidence, policy override, atau jalur bypass approval.
Riset desain lengkap tersedia di
[Skill Agentic Best Practices](https://github.com/misbahul45/xninetzy/blob/main/docs/research/XNINETZY_SKILL_AGENTIC_BEST_PRACTICES.md).

## Menambah skill sendiri

Owner dapat memasang skill terverifikasi melalui MCP:

~~~text
skill_validate
skill_install
skill_resource_list
skill_resource_read
skill_healthcheck
~~~

`skill_install` dapat menerima mapping `resources` berisi file teks di bawah
`references/`, `scripts/`, `assets/`, atau `agents/`. Resource dibatasi ukuran,
diverifikasi dengan manifest hash, ditulis atomik, dan ditolak jika path traversal
atau symlink.

Aturan:

- frontmatter wajib valid;
- folder dan name harus sama;
- instalasi owner-scoped dan idempotent;
- skill tidak boleh menyimpan credential;
- skill tidak dapat menurunkan action policy;
- skill tidak boleh mengklaim fakta tanpa evidence;
- skill baru tersedia untuk LangGraph dan seluruh MCP client.

Skill custom disimpan di katalog user (XNINETZY_SKILLS_DIR atau data runtime),
sedangkan skill bawaan repository berada di services/ai/.agents/skills.

## Saran pengembangan

Mulai dari define-goal untuk menetapkan outcome, lanjut it-learning untuk
roadmap, gunakan jupyter-notebook untuk eksperimen, research untuk sumber,
obsidian-knowledge untuk catatan, lalu security-threat-model sebelum
membuka connector atau browser action.

## Installing shared skills

Skills are installed once into the Xninetzy catalog and are then available to LangGraph, WhatsApp, MCP, Codex, Claude Code, and OpenCode. Do not create a separate client registry.

```text
Use MCP xninetzy to list available skills.
Install the skill named security-threat-model.
Validate the skill and list its resources.
```

The shared tools are `skill_list`, `skill_get`, `skill_suggest_for_request`, `skill_validate`, `skill_install`, `skill_resource_list`, and `skill_resource_read`. Built-in skills are stored in `services/ai/.agents/skills`; installs are owner-scoped, idempotent, size-limited, and validated before they can be injected into an agent prompt.

Use the global language selector in the header to switch between English and Indonesia on localized documentation blocks.

