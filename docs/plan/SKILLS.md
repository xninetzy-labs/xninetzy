# Xninetzy Agent Skills

Katalog Agent Skills adalah sumber workflow lintas LangGraph, WhatsApp, MCP, Codex, Claude Code, dan OpenCode. Registry membaca `SKILL.md` secara dinamis sehingga penambahan skill owner tidak membutuhkan perubahan kode atau restart.

## Katalog built-in

- `cyber-campus` — login HITL, nilai, jadwal, dan navigasi portal.
- `graph-rag` — pencarian graph dan evidence bundle.
- `hebat-academic` — course, aktivitas, deadline, dan materi HEBAT.
- `it-learning` — roadmap, konsep, sesi belajar, mastery, dan recall.
- `life-management` — task, goal, reminder, habit, review, money, dan workout.
- `obsidian-knowledge` — vault-relative note dan knowledge grounding.
- `research` — riset web, YouTube, akademik, dan sitasi.
- `xninetzy-os` — policy akses bersama, grounding, dan loop Capture -> Review.

Sumber built-in berada di `services/ai/.agents/skills`. Skill owner berada di data runtime yang dikonfigurasi melalui `XNINETZY_SKILLS_DIR`. `.claude/skills` diarahkan ke katalog yang sama; akses domain dan state tetap dilakukan melalui MCP server `xninetzy`.

## Tools MCP

- `skill_list` — daftar skill yang lolos validasi.
- `skill_get` — membaca metadata dan workflow satu skill.
- `skill_suggest_for_request` — memilih skill relevan secara deterministik.
- `skill_validate` — memeriksa frontmatter, body, dan batas ukuran.
- `skill_install` — memasang atau memperbarui skill owner secara atomik dengan idempotency key.

`skill_install` hanya menerima owner identity yang diinjeksi MCP. Isi `SKILL.md` adalah instruksi workflow tidak tepercaya, bukan fakta, dan tetap tunduk pada policy tool.

## Konvensi lintas client

Codex membaca `.agents/skills`, Claude Code membaca `.claude/skills`, dan OpenCode membaca katalog Agent Skills yang tersedia. Ketiga client tetap memakai registry MCP yang sama, sehingga tidak ada katalog tool atau state yang dikelola terpisah.

Contoh dari client mana pun:

```text
Gunakan MCP xninetzy. Jalankan skill_suggest_for_request untuk request ini,
lalu skill_get pada skill yang paling relevan sebelum memanggil tool domain.
```

## Validasi

Setiap perubahan skill wajib menjalankan validator skill dan suite AI. Jangan menaruh credential, cookie, WhatsApp session, atau data personal di dalam skill.
