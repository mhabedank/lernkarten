---
name: catalog
description: >-
  Build or update the topic catalog the flashcards are generated from — built from your learning goal first, then filled with references from the ingested knowledge under knowledge/. Triggers: /catalog, "build the topic catalog", "which topics are there".
---

# /catalog — build the topic catalog

Writes `catalog/topics.md`: the topic hierarchy that later serves as the
selection menu for `/cards`.

**The ordering is the whole point.** When `goal.md` exists, the tree comes from
the *goal* first and the references are attached to it afterwards. Build it the
other way round and the catalog is a summary of whatever was ingested, which is
how a deck ends up full of research-methodology cards nobody wanted.

## Steps

1. `knowledge/` empty → point at `/ingest`, done.
2. Read `goal.md` if it exists. **It decides the shape of the tree.**
3. If a catalog already exists: only work in the documents that are newer than
   the catalog (mtime) or do not appear there as a reference yet — keep the
   existing topics instead of re-rolling them.
4. With a lot of material (> ~15 documents or > ~200k words): fan out one
   reading agent per source that returns topics + subtopics + one-sentence
   descriptions + references, then merge and deduplicate. Otherwise read
   directly.
5. Write the catalog (format below), show the tree with the counts, and point
   at the next step.

## With a goal — the normal case

1. **Build the skeleton from `goal.md` before reading anything.** Each `###`
   area becomes its own top-level topic (`##`); the topics listed under it
   become its subtopics. Never merge two areas and never place a subtopic under
   an area it does not belong to — areas are independent by construction, and a
   goal with a technical strand and a behavioural strand must not be forced
   into one hierarchy.
2. **Then walk `knowledge/`** and attach each document to the branch it
   belongs to. Match by meaning, not by string: `goal.md` may be German while
   the papers are English.
3. Three things fall out of that ordering:
   - a branch the goal requires and no document covers → `Status: gap` and
     `References: none`, **keeping the bullet points** that say what it ought to
     cover. That list is what `/research-gaps` works from, and what the user
     reads when deciding whether to register another source.
   - ingested material that fits no branch of the goal → its own subtopic with
     `Status: out of scope`, **keeping its references** so nothing is silently
     lost. It is marked, not deleted; the user may still card it by name.
   - everything else → an ordinary subtopic, exactly as before.

## Without a goal

Build the catalog from the sources exactly as before — no `Status:` lines, no
gaps, no `Goal:` header. A project that has never run `/learning-goal` must get
byte-for-byte what it would have got before this step existed.

Then say one line, once:

> This catalog describes the material you have, not the topic you are learning.
> `/learning-goal` states the target, and `/catalog` will then also show what is
> missing.

That line is the only difference a user without a goal sees, and it is how the
step gets discovered at all. Do not turn it into a warning and do not repeat it.

## Format `catalog/topics.md`

```markdown
# Topic catalog
Updated: 2026-08-10 · Goal: [goal.md](../goal.md) · Sources: <ids>

## <Topic>
Short description (1–2 sentences).

### <Subtopic>
What this subtopic covers; the most important terms/statements in 2–4 bullet
points (this is the working basis for card generation).
References: [slug](../knowledge/<id>/<slug>.md), …
```

Optional lines inside a subtopic, all of which mean today's behaviour when
absent:

- `Status: gap` — required by the goal, covered by nothing. Takes
  `References: none`.
- `Status: out of scope` — ingested but outside the goal. Keeps its references.

Drop the `Goal:` field when there is no `goal.md`.

## Guidelines

- Cut topics by content, not by source — the same thing from two sources is
  ONE topic with two references.
- Aim for 3–10 topics with 2–8 subtopics each; structure more finely rather
  than creating giant subtopics.
- The bullet points per subtopic should carry enough weight to decide what is
  card-worthy without re-reading the full text — but the references stay the
  source of truth when the cards are written.
- A subtopic with neither references nor `Status: gap` is an error, and
  `check_project.py` reports it by name. If a branch has nothing behind it,
  decide which it is.
- A catalog that is almost entirely gaps is a valid, useful state — it is the
  user's to-do list, not a failure.

## Wrap-up

Show the tree, then the counts on one line: how many subtopics are covered, how
many are gaps, how many are out of scope. If there is at least one gap, point at
`/research-gaps`; otherwise point at `/cards`.
