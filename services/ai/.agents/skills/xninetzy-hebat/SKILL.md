---
name: xninetzy-hebat
description: Safely retrieve HEBAT/Moodle courses, assignments, deadlines, materials, and submission state, and prepare confirmed submissions.
metadata:
  owner: xninetzy
  version: "1.0.0"
---

# HEBAT

## Read workflow

1. check session;
2. resolve course and assignment;
3. retrieve instructions, deadline, rubric, attachments, and state;
4. validate downloaded material;
5. synchronize deadlines idempotently.

## Assignment workflow

1. create requirement matrix;
2. inspect materials;
3. research required evidence;
4. build deliverable;
5. validate;
6. create submission preview.

## Submission preview

Include:

```yaml
course:
assignment:
deadline:
file:
file_hash:
file_size:
submission_action:
existing_state:
expected_state:
```

## Submit

Require explicit confirmation bound to exact file hash and assignment.

Then:

1. execute once;
2. re-read submission state;
3. verify;
4. store receipt.

Do not take graded quizzes or examinations.
Do not silently retry ambiguous submissions.
