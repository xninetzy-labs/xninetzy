# Xninetzy AI Test Suite

Test dikelompokkan berdasarkan domain dan lapisan produk agar kepemilikan serta navigasinya jelas.

## Struktur

```text
tests/
├── architecture/          # Struktur namespace dan grouping tools
├── core/                  # Konfigurasi serta provider LLM
├── agent/                 # Routing dan command dispatch
├── workflow/              # Multi-action workflow
├── domains/
│   └── it_learning/       # Domain aktif IT Learning OS
├── interfaces/
│   ├── media/             # Parser dan routing media
│   └── whatsapp/          # Client/tool WhatsApp
├── os/
│   ├── academic/hebat/    # Integrasi HEBAT/Moodle
│   ├── research/          # Research dan deep research
│   ├── reminders/         # Parser, service, dan scheduler
│   ├── memory/            # Semantic memory
│   └── ...                # Graph, HITL, rules, style, dan support OS lain
├── manual/                # Script E2E manual, tidak dikoleksi sebagai test otomatis
└── conftest.py            # Fixture bersama untuk seluruh domain
```

## Menjalankan

Dari `services/ai`:

```bash
uv run pytest
```

Menjalankan satu domain:

```bash
uv run pytest tests/os/research
uv run pytest tests/domains/it_learning
```

## Aturan penempatan

- Test mengikuti domain atau lapisan kode yang menjadi subjek utamanya.
- Test integrasi lintas domain ditempatkan di `agent/` atau `workflow/`.
- Fixture global tetap di root `conftest.py`; fixture khusus domain tinggal dekat test domain.
- Script yang membutuhkan akun atau layanan nyata ditempatkan di `manual/`.
