# Paper Style Card Template

**Version:** 1.1  
**Usage:** Fill one card per corpus paper. Works for primary target-journal papers, secondary field papers, and user/lab exemplars. AI extracts; human reviews.

---

## EXTRACTION RULES (AI must read before starting)

```
PROHIBITED — any of these causes card rejection:
  ✗ Direct quotes from the paper
  ✗ Paraphrased sentences from the paper
  ✗ Reproducing any named finding, statistic, or result

REQUIRED — all descriptions must be:
  ✓ Structural: HOW the paper is organized, not WHAT it says
  ✓ Rhetorical: what moves does the writing make
  ✓ Categorical: tags like active/passive, high/low, early/late
  ✓ Pattern-based: "the intro opens with X type of move"
```

---

## METADATA

```yaml
paper_id: [paper_001]
journal: [JOURNAL NAME]
corpus_role: [primary_target_journal / secondary_field_optional / user_exemplar_optional]
authors: ["LastName, F.", "LastName, F."]
year: [YEAR]
title: "[TITLE]"
relevance_tag: [topic+method / topic / method / supplement]
method_type: [theory / simulation / empirical / calibration / mixed]
extraction_date: [DATE]
extractor: [claude-sonnet / human]
extraction_scope: [full_text]
conversion_status: [converted_checked]
conversion_notes: [brief note, e.g., "full text readable; equations preserved"]
```

---

## A. Abstract Style

- **Opening move:** [e.g., "Opens with a policy-relevant phenomenon, one sentence"]
- **Structure:** [e.g., "phenomenon → gap → method → main finding → implication, 5 sentences"]
- **Tense pattern:** [e.g., "present tense for context and gap, past for findings"]
- **Contribution placement:** [e.g., "finding stated in sentence 4, no explicit 'we contribute' framing"]
- **Length:** [approx word count]
- **Register:** [technical / policy-accessible / mixed]

---

## B. Introduction Architecture

- **Hook type:** [phenomenon / puzzle / policy-failure / theoretical-debate / empirical-gap]
- **Opening move:** [how the first paragraph is structured]
- **Problem-consequence framing:** [yes/no — if yes, describe the structure]
- **Gap identification:** [how and where the gap is stated]
- **Contribution placement:** [early (para 2–3) / late (para 5+) / embedded throughout]
- **Contribution format:** [numbered list / prose / bullet / embedded]
- **Preview / roadmap:** [explicit section-by-section / narrative / absent]
- **Literature positioning:** [standalone section / integrated into intro / both]
- **Intro length:** [approx paragraphs / word count]

---

## C. Contribution Expression

- **Voice:** ["we show" / "this paper" / "our model" / mixed]
- **Claim strength:** [strong assertion / hedged / conditional]
- **Number of contributions:** [1 / 2–3 / 4+]
- **Format:** [numbered / prose / embedded in argument]
- **Placement relative to gap:** [immediately after gap / at end of intro / after literature]
- **Novelty framing:** [how they signal "this hasn't been done before"]

---

## D. Literature Review

- **Structure:** [standalone section / embedded in intro / woven throughout]
- **Organization principle:** [chronological / by theme / by method / by finding]
- **Positioning move:** [how they position their paper relative to prior work]
- **Citation density:** [high / medium / low relative to section length]
- **Critical engagement:** [just-cite / compare-and-contrast / synthesize / dispute]

---

## E. Method / Model Presentation

- **Entry point:** [intuition first / formal setup first / empirical motivation first]
- **Notation density:** [heavy / moderate / light]
- **Formal exposition style:** [theorem-proof / proposition-then-proof / definition-buildup / walkthrough]
- **Verification type:** [proposition / lemma / simulation / calibration / robustness check]
- **Explanation of assumptions:** [explicit and justified / stated but brief / implicit]
- **Link to empirics (if any):** [tight / loose / absent]

---

## F. Results Presentation

- **Primary vehicle:** [prose / tables / figures / mixed]
- **Narrative style:** [result → mechanism → implication / result-only / mechanism-first]
- **Mechanism emphasis:** [explicit and central / mentioned / absent]
- **Robustness signaling:** [where in the paper / how extensive / how framed]
- **Quantitative claim style:** [precise / order-of-magnitude / qualitative-only]

---

## G. Discussion Section

- **Function:** [deepen mechanism / compare to literature / limitations / policy implications / future research]
- **Scope of claims:** [stays close to model / extends to broader phenomena]
- **Policy language register:** [academic / policy-accessible / practitioner-facing]
- **Limitation acknowledgment:** [proactive / minimal / absent]
- **How discussion differs from results:** [what new content appears here]

---

## H. Policy Implications (if present)

- **Placement:** [end of discussion / standalone section / woven into results]
- **Claim specificity:** [specific policy recommendations / general principles / cautious framing]
- **Audience implied:** [academic / policymaker / regulator / industry]
- **Length:** [brief / substantial]

---

## I. Language Style Tags

- **Register:** [technical / policy / interdisciplinary / management / engineering-adjacent]
- **Sentence length:** [short-and-direct / long-and-complex / varied]
- **Voice:** [active-dominant / passive-dominant / mixed]
- **Hedging level:** [low / medium / high]
- **Formality:** [high / medium — does it read academic or accessible?]
- **Transition style:** [explicit connectives / implicit flow / structural headers]
- **Mathematical exposition:** [heavy / moderate / light / absent]

---

## J. What This Journal Does NOT Do

[List writing patterns that are notably absent or that appear penalized in this paper.
Do not copy original text. Describe structural or rhetorical patterns that are missing.]

- [e.g., "No 'this paper is the first to...' framing anywhere in intro"]
- [e.g., "No numbered list of contributions — all embedded in argument"]
- [e.g., "Discussion does not rehash results — it only extends them"]

---

## K. Distinctive Patterns

[Describe 2–4 notable structural or rhetorical moves specific to this paper.
No quotes. Describe the move.]

- [e.g., "Intro opens with a stylized fact presented as a statistic without citation, then the second paragraph establishes why that fact is surprising"]
- [e.g., "Each model section ends with a one-paragraph intuition summary before the next section begins"]
