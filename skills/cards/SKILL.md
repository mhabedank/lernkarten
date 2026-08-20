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
   whole catalog **except the subtopics the catalog marks** — see *Scope*.
   When ambiguous, name the matches and ask briefly.
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
6. Summary: number of cards per topic/subtopic, then the scope report below,
   then point at `/print`.

## Scope — what to skip, and what to say about it

A subtopic carrying `Status:` in `catalog/topics.md` is skipped when `/cards`
runs **with no arguments**:

- `Status: out of scope` — the user declared this material irrelevant.
- `Status: gap` — the goal wants it and no document covers it, so there is
  nothing to read. Writing a card here would mean inventing one.

**Naming one explicitly still generates it.** `/cards research methodology`
produces the cards; the mark is a default, not a lock.

### Report the two asymmetrically

They mean opposite things, so do not give them the same treatment:

- **Out of scope is the feature working.** A bare count, nothing else:
  "12 subtopics skipped as out of scope". No warning, no list. The user already
  decided this; do not re-litigate it on every run.
- **A gap means the deck is incomplete.** A warning that says so in plain
  terms — *these cards do not cover the whole topic* — followed by every gap
  **by name**, then the two ways to act on it: register a source with
  `/sources`, or run `/research-gaps`. A count alone is useless here, because
  the user cannot act on a number.

If there are no gaps, say nothing about gaps at all.

## Subtopics with several parents

A subtopic carrying `Parents:` is written **once**, into the **primary**
(first-named) parent's `cards/<topic-slug>.yaml`, with that primary topic as the
file's `topic:`. It is the topic the printed header band will carry.

If the user names a **non-primary** parent (`/cards governance` for a subtopic
whose primary is Security), still generate it — and say which file the cards
went into, or they will look in the wrong one.

Never write the same subtopic into two files. The catalog models the overlap;
the card file is a projection of it.

## Connection cards

`Related:` names subtopics that belong together without either containing the
other. Use it for exactly two things:

- **Connection and distinction cards** — "What is the difference between X and
  Y?", "How does X constrain Y?". These are what understanding a concept
  actually needs, and nothing else in the catalog says which pairs are worth
  contrasting.
- **De-duplication** — when two branches converge on one idea, write the card
  once rather than once per branch.

Write a connection card **once** for a pair, not once from each side. And write
none at all when the other end is a gap or out of scope: there is nothing to
read at a gap, and out-of-scope material is what the user asked not to be
tested on.

## Card schema

```yaml
topic: 'Display name'
language: german               # language of these cards, plain name or ISO code
grid: a7                       # the card size these cards are written for
cards:
  - subtopic: 'Subtopic'
    front: 'Question/term'
    back: 'Answer'
    source: 'Short reference'   # optional, printed small on the back
```

Always write `language:` — it is the language of the source material, and
`/print` reads it from there so the user never has to think about it.

Always write `grid:` too, for the same reason: it records the card size the
text was sized for, and `/print` reads it so nobody has to remember a flag.
`a7` (2 x 4 per sheet, 105 x 74 mm) unless the user asks for A8; `a8` (4 x 4,
52.5 x 74 mm) halves the paper and halves the width every line has. Omitting
the key still prints at A7, so nothing breaks — but say it rather than imply
it, and `check_project.py --strict` will ask for it.

**One deck is one size.** The key is top level only, never on a card, and two
files in one build that declare different grids are refused unless `/print`
is given an explicit `--grid`.

## Style rules (in addition to CLAUDE.md)

- `front`/`back` are Typst markup, not LaTeX: maths in `$...$` with Typst
  syntax (`(a) / (b)`, `Omega`, `"Var"(X)`), a single `\` for a line break,
  `#list([a], [b])` for a bulleted back with at most 4 items. Escape `#`, `*`,
  `_`, `@`, `<`, `>` and backticks in running text; `%` and `&` need nothing.
- **Emphasis**: `*bold*`, `_italic_` — one star, not two. `**bold**` is
  markdown and Typst reads it as two empty strong elements: the build succeeds
  and the card prints without emphasis, so nothing warns you.
- **The line break has a precondition**: `\` is a break only when whitespace
  follows it. Directly before `*`, `_`, `#`, `@`, `<`, `>`, `$` or a backtick it
  escapes that character instead — `'line\*bold* rest'` loses the break, prints
  a literal star and shifts every star after it. Use `'line\ *bold*'`, or put
  the emphasis somewhere other than the start of the new line.
- Write the strings in single quotes: then `"` needs no escaping and a
  backslash stays a line break. A literal apostrophe is doubled (`''`).
- Atomic: one card tests exactly one fact/concept. Mix definitions, formulas,
  distinctions ("difference between X and Y") and application questions.
- **Size the text to the declared grid.** A line at A8 holds 46 % of what a
  line at A7 holds, so the budgets are not the same card twice:

  | | `grid: a7` | `grid: a8` |
  |---|---|---|
  | `front` | up to ~120 characters | up to ~60 |
  | `back` | up to ~400 characters | up to ~160 |
  | `TOPIC / SUBTOPIC` in the head band | up to ~53 characters | up to ~22 |

  Over the budget is a warning from `check_project.py`, not an error — but at
  A8 it is a real one: two cards beat one that does not fit.
- **The head band clips, it does not wrap.** The printed label is
  `TOPIC / SUBTOPIC` in capitals, and anything past the band's width is cut off
  mid-word. At `grid: a8` that budget is about 22 characters *for both
  together*, so a long topic leaves nothing for the subtopic. Keep both short
  — the card body is where the detail belongs.
- No card whose answer is exhaustively covered by the catalog bullet point but
  not backed by the reference — when in doubt, check the reference.
