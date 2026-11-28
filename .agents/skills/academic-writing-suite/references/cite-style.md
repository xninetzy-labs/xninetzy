# Citation style conversion (APA 7, MLA 9, IEEE, Harvard, Chicago, Vancouver)

Convert or normalize reference lists and in-text citations. The user's list is the only source of facts: never invent a field.

## Procedure
1. Detect the style per entry: `[1]` or initials-first = IEEE/Vancouver; `Surname, I. (Year).` = APA; `Surname, First. "Title." *Container*,` = MLA; `Surname, I. (Year) 'Title'` = Harvard. Mixed lists: convert entry by entry.
2. Parse to a record: authors, year, title, container, volume, issue, pages or article no., publisher, place, DOI/URL, access date, type (article, book, chapter, conference, web, thesis, preprint).
3. Missing field: keep the entry, mark `[MISSING: field]`, do not guess. Optional check: DOI lookup via `get_crossref_paper_by_doi` (paper_research MCP); report mismatches, never overwrite silently. Existence/support checks belong to `citation-validation`.
4. Render in the target style. Order: APA, MLA, Harvard, Chicago bibliography = alphabetical by first-author surname, then year; IEEE and Vancouver = numeric by first in-text appearance.
5. Convert every in-text citation to match and renumber numeric styles consistently.
6. Run the checks below, then emit.

## Templates (journal article first, then variants)
**APA 7**: `Surname, I., & Surname, I. (Year). Sentence-case title. *Journal Title*, *vol*(issue), pp–pp. https://doi.org/x`
- Book: `Surname, I. (Year). *Title* (2nd ed.). Publisher.` Chapter: `... In I. Surname (Ed.), *Book* (pp. x–y). Publisher.` Web: `Org. (Year, Month Day). *Title*. Site. URL` Thesis: `... *Title* [Doctoral dissertation, University]. Repository. URL`
- In-text: `(Surname, Year)`, two authors `(A & B, Year)`, three or more `(A et al., Year)`; narrative `A and B (Year)`. List up to 20 authors; 21+: first 19, `. . .`, last. No place of publication. No "Retrieved from" unless the page changes over time.

**MLA 9**: `Surname, First, and First Surname. "Article Title." *Journal*, vol. 12, no. 3, Year, pp. 1-10. DOI or URL.`
- Book: `Surname, First. *Title*. Publisher, Year.` Web: `Surname, First. "Title." *Site*, Day Mon. Year, URL.`
- In-text: `(Surname page)`, no year, `(Surname and Surname 45)`, three or more `(Surname et al. 45)`. Works Cited, hanging indent.

**IEEE**: `[n] I. Surname, I. Surname, and I. Surname, "Sentence-case title," *Abbrev. Journal*, vol. x, no. x, pp. xx–xx, Mon. Year, doi: x.`
- Book: `[n] I. Surname, *Title*, 2nd ed. City, Country: Publisher, Year.` Conference: `[n] I. Surname, "Title," in *Proc. Conf. Name*, City, Country, Year, pp. xx–xx.` Online: `[n] I. Surname, "Title," Site. URL (accessed Mon. Day, Year).`
- In-text: `[1]`, `[2]–[4]`, `[1], [3]`. More than six authors: first author et al.

**Harvard** (Cite Them Right default; institutions differ, follow their guide if given): `Surname, I. and Surname, I. (Year) 'Title', *Journal*, vol(issue), pp. x–y. doi:x`
- Book: `Surname, I. (Year) *Title*. 2nd edn. Place: Publisher.` In-text: `(Surname, Year)`, `(A and B, Year)`, four or more authors `(A et al., Year)`.

**Chicago author-date**: `Surname, First, and First Surname. Year. "Title." *Journal* vol (issue): pp–pp. DOI.` In-text `(Surname Year, page)`.

**Vancouver**: `n. Surname AA, Surname BB. Title. Abbrev Journal. Year;vol(issue):pp–pp. doi:x` In-text `(1)` or `[1]`, numeric by first appearance.

## Checks before delivering
- Every in-text citation has a list entry and every list entry is cited; no duplicates.
- Sort order, author-count rule, page-range en dash, DOI as `https://doi.org/...`, italics and capitalization match the style.
- Titles in the source language stay in that language; do not translate.
- Numbers of entries in and out are equal; list all `[MISSING: ...]` flags.

## Output
Converted list first, then a table `# | issue | action` for changed or flagged items only. Do not restate unchanged entries when the user asked for a check only.
