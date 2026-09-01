# Contract: the two new `check_project.py` messages

**Feature**: `007-deck-anchors`

The messages are a contract because FR-014 makes them one — "both checks MUST
name the culprit" — and because the tests assert on their content. Both are
**errors** (FR-015), so both exit 1 without `--strict`.

## A-1 — the missing anchor

**Fires when**: a subtopic carries a `Term:` line, a card file holds at least
one card for that subtopic, and no card *in that file* under that subtopic names
any of the term's aliases. The haystack is that file's cards under that subtopic
and nothing else (FR-010): a card in the same file under a different subtopic
does not anchor it.

**Scope**: one finding per `(card file, subtopic)` pair (FR-010, FR-014). A
subtopic split over two files that anchors it in neither produces **two**
findings, not one.

**Shape** — **normative**, one shape, always:

```
ERROR: cards/tides.yaml: subtopic 'Rhythm of the tide': no card names the term
       ('Rhythm of the tide') — one card in this file has to name the concept
       and say what it is
```

```python
report.error(
    where,
    f"subtopic '{subtopic}': no card names the term ('{alias}') — one card in "
    "this file has to name the concept and say what it is",
)
```

It follows the house grammar of `check_cards`: the file goes in `where` and the
reporter prefixes it, the subject is named and quoted first, and the reason
follows an em dash. `check_cards` already writes `subtopic '<name>'` twice (`is
not in the catalog`, `is marked 'Status: …'`), so nothing new is invented here.

**Must contain**, per FR-014:

| Element | Example |
|---|---|
| the card file | `cards/tides.yaml` (as the `where` argument, so the reporter prefixes it) |
| the subtopic | `subtopic 'Rhythm of the tide'` — always, even when it reads the same as the alias |
| the term it looked for | `('Rhythm of the tide')` — **the first alias on the `Term:` line**, verbatim |

**Which alias** (FR-014a): when the `Term:` line carries several, the message
names the **first**, verbatim as the catalog writes it, and lists none of the
others. Matching itself is order-independent — any one alias anchors the file —
but the message has to be deterministic because the tests assert on it. A reader
who needs the other aliases opens the catalog entry the message already names.

**Rejected alternative**, so it is not re-proposed: the shorter

```
ERROR: cards/tides.yaml: no card names 'Rhythm of the tide' — …
```

It reads better in the one case where the subtopic name and the first alias
coincide, and it fails FR-014 in every case where they do not. `### Chart datum
and the Ovray rule` carrying `Term: Chart datum, нуля глубин` would print only
`Chart datum`, and the reader would have no way to tell which catalog entry to
open. A shape that is complete only sometimes is not a contract.

**Silent when**: the subtopic has no `Term:` line (FR-011a); the subtopic has no
cards in that file (FR-010); the card carries no `subtopic:` key or names one
that is not in the catalog (the existing warnings already cover those, and A-1
has nothing to bind to).

## A-2 — the orphaned enumeration item

**Fires when**: a card's `back` contains a `#list(...)` whose items include one
that, after the maths gate and the head-term cut, is named by no **other** card
in the same file.

**Scope**: one finding per orphaned item.

**Shape**:

```
ERROR: cards/geography.yaml: card 1: 'Skarn' is enumerated and never
       explained — no other card in this file names it
```

**Must contain**, per FR-014:

| Element | Example |
|---|---|
| the card file | `cards/geography.yaml` |
| the card | by its **1-based index within the file** (`card 1`), always — never by `id` |
| the orphaned item | **verbatim**, as it was written between the brackets — not the normalised head term |

The item is quoted verbatim so the reader does not have to diff a list of *k*
items by hand (SC-002). Where the head-term cut changed what was matched, the
verbatim item is still what is printed.

**Index, not `id`** (FR-014, decided in the post-checklist session). The draft
asked for the `id` where one exists. It was dropped: no message anywhere in
`scripts/check_project.py` addresses a card by its id — `_check_ids`, the
function that exists to check ids, still writes `card {index}: unusable 'id' —
…` — and an `id` is optional, so an id-where-one-exists rule would give one
check two grammars and the tests two shapes to assert on. The index is the
file's convention and A-2 uses it without exception.

**Silent when**: the item contains a `$…$` span (the maths gate, FR-013a); the
bracket-depth scan is unbalanced (the whole card is skipped, FR-013); the item's
head term is named by any other card in the file.

**Malformed cards** (FR-012a): a list element that is not a mapping, or a
mapping carrying no `back` key, is skipped outright — it contributes neither an
enumeration to scan nor text to the haystack. `check_cards` already reports it
as `card {i}: 'front' and 'back' are required`, and one malformed card must not
produce two findings. A `back` that is present but is not a string is coerced
with `str()`, exactly as the surrounding per-card loop does, and scanned
normally; the coerced text holds no `#list(`, so nothing is reported and nothing
raises.

## Both

- Reported through `report.error(where, message)`, so `main()` prefixes
  `ERROR: ` and the run exits 1.
- Never through `report.warn` — FR-015. CI runs the fixture under `--strict`
  where a warning already fails, so an advisory would buy nothing and would read
  as optional to a user who is not CI.
- Ordering is deterministic: A-2 per file in card order as each file finishes;
  A-1 over `sorted(anchor_text)` after every file is read.
