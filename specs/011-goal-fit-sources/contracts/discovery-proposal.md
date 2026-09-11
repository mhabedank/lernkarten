# Contract: the discovery proposal

**Produced by**: `/sources --discover` · **Consumed by**: the user, in the run ·
**Stored**: nowhere

This is not a file format. It is the **output contract of one mode of one
skill**, and it is written down for the same reason the card layout is: it has
rules that hold, and the only thing that can hold them is a prompt somebody may
later edit.

The parts of it that are checkable are checked in `scripts/check_docs.py`
against `skills/sources/SKILL.md`. The rest is on the manual checklist in
`docs/testing.md`, named, with FR numbers.

## Two layers: the neutral contract, and the addenda

Everything above the heading **C2 — material-class addenda** is **C1 — the
discovery contract**, and it is **material-class neutral**. It holds for any kind
of source: a practitioner blog, a public dataset, a standards document, research
literature. Nothing in it may be written in terms of one class of material
(FR-039).

**C2 — material-class addenda** is the last section of this file. An addendum says what
**one class** of source additionally requires of its credibility sentence, and
that is the *only* thing an addendum may do: it never relaxes an exclusion, changes a
cap, adds a candidate field or touches an entry condition.

**This contract ships exactly one addendum** — practitioner material (FR-019).
Neutrality is a shape, not a promise of coverage: no other class of material is
supported here.

`scripts/check_docs.py` asserts the two layers as **separate** checks, so a later
class is an added check and never an edit to a neutral one (FR-039, SC-016).

There is a **second axis** this contract does not cover: *which* classes of
material discovery searches. It is deferred deliberately, with its hook already
in place — see [What this is *not*](#what-this-is-not-choosing-which-classes-discovery-searches)
below (FR-040).

## Entry

**`/sources --discover`**, or the same request in words ("find me sources for my
goal", "look for material on X"). That is the **only** way in.

- Never started by the skill itself, never a follow-up prompt at the end of an
  ordinary run, never the default of any invocation (FR-035).
- An ordinary `/sources` run — a registration, a bare listing, a removal —
  neither enters it nor mentions it (FR-036).
- `/ingest`, `/catalog`, `/cards` and `/print` neither enter it nor mention it
  (FR-037), `/catalog`'s FR-014 report included.

The accepted cost, recorded deliberately in clarification round 2: **a user who
does not know discovery exists finds it only in the documentation.** There is no
hint anywhere in a run.

## Preconditions

| Condition | Result |
|---|---|
| no `goal.md` | say there is nothing to search for, point at `/learning-goal`, write nothing (FR-025) |
| no network | say it could not search, point at the ordinary registration path for material the user already has, write nothing, exit cleanly (FR-026) |
| otherwise | proceed |

Neither degraded path is a failure. Both are the `/research-gaps` pattern
(`skills/research-gaps/SKILL.md:78`), unchanged.

## Shape of the proposal

Grouped by the required topic or `### <Area>` of `goal.md` the candidates serve.
Every area gets a line, **including the areas where nothing was found** — that is
what makes a goal area nothing serves visible as such.

```
Found 31 candidates, showing 8.

Tides — 3 of 14
  1. <name>
     <where it lives — a URL that was actually retrieved>
     Class:  <experience report | research literature | reference work |
              standards document | public dataset | magazine or trade
              article | whatever it actually is>
     Serves: Range and the rule of twelfths
     What it is: <one sentence saying what it is and what it is not>
     Entry:  id: <kebab-case>   type: web   url: <...>

  2. ...

Signals, flags and the radio — 2 of 4
  ...

Geography — nothing found.

Nothing is registered until you say which ones you want.
```

### Caps

| Cap | Value | Why |
|---|---|---|
| per area | **3** | a choice, not a browse — the user is picking sources, not reading search results |
| per run | **10** | a proposal a reader takes in on one pass, for a goal with four or five areas |
| areas shown | **all of them** | an area with nothing found is information, and hiding it defeats the grouping |

The **found** and **shown** counts are reported per area and once for the run
(FR-027). A capped list is honest only if the count says it was capped.

The reasoning behind the two numbers is in
[research.md](../research.md#r3--how-many-candidates-discovery-shows). They are
prompt constants: changing them costs one edit and one checklist row.

## Per-candidate fields

| Field | Rule |
|---|---|
| name | what it is |
| location | **a URL discovery actually retrieved.** A URL it has not seen is not a candidate — `/research-gaps`'s "Never invent" rule, unchanged (FR-021) |
| class | **which class of material it is** (FR-017) — an experience report, research literature, a reference work, a standards document, a public dataset, a magazine or trade article, or whatever it actually is. **Not a closed vocabulary**: a phrase in the run, never validated, never written to disk, and **not** the `nature:` key of FR-015 (see *The class of material*, below) |
| serves | the required topic or area of `goal.md`. Also the grouping key |
| credibility | **one sentence** naming what the source is and what it is not (FR-018). The *form* is fixed here for every class of material; what a particular class must additionally name is an addendum, below |
| entry | a registerable `sources.yaml` entry: known `type`, kebab-case unique `id`, the required field for its type (FR-017) |

### The credibility sentence (neutral)

**One sentence naming what the source is and what it is not** (FR-018). Never a
score, a rating, a percentage, a star count or a rank — issue #33 rejected
invented numerators and the objection applies unchanged.

That is the whole of the neutral rule. It says nothing about what *kind* of
source a candidate is, and it is held against every candidate equally. Any
addition to it belongs to an addendum.

## The class of material

Every candidate says **which class of material it is**, in words (FR-017). The
examples above are examples: a candidate that is none of them names its own class
in its own words, and nothing is dropped, renamed or refused over it.

**It is not a key and not a vocabulary.**

| It is | It is not |
|---|---|
| a phrase in run output | a field on a `sources.yaml` entry |
| written by the same judgement that decides whether an addendum fires | a closed, validated set anything enumerates |
| free prose, in whatever words fit | the `nature:` key of FR-015 |

`nature:` and this are at different layers and must not be conflated. `nature:`
is closed, validated by `check_project.py`, and written by `/ingest` into a
**stored document's** frontmatter after the source has been registered and
fetched. This is prose about a source that has **not** been registered at all,
and it disappears with the run.

**Why state it at all**, when C1 is otherwise class-neutral: the class is
*already* being determined — the C2 addendum below cannot know whether to fire
otherwise — so naming it costs nothing and it makes the grouping of FR-027
legible, because a reader can see what kind of material each goal area is being
served by.

### What this is *not*: choosing which classes discovery searches

Selecting the classes discovery **goes looking for** — only experience reports
and post-mortems, only research literature, magazine articles as well — is a
**second axis**, and it is **out of scope for this feature** (FR-040). Discovery
searches whatever serves the goal, and the addendum fires only when a find
happens to belong to its class.

This contract therefore has **no filter, no class-selection argument and no class
vocabulary**. What it has is the **hook**: the per-candidate class above is the
field a later filter would select on, and such a filter must be addable by
building on it without reopening anything in C1 — the same obligation FR-039
places on addenda, applied to the other axis.

## Exclusions — removed before anything is shown

| Excluded | Requirement |
|---|---|
| not retrieved | FR-021 |
| paywalled or login-gated | FR-023 — say it was found and why it is not proposed. Never enter credentials. The rule `/ingest` already holds |
| already in `sources.yaml` | FR-024 |

## What it writes

**Nothing**, until the user picks. Not to `sources.yaml`, not to `knowledge/`,
not to `catalog/` (FR-016). A run in which the user picks nothing creates zero
files and modifies zero files (SC-005).

When the user picks, the chosen entries go through the **ordinary registration
path** (FR-020), which means the goal-fit assessment of FR-001 applies to them
exactly as it does to a source the user named — including the off-goal warning,
including the fact that nothing is persisted about the verdict.

## The seam against `/research-gaps`

Same network, different output, and both `skills/sources/SKILL.md` and the docs
have to state it (FR-022):

| | Discovery | `/research-gaps` |
|---|---|---|
| needs | a `goal.md` | a catalog with `Status: gap` subtopics |
| produces | **sources to read**, proposed | **documents**, synthesised into `knowledge/` |
| writes | nothing until the user picks | a `type: research` entry and its documents |
| when it can run | a user who has a goal and no material | only after `/catalog` |

Discovery **must not** synthesise documents into `knowledge/` and **must not**
create a `type: research` entry.

## Where the network is reached

`/sources` reaches the network **only** in discovery mode (FR-033). Registering
a source the user named and listing the register make no network request, as
today — `/sources` registers a URL without fetching it and continues to.

The distinction the docs must state is not "which step touches the network",
which was never true (`/ingest` fetches web pages with WebFetch and Zotero
collections over HTTP). It is:

> `/research-gaps` and `/sources --discover` **go looking for material the user
> did not choose**. `/ingest` **fetches what the user named**.

## C2 — material-class addenda

An addendum is attached to the credibility sentence of one class of material. One
exists.

### Addendum: practitioner material (FR-019)

Applies to an incident post-mortem, a case study, a fuck-up report, a company or
engineering blog post about something that happened. For such a candidate the
credibility sentence must **additionally** name the two properties the usual
proxies miss:

- a company account of its own incident is a **primary source and an interested
  one**;
- published incidents are a **selected sample** — companies publish the failures
  they recovered from.

A candidate that is *not* practitioner material is **not** held to either
property. It still carries the neutral sentence, and nothing else.

### Adding an addendum later

A new class of material is a new sub-section here plus one new check in
`scripts/check_docs.py`. Nothing above this heading is reopened, reworded or
re-scoped (FR-039).

[Issue #43](https://github.com/mhabedank/lernkarten/issues/43) — *Public research
sources: arXiv and friends* — is the first candidate, and it is **out of scope
here**. What it inherits, both of them: this whole neutral contract, including
FR-023's refusal to propose paywalled or login-gated material, which is the same
rule as its own restriction to openly accessible sources; **and** the
per-candidate class above, so #43 can tell its own material apart from everything
else without adding a field of its own. What it brings with it and this feature
does **not** build: bibliographic identity (DOI, authors, year, venue, citation
count) and any source-specific search backend. No arXiv work, no new source type
and no new frontmatter key are part of this contract.
