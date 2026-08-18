# Phase 1 Data Model: Goal-driven catalog

For this project a "data model" is a *file format* model — the entities live on
disk as markdown and YAML, and the deterministic half only ever validates them.
The wire formats themselves are in [contracts/](contracts/); this file is the
shape and the rules.

## Entity overview

```
goal.md ──────────────── drives ──────────────► catalog/topics.md
  │                                                  │
  │ Area 1..n                                Topic (##) 1..n
  │   └── Required topic 1..n                  └── Subtopic (###) 1..n
  │ Out-of-scope entry 0..n                          │
  │                                    Parents (1..n topics, primary first)
  │                                    Related (0..n subtopics, undirected)
  │                                    Status  (none | gap | out of scope)
  │                                    References (0..n → knowledge/)
  ▼
sources.yaml ── type: research ──► knowledge/<research-id>/*.md
```

---

## 1. LearningGoal — `goal.md`

One per project, at the root. Absent is valid and means "pre-feature behaviour".

| Field | Where | Type | Rules |
|---|---|---|---|
| `goal` | frontmatter | string | required, non-empty; a one-line statement |
| `kind` | frontmatter | enum | required; one of `exam`, `meeting`, `interview`, `self-study` |
| `depth` | frontmatter | enum | required; one of `awareness`, `working`, `expert` |
| `updated` | frontmatter | date | required; ISO `YYYY-MM-DD`, matched by the existing `DATE` regex |
| statement | body | prose | 1–3 sentences, not validated |
| areas | `## Required topics` → `### <Area>` | list | **at least one area**, each with **at least one topic** |
| out of scope | `## Out of scope` | list | may be empty; the section itself is expected |

**Validation** (`check_goal()`):

- a missing or empty required frontmatter key → error naming the key
- `kind` / `depth` outside the closed set → error naming the value *and* the set
- `updated` not ISO → error
- no area, or an area with no topics → error naming the area
- a required topic absent from `catalog/topics.md` → **warning** (drift; the
  catalog should be re-run, but the project is not broken)

**Why an enum and not free text**: `kind` and `depth` are read by three prompts
to decide breadth and register. A closed set is the difference between a
checkable contract and a suggestion. Both sets are small and additive — widening
one later is a one-line change plus a doc edit.

---

## 2. Catalog — `catalog/topics.md`

A **bipartite graph**, rendered as a heading hierarchy. Topics contain subtopics;
the catalog stays exactly two levels deep. Edges run only from topic to subtopic,
so no cycle can form and there is nothing to check for acyclicity.

### Topic (`##`)

| Field | Type | Rules |
|---|---|---|
| name | string | unique within the catalog |
| description | prose | 1–2 sentences |
| `Also covers:` | 0..n subtopic names | optional; each name must be a subtopic whose `Parents:` includes **this** topic |

### Subtopic (`###`)

| Field | Type | Rules |
|---|---|---|
| name | string | unique within the catalog |
| bullets | prose | the working basis for cards |
| `Parents:` | 1..n topic names, **primary first** | optional. Absent ⇒ the containing heading is the only parent. Present ⇒ every name must be an existing topic, and the **first** must be the heading this subtopic sits under |
| `Status:` | enum | optional; `gap` or `out of scope`. Absent ⇒ in scope and covered |
| `Related:` | 0..n subtopic names | optional, **undirected**; each must be an existing subtopic |
| `References:` | 0..n links, or the literal `none` | `none` is valid only with `Status: gap` |

### Invariants

| # | Invariant | Severity |
|---|---|---|
| C-1 | every `Parents:` name is a topic in this catalog | error |
| C-2 | the primary (first) parent equals the heading the subtopic sits under | error |
| C-3 | every non-primary parent carries a reciprocal `Also covers:` entry | error |
| C-4 | every `Also covers:` name is a subtopic whose `Parents:` includes that topic | error |
| C-5 | every `Related:` name is a subtopic in this catalog | error |
| C-6 | a subtopic has references, or `Status: gap` | error |
| C-7 | `Status:` is `gap` or `out of scope`, nothing else | error |
| C-8 | every reference link resolves on disk | error *(existing behaviour, unchanged)* |
| C-9 | a subtopic appears **once** in the counts and once in the set handed to `check_cards()`, regardless of how many parents it has | error if violated |

C-3 and C-4 are the pair that matters. The failure this format actually invites
is a half-edited catalog — a `Parents:` line updated without its `Also covers:`
counterpart, or the reverse. Both directions are errors rather than warnings,
because the next step would otherwise write cards into a file the user cannot
find.

### Projection: which card file a subtopic materialises into

A printed card carries `TOPIC / SUBTOPIC` in its header band
(`templates/card.typ:56`), so exactly one topic must be chosen before the cards
are written. The rule:

1. The **primary parent** decides the `cards/<topic-slug>.yaml` file and the
   `topic:` value in it.
2. Every other parent lists the subtopic under `Also covers:`, naming where its
   cards live.
3. `/cards <secondary parent>` still reaches the subtopic, generates it once,
   and reports the file it went into.
4. If the primary parent is out of scope and another parent is required,
   `/catalog` makes the in-scope parent primary.

The graph is the model; this projection is how it is stored and printed. Neither
constrains the other.

---

## 3. Source — `sources.yaml`, new type `research`

Extends `SOURCE_TYPES` in `check_project.py`, which currently maps
`folder`/`pdf` → `path`, `web` → `url`, `zotero` → `None`.

| Field | Rules |
|---|---|
| `id` | kebab-case, unique — unchanged rule |
| `type` | `research` |
| `gap` | **required** — the subtopic name this source was created to close |
| `path` / `url` | **not** required, and not expected |

`research` joins `zotero` as a type with no path or url: the URLs live in the
frontmatter of the documents under `knowledge/<research-id>/`, one per retrieved
page, using the existing `source` / `url` / `ingested` contract unchanged.

**Why a distinct type rather than `web` entries**: provenance. A `web` source is
something the user chose; a `research` source is something the model went and
found. Keeping them apart means the user can always tell their own material from
supplied material, and can delete all of the latter by removing one register
entry and one folder.

---

## 4. Cards — `cards/*.yaml`

**Unchanged.** No new key, no changed meaning. This is what keeps
`scripts/build_pdf.py`, `templates/card.typ` and `templates/cards.typ` entirely
outside this feature.

The only new *behaviour* is which cards get written, and into which file — both
decided upstream in `/cards`, both invisible to the build.

---

## State transitions

A subtopic moves between three states, and every transition is driven by a
pipeline step rather than by hand:

```
        /catalog (goal requires it, nothing covers it)
                       │
                       ▼
                   ┌───────┐
                   │  gap  │
                   └───┬───┘
                       │ /research-gaps writes a document, or
                       │ the user registers a source and runs /ingest + /catalog
                       ▼
                 ┌────────────┐        /learning-goal moves the topic
                 │  covered   │◄──────────── out of scope, then /catalog
                 └─────┬──────┘
                       │ /learning-goal puts the topic out of scope,
                       │ or /catalog finds it matches no required topic
                       ▼
              ┌──────────────────┐
              │  out of scope    │   references kept; /cards skips unless named
              └──────────────────┘
```

Deleting a `research` source and its knowledge folder returns its subtopics to
`gap` on the next `/catalog` run — the reverse edge, and the reason the
projection has to be re-derivable rather than remembered.
