---
layout: ../../layouts/DocsLayout.astro
title: Provider LLM
description: Gunakan Flaz sebagai default atau pilih OpenAI, Anthropic, OpenRouter, Ollama, dan endpoint OpenAI-compatible.
section: AI & developer tools
---

Provider chat dipisahkan dari agent. Xninetzy memilih provider/model dari registry, lalu membuat LangChain chat model yang dipakai LangGraph dan tool-calling flow.

## Flaz sebagai default

Flaz memakai `ChatOpenAI` dari `langchain-openai` dengan custom base URL:

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_API_KEY=
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_MODELS=deepseek-v4-pro
```

Masukkan key tanpa echo:

```bash
cd services/ai
uv run python scripts/configure_flaz.py
```

## Mengaktifkan beberapa provider

```dotenv
LLM_ENABLED_PROVIDERS=flaz,openai,anthropic,openrouter,ollama,generic

OPENAI_API_KEY=
OPENAI_MODEL=gpt-model-name
OPENAI_MODELS=gpt-model-name

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-model-name
ANTHROPIC_MODELS=claude-model-name

OPENROUTER_API_KEY=
OPENROUTER_MODEL=provider/model
OPENROUTER_MODELS=provider/model

OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=local-model
OLLAMA_MODELS=local-model

GENERIC_OPENAI_API_KEY=
GENERIC_OPENAI_BASE_URL=https://provider.example/v1
GENERIC_OPENAI_MODEL=model-name
GENERIC_OPENAI_MODELS=model-name
```

Provider dianggap ready ketika:

1. namanya masuk `LLM_ENABLED_PROVIDERS`;
2. default model terisi;
3. model berada pada `*_MODELS`;
4. base URL tersedia jika dibutuhkan;
5. credential wajib tersedia.

## Memilih provider dari WhatsApp

```text
/llm
/llm list
/llm use flaz deepseek-v4-pro
```

Pilihan disimpan per user di SQLite. API key tidak disimpan sebagai preference dan tidak ditampilkan command.

## OpenAI-compatible provider

Gunakan `generic` jika vendor mengikuti API chat completions OpenAI:

```dotenv
LLM_ENABLED_PROVIDERS=generic
LLM_DEFAULT_PROVIDER=generic
GENERIC_OPENAI_API_KEY=your-key
GENERIC_OPENAI_BASE_URL=https://provider.example/v1
GENERIC_OPENAI_MODEL=model-name
GENERIC_OPENAI_MODELS=model-name,model-name-fast
```

Kompatibel secara endpoint belum tentu kompatibel secara tool calling. Uji model dengan chat biasa dan request yang memanggil tool.

## Ollama lokal

```dotenv
LLM_ENABLED_PROVIDERS=ollama
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=your-tool-capable-model
OLLAMA_MODELS=your-tool-capable-model
```

Pastikan konteks, structured output, dan tool calling model cukup untuk workflow yang dipakai.

## Provider chat vs coding runtime

Keduanya berbeda:

| Lapisan | Contoh | Tugas |
|---|---|---|
| Provider chat | Flaz, OpenAI, Anthropic | menjawab pesan dan memilih tool |
| Coding runtime | Codex, Claude Code, OpenCode | menjalankan CLI pada repository |

Mengganti `/llm use` tidak otomatis mengganti `/agent use`.

## Diagnosis

Jika model tidak dapat dihubungi:

1. jalankan `/llm list`;
2. periksa enabled providers dan allowlist model;
3. periksa base URL tanpa mencetak key;
4. pastikan service sudah restart setelah `.env` berubah;
5. uji health endpoint provider dari host yang sama;
6. periksa log untuk status HTTP, bukan request header.
