---
name: learning-goal
description: >-
  State what you are actually trying to learn, so the flashcards cover the topic rather than whatever happened to be ingested. Writes goal.md from prose, a pasted brief or a URL. Triggers: /learning-goal, "set my learning goal", "what am I studying for".
---

# /learning-goal — state the target

Maintains `goal.md` in the project root: the one statement of what the user
needs to be able to do. Everything downstream judges relevance against it —
`/catalog` marks a required topic nothing covers as a gap, and material that
fits no required topic as out of scope.

The name is `learning-goal`, not `goal`: this plugin ships into environments
that may already have a skill called `goal`.

## Steps

1. Read `goal.md` if it exists. Its shape is the contract below.
2. Take whatever the user gave you — prose, a pasted job ad or module
   handbook, a URL, or any mix. **Fetch what you were given links to** and read
   it. A brief is a statement of the target, so do **not** register it in
   `sources.yaml`; a user who wants the syllabus itself carded registers it
   with `/sources`.
3. Distil it into required topics grouped by area (see below).
4. If `goal.md` already exists, reconcile rather than overwrite — see
   *Re-runs*.
5. Write `goal.md`, then show the areas and their topics back as a short tree
   and point at the next step.

## The file

```markdown
---
goal: 'One line: what being ready looks like'
kind: exam            # exam | meeting | interview | self-study
depth: working        # awareness | working | expert
updated: 2026-08-18   # today, ISO
---

# Learning goal

One to three sentences on what being ready actually looks like.

## Required topics

### <Area>
- A topic somebody pursuing this goal has to know
- Another one

### <Another area>
- ...

## Out of scope

- Something the material will contain that this goal does not want
```

`kind` and `depth` are closed sets — `scripts/check_project.py` rejects
anything else and names the value it found.

## Areas are independent

An area is a strand of the goal. A job interview legitimately means "the
technology stack" **and** "the company and the behavioural round" — two strands
with nothing in common. Write them as **separate areas** and never force one
into the other's hierarchy; nothing downstream looks for a relation between
them. Each area becomes its own top-level topic in the catalog.

One goal per project. A user pursuing two unrelated *targets* wants two project
folders; a single target with unrelated *strands* wants areas.

## Depth

`depth` is a **ceiling, not a slice**. It names the *highest* kind of card the
deck carries, and every level includes the ones below it: `expert` implies
`working` implies `awareness`. An `expert` deck therefore still carries the
cards that name the concepts and the cards that put them to use — it goes
further than a `working` deck, it does not start later than one.

- `awareness` — recognise the term and say what it is for
- `working` — all of the above, and use it unsupervised, decide with it
- `expert` — all of the above, and argue the edge cases and the trade-offs

Pick it deliberately: it decides where the deck *stops*, never where it begins.
A deck that jumped straight to the edge cases would test judgement about
concepts it never named.

## Re-runs

Never silently overwrite. Compare the new input against the stored goal:

- **Only additions** (a new area, a new topic) → merge without asking, keep
  every existing area and topic, move `updated` to today. Say what you added.
- **A contradiction** → list **every** one, ask the user to resolve each, and
  write only what they chose. Contradictions are: `kind` or `depth` changed; a
  topic crossing between required and out of scope; an area or topic dropped.
  Never prefer either version on your own.
- **A contradiction that narrows scope** → also name what already depends on
  it: read `catalog/topics.md` and `cards/*.yaml`, and say which subtopics and
  which card files would become out of scope. The user is deciding whether to
  throw work away and needs to see how much.

## When the brief is too vague

If the input supports no required topic at all, **ask** — do not invent a
syllabus. Write no file until you have at least one area with one topic. A
made-up goal is worse than no goal, because everything downstream trusts it.

## Wrap-up

Show the areas and topics as a tree, then point at the next step: `/sources`
registers the material, `/ingest` reads it, and `/catalog` builds the topic
tree from this goal. If a catalog already exists, say that it should be rebuilt
so the new goal takes effect.
