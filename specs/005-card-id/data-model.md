# Phase 1 Data Model: A short, stable card id

**Feature**: `specs/005-card-id` · **Date**: 2026-08-21

For this project a "data model" is a *format* change. The authoritative wire
format is [contracts/cards-yaml.md](./contracts/cards-yaml.md); this file
describes the entities and the in-memory shapes the code passes around.

## Entities

### Card id

A short, opaque, human-sayable handle for one card.

| Attribute | Value |
|---|---|
| Representation | a YAML string on the card, upper case |
| Length | exactly 5 |
| Alphabet | `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (Crockford Base32) |
| Id space | 32⁵ = 33 554 432 |
| Scope of uniqueness | one project — every `cards/*.yaml` together |
| Assigned by | `/cards` on write, or `lernkarten id --backfill` |
| Encodes | **nothing.** Not topic, subtopic, language, deck or position |

**Lifecycle** — this is the whole point of the feature, so it is stated as
transitions rather than prose:

| From | Event | To |
|---|---|---|
| *(none)* | `/cards` writes a new card | assigned, permanent |
| *(none)* | `lernkarten id --backfill` | assigned, permanent |
| assigned | card text edited | **unchanged** |
| assigned | card moved within the file | **unchanged** |
| assigned | cards inserted or deleted before it | **unchanged** |
| assigned | file renamed | **unchanged** |
| assigned | build filtered by `--topic` / `--subtopic` | **unchanged** |
| assigned | collision with a card from another deck | **reassigned** if it is not the first occurrence — the only transition that changes an assigned id |

The five "unchanged" rows are exactly what breaks today, and each is an
assertion in the test plan (SC-002).

### Project id space

The set of ids in use across one project's card files.

- Populated by reading every `cards/*.yaml` before assigning anything.
- Assignment draws from the alphabet and **redraws while the candidate is in the
  set**, which is what makes in-project collisions impossible rather than merely
  unlikely (FR-003a). The 5-character choice therefore prices cross-project
  mixing, not in-project safety.
- Not persisted. It is derived on each run — there is no index file, no cache and
  no registry. This keeps FR-012 true: id work needs no state outside the card
  files themselves.

## In-memory shapes

### The card dict (`build_pdf.load_cards`)

Unchanged in shape; one field changes provenance.

```python
{
    "id":       "A45DK",   # WAS f"{path.stem}-{i}"; NOW read from the file
    "topic":    "...",
    "subtopic": "...",
    "front":    "...",
    "back":     "...",
    "source":   "...",
}
```

`id` stays a plain string so `templates/card.typ` needs no change to how it
*reads* the value — only to how it sizes it. When the file carries no `id`, the
value is the **empty string**, never a missing key, so the template never sees an
absent field. The template then renders the side marker alone — `1/2` or `2/2`,
with no `·` separator — which is the fallback FR-005 specifies (US2 scenario 3).

### Card position (`cardid.cards_in`)

What `yamlio.compose()` yields (PyYAML's `compose`, reached through the bootstrap), reduced to what the splice needs:

```python
[
    {
        "has_id":     False,
        "first_key":  ("subtopic", line, column),   # 0-based, from start_mark
        "last_value": line,                          # from end_mark
    },
    ...
]
```

Line and column come from PyYAML's marks, never from scanning text — that is
what keeps this a *use* of the library rather than a re-implementation of it
(Principle III; see [research.md § R-1](./research.md)).

### Reassignment record

One per collision resolved, for the report FR-013c requires:

```python
{"file": Path, "card": int, "old": "A45DK", "new": "QT8M2"}
```

The report renders these **with the consequence stated**, not as a bare
substitution list.

## Validation rules

Derived from FR-003, FR-004, FR-008 and FR-009. Each row is an assertion in
`tests/test_cardid.py` or `tests/test_check_project.py`.

| Rule | Invalid example | Message must name |
|---|---|---|
| Exactly 5 characters | `A45D`, `A45DKM` | file, card, the length found |
| Alphabet only | `A45DI`, `A45DL`, `A45DO`, `A45DU`, `A4-DK` | file, card, the offending character |
| Is a string | `id:`, `id: 12345`, `id: [a]` | file, card, the type found |
| Unique in project | two cards with `A45DK` | file **and** card for **both** |

**Comparison normalisation** (FR-004), applied before the uniqueness test so a
lower-case or confusable-typed id resolves to the card the user meant:

```
upper-case  →  I→1,  L→1,  O→0
```

`U` is excluded from the alphabet but is **not** folded — it has no numeric
twin; it is absent so a printed id cannot spell something unfortunate.

## Relationships

- **Card 1 ← 1 id** — a card has at most one id; an id names at most one card
  within a project.
- **Deck (file) 1 ← n cards** — ids are unique across *all* decks in the
  project, not per file. That is why backfill and reassignment take the whole
  file set, not one file at a time.
- **No relationship to topic, subtopic or grid.** Deliberate: the id is a
  handle, and coupling it to any of these would reintroduce the instability the
  feature removes.

## What this model does not carry

- **No revision or version.** `A45DK@2` addressing depends on this primary key
  being fixed and belongs to the follow-on ticket.
- **No timestamp.** An "assigned at" field was considered for the collision rule
  and rejected — it would add a schema key this feature does not otherwise need
  (see the Clarifications entry for FR-013b).
- **No global namespace.** Out of scope by the spec.
