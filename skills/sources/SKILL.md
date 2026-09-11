---
name: sources
description: >-
  Register, list or remove knowledge sources for the flashcards — folders, PDF collections, Zotero collections, web pages — saying what each one serves in your learning goal; and, when you ask for it, go looking for sources you do not have yet. Triggers: /sources, "add a source", "which sources do I have", /sources --discover, "find me sources".
---

# /sources — manage knowledge sources

Maintains the source register `sources.yaml` in the project root.

## Steps

1. Read `sources.yaml`. If the file does not exist (fresh clone — it is
   deliberately not versioned), create it with the comment header from
   `sources.example.yaml` and an empty `sources:` list; do NOT copy the
   example entries.
2. **Without arguments**: show every registered source as a compact table
   (id, type, path/URL/collection, note) and briefly explain how to add one.
   While doing so, check whether each source is still reachable (does the
   folder/file exist?) and flag dead ones.
3. **With `--discover`**, or the same request in words ("find me sources for my
   goal"): this is **not** a source to register — it is the discovery mode. Go
   to *Finding sources* below and do nothing else. Check this before step 4, so
   `--discover` is never read as a path.
4. **With arguments** (e.g. `/sources ~/Documents/University/Statistics` or
   "add my Zotero"): create the source(s) — see below — and, when `goal.md`
   exists, say what each one contributes to it, per *Goal fit* below. Then show
   the updated list.
5. **Removing** ("remove lecture-notes"): delete the entry from
   `sources.yaml`. Do NOT automatically delete already ingested texts under
   `knowledge/<id>/` — just point them out.

Steps 2, 4 and 5 are ordinary runs: they reach no network and they neither
enter discovery nor mention it.

## Creating a source

Determine the type yourself (heuristic: existing folder → `folder`, `.pdf`
file → `pdf`, URL → `web`, the word "Zotero" → `zotero`) and assign a
descriptive kebab-case `id`. Ask only when it is genuinely ambiguous.

Schema per entry (the comment header in `sources.yaml` shows examples):

- `folder`: `path` (required), `pattern` (optional, glob), `note`
- `pdf`: `path` (required), `pages` (optional, e.g. "1-150"), `note`
- `zotero`: `collection` (name of the Zotero collection; omit for the whole library), `note`
- `web`: `url` (required), `depth` (optional: 0 = this page only,
  1 = plus directly linked subpages on the same domain; default 0), `note`
- `research`: `gap` (required — the catalog subtopic it closes), `note`. No
  `path` and no `url`: the URLs live in the documents. **You do not write these
  by hand** — `/research-gaps` creates them when it closes a gap. Deleting one
  together with its `knowledge/<id>/` folder returns the affected subtopics to
  `Status: gap` on the next `/catalog` run, which is the supported way to throw
  model-supplied material away.

Validate before writing: expand paths (`~`), check that they exist; for
Zotero check whether the local API answers
(`curl -s http://localhost:23119/api/users/0/collections`) — if not, create
the entry anyway and point out that Zotero has to run during `/ingest`.

## Goal fit

Only when `goal.md` exists. Read `goal.md` before you write an entry, and say in
the run what you expect that source to contribute to the goal — naming at least
one required topic or `### <Area>` it serves — or warn that it serves none of
them.

The assessment is **advisory and never blocking**. The entry is written whatever
the verdict, an off-goal source is registered anyway with the warning shown, and
the run does not pause to ask. Nothing about the verdict is persisted: no `fit:`
key, no `assessed:` key, no timestamp. A source entry after this step carries
exactly the keys it carried before it.

An off-goal warning names the source `id` **and** the line of `goal.md` it
conflicts with — a required topic, an entry under `## Out of scope`, or the
`kind`/`depth` pair. Never a bare "this looks off-goal".

Judge *this source for this goal*. Never the subject, never the publisher, never
the source's worth in general: what someone reads is their business, and the only
question here is what it does for the goal they wrote down.

Reason from the `kind` and the `depth` in `goal.md`, and say which of the two you
used. They weigh independently, and either one alone is enough to say something:
`depth: expert` weighs practitioner material up, and so does `kind: interview`
or `kind: meeting` — the edge cases and the trade-offs are the content. `kind:
exam` weighs it down, and so does `depth: awareness` — an exam asks what the
term means, not how it failed at one company on one Tuesday. When the two pull
against each other, say so and say which way you came down.

Never invent a claim about a source you have not looked at. Registering fetches
nothing, so where you reason from the URL, the `note` and the `type` alone,
say so in the sentence itself.

The assessment happens **at registration**. A listing does not re-assess, and a
goal written after the sources were registered does not re-judge the register:
the next source registered is assessed, the ones already there are left alone.

With no `goal.md` there is no assessment and no warning, and the entry carries
exactly the keys that source type carries today. At most one line per run points
at `/learning-goal`, never one per source:

> There is no `goal.md` yet. `/learning-goal` says what you are learning, and
> `/sources` will then say what each source contributes to it.

Say that once, at the end of the run. Do not turn it into a warning and do not
repeat it.

When you register an archive — a blog, a series of posts, anything whose front
page links to the rest — say what the fetch will reach: `type: web` with
`depth: 1` gets the index page plus the posts on the same domain linked from it,
capped at 20 by `/ingest`. A ten-year archive is not ingested in full, and that
is worth knowing at registration rather than at `/ingest`.

## Finding sources

Entered as `/sources --discover`, or as the same request in words — "find me
sources for my goal", "look for material on X". Both are the same entry.

Discovery is entered **only on an explicit request**, made at invocation. It
never starts by itself, it is never offered as a follow-up at the end of an
ordinary run, and it is never the default of any invocation.

An **ordinary run** — registering a source the user named, listing the register,
removing a source — **neither enters discovery nor mentions it**. No candidate,
no proposal, no closing line asking whether you should go looking for more
material. A user who did not ask for discovery does not hear that it exists;
the documentation is where they find it, and that is the trade deliberately
made.

`/sources` reaches the network only in discovery mode. Registering a source the
user named and listing the register make no request, exactly as before.

**Preconditions.** With no `goal.md` there is nothing to search for: say so,
point at `/learning-goal`, write nothing. With no network, say you
could not search, point at the ordinary way to register material the user
already has, write nothing and exit cleanly. Neither is a failure.

**What it writes.** Discovery writes nothing until the user picks — not into
`sources.yaml`, not into `knowledge/`, not into `catalog/`. A run in which
nobody picks anything leaves the project exactly as it was.

### The proposal

Group the candidates by the required topic or `### <Area>` of `goal.md` they
serve, and say how many you found and how many you are showing — per area, and
once for the run. List every area, including the ones where
nothing was found: an area nothing serves is the most useful line in the report.

Show at most 3 candidates per area and at most 10 in one run. This is a choice
to make, not a page of search results to read.

```
Found 31 candidates, showing 8.

Tides — 3 of 14
  1. <name>
     <the URL you retrieved>
     Class:  <which class of material it is>
     Serves: Range and the rule of twelfths
     What it is: <one sentence saying what it is and what it is not>
     Entry:  id: <kebab-case>   type: web   url: <...>

  2. ...

Signals, flags and the radio — 2 of 4
  ...

Geography — nothing found.

Nothing is registered until you say which ones you want.
```

Six fields per candidate:

- **name** — what it is;
- **location** — a URL you retrieved. One you have not seen is not a candidate;
- **class** — which class of material it is: an experience report, research
  literature, a reference work, a standards document, a public dataset, a
  magazine or trade article. Those are examples and not a list to choose from —
  a candidate that is none of them names its own class in its own words, and
  nothing is dropped, renamed or refused over it. It is a phrase in the run,
  never a key on disk, and it is not the `nature:` key `/ingest` writes;
- **serves** — the required topic or area it would serve, which is also the key
  the proposal is grouped by;
- **credibility** — one sentence naming what the source is and what it is not.
  Never a score, never a rating, never a percentage, never any other number;
- **entry** — an entry ready to register: a known `type`, a unique kebab-case
  `id`, and the field that type requires.

### What is never proposed

- **What you did not retrieve.** Never invent a candidate.
- **Paywalled or login-gated material.** Say you found it and why it is not
  proposed, and never enter credentials — the rule `/ingest` already holds.
- **A source already in `sources.yaml`.**

### When the user picks

Picked entries go through the ordinary registration path above, goal-fit
assessment and all. The rest is dropped and nothing is kept about it.

Write no documents into `knowledge/` and create no `type: research` entry.
That is what `/research-gaps` does, and the seam is worth having in mind:
`/research-gaps` wants a catalog with `Status: gap` subtopics and writes
synthesised documents into the project; discovery wants a `goal.md` and
proposes sources to read. Same network, different output.

### Practitioner material

An incident post-mortem, a case study, a fuck-up report, a company or
engineering blog post about something that happened. For a candidate of that
kind — and only for one — the credibility sentence names two more things the
usual proxies do not show:

- a company's account of its own incident is a **primary source and an
  interested one**: nobody else has the timeline, and nobody has a stronger
  interest in how it reads;
- material of this kind gets published only by the parties who came through the
  incident and had an account they were willing to show, so the cases that ended
  badly are not among what can be found — and they stay missing however much of
  it there is.

Say both things rather than naming them. "A selected sample" is a term the
reader may never have met, and this sentence is written for that reader. It
stays one sentence: the second property costs a clause, not a paragraph. A
candidate that is not practitioner material is held to neither property — it
carries the neutral sentence and nothing else.

## Wrap-up

Point at the next step: `/ingest` reads the sources.
