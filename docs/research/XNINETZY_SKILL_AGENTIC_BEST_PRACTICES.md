# Xninetzy Skills dan Agentic Best Practices

Tanggal riset: 2 Agustus 2026

Dokumen ini merangkum riset primer dan menerjemahkannya menjadi aturan implementasi untuk katalog skill Xninetzy. Fokusnya bukan menambah jumlah skill, melainkan membuat skill dapat ditemukan, dimuat bertahap, dieksekusi dengan guard, dan dievaluasi lintas LangGraph, MCP, Codex, Claude Code, OpenCode, serta WhatsApp.

## Temuan primer

### Anthropic

Anthropic menjelaskan Agent Skills sebagai folder portable yang berisi `SKILL.md`, instruksi, resource, dan script. Metadata `name` dan `description` dimuat lebih dahulu; body dan resource dimuat saat relevan. Pola progressive disclosure mengurangi context bloat dan membuat katalog besar tetap dapat digunakan.

Prinsip tool-agent yang diterapkan:

- satu tool memiliki tujuan yang jelas dan tidak tumpang tindih;
- nama serta parameter harus mudah dipahami oleh agent baru;
- hasil tool harus high-signal, bounded, dan dapat dipakai untuk langkah berikutnya;
- skill dimulai dari evaluasi nyata, bukan dari asumsi penulis;
- skill dari sumber eksternal harus diaudit karena instruksi atau script dapat menjadi supply-chain risk;
- skill tidak boleh menggantikan policy, authorization, evidence, atau approval.

Sumber:

- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- https://www.anthropic.com/engineering/writing-tools-for-agents
- https://www.anthropic.com/engineering/code-execution-with-mcp
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Codex dan Agent Skills standard

Codex menggunakan `AGENTS.md` sebagai instruksi repository-scoped dan skill sebagai paket workflow yang dapat dipakai ulang. Katalog skill harus portable, memiliki frontmatter valid, resource opsional, dan dapat ditemukan tanpa registry client-specific.

Penerapan di Xninetzy:

- `services/ai/.agents/skills` menjadi katalog builtin canonical;
- user skill tetap owner-scoped dan idempotent;
- semua interface memanggil registry yang sama;
- `AGENTS.md` menjelaskan policy dan ownership, sedangkan `SKILL.md` menjelaskan prosedur domain;
- skill tidak diberi akses untuk menurunkan permission atau melewati HITL.

Sumber:

- https://github.com/openai/codex/blob/main/docs/agents_md.md
- https://github.com/openai/skills
- https://agentskills.io

### LangChain dan LangGraph

LangGraph memisahkan state thread dari store jangka panjang. Checkpointer diperlukan untuk pause/resume HITL, recovery, dan thread continuity; store digunakan untuk preference/fact lintas thread. Panduan Thinking in LangGraph menekankan node diskret, raw state, retry untuk kegagalan transient, dan error sebagai bagian dari alur.

Penerapan di Xninetzy:

- tool dan domain tetap canonical di bawah interface;
- skill metadata menjadi routing hint, bukan instruksi absolut;
- skill body dimuat dengan `skill_get` setelah relevan;
- resource dimuat satu per satu dengan `skill_resource_list` dan `skill_resource_read`;
- side effect tetap melalui action policy/HITL dan idempotency;
- episode Lightning merekam skill/routing/outcome untuk evaluasi.

Sumber:

- https://docs.langchain.com/oss/python/langgraph/overview
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
- https://docs.langchain.com/oss/python/langchain/human-in-the-loop

## Kontrak skill Xninetzy

Setiap skill harus memenuhi urutan:

```text
trigger metadata -> inspect state -> choose tool -> plan -> act -> verify -> record outcome -> adapt
```

`SKILL.md` hanya berisi workflow guidance. Evidence harus berasal dari tool/domain. Output skill harus menyebutkan state yang dibaca, tindakan, bukti, ketidakpastian, dan review berikutnya.

### Trust dan provenance

- `trusted-builtin`: skill yang dikirim di repository;
- `owner-installed`: skill yang dipasang owner melalui `skill_install`;
- `untrusted`: sumber lain yang belum diverifikasi.

Katalog mencatat SHA-256, line count, resource inventory, trust level, serta quality warnings. User skill tidak auto-inject secara default; skill tersebut tetap bisa dipanggil eksplisit setelah owner memasangnya.

### Progressive disclosure

1. `skill_list` memuat metadata ringkas.
2. `skill_suggest_for_request` memberi ranking, confidence, dan alasan.
3. `skill_get` memuat body skill yang relevan.
4. `skill_resource_list` menunjukkan resource tanpa memuat semuanya.
5. `skill_resource_read` memuat satu resource bounded dan path-confined.
6. `skill_healthcheck` memeriksa katalog, resource, provenance, dan warning.

### Quality gate

Validator memeriksa frontmatter, nama folder, description, ukuran, resource path, referensi file, pola credential, dan panjang body. Warning tidak disembunyikan dari owner. Skill dengan peringatan provenance harus diaudit sebelum dipakai untuk workflow sensitif.

## Audit codebase sebelum perbaikan

Masalah yang ditemukan:

- `build_relevant_skill_context` menyuntik body penuh sampai batas karakter sehingga progressive disclosure belum nyata;
- ranking hanya lexical dan tidak memberi confidence atau alasan pemilihan;
- model tidak menyimpan trust, line count, resource, atau quality signal;
- MCP hanya menyediakan `skill_get`, sehingga resource terbundel tidak dapat dimuat lintas client;
- pemasangan user skill tidak memiliki catalog healthcheck;
- skill bawaan belum seragam pada output contract, verification, dan failure boundary.

Perbaikan yang diterapkan:

- metadata-first injection di LangGraph;
- confidence/reason tracking pada ranking deterministic;
- trust/provenance/resource metadata pada `SkillDefinition`;
- bounded resource API dan path confinement;
- catalog healthcheck dan warning transparan;
- user-skill auto injection opt-in melalui `XNINETZY_SKILL_AUTO_INJECT_USER=false`;
- delapan skill bawaan diperbarui ke pola inspect-plan-act-verify-adapt;
- registry MCP canonical bertambah dengan `skill_resource_list`, `skill_resource_read`, dan `skill_healthcheck`.

## Evaluasi berkelanjutan

Gunakan minimal tiga kelas evaluasi per skill:

1. trigger benar: request memilih skill yang tepat;
2. procedure benar: agent memuat body/resource yang dibutuhkan dan memilih tool domain;
3. boundary benar: agent berhenti atau meminta approval saat state, evidence, atau permission tidak cukup.

Simpan trace dan outcome melalui Lightning. Bandingkan success rate, tool-call precision, duplicate side effects, citation validity, latency, dan approval violations. Perubahan skill tidak boleh dianggap lebih baik hanya karena respons lebih panjang.

## Batas keamanan

Skill tidak boleh menerima credential, cookie, token, CAPTCHA, atau path arbitrer sebagai instruksi. Isi skill dan resource diperlakukan sebagai untrusted data. Policy, authorization, HITL, workspace guard, dan owner scope tetap berada di kode/domain, bukan di markdown skill.
