# Revision Log Template

**Version:** 1.0  
**Usage:** One log file per manuscript section. One entry per revised paragraph.

---

## LOG METADATA

```yaml
manuscript_slug: [PAPER_SLUG]
section: [introduction / abstract / methods / results / discussion]
writing_destination: [TARGET JOURNAL OR WRITING CONTEXT]
skill_used: dynamic_writing_skill.md
revision_date: [DATE]
total_paragraphs_revised: [N]
total_paragraphs_unchanged: [N]
```

---

## ENTRY FORMAT

Repeat the block below for each revised paragraph. Unchanged paragraphs do not need an entry.

---

```
---
entry_id: [section]-para-[N]
paragraph_number: [N]
lines_original: [X–Y]
severity: [HIGH / MED / LOW]
problem_types: [STYLE / LOGIC / AI-TASTE / JOURNAL-MISMATCH]
human_decision: [ACCEPTED / ACCEPTED-WITH-EDITS / REVERTED]
---
```

### Original Text

[Paste original paragraph verbatim. Do not edit.]

---

### Diagnosis

**Problem type(s):** [STYLE] [LOGIC] [AI-TASTE] [JOURNAL-MISMATCH]

**Issues identified:**
- [Issue 1: specific description — e.g., "Opens with 'This paper contributes to the literature' — generic contribution framing not used in target journal"]
- [Issue 2: ...]
- [Issue 3: ...]

**Journal match score:** [1–5]
*(1 = very unlike target journal; 5 = well-matched)*

---

### Revised Text

[Paste accepted revised paragraph verbatim.]

*If human accepted with edits, paste the final human-edited version.*

---

### Rationale

**Rules applied:**
- Rule 1: [rule name] — Source: [target-journal / secondary-corpus / user-exemplar / static-base / cleanup / logic-fix]
- Rule 2: [rule name] — Source: [...]

**Conflict resolved?** [yes / no]
- If yes: [describe which rule won and why, e.g., "Target-journal pattern for embedded contribution overrode general econ rule for numbered list"]

**Signal-weak application?** [yes / no]
- If yes: [which rule, and note it was flagged]

**What was preserved verbatim:**
- [list any citations, equations, variable names that were present and kept unchanged]

---

### Reusability Assessment

**Worth generalizing?** [YES / NO / MAYBE]

**If YES or MAYBE:**

- **Rule candidate:** "[Write the generalizable rule in one complete sentence. Must be actionable.]"
- **Condition:** [When does this rule apply? e.g., "When writing contribution statements for empirical journals in env. economics"]
- **Target skill:** [this-dynamic-skill-only / dynamic-general / static-base-candidate]
- **Evidence strength:** [single case / consistent with N other entries / confirmed pattern]

**If NO:** [Brief reason why this revision is too context-specific to generalize]

---

*[Repeat for next paragraph entry]*

---

## AGGREGATED RULE CANDIDATES

*[AI fills this at end of each section log. Human marks final decision.]*

List all rule candidates identified in this section's entries:

| Entry ID | Rule Candidate | Target Skill | Human Decision |
|----------|---------------|--------------|----------------|
| intro-para-3 | "[rule text]" | journal-adaptive-general | [ACCEPT / REJECT / REVISE] |
| intro-para-5 | "[rule text]" | this-journal-only | |

---

## SECTION SUMMARY

**Journal match score — before revision:** [average of original scores]  
**Journal match score — after revision:** [average of revised scores]  

**Key patterns improved:**
- [pattern 1]
- [pattern 2]

**Remaining issues (not revised):**
- [anything left unchanged that still has a mismatch]
- [reason it was not revised — e.g., "too close to data/model result, cannot rephrase without changing meaning"]

**Notes for next section:**
- [anything learned from this section that should inform the next]
