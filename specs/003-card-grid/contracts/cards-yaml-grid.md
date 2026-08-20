# Contract: `cards/*.yaml` — new optional key `grid`

**Written by**: `/cards` · **Read by**: `lernkarten build` / `check`
(`load_cards()` in `scripts/build_pdf.py`), `check_cards()` in
`scripts/check_project.py`

This is a change to one of the five file formats in constitution I, and is
therefore a breaking change. It is made **additive and optional** so that no
project on disk needs migrating.

## Shape

```yaml
topic: 'Example: Probability'
language: english
grid: a8              # NEW — optional. Absent means a7.
cards:
  - subtopic: 'Basics'
    front: 'What is a sample space $Omega$?'
    back: 'The set of all possible outcomes of a random experiment.'
    source: 'Example source'
```

`grid` sits at the top level beside `topic` and `language`, not on a card. One
deck is written for one size.

## Accepted values

| Value | Grid | Card at `--margin 5` | Card at `--margin 0` | Per sheet |
|---|---|---|---|---|
| `a7`, `2x4` | 2 columns × 4 rows | 100 × 71.75 mm | 105 × 74.25 mm (DIN A7) | 8 |
| `a8`, `4x4` | 4 columns × 4 rows, **on a landscape A4** | 71.75 × 50 mm | 74.25 × 52.5 mm (DIN A8 landscape) | 16 |
| *(absent)* | 2 × 4 | as `a7` | as `a7` | 8 |

Values are case-insensitive. `a7` and `2x4` are the same grid and must be
indistinguishable in effect; the same for `a8` and `4x4`.

> **Bugfix**: 2026-08-20 — [BUG-007](../bugs/BUG-007.md). The A8 row read
> `52.5 × 74.25 mm`, which is *portrait*. Every A-series halving flips the
> orientation, so the sheet turns for `a8` and the card stays landscape.

## Rules

| Rule | Severity |
|---|---|
| `grid` absent | — *(means `a7`; the pre-feature behaviour)* |
| `grid` is one of `a7` / `a8` / `2x4` / `4x4`, any case | — |
| `grid` is well-formed `COLSxROWS` but unsupported (e.g. `3x4`, `2x6`) | **error** — message names the file, the value and the supported set |
| `grid` is malformed (`3X4` with a capital X is fine; `3 x 4`, `3,4`, `eight`) | **error** — message names the file and the value |
| `grid` is `0x4`, `3x0` or negative | **error** |
| `grid` appears on an individual card rather than at the top level | **error** — names the file and the card index (FR-021) |
| two files in one build declare *different* grids, and no `--grid` given | **error** — message names **both** files and **both** values |
| two files declare different grids **and** `--grid` is given | — *(the flag resolves it)* |

## Precedence

```
--grid on the command line   →  wins over everything
deck-declared grid: key      →  used when no flag is given
neither                      →  a7
```

An explicit flag always overrides the file. This is what makes "print my A8 deck
at A7 just this once" possible without editing the deck.

## Interaction with the card-style limits

~~The warning thresholds in `scripts/check_project.py` become grid-dependent,
because a line at A8 holds 46 % of what a line at A7 holds.~~ **Retired by
BUG-007 (FR-027).** Under the uniform scale of FR-025 the two grids are
proportionally identical, and the scaled A8 card measures slightly *roomier*
than A7 — first overflow at 520 characters against 500. One set of thresholds
covers both. The table below recorded the measurement against the portrait
card and is kept for the record only (see [research.md](../research.md) R3):

| | A7 | A8 |
|---|---|---|
| `front` warn above | 120 chars | **60 chars** |
| `front` hard overflow at | 291 chars | 145 chars |
| `back` warn above | 400 chars | **160 chars** |
| `back` hard overflow at | 455 chars | 185 chars |
| `TOPIC / SUBTOPIC` label budget | ~53 chars | **~22 chars** |

The label budget is new in both columns — nothing checks it today, which is why
11 of the 38 cards shipped in this repo already clip their label silently at A7.
See [research.md](../research.md) R4.

## Backwards compatibility

Total. Every existing card file omits `grid`, which means `a7`, which is what
the build does today. `lernkarten build cards/*.yaml` with no flag produces a
byte-identical PDF to the one it produced before this feature. That is asserted,
not assumed — see SC-002.
