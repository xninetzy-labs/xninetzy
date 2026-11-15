---
name: exam_qa
description: 'Offline practice-exam system: dry-run drills, scored practice and exam simulations with evidence, fixtures and deterministic question selection. Never completes real graded exams; a graded run needs an approval_id. Use for exam practice.'
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: 0.1.0
  lifecycle: fixture -> scenario -> authorize -> select -> run -> grade -> evidence
  keywords: actual any authoring authorization autonomously before cancelled capture collection complete construction enforces environment every examinations failed first fixture gate hitl institutional local machine mock only owner planned platforms produces provider ready resolution running runs scenario state step submitted test transitions where
---

# Exam QA

This skill is the **deterministic, offline-first, owner-authorized exam
practice OS**. It must never autonomously complete graded institutional
exams. The system enforces an authorization gate (`exam_authorization`
table + `approval_id`) before any `exam` scenario runs end-to-end.

The core loop:

**Fixture → Scenario → Authorize → Select → Run → Grade → Evidence**

Every step produces an auditable artifact:

- `ExamFixture` — questions + metadata, immutable
- `ExamScenario` — fixture binding, time limit, pass threshold
- `ExamRunState` — phase transitions via the canonical state machine
- `EvidenceBundle` — per-question answer + score + captured_at
- `EnvironmentSnapshot` — offline / sandboxed / python / platform

## When to use

Use this skill for:

- Owner-driven practice drills (`scenario.kind == "dry_run"` or `"practice"`)
- Fixture authoring from a transcript or topic outline
- Replaying a graded run from evidence bundles

Do **not** use this skill for:

- Filling HEBAT quizzes (covered by `xninetzy-academic-safety`)
- Answering live exam questions in real institutional portals
- Anything requiring external network or scraping