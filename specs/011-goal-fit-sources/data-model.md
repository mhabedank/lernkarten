# Data model: what this feature adds, and where it lives

Three of this feature's four entities never touch the disk. That is the point of
the design, not an oversight, so this file says for each one **where it lives**
and **what can therefore be asserted about it**.

Formats are in [contracts/](contracts/). The ordered red assertions are in
[plan.md](plan.md#test-plan-first).

| Entity | Lives | Assertable by |
|---|---|---|
| Goal-fit assessment | the run only | `check_docs.py` (the rule is in the prompt) + named manual rows |
| Candidate source | the run only, until picked | `check_docs.py` + named manual rows; once picked it is an ordinary `sources.yaml` entry that today's `check_project.py` already validates |
| Credibility sentence | inside a candidate | as above |
| Experience report | **on disk** — `nature: experience` | `check_project.py`, by name and by allowed value |

---

## 1. `nature:` — the one thing that lands on disk

**Written by** `/ingest` · **read by** `/catalog` and `/cards` · **validated by**
`check_knowledge()` in `scripts/check_project.py`.

```yaml
---
source: field-notes
document: "Ovray Cove, 14 March — what the harbour office wrote down"
path: "raw/field-notes/ovray-grounding.md"
nature: experience        # optional — see below
ingested: 2026-09-07
---
```

### Vocabulary

```python
# `nature:` says what kind of thing the document *is*, where that changes how it
# may be used rather than how much of it came out. An experience report is
# evidence about one situation — an incident write-up, a case study, a company
# post-mortem — so /cards attributes it to the case instead of stating it as a
# rule. Closed, like `content:` and `visual:`, and for the same reason: a marker
# nothing can act on is worse than no marker.
NATURES = ("experience",)
```

Placed beside `CONTENT_STATES` (`scripts/check_project.py:47`) and
`VISUAL_KINDS` (`:54`), because it is the same kind of thing and the next reader
should find the three together.

### Rules

| Rule | Severity | Message names |
|---|---|---|
| `nature:` absent | **not a finding, ever** | — |
| `nature:` present and in `NATURES` | none | — |
| `nature:` present and not in `NATURES` | error | the document, the bad value, and the allowed set |

The absence rule is load-bearing and is stated as a rule rather than left to
fall out of the code: it is the whole of FR-031's backwards-compatibility
promise and of SC-013's middle clause. It is enforced the way `content:` already
is — `if nature is not None and str(nature) not in NATURES` — which is also why
a YAML-parsed non-string is compared as text instead of crashing the checker.

### What a document is *not* marked for

`nature:` is a single value about the whole document, never a per-paragraph
judgement. A reference work with one anecdote in it is not an experience report;
the marker is for material whose **subject is the reported case**. `/ingest`
carries that sentence, and it is the difference between a marker that means
something and a marker on half the corpus.

---

## 2. Experience-only subtopic — derived, never stored

This is the entity that makes part of piece B assertable, and it exists only
inside one `check_project.py` run.

**Definition.** A subtopic in `catalog/topics.md` **all** of whose `References:`
resolve to `knowledge/` documents carrying `nature: experience`.

**Not** "at least one reference is an experience report". A subtopic with one
incident write-up and three handbook chapters may perfectly well carry a card
stating the general rule from the handbook, and demanding attribution there
would be wrong. US3 scenario 3 says *"a subtopic whose only references are
experience reports"*, and that is the set this derives.

**Derivation path** — it copies the `sparse` plumbing exactly, which is the
precedent for threading a per-document fact from `check_knowledge` down to the
catalog and the cards:

```
check_knowledge()  → returns (sparse, experience)      # sets of project-relative paths
check_catalog(..., sparse, experience)
                   → returns (subtopics, marked, terms, experience_only)
check_cards(..., experience_only)
                   → the FR-011 attribution rule
```

`check_knowledge` returns `sparse` today (`scripts/check_project.py:380`,
`:425-426`, `:428`); `check_catalog` already takes it as its fifth parameter
(`:690`) to judge a subtopic that rests on nothing but cover sheets. The second
set travels the same road for the same reason.

### The rule it carries (FR-011)

| Rule | Severity | Message names |
|---|---|---|
| a card whose `subtopic:` is experience-only carries no `source:` | **error** | the card file, the card index, the subtopic |

**Why error and not warning.** `check_cards` already warns "no source reference"
for every card without one (`:1097-1098`), so a warning here would say nothing
new and `--strict` would flatten the distinction. FR-011 is a MUST. And the
error cannot break a project that exists today: no document on disk carries
`nature:` yet, so `experience_only` is empty for every project written before
this feature. The stricter severity is free.

**What it does not assert.** Whether the card is *phrased* about the case, and
whether it drops the scale (FR-012). Both are judgements about prose; both are
named manual rows.

---

## 3. Goal-fit assessment — the run, and nothing else

**Produced by** `/sources` at registration · **stored** nowhere.

| Field | Value |
|---|---|
| verdict | *serves* (names ≥ 1 required topic or area) or *off-goal* |
| grounds | the named `goal.md` line: a required topic, an `## Out of scope` entry, or the `kind`/`depth` pair |
| subject | the source `id` |
| lifetime | one run |

**State transitions: none.** There is no stored verdict to become stale, which
is the entire content of clarification Q2. `sources.yaml` after this feature has
exactly the keys it has today — no `fit:`, no `assessed:`, no timestamp. See
[contracts/sources-yaml-unchanged.md](contracts/sources-yaml-unchanged.md),
which exists to make that a *contract* rather than an absence somebody has to
remember.

**Trigger.** Registration of a new entry, once. Not a listing (FR-008), not a
removal, and not on a goal written later (see
[research.md](research.md#r1--a-goal-written-after-the-sources-are-registered)).

**Reasoning inputs**, in the order the skill uses them:

1. `## Required topics` and its `### <Area>` headings — a match here is the
   *serves* verdict and supplies the name it must quote.
2. `## Out of scope` — a match here is the off-goal verdict and supplies the
   line it must quote.
3. `kind` and `depth` — the weighting of FR-005. `depth: expert`, or
   `kind: interview`/`meeting`, weighs practitioner material up; `kind: exam`
   with `depth: awareness` weighs it down. The assessment says which of the two
   it used.

A source may hit 1 and 2 at once — serving one required topic and sitting
squarely inside `## Out of scope` for another. The run says both (spec.md:193).

**Absent `goal.md`** ⇒ the entity does not exist. No line, no warning, no key,
and at most one pointer at `/learning-goal` per run.

---

## 4. Candidate source — the run, until the user picks

**Produced by** `/sources --discover` · **stored** nowhere until picked.

| Field | Required | Notes |
|---|---|---|
| name | yes | what it is |
| location | yes | where it lives — a URL discovery actually retrieved |
| class | yes | **which class of material it is** (FR-017) — an experience report, research literature, a reference work, a standards document, a public dataset, a magazine or trade article, or whatever it actually is. Free prose, **not** a closed vocabulary, never validated, never stored, and **not** the `nature:` key of §1 |
| serves | yes | the required topic or `### <Area>` of `goal.md` it would serve; also the grouping key |
| credibility | yes | one sentence, never a number (§5). The field is the same for every class of material; an **addendum** may add what the sentence must name for its own class (§5) |
| entry | yes | a registerable `sources.yaml` entry: a known `type`, a kebab-case unique `id`, the required field for its type |

**Lifecycle.**

```
proposed ──user picks──▶ registered through the ordinary /sources path (FR-020)
   │                         └─▶ the goal-fit assessment of §3 applies to it
   └──user declines──▶ gone. sources.yaml, knowledge/ and catalog/ unchanged
```

**Exclusions**, each of which removes a candidate before it is ever shown:

| Excluded | Requirement |
|---|---|
| not actually retrieved | FR-021 — a URL it has not seen is not a candidate |
| paywalled or login-gated | FR-023 — reported as found, never proposed, credentials never entered |
| already in `sources.yaml` | FR-024 |

**Never produced by**: `/ingest`, `/catalog`, `/cards`, `/print`, or any
`/sources` run that did not carry the explicit request (FR-035 – FR-037). There
is exactly one producer.

### The `class` field, and the thing it is not

`class` is stated because the run has **already determined it**: the addendum of
§5 cannot know whether to fire without it. Saying it out loud therefore costs
nothing, and it makes the grouping of FR-027 legible — a reader sees what kind of
material each goal area is being served by.

|  | `class` (this field) | `nature:` (§1) |
|---|---|---|
| layer | a candidate, before registration | a stored document, after ingestion |
| lives | the run only | `knowledge/<id>/<doc>.md` frontmatter |
| vocabulary | **none** — free prose, any words that fit | **closed** — `NATURES` |
| validated | never; nothing enumerates it | `check_project.py`, by name and value |
| written by | `/sources --discover`, into the run | `/ingest`, onto disk |

They are not the same thing and neither derives from the other. A candidate that
names its class *experience report* has not been ingested and carries no
`nature:` key; nothing about the class survives the run.

**No filter selects on it — yet.** Choosing which classes discovery *searches* is
a second axis and is deliberately out of scope (FR-040). `class` is the hook a
later filter would attach to, and this feature ships no class-selection argument,
no class list and nothing that reads a class back.

---

## 5. Credibility sentence

One sentence naming **what the source is and what it is not**. Not a score, not
a rating, not a percentage, not a star count, not a rank (FR-018 — issue #33
rejected invented numerators and the objection is unchanged).

That rule is **material-class neutral** (C1) and is held against every candidate
equally. What one class of material additionally requires of the sentence is an
**addendum** (C2, FR-039), and this feature ships exactly one, below.

**Addendum — practitioner material.** For practitioner material the sentence must
also carry the two properties the usual proxies miss (FR-019):

1. a company account of its own incident is a **primary source and an interested
   one** — nobody else has the timeline, and nobody has a stronger interest in
   how it reads;
2. published incidents are a **selected sample** — companies publish the
   failures they recovered from.

A candidate that is **not** practitioner material carries the neutral sentence
and nothing more: no addendum reaches outside its own class. Which candidates
those are is legible because §4's `class` field says so — the same judgement,
written down once and used twice.

The same selected-sample sentence reappears in `/catalog` and `/cards` output
for a subtopic that rests only on incident reports (FR-013), which is why it is
one entity here and not two.

---

## 6. Experience report

Material whose subject is what happened in one situation: an incident
post-mortem, a case study, a fuck-up report, an application scenario, a company
or engineering blog post about an outage.

It is a **primary source and an interested one**, drawn from a **selected
sample**, and valuable exactly where a reference work is thin — which is why
`depth: expert` and `kind: interview` weigh it up and `kind: exam` with
`depth: awareness` weighs it down.

**Not a source type.** A post-mortem is a URL and `type: web` already exists.
The judgement is around the fetch, not in it. What marks it on disk is `nature:`
(§1); what reads that marker is `/catalog` and `/cards`; what it changes is
phrasing and attribution, never whether the material is taken in.
