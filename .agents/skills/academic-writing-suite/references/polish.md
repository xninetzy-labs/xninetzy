# Paragraph-level polish (grammar, word choice, voice, coherence, syntax)

Edit for readers. Never aim at lowering AI-detector scores. Preserve claims, numbers, citations, terminology and the author's voice.

1. Process paragraph by paragraph in order. Skip code, equations and block quotes.
2. Check per paragraph:
   - grammar, agreement, tense consistency (past for methods/results, present for established facts)
   - word choice: precise, no inflation, no unexplained jargon
   - voice: active unless the agent is irrelevant
   - coherence: topic sentence, transitions, old-then-new information order
   - syntax: one idea per sentence, parallel structure, cut stacked clauses
   - hedging calibrated to the strength of the evidence
   - one term per concept across the document
3. Output per paragraph: the polished text, then at most three lines `[type] before → after` for material changes. Unchanged paragraph: `no change`.
4. Flag, never fix silently: unsupported claims, missing citations, number mismatches, ambiguous referents.
5. If the text was AI-generated, finish with `anti-slop`; for stock AI phrasing use `humanize.md`.
6. More than ten paragraphs: return only changed sentences with their location, not the whole text.
