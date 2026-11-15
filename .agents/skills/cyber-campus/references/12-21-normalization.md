# cyber-campus — §12–21

Contents: 12. Normalization; 13. Grade Model; 14. Schedule Model; 15. KRS Model; 16. Course Offering Model; 17. Quota Analysis; 18. Prerequisite Analysis; 19. Eligibility; 20. Credit Constraints; 21. Schedule Conflict Detection

## 12. Normalization

Convert raw portal data into typed records.

### Course

```yaml
course:
  code:
  name:
  credits:
  class:
  lecturer:
  schedule:
  room:
  quota:
  enrolled:
  remaining:
  prerequisites:
  eligibility:
```

Do not invent unavailable fields.

Use:

```text
null
unknown
not_exposed
```

when appropriate.

---

## 13. Grade Model

```yaml
grade:
  course_code:
  course_name:
  credits:
  letter:
  numeric:
  quality_points:
  period:
  status:
```

Preserve distinctions between:

```text
not_taken
registered
graded
incomplete
withheld
not_published
```

Do not calculate GPA using guessed values.

---

## 14. Schedule Model

```yaml
schedule:
  course_code:
  class:
  day:
  start:
  end:
  room:
  instructor:
  period:
```

Normalize time explicitly.

Check:

```text
same day
overlapping intervals
adjacent classes
room conflicts
```

Do not declare a conflict when time information is incomplete.

---

## 15. KRS Model

```yaml
krs:
  period:
  status:
  courses:
    - course_code:
      class:
      credits:
      status:
  total_credits:
  submitted:
  submitted_at:
  receipt:
```

Possible status:

```text
DRAFT
STAGED
SUBMITTED
APPROVED
LOCKED
UNKNOWN
```

---

## 16. Course Offering Model

```yaml
offering:
  course_code:
  class:
  credits:
  quota:
  enrolled:
  remaining:
  schedule:
  lecturer:
  prerequisites:
  eligibility:
  registration_window:
  source:
```

Quota is time-sensitive.

Therefore:

```text
offering.quota.freshness
```

must be available when used for KRS decisions.

---

## 17. Quota Analysis

Never say:

```text
"quota is available"
```

without current evidence.

Distinguish:

```text
OPEN
FULL
UNKNOWN
CLOSED
WINDOW_NOT_OPEN
WINDOW_CLOSED
```

For numeric quota:

```text
remaining = quota - enrolled
```

only when both values are current and compatible.

---

## 18. Prerequisite Analysis

Represent:

```text
course
  ↓
required prerequisite
  ↓
student academic record
```

Classify:

```text
SATISFIED
NOT_SATISFIED
IN_PROGRESS
WAIVED
UNKNOWN
```

Do not infer prerequisite satisfaction from course names alone.

---

## 19. Eligibility

Eligibility may depend on:

```text
semester
program
cohort
completed credits
prerequisites
academic status
registration window
quota
faculty rules
special restrictions
```

Each factor should be separately evaluated.

---

## 20. Credit Constraints

Check:

```text
minimum credits
maximum credits
program limit
semester limit
special overload rules
```

Output:

```yaml
credit_check:
  current:
  proposed:
  minimum:
  maximum:
  status:
```

Do not assume a universal credit ceiling.

Use current portal rules where exposed.

---

## 21. Schedule Conflict Detection

For proposed KRS:

```text
course A
  09:00-11:00

course B
  10:00-12:00
```

=> conflict.

Represent:

```yaml
conflict:
  course_a:
  course_b:
  day:
  overlap_start:
  overlap_end:
  severity:
```

Do not infer conflicts when:

```text
day unknown
time unknown
timezone ambiguous
```

---
