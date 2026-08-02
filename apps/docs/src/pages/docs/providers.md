---
layout: ../../layouts/DocsLayout.astro
title: LLM providers
description: Use Flaz by default or select OpenAI, Anthropic, OpenRouter, Ollama, and OpenAI-compatible endpoints.
section: AI & developer tools
---

Chat providers are separate from the agent. Xninetzy selects a provider and
model from the registry, then creates the LangChain chat model used by
LangGraph and tool-calling flows.

## Flaz as the default

Flaz uses `ChatOpenAI` from `langchain-openai` with a custom base URL:

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_API_KEY=
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_MODELS=deepseek-v4-pro
```

Enter the key without terminal echo:

```bash
cd services/ai
uv run python scripts/configure_flaz.py
```

## Enable multiple providers

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

A provider is ready when:

1. its name is in `LLM_ENABLED_PROVIDERS`;
2. its default model is configured;
3. the model is in its `*_MODELS` allowlist;
4. a base URL is configured when required;
5. required credentials are present.

## Select a provider from WhatsApp

```text
/llm
/llm list
/llm use flaz deepseek-v4-pro
```

The selection is stored per owner in SQLite. API keys are never stored as a
preference or displayed by commands.

## Generic OpenAI-compatible provider

Use `generic` when a vendor implements the OpenAI chat-completions API:

```dotenv
LLM_ENABLED_PROVIDERS=generic
LLM_DEFAULT_PROVIDER=generic
GENERIC_OPENAI_API_KEY=your-key
GENERIC_OPENAI_BASE_URL=https://provider.example/v1
GENERIC_OPENAI_MODEL=model-name
GENERIC_OPENAI_MODELS=model-name,model-name-fast
```

Endpoint compatibility does not guarantee tool-calling compatibility. Test the
model with ordinary chat and with a request that invokes a tool.

## Local Ollama

```dotenv
LLM_ENABLED_PROVIDERS=ollama
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=your-tool-capable-model
OLLAMA_MODELS=your-tool-capable-model
```

Verify that the model's context window, structured output, and tool calling are
sufficient for the intended workflow.

## Chat provider versus coding runtime

| Layer | Examples | Responsibility |
|---|---|---|
| Chat provider | Flaz, OpenAI, Anthropic | Answer messages and select tools |
| Coding runtime | Codex, Claude Code, OpenCode | Run a CLI inside a repository |

Changing `/llm use` does not change `/agent use`.

## Diagnosis

If the model cannot be reached:

1. run `/llm list`;
2. inspect enabled providers and model allowlists;
3. verify the base URL without printing the key;
4. restart the service after changing `.env`;
5. test the provider health endpoint from the same host;
6. inspect HTTP status codes in logs, not request headers.
