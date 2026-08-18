---
name: research-gaps
description: >-
  Close the gaps in the topic catalog by researching them on the web, so the flashcards cover the whole goal and not only the material you happened to have. Triggers: /research-gaps, "close the gaps", "research what is missing".
---

# /research-gaps — fill what nothing covers

Takes the `Status: gap` subtopics of `catalog/topics.md` as its work list,
researches each one, and writes what it finds into `knowledge/` as a source of
its own — so the catalog entry stops being a gap and `/cards` picks it up on
the next run.

The name is `research-gaps`, not `research`: this plugin ships into
environments that may already have a skill called `research`.

**This is the only step that reaches the network**, and the only one that puts
material into the project the user did not choose. Both facts shape everything
below.

## Steps

1. No `catalog/topics.md` → point at `/catalog`, done.
2. Collect the subtopics marked `Status: gap`. **If there are none, say so and
   exit without touching anything.**
3. Without arguments, work the whole list; with arguments, only the gaps that
   match.
4. Per gap: search the web, read what you find, and write one synthesised
   document. Follow the `depth` in `goal.md` — `awareness` wants a page,
   `expert` wants the trade-offs — and aim at the 3–8 cards a subtopic normally
   yields, not an exhaustive survey.
5. Register the source, write the document, update the catalog entry.
6. Report what closed and what did not.

## What gets written

**One source per run** in `sources.yaml`, or one per gap if the subjects are
unrelated:

```yaml
  - id: <gap-slug>-research
    type: research
    gap: 'The exact subtopic name from catalog/topics.md'
    note: 'Synthesised for a catalog gap'
```

`gap:` is required — `check_project.py` reports a `research` source without
one, by id. There is no `path` or `url` on the entry itself; the URLs live in
the documents, because one gap may take several pages to close.

**One document per gap** under `knowledge/<research-id>/`, using the existing
frontmatter contract, with `url:` naming what it was built from:

```markdown
---
source: <research-id>
document: "<Subtopic> — synthesised for a catalog gap"
url: "https://…"
ingested: 2026-08-18
---
```

Say in the document body that it was synthesised and from where. The user has
to be able to tell their own material from what the model brought in — and
deleting the source entry plus the folder has to remove all of it.

**The catalog entry**: drop its `Status: gap` line and replace
`References: none` with a reference to the new document. Leave the bullet
points; they were the brief.

## Never invent

**Do not write a document with no retrieved source behind it.** If the search
returns nothing usable, that gap stays a gap — report it and move on. Filling
it from your own recall produces cards the user will trust and cannot check,
which is worse than the gap it replaces.

## No network

Report which gaps could not be closed, write nothing, and exit cleanly. This is
a degraded path, not a failure: the catalog is still correct, and the user can
register a source of their own instead.

## Wrap-up

Say how many gaps closed and how many are still open, name the ones still open,
and point at `/cards` if anything closed. If the user wants their own material
instead, `/sources` is the way.
