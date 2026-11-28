# Dynamic Writing Skill Template

**Version:** 1.1  
**Usage:** Generated from corpus style profiles + optional static base writing rules. One per writing destination and manuscript context.

---

## SKILL METADATA

```yaml
skill_type: dynamic-academic-writing
writing_destination: [TARGET JOURNAL OR WRITING CONTEXT]
target_sections: [abstract / introduction / methods / results / discussion / policy]
paper_type: [theory+simulation / empirical / model+calibration / mixed]
primary_corpus: [TARGET JOURNAL OR PRIMARY CORPUS NAME]
secondary_corpus: [FIELD TOP PAPERS / TOPIC-SIMILAR PAPERS / NONE]
user_exemplars: [USER / ADVISOR / LAB SAMPLES / NONE]
conversion_summary: [N converted and checked / N retried / N replaced]
static_base_skill: [base_rules/economics.md / custom file / none]
generated_from: style_profile_[DATE].md
created_date: [DATE]
priority_version: 1
status: [active / superseded]
```

---

## PART 1 — PRIORITY RULES (Non-Negotiable)

These rules override everything else. Apply in order.

### Priority 1 — HARD PRESERVE (never touch)

The following elements must be preserved verbatim in all revisions:
- All `\cite{}` commands and citation keys
- All LaTeX math environments (`\begin{equation}`, `\begin{align}`, etc.)
- All variable names, notation, and mathematical symbols
- All numerical results, statistics, and quantitative claims
- All footnotes and their content
- All figure and table references (`\ref{}`, `\label{}`)
- All model names, dataset names, and proper nouns
- All author-defined terminology and concept names

### Priority 2 — TARGET JOURNAL PATTERNS

Apply reviewed writing patterns from the primary target-journal corpus.
When P2 conflicts with P3 or P4, P2 wins unless the user explicitly overrides it. Log the conflict in the revision log.

### Priority 3 — SECONDARY CORPUS / EXEMPLAR FOLLOW

Apply high-quality field, topic-similar, user, advisor, or lab patterns from optional secondary inputs when P2 is absent, weak, or underspecified.

### Priority 4 — STATIC BASE SKILL DEFAULT

Apply the selected static base skill when P2 and P3 have no guidance on a dimension.

### Priority 5 — ALWAYS REMOVE (anti-patterns)

Remove these regardless of other rules:
- AI-taste openers: "This paper explores...", "In this study, we...", "It is worth noting that..."
- Generic contributions: "contributes to the literature on X by..."
- Hollow transitions: "Furthermore", "Additionally", "Moreover" used without logical function
- Circular emphasis: "importantly", "notably", "significantly" without quantification
- Template conclusions: "Future research should...", "More work is needed on..."
- Redundant meta-commentary: "As mentioned above", "As we will show below"

---

## LOADING INSTRUCTION FOR REVISION SESSIONS

When running Module E revision, load SKILL.md sections as follows:

```
ALWAYS LOAD:
  Part 1 — Priority Rules
  Part 3 — Conflict Resolutions
  Part 4 — Signal-Weak Flags
  Part 5 — Language Register Calibration

LOAD ON DEMAND (only for the section being revised):
  Part 2A — if revising Abstract
  Part 2B — if revising Introduction
  Part 2C — if revising Literature Review
  Part 2D — if revising Methods/Model
  Part 2E — if revising Results
  Part 2F — if revising Discussion / Policy Implications
  Part 2G — if revising Conclusion

DO NOT LOAD:
  Style Profile or Journal Style Card (superseded by this SKILL.md)
  Corpus papers or Paper Style Cards
  Any file from 01_corpus/ or 02_journal_style/
```

This keeps each revision session context small: Part 1 + one Part 2 block + the section text.

---

## PART 2 — SECTION-SPECIFIC GUIDANCE

### Part 2A — Abstract

**Revision mode:** [HIGH = 3-round / MED = merged / LOW = fast-scan]  
**Corpus norm:** [fill from primary corpus and secondary corpus if relevant — structure, length, tense, register]

**Structure:**
[e.g., "context → gap → method → main finding → implication, 4-5 sentences"]

**Tense:**
[e.g., "present for context and gap; past for method and findings"]

**Contribution placement:**
[e.g., "finding stated directly, no 'this paper contributes' framing"]

**Guidance:**
- [specific instruction derived from journal style card]
- [flag caution items, such as "only appears in secondary corpus" or "conflicts with static base skill"]

**Do not:**
- [anti-patterns specific to this journal's abstract style]

---

### Part 2B — Introduction

**Revision mode:** [HIGH = 3-round / MED = merged / LOW = fast-scan]  
**Journal norm:** [fill from Journal Style Card]

**Required sequence:**
[e.g., "operational context → supply-chain consequence → gap → RQs → model preview → contributions → roadmap"]

**Opening move:**
[describe the required/preferred hook type for this journal]

**Problem framing:**
[describe how to build urgency]

**Gap statement:**
[where and how to state the gap; what vocabulary signals it]

**Research questions:**
[explicit / implicit / absent — and format]

**Contribution format:**
[numbered/embedded, voice, claim scope]

**Literature:**
[integrated vs standalone, how to position vs prior work]

**Roadmap:**
[explicit vs narrative vs absent]

**Do not:**
- [intro anti-patterns]

---

### Part 2C — Literature Review

**Revision mode:** [HIGH / MED / LOW]  
**Journal norm:** [fill from Journal Style Card]

**Structure:**
[thematic / chronological / by method — and how themes are sequenced]

**Positioning move:**
[how papers in this journal distinguish their contribution from prior work in the lit review]

**Citation density:**
[high / moderate — and what counts as sufficient coverage]

**Common failure:**
[e.g., "lit review that summarizes without positioning" / "lists papers without synthesizing the gap"]

**Do not:**
- [lit review anti-patterns]

---

### Part 2D — Methods / Model

**Revision mode:** [HIGH / MED / LOW]  
**Journal norm:** [fill from Journal Style Card]

**Entry point:**
[intuition first / formal first — and how to make the transition]

**System description:**
[how to describe actors, decisions, and assumptions before notation]

**Exposition style:**
[theorem-proof / proposition-then-proof / definition-buildup / walkthrough]

**Notation density:**
[high / moderate — and where to introduce notation]

**Assumption justification:**
[how explicit and how lengthy explanations of assumptions should be]

**Verification:**
[what type of formal check or numerical validation is expected in this journal]

**Do not:**
- [method anti-patterns — e.g., "notation before system motivation"]

---

### Part 2E — Results

**Revision mode:** [HIGH / MED / LOW]  
**Journal norm:** [fill from Journal Style Card]

**Narration style:**
[e.g., "result → mechanism → parameter comparison → managerial implication"]

**Comparison structure:**
[how to present comparisons across model cases, structures, or policies]

**Mechanism emphasis:**
[required / optional — and how explicit to be]

**Robustness:**
[where in the section, how to frame, how much space]

**Quantitative claims:**
[precise / order-of-magnitude / qualitative-only — what this journal expects]

**Do not:**
- [results anti-patterns — e.g., "repeating the model setup", "significance without effect size"]

---

### Part 2F — Discussion and Policy Implications

**Revision mode:** [HIGH / MED / LOW]  
**Journal norm:** [fill from Journal Style Card]

**Function:**
[what discussion must add beyond results in this journal — mechanism deepening / policy application / limitation / future scope]

**Scope of claims:**
[how far the paper is expected to generalize beyond the model]

**Policy language register:**
[academic / policy-accessible — and how specific recommendations should be]

**Limitation acknowledgment:**
[proactive / brief / absent — what this journal expects]

**Do not:**
- [discussion anti-patterns — e.g., "rehashing results", "overclaiming beyond model scope"]

---

### Part 2G — Conclusion

**Revision mode:** [HIGH / MED / LOW — usually LOW]  
**Journal norm:** [fill from Journal Style Card]

**Function:**
[what conclusion adds beyond discussion — what this journal expects here]

**Length:**
[short / medium — and what signals too long]

**Future research:**
[required / optional / absent — and how specific to be]

**Do not:**
- [conclusion anti-patterns — e.g., "repeating the paper", "opening new claims not established in results"]

---

## PART 3 — CONFLICT RESOLUTIONS

Explicit rules for known conflicts between journal norms and general rules.

| Dimension | Static Base Rule | Target-Journal Pattern | Secondary/Exemplar Pattern | Resolution |
|-----------|------------------|------------------------|-----------------------------|------------|
| [e.g., Passive voice] | Avoid | Common in methods | none | Use passive in methods only |
| [e.g., Contribution format] | Numbered list | Embedded prose | none | Use embedded prose |
| [e.g., Hedging] | Minimize | Moderate | More policy-accessible in secondary corpus | Use direct claims for model results; hedge policy scope |

---

## PART 4 — CAUTIONS AND CONFLICTS

These guidance items require human judgment before application.

- [e.g., "Secondary corpus uses broader policy language; keep JEEM economics-facing tone."]
- [e.g., "Static base skill prefers numbered contributions; target-journal pattern uses embedded prose."]

---

## PART 5 — LANGUAGE REGISTER CALIBRATION

Based on the journal's language profile:

- **Voice:** [instruction, e.g., "Prefer active voice; passive acceptable in methods and results"]
- **Sentence length:** [instruction]
- **Hedging:** [specific guidance — when to use, when not to]
- **Mathematical prose:** [how to introduce and explain equations]
- **Transitions:** [preferred transition style for this journal]
- **Formality:** [calibration]

---

## PART 6 — QUICK REFERENCE CHECKLIST

Before submitting a revised section, verify:

```
□ All citations preserved verbatim
□ All equations and notation unchanged
□ No new empirical claims added
□ Contribution format matches journal preference
□ Hook type matches journal preference
□ Hedging level calibrated to journal norm
□ Anti-AI-taste pass completed
□ Cautions and conflicts checked by human reviewer
□ Conflict resolutions applied per Part 3 table
```
