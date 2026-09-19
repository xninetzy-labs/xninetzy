# Skills Index — Xninetzy

> 69 skill directories + 1 top-level SKILL.md (70 files total).
> Regenerate with:
> `find .agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md | sort`

| Skill | Purpose |
|---|---|
| api-security | Authorized API/MCP security assessment |
| architecture-analysis | Static architectural analysis (modules, deps, cycles, layers) |
| benchmark-analysis | Benchmark methodology + interpretation |
| career | Career intelligence orchestration |
| cli-creator | CLI design + implementation |
| code-review | Code review heuristics |
| consulting-pptx | Composite PPTX meta-skill |
| consulting-pptx-skill | Carnot upstream PPTX skill |
| context-engineering | Context construction for LLM agents |
| contradiction-hunter | Find internal contradictions in sources |
| cyber-campus | Cyber campus workflows |
| debugging | Structured debugging |
| define-goal | Goal definition + scoping |
| dependency-audit | Dependency audit + supply-chain review |
| evidence-grader | Evidence grading + provenance |
| gh-fix-ci | GitHub Actions CI repair |
| graph-rag | GraphRAG patterns |
| hebat-academic | HEBAT academic workflows |
| hebat-assignment | HEBAT assignment workflows |
| it-learning | IT learning coach |
| jupyter-notebook | Notebook engineering |
| life-management | Life management workflows |
| literature-review | Academic literature review |
| mcp-development | MCP tool-surface engineering |
| mcp-discovery | MCP server discovery |
| memory-chat | Memory-aware chat |
| memory-management | Memory OS operations |
| multi-agent-orchestration | Multi-agent orchestration |
| obsidian-knowledge | Obsidian vault workflows |
| paper-analysis | Paper analysis + critique |
| pdf | PDF read/extract/create/edit |
| playwright | Playwright browser automation |
| playwright-interactive | Interactive Playwright sessions |
| playwright-mcp-workflows | Playwright MCP workflows |
| pptx-skills | Anyideaz upstream PPTX skill |
| regression-analysis | Regression analysis + interpretation |
| repo-context-packaging | Repo context packaging |
| research | Research orchestration |
| research-critic | Critical appraisal of research |
| research-planner | Research planning |
| screenshot | Screenshot workflows |
| secret-audit | Secret audit |
| security-best-practices | Security best-practices catalog |
| security-ownership-map | Security ownership mapping |
| security-research | Security research workflows |
| security-review | Security review |
| security-threat-model | Threat modeling |
| self-improvement | Self-improvement loop |
| skill-creator | Skill authoring |
| skill-improvement-opportunity-logger | Log skill improvement opportunities |
| skill-security-review | Skill security review |
| source-selector | Source selection heuristics |
| structured-project-execution | Structured project execution |
| tdd-workflow | TDD workflow |
| transcribe | Transcription workflows |
| xninetzy-academic-safety | Academic safety guardrails |
| xninetzy-artifact-orchestrator | Artifact orchestration |
| xninetzy-assignment-orchestrator | Assignment orchestration |
| xninetzy-cyber-campus | Xninetzy cyber-campus flows |
| xninetzy-deep-research | Deep research harness |
| xninetzy-hebat | HEBAT orchestration |
| xninetzy-krs | KRS (course registration) orchestration |
| xninetzy-learning-coach | Learning coach |
| xninetzy-mcp-lightning | Lightning RL bandit service |
| xninetzy-memory | Memory OS |
| xninetzy-obsidian-orchestra | Obsidian orchestra |
| xninetzy-os | Xninetzy OS surface |
| xninetzy-research-memory | Research memory |
| xninetzy-security-testing | Security testing |
| xninetzy-uacc | UACC flows |
| xninetzy-web-analysis | Web analysis |

## Notes

- All skills live under `.agents/skills/<name>/SKILL.md` with YAML frontmatter.
- Integrity enforced by `tests/governance/test_skill_frontmatter.py`.
- Currently **69/69 SKILL.md files have broken YAML frontmatter**
  (see `KNOWN_ISSUES.md` ISS-20260919-01 + `docs/runbooks/skill-repair.md`).
- Install into supported harnesses via
  `XNINETZY_SKILL_INSTALL_TARGETS=opencode,claude,codex python scripts/install_skills.py`.
