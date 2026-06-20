# Xninetzy Agent System — Visualisasi

> **Xninetzy = WhatsApp-first IT Learning OS.**
> Dokumen ini fokus **visualisasi**: bagaimana sistem AI agent bekerja sekarang dan arahnya ke depan.
> Semua diagram pakai [Mermaid](https://mermaid.js.org/) (render otomatis di GitHub) + ASCII.

---

## 1. Peta Produk (Big Picture)

```mermaid
flowchart TB
    User([👤 User WhatsApp]) --> WA[WA Engine]
    WA --> API[FastAPI /chat]

    API --> CORE{{Xninetzy Core Agent}}

    CORE --> DOMAIN[🎯 IT Learning OS<br/>domain aktif]

    DOMAIN -.pakai.-> KOS[📚 Knowledge OS]
    DOMAIN -.pakai.-> ROS[🔬 Research OS]
    DOMAIN -.pakai.-> GOS[🕸️ Graph OS]
    DOMAIN -.pakai.-> NOS[📝 Notes / Obsidian]
    DOMAIN -.pakai.-> AOS[🎓 Academic / HEBAT connector]
    DOMAIN -.pakai.-> LOS[🌱 Life / Reminder OS]

    subgraph FUTURE [domains/future — belum aktif]
        BIO[🧬 Biology]
        NEU[🧠 Neuroscience]
        ITB[🧬+💻 IT+Biology]
    end
    CORE -. nanti .-> FUTURE

    classDef active fill:#1f6feb,stroke:#0b3d91,color:#fff
    classDef support fill:#eaf2ff,stroke:#1f6feb,color:#0b3d91
    classDef future fill:#f5f5f5,stroke:#bbb,color:#888,stroke-dasharray: 4 3
    class DOMAIN active
    class KOS,ROS,GOS,NOS,AOS,LOS support
    class BIO,NEU,ITB future
```

---

## 2. Request Lifecycle — 3 Jalur Masuk

Pesan masuk tidak selalu lewat agent. Ada **3 jalur** yang dicek berurutan di `interfaces/api/routes/chat.py`:

```mermaid
flowchart TD
    IN([📩 ChatRequest]) --> CMD{Slash command?<br/>parse_command}
    CMD -- ya --> TOOL[⚙️ Invoke 1 tool langsung<br/>bypass LangGraph] --> OUT([📤 Reply])

    CMD -- tidak --> WF{Multi-action?<br/>is_multi_action_request}
    WF -- ya --> WFE[🔀 Workflow Engine<br/>staged + progress WA] --> OUT

    WF -- tidak --> HIST[(💬 ChatStore<br/>ambil history)]
    HIST --> GRAPH[🧠 LangGraph flow] --> OUT

    classDef fast fill:#fff4e6,stroke:#e8a33d,color:#7a4b00
    classDef brain fill:#e6f4ea,stroke:#34a853,color:#0b5
    class TOOL,WFE fast
    class GRAPH brain
```

| Jalur | Trigger | Karakter |
|------|---------|----------|
| **1. Command** | pesan diawali `/...` | deterministik, cepat, 1 tool |
| **2. Workflow** | request majemuk (banyak aksi) | bertahap, lapor progress |
| **3. Agent graph** | selain di atas | reasoning penuh (ReAct) |

---

## 3. LangGraph State Machine (jalur utama)

```mermaid
stateDiagram-v2
    [*] --> orchestrator
    orchestrator --> agent: route = agent
    orchestrator --> direct: route = direct
    orchestrator --> clarify: route = clarify
    agent --> format
    direct --> format
    clarify --> format
    format --> [*]

    note right of orchestrator
        LLM flash (cepat) +
        Context Routing hint
        (domain / intent / mode)
    end note
    note right of agent
        ReAct + semua tools
        LLM pro (reasoning)
    end note
```

**Aturan routing orchestrator:**

```
            ┌─────────────────────────────────────────────┐
   pesan →  │ butuh AKSI / DATA / TOOL ?  ──────► AGENT     │
            │ cukup penjelasan teks ?      ──────► DIRECT    │
            │ benar-benar ambigu ?         ──────► CLARIFY   │
            └─────────────────────────────────────────────┘
              ragu antara AGENT vs DIRECT  →  selalu AGENT
```

---

## 4. Anatomi `agent` Node (ReAct + injeksi konteks)

Sebelum ReAct loop jalan, system prompt dirakit dari banyak sumber (semua *best-effort*, gagal = dilewati):

```mermaid
flowchart LR
    MSG([message + metadata]) --> CR[🧭 Context Routing<br/>domain/intent/mode]
    MSG --> PC[👤 Personal context]
    MSG --> MC[📎 Media context]
    MSG --> RC[📏 Rules]
    MSG --> SC[🎨 Style]
    MSG --> MEM[🧠 Memory relevan]

    CR & PC & MC & RC & SC & MEM --> SYS[[🧾 AGENT_PROMPT<br/>system prompt]]
    SYS --> REACT

    subgraph REACT [ReAct loop · LLM pro]
        direction LR
        THINK[💭 reason] --> ACT[🔧 tool call] --> OBS[👀 observe] --> THINK
        THINK --> ANS[✅ final answer]
    end

    ANS --> FMT[format node] --> REPLY([📤 reply WhatsApp])
```

ASCII bentuk system prompt yang dikirim ke model:

```
┌─ AGENT_PROMPT ─────────────────────────────┐
│ Identitas: WhatsApp-first IT Learning OS    │
│ Konteks: sender / chat / waktu / quoted     │
│ [Context Routing] domain= intent= mode=     │  ◄── baru (phase 2)
│ [Personal] [Media] [Rules] [Style] [Memory] │
│ Kategori tools ...                          │
│ Aturan: Memory · Media · Format WA ·        │
│         Deep Research · HITL · Research ·   │
│         Learning OS · IT Learning           │
└─────────────────────────────────────────────┘
```

---

## 5. Context Layer (deterministik, tanpa LLM)

`app/xninetzy/context/` — preprocessing berbasis rule yang menghasilkan **ContextPacket**.

```mermaid
flowchart LR
    RAW([raw message]) --> N[normalizer<br/>normalize_message]
    N --> D[domain_classifier]
    N --> I[intent_classifier]
    D & I --> M[mode_router]
    D & I & M --> P[[ContextPacket]]

    P --- F["raw_message · normalized_message<br/>domain · intent · mode · metadata"]
```

**Prioritas domain** (it_learning dulu, biar HEBAT tidak jadi pusat):

```mermaid
flowchart TD
    T([text]) --> C1{it_learning?}
    C1 -- ya --> ITL[it_learning]
    C1 -- tidak --> C2{academic?}
    C2 -- ya --> AC[academic]
    C2 -- tidak --> C3{knowledge?}
    C3 -- ya --> KN[knowledge]
    C3 -- tidak --> C4{research?}
    C4 -- ya --> RE[research]
    C4 -- tidak --> C5{life?}
    C5 -- ya --> LF[life]
    C5 -- tidak --> GEN[general]

    classDef hot fill:#1f6feb,stroke:#0b3d91,color:#fff
    class ITL hot
```

**Contoh hasil klasifikasi:**

| Pesan | domain | intent | mode |
|------|--------|--------|------|
| "buat roadmap belajar Docker" | `it_learning` | `create_roadmap` | `study` |
| "cek tugas HEBAT" | `academic` | `chat` | `quick` |
| "riset paper Graph RAG" | `it_learning` | `research` | `research` |
| "ingatkan aku besok jam 8" | `life` | `reminder` | `life` |
| "halo apa kabar" | `general` | `chat` | `quick` |

> Status: rule-based. **Ke depan** bisa di-upgrade ke LLM/embedding classifier tanpa mengubah kontrak `ContextPacket`.

---

## 6. Domain & Support OS Map

```mermaid
flowchart TB
    subgraph DOMAINS [domains/]
        ITL["🎯 it_learning<br/>skill_tree · roadmap · study<br/>prompts · tools · workflows"]
        FUT["📦 future/<br/>biology · neuroscience · it_biology<br/>(placeholder)"]
    end

    subgraph OS [os/ — support services]
        K[knowledge]:::s
        R[research]:::s
        G[graph]:::s
        NO[notes]:::s
        AC["academic/hebat<br/>(connector)"]:::s
        LI[life]:::s
        REM[reminders]:::s
        MEM[memory]:::s
        RU[rules]:::s
        ST[style]:::s
        HI[hitl]:::s
        NT[notifications]:::s
        LG[lightning]:::s
    end

    subgraph IF [interfaces/]
        APIX[api]:::i
        WAX[whatsapp]:::i
        MEDX[media]:::i
    end

    ITL ==> OS
    IF ==> ITL

    classDef s fill:#eaf2ff,stroke:#1f6feb,color:#0b3d91
    classDef i fill:#fef0f5,stroke:#d6336c,color:#86134a
```

---

## 7. Tools Registry — Grouping by Domain/OS

`get_all_tools()` (≈127 tools) tetap utuh; `get_tool_groups()` cuma untuk navigasi.

```mermaid
mindmap
  root((🔧 Tools))
    core
      calculate
      datetime_now
    it_learning
      learning_create_roadmap
      learning_generate_today_plan
      learning_review_week
    knowledge
      knowledge_search
      knowledge_answer
    research
      research_light
      deep_research_topic
    graph
      graph_search
      graph_get_context
    notes
      obsidian_create
      obsidian_search
    academic
      hebat_login_status
      hebat_sync_assignments
    life
      goal_create
      task_capture
    reminders
      reminder_create
    whatsapp
      wa_send_text
    media
      media_read_document
```

---

## 8. Multi-Action Workflow (jalur 2)

Untuk request majemuk, mis. *"riset RAG, lalu buat roadmap, terus ingatkan besok"*:

```mermaid
sequenceDiagram
    autonumber
    participant U as 👤 User
    participant C as /chat
    participant P as workflow.plan
    participant E as workflow.executor
    participant N as notifier (WA)
    participant T as tools

    U->>C: pesan majemuk
    C->>P: is_multi_action_request?
    P-->>C: ya → rencana aksi (DAG)
    C->>E: run_workflow(plan)
    loop tiap step (sesuai dependency)
        E->>T: jalankan tool
        T-->>E: hasil
        E->>N: progress summary
        N-->>U: "⏳ step k/n selesai"
    end
    E-->>U: ✅ ringkasan akhir
    Note over E,T: kegagalan non-kritis → lanjut<br/>kegagalan kritis → stop + partial
```

---

## 9. Human-in-the-Loop (HITL) — gerbang aksi berisiko

```mermaid
flowchart LR
    A[Agent ingin aksi besar] --> Q{Perlu approval?}
    Q -- tidak --> DO[langsung jalan]
    Q -- ya --> REQ[hitl_request_approval] --> ADM([👮 Admin di WA])
    ADM -- approve --> DO
    ADM -- reject --> CANCEL[batalkan + info user]

    classDef gate fill:#fff4e6,stroke:#e8a33d,color:#7a4b00
    class Q,REQ gate
```

Wajib approval: **upload tugas HEBAT**, **roadmap aktif + banyak task**, **simpan hasil research besar** ke Obsidian/Knowledge/Graph, **deep research** (admin-only).

---

## 10. Arsitektur Berlapis (layered view)

```
╔══════════════════════════════════════════════════════════════╗
║  INTERFACES      WhatsApp · API · Media                        ║
╠══════════════════════════════════════════════════════════════╣
║  CONTEXT         normalize → domain/intent → mode → Packet     ║
╠══════════════════════════════════════════════════════════════╣
║  AGENT/CORE      orchestrator → agent(ReAct)/direct/clarify    ║
║                  → format                                      ║
╠══════════════════════════════════════════════════════════════╣
║  ORCHESTRATION   workflow engine (multi-action, DAG, HITL)     ║
╠══════════════════════════════════════════════════════════════╣
║  DOMAIN          🎯 it_learning      (future: bio/neuro)       ║
╠══════════════════════════════════════════════════════════════╣
║  SUPPORT OS      knowledge·research·graph·notes·academic·life  ║
║                  reminders·memory·rules·style·hitl·lightning   ║
╠══════════════════════════════════════════════════════════════╣
║  INFRA           core(config/llm/log) · db(sqlite) · tools     ║
╚══════════════════════════════════════════════════════════════╝
        ▲ interface     ▼ infra      (atas = dekat user)
```

---

## 11. Arah Ke Depan (target evolusi)

Garis putus = belum ada / parsial sekarang.

```mermaid
flowchart TB
    P[ContextPacket] --> ST[(AgentState)]:::now
    ST -. simpan sekali, hindari hitung ganda .-> ORCH[orchestrator]:::soon

    ORCH --> MODE{mode}:::soon
    MODE -- quick --> Qk[jawab cepat]
    MODE -- study --> Sd[mode belajar IT<br/>roadmap/konsep/praktik]
    MODE -- deep_think --> Dt[reasoning panjang]
    MODE -- research --> Rs[Research OS + subplan]
    MODE -- life --> Lf[Life/Reminder]

    CL[Context classifier]:::now -. upgrade .-> CLAI[LLM/embedding classifier]:::future
    SKL[skills/it_learning]:::now -. tumbuh .-> CURR[curriculum + concepts<br/>per skill_tree]:::future
    FUT[domains/future]:::future -. aktifkan setelah IT stabil .-> XBR[cross-domain bridge<br/>IT + Biology]:::future

    classDef now fill:#e6f4ea,stroke:#34a853,color:#0b5
    classDef soon fill:#fff4e6,stroke:#e8a33d,color:#7a4b00
    classDef future fill:#f5f5f5,stroke:#bbb,color:#888,stroke-dasharray:4 3
```

**Roadmap singkat:**

```
[ now ]   ─►  IT Learning OS + context rule-based + HITL + workflow
[ next ]  ─►  ContextPacket disimpan di AgentState (sekali hitung)
              mode router benar-benar memilih model/tool
[ later ] ─►  classifier LLM/embedding · curriculum per skill_tree
[ vision ]─►  aktifkan domains/future + jembatan cross-domain (IT+Biology)
```

---

## 12. Legenda

| Simbol | Arti |
|--------|------|
| 🎯 | Domain aktif (it_learning) |
| 📦 / putus-putus | Future / belum aktif |
| 🔧 | Tools |
| 👮 | Admin (HITL) |
| `─►` | alur / evolusi |
| `-.->` (dashed) | belum ada / opsional / arah ke depan |

> Sumber kebenaran tetap kode di `app/xninetzy/`. Jika diagram dan kode beda, **kode yang benar** — perbarui dokumen ini.
