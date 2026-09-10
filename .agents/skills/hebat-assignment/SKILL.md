---
name: hebat-assignment
description: Reusable foundation for producing HEBAT academic assignments across courses and project types. Use for source retrieval, content understanding, planning, design, document production, quality assurance, citations, and submission readiness for any HEBAT deliverable.
metadata:
  owner: xninetzy
  version: "2.0.0"
  scope: general
  language: en
  applies_to: all HEBAT assignments
---

# HEBAT Assignment Foundation

This skill is the reusable foundation for **all HEBAT assignments**, regardless of course, lecturer, project theme, team structure, or assignment format.

Its purpose is to ensure every HEBAT deliverable is:

* grounded in the actual HEBAT materials and assignment requirements,
* academically understandable and evidence-based,
* consistent in structure and visual design,
* ready for submission,
* reusable across different courses and project contexts.

The skill should prioritize **understanding before writing, structure before styling, and verification before delivery**.

## When to use

* preparing any HEBAT academic deliverable,
* planning structure, references, and visual design for an assignment,
* running content and visual QA before submission,
* preparing submission files and links.

## When NOT to use

* retrieval and LMS workflow — use `hebat-academic`;
* cross-domain assignment orchestration — use `xninetzy-assignment-orchestrator`;
* artifact generation outside HEBAT context — use `xninetzy-artifact-orchestrator`.

## Core principles

### Retrieve the authoritative assignment context first

Before designing or writing, collect the most relevant available materials:

1. HEBAT module or learning materials,
2. assignment brief,
3. lecturer instructions or course contract,
4. weekly progress requirements,
5. previous approved deliverables when available,
6. required submission format and naming convention.

Do not invent requirements that are not present in the available assignment context. When multiple instructions conflict, prioritize:

**official lecturer/course instructions → assignment brief → HEBAT materials → general academic conventions.**

### Build understanding before drafting

Before producing the final deliverable, understand the topic through the available knowledge sources:

* HEBAT materials,
* Obsidian or personal knowledge base,
* stored knowledge and memory when appropriate,
* project notes and prior work,
* relevant academic literature,
* credible web sources,
* supporting datasets or field evidence.

The goal is not to collect information indiscriminately, but to determine:

**What is the problem? Why does it matter? What is the relevant context? What evidence supports the discussion? What does the assignment actually require?**

### Use a consistent planning structure

Before building the document, define:

**Input → Understanding → Argument → Evidence → Structure → Design → Build → QA → Submission**

Every assignment should have a clear relationship between its requirements and its final output.

## General workflow

1. **Retrieve** authoritative assignment context and supporting materials.
2. **Understand** theme, learning objectives, problem/context, scope, key concepts, methodology, expected output, evaluation criteria, and submission requirements.
3. **Research** appropriate evidence from HEBAT materials, academic papers, institutional sources, official datasets, field observations, and credible web sources. Every source should support a meaningful claim, decision, or section.
4. **Plan** the logical structure before producing the final document. Adapt structure to the assignment rather than forcing every assignment into one template.
5. **Design** the document structure and visual system before building: page hierarchy, heading hierarchy, typography, spacing, table style, caption style, figure treatment, citation style, page layout, and cover layout.
6. **Build** the deliverable in the requested format. For document-based assignments: **DOCX → PDF → visual/structural QA**.
7. **Verify** both content and presentation: requirements, factual consistency, citations, headings, page numbering, table/figure placement, cover layout, page overflow, typography, spacing, links, filename, and submission format.
8. **Deliver** the final submission-ready files and required links/materials.

## Reusability rule

This skill must remain **course-agnostic**. Do not hard-code a course code, lecturer, project theme, SDG, methodology, submission channel, or Figma structure. Dynamically retrieve those values from the relevant assignment context. The foundation defines **how the assignment should be handled**, while course-specific materials define **what the assignment requires.**

## Decision rule

When uncertain, follow this priority:

**Official requirement → Assignment brief → Course/HEBAT material → Verified project context → Academic best practice → General formatting defaults.**

Never let a generic formatting rule override an explicit lecturer requirement.

## Reference map

* `references/doc-standard.md` — DOCX body, headings, cover page, table of contents, and section title conventions.
* `references/quality-and-evidence.md` — content quality, research and evidence rules, tables and figures, conclusion standard, references, academic tone, and visual design system.
* `references/qa-and-submission.md` — quality assurance passes, submission readiness, and general submission rule.

## Routing

* LMS retrieval and submission workflow → `hebat-academic`.
* Cross-domain assignment orchestration → `xninetzy-assignment-orchestrator`.
* Artifact generation tooling → `xninetzy-artifact-orchestrator`.
* Research evidence → `xninetzy-deep-research`.

## Completion contract

Every HEBAT assignment foundation operation returns the relevant subset of:

* Document foundation used (which defaults applied);
* Any explicit override from the assignment brief;
* Content QA status (requirements addressed, evidence checked, conclusion complete, references complete);
* Visual QA status (cover, layout, typography, page integrity);
* Submission readiness status and required channels followed.