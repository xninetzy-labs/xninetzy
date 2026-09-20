---
name: "exam_qa"
description: "Offline-first practice exam and test-running OS for the owner. Use for dry-run drills, scored practice runs, and graded exam simulations where every step produces evidence. NEVER use to autonomously complete graded examinations on real institutional platforms; the system enforces an authorization gate (HITL approval_id) before any actual graded run. Use for fixture authoring, scenario construction, deterministic question selection, provider resolution (mock/local only), state-machine transitions (planned/ready/running/submitted/graded/failed/cancelled), evidence collection, and environment capture."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "0.1.0"
  lifecycle: "fixture -> scenario -> authorize -> select -> run -> grade -> evidence"
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