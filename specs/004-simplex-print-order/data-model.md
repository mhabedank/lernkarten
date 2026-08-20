# Phase 1 Data Model: Sheets, faces and the two orderings

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

This project's "data model" is normally one of the five file formats. **This
feature changes none of them** — see [Format Contracts](spec.md) in the spec,
where all four rows read *none*, and FR-012, which forbids a deck key on
purpose. What follows is the model of the thing that does change: the sequence
of pages inside the output PDF.

## Entities

### Card

Unchanged. What the build already loads from `cards/*.yaml`: `topic`,
`subtopic`, `front`, `back`, optional `source`, plus a synthesised `id` and a
resolved `language`. It has two **faces** and knows nothing about pagination.

### Sheet

One physical piece of paper. Derived, never stored.

| Field | Value |
|---|---|
| `index` | `0 … N-1`, in card order |
| `cards` | up to `columns × rows` cards, sliced in order |
| `faces` | exactly two: the front and the back of these same cards |

`N = ⌈cards ÷ (columns × rows)⌉`. The count of sheets is decided by the grid
alone and is **identical in both print orders** — this is what makes FR-004
true without a second implementation of the page-count rule.

### Face

One printable page. Derived.

| Field | Value |
|---|---|
| `sheet` | which sheet it belongs to, `0 … N-1` |
| `is_back` | `false` = the question side, `true` = the answer side |
| `mirror` | **the same boolean as `is_back`** |

`mirror` and `is_back` being one value is the load-bearing simplification. The
back of a sheet is column-mirrored so that turning the paper about its long
edge puts each back behind its own front; that is true of a duplex printer
turning the sheet and of a person turning the stack, so it holds in both orders
and no ordering can desynchronise it (FR-003).

Every face carries its own evidence in the printed footer:
`<card-id> · 1/2` on a front, `<card-id> · 2/2` on a back
(`templates/card.typ:96`). That is how the tests read the order back.

### Print order

The only new concept. A **property of the run**, never of a deck (FR-012).

| Value | Meaning | Who turns the paper |
|---|---|---|
| `duplex` (default) | front, back, front, back … | the printer, between the two impressions |
| `simplex` | all `N` fronts, then all `N` backs | the user, between the two print jobs |

## The mapping

Both orders are permutations of the same `2N` faces. Writing a face as
`(sheet, is_back)`:

```text
duplex   →  (0,F) (0,B) (1,F) (1,B) (2,F) (2,B) (3,F) (3,B)
simplex  →  (0,F) (1,F) (2,F) (3,F) (0,B) (1,B) (2,B) (3,B)
```

Read as a function from 0-based page position `p` to a face:

| Order | Page `p` carries |
|---|---|
| `duplex` | sheet `⌊p / 2⌋`, back iff `p` is odd |
| `simplex` | sheet `p mod N`, back iff `p ≥ N` |

### Invariants

These hold in both orders and are what the tests assert:

1. **Length**: `2N` faces, so the page count is `2N` either way (FR-004, SC-001).
2. **Completeness**: every `(sheet, is_back)` pair appears exactly once — no
   face is dropped, duplicated or blank-padded. A partly filled last sheet has
   a partly filled front *and* a partly filled back, so the halves stay equal.
3. **Pairing**: for every sheet, its back page is the column-wise mirror of its
   front page, row for row (FR-003, SC-002).
4. **Degeneracy at `N = 1`**: the two orders are the same sequence,
   `(0,F) (0,B)`. A one-sheet deck produces an identical PDF layout either way;
   only the closing line differs, because the instructions still differ.

### What a reader can recover

| Question | Answered by |
|---|---|
| Is page `p` a front? | every face mark on it reads `1/2` |
| Which sheet is page `p`? | the set of card ids in its footers |
| Is the back mirrored? | page `p`'s id grid equals its front's, row-reversed |

All three come from `pdftotext -bbox-layout`, which
`tests/test_e2e.py::card_grid_per_page` already uses.

## State transitions

None. There is no state: a build reads card files, computes `N`, emits `2N`
faces in the requested order and exits. Running it twice with the same flag
gives the same order; dropping the flag gives the duplex order with nothing
left over (the idempotence edge case in the spec).
