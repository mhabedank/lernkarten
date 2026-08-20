# Quickstart: validating the press-sheet grid

**Feature**: `feat/card-grid` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Runnable checks that prove the feature works end to end. Every command is one a
user or CI would actually run. Expected values are **measured**, not guessed —
see [research.md](./research.md).

## Prerequisites

```bash
python3 --version                 # 3.12 or newer
lernkarten engine --check         # fetches Typst once, ~15 MB, then cached
```

`DEMO=tests/fixtures/demo-project/cards` for the commands below.

---

## 1. The paper saving — the reason the feature exists

```bash
lernkarten build $DEMO/*.yaml -o /tmp/a7.pdf                # default
lernkarten build $DEMO/*.yaml -o /tmp/a8.pdf --grid a8      # dense
```

| | Expected |
|---|---|
| `/tmp/a7.pdf` | **8 pages**, summary says `8 pages, duplex` |
| `/tmp/a8.pdf` | **4 pages**, summary says `4 pages, duplex` |

Half the sheets for the same 29 cards. That is SC-001.

## 2. The alias resolves to the same grid

```bash
lernkarten build $DEMO/*.yaml -o /tmp/alias.pdf --grid 4x4
cmp /tmp/a8.pdf /tmp/alias.pdf && echo "identical"
```

Expect `identical`. `a8` and `4x4` are the same grid (FR-002).

## 3. Nothing changes for an existing project

```bash
git stash                                                   # pre-feature build
lernkarten build $DEMO/*.yaml -o /tmp/before.pdf
git stash pop
lernkarten build $DEMO/*.yaml -o /tmp/after.pdf
cmp /tmp/before.pdf /tmp/after.pdf && echo "byte-identical"
```

**Measured**: the engine embeds a `CreationDate`, so two *consecutive* builds of
the same input already differ in bytes. Compare **page count, byte length and extracted text** instead — all three are identical, and that is what SC-002 means. `cmp` is the wrong tool here.

## 4. Exact A-series dimensions at zero margin

```bash
lernkarten build $DEMO/*.yaml -o /tmp/a7-0.pdf --grid a7 --margin 0
lernkarten build $DEMO/*.yaml -o /tmp/a8-0.pdf --grid a8 --margin 0
```

| Grid | Expected card | Standard |
|---|---|---|
| `a7` | 105 × 74.25 mm | DIN A7 |
| `a8` | ~~52.5 × 74.25 mm~~ **74.25 × 52.5 mm** | DIN A8 **landscape**, on a landscape A4 *(BUG-007)* |

That is SC-003 — the reason these two grids were chosen and not the ticket's
3 × 4. Both drop into a box you can buy.

## 5. Overflow still reports, at both grids

```bash
lernkarten check tests/fixtures/demo-project/broken/overflowing.yaml
lernkarten check tests/fixtures/demo-project/broken/overflowing.yaml --grid a8
```

Both must print `WARNING: card overflowing-2 does not fit`. **Measured**: the
same single card is reported at both grids.

```bash
lernkarten check tests/fixtures/demo-project/broken/overflows-only-at-a8.yaml
lernkarten check tests/fixtures/demo-project/broken/overflows-only-at-a8.yaml --grid a8
```

The first must print **no** warning; the second **must** report the card. This
is the check that catches the FR-010 trap: if the grid reaches the compile call
but not the overflow query, the second command evaluates A7 geometry, stays
silent, and the result is wrong while the PDF is right.

```bash
lernkarten check $DEMO/*.yaml --grid a8
```

Must print **no** `WARNING` — a regression guard, **not** the trap-catcher.
Measured: zero of the 29 demo cards overflow at A8. Because they overflow at
neither grid, this command stays silent under the bug as well, so it cannot
detect it on its own.

## 6. A bad grid is refused, and writes nothing

```bash
for g in 3X4 "3 x 4" 3,4 0x4 3x0 -1x4 3x4 2x6 eight; do
  lernkarten build $DEMO/*.yaml -o /tmp/should-not-exist.pdf --grid "$g"
  echo "  exit=$?"
done
test ! -f /tmp/should-not-exist.pdf && echo "no PDF written"
```

Every one exits non-zero. `3x4` and `2x6` are *well-formed but unsupported* and
must be refused with a message listing `2x4 (A7)` and `4x4 (A8)`. Nothing is
written. That is SC-004.

## 7. The deck declares its own size

```bash
GRIDS=tests/fixtures/demo-project/grids
lernkarten build $GRIDS/tides-a8.yaml -o /tmp/declared.pdf            # deck says a8
lernkarten build $GRIDS/tides-a8.yaml -o /tmp/override.pdf --grid a7  # flag wins
```

Note the deck lives in `grids/`, **not** in `$DEMO`. A deck declaring a grid must
stay out of the directory `tests/test_e2e.py` globs, or every unflagged demo
build in §1 and §3 changes size or fails on the FR-014a conflict.

The first uses A8 with no flag; the second is A7 despite the deck. Then the
conflict case:

```bash
lernkarten build <two decks declaring different grids> -o /tmp/x.pdf
```

Exits non-zero, naming **both** files and **both** values. With `--grid` added
it succeeds. That is SC-008.

## 8. The four gates

```bash
ruff check . && ruff format --check .
pytest
lernkarten check cards/example.yaml
python3 scripts/check_docs.py
```

All green. Then, once, before the PR:

```bash
LERNKARTEN_E2E=1 pytest tests/test_e2e.py
python3 scripts/check_project.py tests/fixtures/demo-project --strict
```

---

## 9. The release gate — on paper, not on screen

**This blocks the merge and cannot be automated** (SC-007).

```bash
lernkarten build $DEMO/*.yaml tests/fixtures/demo-project/grids/tides-a8.yaml \
  -o /tmp/gate.pdf --grid a8
```

The `grids/` deck is not optional here — it is the only short-label material in
the repo, and check 4 below is vacuous without it.

Print `/tmp/gate.pdf` **duplex, flip on long edge, 100 % scale** on real card
stock. Then check, in this order:

| # | Check | Pass condition |
|---|---|---|
| 1 | Registration | every back sits behind its front. A8 has 5 vertical cut lines to A7's 3, and a 0.5 mm offset costs 1.0 % of a 50 mm card against 0.5 % of a 100 mm one |
| 2 | Cutting | cuts on the crop marks yield 50 × 71.75 mm cards with nothing clipped that should not be |
| 3 | Box fit | a cut card drops into a DIN A8 Lernbox |
| 4 | Head band | a label **within the ~22-character budget** is complete and legible at 6 pt |
| 5 | Head band, over budget | an over-budget label clips cleanly at the band edge and does not disturb the layout |

**Check 4 cannot be done with the demo corpus** — all 38 shipped cards exceed
the A8 label budget, and 11 already exceed the A7 one today. Print a card with a
short label (`STATISTICS / BAYES`, 18 characters) alongside, or the check is
vacuous. See [research.md](./research.md) R4.

Record the outcome in the PR description. A screenshot of a PDF viewer is not
this check.
