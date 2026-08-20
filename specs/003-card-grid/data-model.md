# Data Model: Configurable press-sheet grid

**Feature**: `feat/card-grid` | **Spec**: [spec.md](./spec.md) | **Format contract**: [contracts/cards-yaml-grid.md](./contracts/cards-yaml-grid.md)

The *file format* is in the contract. This file covers the **in-process model**:
how a grid is represented once read, how it is resolved from three possible
sources, and what has to be threaded where.

## Entity: Grid

A grid is two positive integers. It is the only new value this feature
introduces, and it is deliberately not an object.

| Field | Type | Meaning |
|---|---|---|
| `columns` | int | cards across the A4 sheet |
| `rows` | int | cards down the A4 sheet |

Represented as a plain `tuple[int, int]`, mirroring how `margin` is a plain
`float` and `logo` a plain `bool`. Constitution V says code lands in an existing
module where one fits — a two-int tuple in `scripts/build_pdf.py` fits; a class
would be new structure for nothing.

### Derived, never stored

Everything else follows and must not be cached anywhere:

```
sheet_w, sheet_h = sheet(grid)          # 210 x 297 at a7, 297 x 210 at a8
cw        = (sheet_w - 2 * margin) / columns
ch        = (sheet_h - 2 * margin) / rows
scale     = min(cw / 100mm, ch / 71.75mm)   # 1.0 at a7, 0.6969 at a8
per_page  = columns * rows
pages     = 2 * ceil(len(cards) / per_page)
crop marks: columns + 1 vertical, rows + 1 horizontal
mirroring : column -> columns - 1 - column
```

> **Bugfix**: 2026-08-20 — [BUG-007](./bugs/BUG-007.md). ~~`cw = (210mm - …)`,
> `ch = (297mm - …)`~~ — the sheet was a literal 210 × 297, which makes 4 × 4 a
> *portrait* card. Every A-series halving flips the orientation, so the sheet
> turns with the grid (FR-024) and `scale` is derived rather than fixed
> (FR-025). Everything below still follows from `columns` and `rows`; there are
> simply two more inputs.

This is already how `templates/cards.typ` works. The only change there is that
`columns` and `rows` stop being literals and come in through `--input`.

### The supported set

A closed allowlist of two, with aliases:

| Canonical | Aliases | A-series |
|---|---|---|
| `(2, 4)` | `2x4`, `a7` | DIN A7 landscape |
| `(4, 4)` | `4x4`, `a8` | ~~DIN A8 portrait~~ **DIN A8 landscape**, on a landscape A4 sheet |

Anything else — well-formed or not — is refused. The allowlist exists because
every offered grid has to have been printed and looked at (spec Clarifications,
Q1); it is one line to extend when a third size earns its place.

## Resolution

Three possible sources, one winner. This is the only genuinely new logic.

```
resolve_grid(flag_value, deck_values) -> (columns, rows)

  1. flag_value given      -> parse, validate, return it.
                              Deck values are not even consulted.
  2. no flag, deck values all agree (or all absent)
                           -> return that value, or (2, 4) if all absent.
  3. no flag, deck values disagree
                           -> ERROR naming every file and its value.
```

Step 3 is the case that does not exist for `margin` or `logo`, because those
have never been declarable in a card file. It is why this is a function and not
an `or` chain.

**Why error rather than pick one**: one PDF is one grid. Silently choosing the
majority, or the first, or the smallest, guarantees that the other deck's cards
are typeset at a size they were not written for — and at A8 that means the
overflow warnings fire on cards their author never got wrong. An error the user
resolves with one flag is cheaper than a PDF they have to distrust.

## State transitions

None. A grid is resolved once per invocation, before any typesetting, and never
changes during a run. There is no persistence beyond the card file itself.

## Where the grid has to reach

Five sites in `scripts/build_pdf.py`, and missing one is a silent bug
(see [research.md](./research.md) R6):

| Site | Consequence of missing it |
|---|---|
| `typeset()` | the PDF is drawn at the wrong size — loud, obvious |
| `overflowing()` | **the PDF is right and every overflow warning is wrong** — silent |
| `offending_card()` | a build failure names the wrong card |
| `report_failure()` | inherits the above |
| the page report | the summary line contradicts the PDF |

`typeset()` and `overflowing()` each build their own `--input` list today. They
should build it through **one shared helper**, so the two cannot drift apart
again. That is the structural fix.

The test that catches it is **not** the A8 build of `overflowing.yaml` — that
card is reported at both grids and so passes under the bug. It is the assertion
that a card which *fits A7 and overflows A8* is reported only at A8
(`broken/overflows-only-at-a8.yaml`). An assertion of absence cannot detect this.

## What does not change

- `faces(cw, ch, show-logo:, scale:)` in `templates/card.typ` — signature and
  body untouched. It already takes the card size as arguments.
- ~~`scale` stays `1.0`. Never passed anything else. The 11 pt floor in
  `docs/design.md` depends on it.~~ **Wrong (BUG-007, FR-025).** `scale` is
  `min(cw / 100mm, ch / 71.75mm)` — 1.0 at `a7`, 0.6969 at `a8`. The floor does
  depend on it, which is why the floor needs **scoping** rather than lowering:
  it binds the card at its reference size, and a grid may render that card at an
  A-series scale.
- ~~`head-h` (8.6 mm) and `foot-h` (6.2 mm) stay absolute. Both supported grids
  keep `rows = 4`, so the bands remain 20.6 % of card height at either size —
  the vertical proportion worry from the ticket does not arise in the shipped
  set.~~ **This is the sentence BUG-007 turns on.** The worry it dismissed is
  the one that bites: on the corrected landscape card, absolute bands would take
  **29.6 %** of card height, not 20.6 %. Under FR-025 the bands scale with the
  card — 6.0 / 4.3 mm at `a8` — so the proportion is identical at both grids and
  the concern genuinely does not arise, for a different reason than the one
  given here.
- The `<overflow>` mechanism, the crop-mark rule at `--margin 0`, the duplex
  mirroring rule — all unchanged in behaviour, only re-derived from two
  variables instead of two literals.
