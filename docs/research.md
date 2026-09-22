# Research / STORM-style Deep Research

Xninetzy provides a STORM-style research capability built natively on top of existing retrieval, evidence, and knowledge infrastructure. No separate MCP server. No `knowledge-storm` vendoring.

## Components

- `xninetzy/os/research/engine.py` — ResearchEngine with `start_run`, `discover_perspectives`, `generate_questions`, `advance_run`, `build_research_packet`.
- `xninetzy/schemas/research_packet.py` — `ResearchRun`, `ResearchPacket`, `ResearchPerspective`, `ResearchQuestion`, `Evidence`, `Claim`, `Contradiction`, `ResearchGap`, `OutlineSection`, `ResearchOutline`.
- `xninetzy/tools/ecosystem/storm_tools.py` — 6 MCP tools: `research_storm_start`, `research_storm_perspectives`, `research_storm_questions`, `research_storm_advance`, `research_storm_packet`, `research_storm_capabilities`.

## Modes

`QUICK_RESEARCH`, `STANDARD`, `DEEP_RESEARCH`, `LITERATURE_REVIEW`, `CORPUS_RESEARCH`, `TECHNICAL_RESEARCH`, `PROPOSAL_RESEARCH`, `CONSULTING_RESEARCH`, `INTERACTIVE_RESEARCH`.

## Source modes

`WEB_ONLY`, `CORPUS_ONLY`, `HYBRID`.

## Pipeline

```
brief
  ↓
perspectives (5 default)
  ↓
questions per perspective (4 default)
  ↓
sources
  ↓
evidence
  ↓
claims
  ↓
contradictions + gaps
  ↓
outline
  ↓
ResearchPacket
```

## Usage

```python
from xninetzy.os.research.engine import start_run, advance_run, build_research_packet
from xninetzy.schemas.research_packet import SourceRecord, ResearchBrief

run = start_run(topic="JITAI for diabetes", mode="DEEP_RESEARCH")
srcs = [SourceRecord(url="...", excerpt="...") for _ in range(5)]
run = advance_run(run, srcs)
packet = build_research_packet(run, srcs)
```

## MCP

`research_storm_packet` returns the full ResearchPacket dict for downstream consumption by writing skills (`proposal-writer`, `academic-writer`, `research-paper-writer`, etc.).
