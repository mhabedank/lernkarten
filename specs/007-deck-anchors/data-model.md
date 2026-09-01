# Data Model: Deck anchors

**Feature**: `007-deck-anchors` | **Date**: 2026-09-01

This project has no database. Its "data model" is the file formats of
constitution I, plus the in-memory structures `scripts/check_project.py` builds
from them. Exactly one of the six formats changes, additively.

## 1. The format change — `catalog/topics.md`

### `Term:` — a new optional subtopic attribute

```markdown
### Rhythm of the tide
Semidiurnal tide, the length of the tidal day and the daily shift of high water.
Term: Rhythm of the tide, Tidenrhythmus, παλίρροια
References: [tide-cycle](../knowledge/field-notes/tide-cycle.md)
```

| Property | Value |
|---|---|
| Applies to | a subtopic (`###`) |
| Cardinality | 0 or 1 per subtopic |
| Required | **no** — absent means the behaviour this repo had before the feature |
| Value | one or more aliases, comma-separated |
| Parsed by | `ATTRIBUTE` → `parse_catalog` → `Entry.attributes["term"]` → `catalog_names()` |
| Consumed by | A-1 only |
| Order significance | none — any one alias anchoring a file satisfies that file |

**Validation** (all in `check_catalog`):

| Rule | Severity | Message shape |
|---|---|---|
| the line is present and parses to at least one alias | — | *(the normal case)* |
| the line is present and empty, or parses to zero aliases | **error** | `subtopic 'X': 'Term:' is empty — name the term, or leave the line out` |
| the line is absent | — | A-1 emits nothing for that subtopic (FR-011a) |
| the line sits on a topic (`##`) | *ignored* | consistent with `Parents:` on a topic today |

**Matching semantics** — this is the contract, not an implementation detail:

- an alias is normalised by `topic_key()`: lower-cased, every non-`\w`
  non-whitespace character replaced by a space, whitespace collapsed. `\w` is
  Unicode-aware, so Greek, Cyrillic and umlauts survive.
- a card's text is `front + " " + back`, normalised the same way, concatenated
  over every card in that file that carries this subtopic.
- an alias **matches** when its normalised form occurs as a **space-padded token
  sequence**: `f" {alias_key} " in f" {text_key} "`.
- therefore `Nipptidenhub` does **not** anchor `Tidenhub`, and `settlement`
  does not anchor `Settlements`. Substrings are not matches; only whole token
  runs are.
- there is **no stemming**. An inflecting language needs the alias written in
  the form the cards use (`нуля глубин`, not `нуль глубин`).

**Backwards compatibility**: additive. Every `catalog/topics.md` written before
this feature parses identically and gains no finding. The `ATTRIBUTE` regex
grows by one alternative; a line reading `Term: …` in an old catalog would
previously have been discarded as body prose and is now captured — a behaviour
change only for a file that already used the word, which no format documented
and the demo does not contain.

### Unchanged in the same file

`Status:`, `Parents:`, `Also covers:`, `Related:`, `References:`, `Goal:` — all
unchanged, all still optional, all still parsed by the same machinery.

## 2. The formats that do **not** change

| Artifact | Change |
|---|---|
| `goal.md` frontmatter | **none**. `depth` keeps exactly `awareness`, `working`, `expert`; `GOAL_DEPTHS` is untouched (FR-002). Only the *prose* in `skills/learning-goal/SKILL.md` changes |
| `cards/*.yaml` schema | **none**. No `level:` key, no anchor marker (FR-018). The demo deck's *content* changes; its schema does not |
| `sources.yaml` | none |
| `knowledge/<id>/<doc>.md` | none |
| `figures/<id>/<file>` | none |

## 3. In-memory structures

### Existing, reused unchanged

| Structure | Where | Role here |
|---|---|---|
| `Entry(kind, name, heading, attributes)` | `check_project.py:405` | carries `attributes["term"]` for free once `ATTRIBUTE` knows the key |
| `Catalog(entries)` | `:418` | unchanged |
| `Report(errors, warnings, counts)` | `:88` | both checks call `report.error(...)` only |
| `topic_key(text)` | `:128` | the single normaliser for both checks |
| `catalog_names(line, known=())` | `:463` | splits the alias list; strips a trailing parenthetical |

### New

#### `terms` — the A-1 input

```python
terms: dict[str, list[str]]  # {subtopic name: [alias, ...]}
```

Built in `check_catalog` alongside `marked`, from every subtopic whose `Term:`
line yields at least one alias. Returned as the third element of
`check_catalog`'s tuple and passed to `check_cards(..., terms=terms)`.
Empty dict when the catalog has no `Term:` line anywhere — which is every
project written before this feature, and is why A-1 is silent on them.

#### `anchor_text` — the A-1 accumulator

```python
anchor_text: dict[tuple[str, str], str]  # {(where, subtopic): normalised text}
```

Filled inside `check_cards`'s existing per-card loop, judged after it — the same
shape the file already uses for `figure_faces` and `by_subtopic`, and for the
same stated reason: the question is about a whole file, not about one card.
The key `where` is the `cards/<name>.yaml` string, which is what makes the
binding per file (FR-010/D2).

#### `Enumeration item` — the A-2 unit

Not a persisted structure; the output of the bracket-depth scan over one card's
`back`.

```
back  ──scan──▶  ["Torvig", "Little Kestrel", "Skarn", ...]  or  None
                                                                  └─ unbalanced: skip the card
each item ──maths gate──▶ skipped if it contains a "$"
          ──head term──▶  cut at the first of: — – , : ; " ("
          ──topic_key──▶  the key matched against the other cards in the file
```

## 4. Entity definitions (from the spec)

| Entity | Definition | Identified by |
|---|---|---|
| **Subtopic term** | the concept a `###` heading is about, made addressable by its optional `Term:` line. A subtopic without one has no term as far as the checker is concerned | the subtopic name |
| **Anchor** | a card in a given file, under a given subtopic, whose `front + back` names one of that subtopic's aliases. Not a card *type* — same schema, same budget, same style rules; what makes it the anchor is that it names the term | `(card file, subtopic)` |
| **Enumeration card** | a card whose `back` contains at least one `#list(...)`. A card with no `back`, or one that is not a mapping, is not one — A-2 skips it and the existing required-keys error covers it (FR-012a) | its 1-based index within the file, never its `id` (FR-014) |
| **Enumeration item** | one `[...]` element of a `#list(...)` body | its verbatim text |
| **Orphan** | an enumeration item, not skipped by the maths gate, whose head term is named by no *other* card in the same file | the item verbatim |

## 5. Invariants

| # | Invariant | Enforced by |
|---|---|---|
| I-1 | A subtopic with a `Term:` line and at least one card in a file has an anchor in **that** file | A-1, error |
| I-2 | A subtopic with **no** cards in a file produces no A-1 finding for that file | A-1, by construction — `anchor_text` only has keys for pairs that have cards |
| I-3 | A subtopic with **no** `Term:` line produces no A-1 finding anywhere | A-1, by construction — `terms.get(subtopic)` is `None` |
| I-4 | Every non-maths enumeration item is named by some **other** card in the same file | A-2, error |
| I-5 | An item named only on the card that enumerates it is still an orphan | A-2 — the haystack excludes the enumerating card |
| I-6 | An unbalanced `#list(` fragment produces no finding | A-2 — the scan returns `None` and the card is skipped |
| I-9 | A card with a missing or non-mapping `back` produces no A-2 finding (FR-012a) | A-2 — skipped before the scan; `check_cards` already reports it |
| I-10 | A subtopic marked `Status: gap`/`out of scope` that has cards is still checked by A-1 (FR-009a) | A-1 — keyed on `anchor_text`, which is built from cards, not from `marked` |
| I-7 | An empty `Term:` line is an error (FR-011b) | `check_catalog` |
| I-8 | `depth` remains exactly `awareness \| working \| expert` | `GOAL_DEPTHS`, unchanged |

## 6. Ordering of findings

Both checks report inside `check_cards`, which walks `sorted(root.glob("*.yaml"))`.
A-2 reports per file, in card order, as each file's inner loop finishes. A-1
reports after every file has been read, over `sorted(anchor_text)`, so the output
is stable across platforms and runs — which matters because tests assert on
message content.
