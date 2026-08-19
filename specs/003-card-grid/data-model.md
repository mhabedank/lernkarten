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
cw        = (210mm - 2 * margin) / columns
ch        = (297mm - 2 * margin) / rows
per_page  = columns * rows
pages     = 2 * ceil(len(cards) / per_page)
crop marks: columns + 1 vertical, rows + 1 horizontal
mirroring : column -> columns - 1 - column
```

This is already how `templates/cards.typ` works. The only change there is that
`columns` and `rows` stop being literals and come in through `--input`.

### The supported set

A closed allowlist of two, with aliases:

| Canonical | Aliases | A-series |
|---|---|---|
| `(2, 4)` | `2x4`, `a7` | DIN A7 landscape |
| `(4, 4)` | `4x4`, `a8` | DIN A8 portrait |

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
again. That is the structural fix; the test that catches it is the A8 build of
`overflowing.yaml`.

## What does not change

- `faces(cw, ch, show-logo:, scale:)` in `templates/card.typ` — signature and
  body untouched. It already takes the card size as arguments.
- `scale` stays `1.0`. Never passed anything else. The 11 pt floor in
  `docs/design.md` depends on it.
- `head-h` (8.6 mm) and `foot-h` (6.2 mm) stay absolute. Both supported grids
  keep `rows = 4`, so the bands remain 20.6 % of card height at either size —
  the vertical proportion worry from the ticket does not arise in the shipped
  set.
- The `<overflow>` mechanism, the crop-mark rule at `--margin 0`, the duplex
  mirroring rule — all unchanged in behaviour, only re-derived from two
  variables instead of two literals.
