---
name: "exam_qa:author-fixture"
description: "Build an ExamFixture from a topic outline or transcript. Produces a JSON-or-YAML-shaped fixture with deterministic question IDs, prompts, expected answers, and tags. No grading or scenario binding happens here."
metadata:
  scope: "task"
  owner: "xninetzy"
  language: "en"
  version: "0.1.0"
  lifecycle: "intake -> parse -> validate -> emit"
---

# Task: Author a Fixture

## Inputs

- Topic + subject
- Free-form outline, transcript, or Q&A list

## Procedure

1. Extract each question, expected answer, and tag.
2. Assign a deterministic `question_id` (slug or hash of prompt).
3. Call `build_fixture` from `xninetzy.context.exam_qa.fixture`.
4. Persist via SQLite (no global registry required).

## Outputs

- `ExamFixture` with `fixture_id`, `format`, `questions` tuple
- Validation that every question has `id` and `expected_answer`