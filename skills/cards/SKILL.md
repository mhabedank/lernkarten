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
6. Summary: number of cards per topic/subtopic, **how many of them carry a
   picture** (the deck now depends on files outside `cards/`), then the scope
   report below, then point at `/print`.

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

## Cards from a figure

A knowledge document may carry a `figures:` list — pictures `/ingest` judged
worth *showing* rather than only describing. A kept figure has a `path:` and a
`caption:`, and is marked in the body where it sat. Write **three kinds** of
card from one, not one:

- **The description card.** Prompt on the front, picture on the back:
  `front: 'Describe the CRISP-DM cycle'`, `back_image:` the figure, and a
  `back:` that says in one or two lines what the picture shows — the figure's
  `caption:` is the starting point. One per figure.
- **The recognition card.** Picture on the front, answer in text on the back:
  `front: 'What does this chart show?'`, `front_image:` the figure. One per
  figure. **Check the picture does not answer its own question**: a chart whose
  title is printed inside it gives the game away, and then the card tests
  reading, not recall. Ask something the picture does not label — which phase
  follows which, what the axis means — or leave the recognition card out.
- **Detail cards.** Ordinary text-only cards about what is *in* the picture,
  written from the transcription: "Which phase does CRISP-DM return to after
  Evaluation?". At least one, always. A figure that yields only picture cards
  teaches the diagram and never what it means, and `check_project.py` says so.

Rules that hold for all three:

- **The text on a face carrying a picture is never empty.** A back that is only
  a picture has no answer to read; a front that is only a picture has no
  question on it. The picture shows it, the text says what it shows.
- **One figure, one description card and one recognition card.** Printing a
  diagram onto six cards in a row wastes paper and teaches nothing extra.
- The path goes in `front_image:`/`back_image:` exactly as the knowledge
  document's `path:` spells it — relative to the project root.
- The existing scope rules are unchanged: a subtopic marked `Status: gap` or
  `out of scope` gets no cards, figure or otherwise, unless it is named.

## Card schema

```yaml
topic: 'Display name'
language: german               # language of these cards, plain name or ISO code
grid: a7                       # the card size these cards are written for
cards:
  - id: A45DK                   # five characters, assigned once, never changed
    subtopic: 'Subtopic'
    front: 'Question/term'
    back: 'Answer'
    back_image: 'figures/<source-id>/<slug>.png'   # optional; front_image too
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

**Write an `id:` on every card you create, and never change one you did not.**
It is the handle a user reads off the printed card and says out loud —
*"A45DK uses GAN without defining it"* — so it has to keep naming the same card
after the edit that conversation asks for.

- **Five characters** from `0123456789ABCDEFGHJKMNPQRSTVWXYZ` — Crockford
  Base32. `I`, `L`, `O` and `U` are not in it: the first three are misread as
  `1`, `1` and `0` off a printed card, and the fourth is left out so an id
  cannot spell something unfortunate.
- **Unique within the project.** Read the ids already in `cards/*.yaml` before
  you write new ones, and draw again on a clash.
- **First key on the card**, before `subtopic`, so a diff that adds ids stays
  readable.
- **Never rewrite an existing id** — not when you correct the card, not when
  you move it, not when you rename the file. That is the whole point: an id
  that changed when a card was fixed would break at the exact moment it was
  being used.
- A deck written before ids existed still builds. `lernkarten id --backfill
  cards/*.yaml` fills in the gaps; do not hand-write ids into an old deck
  yourself.

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
- **The budget does not depend on the grid.** A denser grid renders the same
  card at a uniform scale, so `a7` and `a8` hold the same text: front up to
  ~120 characters, back up to ~400. Over that is a warning from
  `check_project.py`, not an error — two cards beat one that does not fit.
  Write for the content, not for the size the deck happens to declare.
- No card whose answer is exhaustively covered by the catalog bullet point but
  not backed by the reference — when in doubt, check the reference.
