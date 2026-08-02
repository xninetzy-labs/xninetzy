---
layout: ../../layouts/DocsLayout.astro
title: Introduction to Xninetzy
description: Understand Xninetzy as a Personal Learning OS, not only a WhatsApp chatbot.
section: Start
---

Xninetzy is a **WhatsApp-first Personal Learning OS and Life OS**. It connects
conversations, a knowledge base, notes, academic work, reminders, and coding
agents through one shared tool registry.

## The problem it solves

Personal information is usually scattered across Moodle materials, chat
insights, Obsidian notes, and technical repositories. Xninetzy provides one
entry point to:

- capture information from messages, documents, PDFs, and images;
- hold ambiguous input in the OS Inbox until its next action is clear;
- search and develop Obsidian notes;
- read HEBAT or Moodle courses and materials;
- create roadmaps, tasks, goals, and reminders;
- conduct research and preserve its results;
- give Codex, Claude Code, and OpenCode the same tools through MCP.

## Design principles

### Local-first and single-owner

The default configuration targets one owner on a local machine or private
network. SQLite, FAISS, WhatsApp sessions, HEBAT browser profiles, and media stay
local.

### Natural language with deterministic escape hatches

Ordinary messages pass through LangGraph. Slash commands such as `/llm`,
`/approve`, and `/today` use deterministic routes so important actions do not
depend on model interpretation.

### Human in the loop

Roadmap drafts are not activated automatically. Assignment uploads, selected
overwrites, and high-impact actions require a confirmation token or
administrator approval.

### Capture before commitment

Xninetzy does not turn every idea into a task. Important but unclear input enters
the OS Inbox, then becomes a task or an archived item through triage. The
attention queue combines deadlines, priorities, learning state, and inbox state,
so `/today` answers “what should I focus on next?” from real data.

### Provider freedom

Flaz is the default, not a lock-in. Providers are selected from a registry, and
the owner can change their model preference without changing agent code.

## What Xninetzy is not

Xninetzy is not an internet-ready multi-tenant SaaS. Its HTTP API has a shared
secret and owner guard, but the deployment model remains local and
single-owner. It is also not a replacement for vault backups, an official LMS,
or the WhatsApp Business API.

> Run it on loopback or a private network. Read the [security guide](/docs/security/) before exposing a port to another machine.

## Main components

| Component | Technology | Responsibility |
|---|---|---|
| AI service | Python, FastAPI, LangGraph | Routing, agents, registry, memory, HEBAT, Obsidian, MCP |
| WhatsApp engine | Node.js, TypeScript, Baileys | WhatsApp socket, media, group triggers, HTTP tool bridge |
| Terminal CLI | Ink, React | Alternative client for `/api/chat` |
| Documentation | Astro | Static operator and contributor documentation |

## Choose your next path

- New installation: open [Quick start](/docs/getting-started/).
- Choose a model: open [LLM providers](/docs/providers/).
- Connect a vault: open [Obsidian](/docs/obsidian/).
- Understand capture and daily focus: open [OS kernel](/docs/os-kernel/).
- Use coding clients from any directory: open [Global MCP](/docs/mcp/).
- Review safety boundaries: open [Security](/docs/security/).
