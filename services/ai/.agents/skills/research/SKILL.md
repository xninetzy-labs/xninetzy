---
name: research
description: Research a topic using internal knowledge, official web sources, papers, or YouTube and synthesize a cited brief. Use for current verification, literature exploration, source comparison, learning resources, deep research, contradictory evidence, and converting verified findings into a proposed learning action.
metadata:
  triggers: "research riset source compare literature paper citation web current verification youtube deep research"
  lifecycle: "question-source-plan-retrieve-assess-synthesize-act"
  version: "1.1"
---

# Grounded research

Separate sourced facts, inference, recommendations, and unresolved gaps. A skill is not evidence and a search snippet is not a verified source.

## Workflow

1. Define the research question, scope, date boundary, and decision or learning outcome.
2. Check owner knowledge with `knowledge_search` or `knowledge_answer` when personal context matters.
3. Select light research for a narrow question and staged deep research for broad or high-uncertainty work.
4. Create queries for the main claim, alternatives, primary sources, and contradictory evidence.
5. Prefer official documentation, original papers, institutional sources, and directly relevant data.
6. Inspect source pages or full paper content; record title, publisher, date, URL/DOI, and retrieval status.
7. Synthesize only claims supported by the selected evidence and mark inference explicitly.
8. Run a final citation and contradiction check before presenting the brief.
9. Propose one next learning or action step; save notes, tasks, graph links, or large briefs only after approval.

For YouTube, rank by conceptual fit, prerequisites, freshness, and transcript quality. Treat videos as supplementary evidence for scientific or academic claims. Stop or narrow the scope when source quality or coverage is insufficient.

## Completion contract

Return the direct answer, key findings, disagreements, source quality and limitations, citations or stable references, and a bounded next action. Never return a raw link dump.
