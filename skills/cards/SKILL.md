---
name: cards
description: >-
  Generate flashcards — across the whole topic catalog or filtered by topic/subtopic. Writes YAML card files under cards/. Triggers: /cards, "make flashcards", "cards about <topic>".
---

# /cards — generate flashcards

Creates flashcards from the topic catalog and the references under
`knowledge/`, as YAML files in `cards/<topic-slug>.yaml`.

## Steps

1. No `catalog/topics.md` → point at `/catalog`, done.
2. **Determine the selection**: arguments name a topic/subtopic (match fuzzily,
   e.g. "bayes" → subtopic "Bayes' theorem"). Without arguments: cover the
   whole catalog. When ambiguous, name the matches and ask briefly.
3. **Per subtopic**: read the referenced files (not just the catalog bullet
   points!) and write cards. Aim for 3–8 cards per subtopic, depending on how
   dense the material is. With > 5 subtopics, parallelise generation via an
   agent fan-out (one agent per topic; put the reference paths and the style
   rules in the prompt).
4. **Merge into existing files**: if `cards/<topic-slug>.yaml` exists, append
   the new cards; do not duplicate cards whose `front` already exists in
   substance. Replace only on an explicit request ("regenerate").
5. Validate after writing: `lernkarten check cards/*.yaml`
   (checks the schema and test-compiles). Fix errors right away.
6. Summary: number of cards per topic/subtopic, then point at `/print`.

## Card schema

```yaml
topic: 'Display name'
language: german               # language of these cards, plain name or ISO code
cards:
  - subtopic: 'Subtopic'
    front: 'Question/term'
    back: 'Answer'
    source: 'Short reference'   # optional, printed small on the back
```

Always write `language:` — it is the language of the source material, and
`/print` reads it from there so the user never has to think about it.

## Style rules (in addition to CLAUDE.md)

- `front`/`back` are Typst markup, not LaTeX: maths in `$...$` with Typst
  syntax (`(a) / (b)`, `Omega`, `"Var"(X)`), a single `\` for a line break,
  `#list([a], [b])` for a bulleted back with at most 4 items. Escape `#`, `*`,
  `_`, `@`, `<`, `>` and backticks in running text; `%` and `&` need nothing.
- Write the strings in single quotes: then `"` needs no escaping and a
  backslash stays a line break. A literal apostrophe is doubled (`''`).
- Atomic: one card tests exactly one fact/concept. Mix definitions, formulas,
  distinctions ("difference between X and Y") and application questions.
- No card whose answer is exhaustively covered by the catalog bullet point but
  not backed by the reference — when in doubt, check the reference.
