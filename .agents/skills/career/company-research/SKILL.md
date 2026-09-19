---
name: company-research
description: Research a company via legal public sources only. Surfaces funding, products, team size, hiring signal. No scraping.
metadata:
  type: workflow
  layer: career
  consumes:
    - research_search
    - knowledge_search
    - web_search
  produces:
    - company_research_report
  tier: 0
---

# company-research

Company background research using legal sources. Sources include
Crunchbase (paid, optional), Wikipedia, OpenAlex affiliations, public
news via RSS, official company blog RSS feeds.

## When to invoke

- Owner asks "tell me about company X"
- Before applying to a specific role

## Inputs

```yaml
company_name: "<name>"
domain: "<optional company domain>"
```

## Workflow

```yaml
steps:
  - id: wikipedia
    tool: research_fetch
    args: { identifier: "<name>", source: wikipedia }
    tier: 0
  - id: papers
    tool: research_search
    args: { intent: company, query: "<name>" }
    tier: 0
  - id: news
    tool: research_search
    args: { intent: news, query: "<name>" }
    tier: 0
```

## Output structure

```yaml
company_research_report:
  company: "<name>"
  wikipedia_url: "<url | null>"
  papers_count: <int>
  news_count: <int>
  summary: "<paragraph>"
  recent_news: ["..."]
```

## Constraints

- Only legal public sources.
- Cite every claim with URL.
- Do not fabricate funding/team-size numbers absent from sources.

## Anti-patterns

- Do NOT scrape LinkedIn employee count.
- Do NOT infer financials from third-party scrapers.
