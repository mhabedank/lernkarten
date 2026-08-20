# Contract: the `--sides` option and what the build says

**Feature**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

The interface this project exposes is a command line and the sentences it
prints. Both are contracts: `skills/print/SKILL.md` reads the closing line and
repeats it to the user, `tests/test_e2e.py` asserts on it, and `docs/` quotes
it. This file is what those three have to agree on.

## The option

```text
--sides {duplex,simplex}    how the two faces of a sheet are sequenced:
                            duplex  = front, back, front, back (default) —
                                      the printer turns the sheet
                            simplex = all fronts, then all backs — you turn
                                      the stack between two print jobs
```

| Property | Value | Requirement |
|---|---|---|
| Accepted values | exactly `duplex` and `simplex` | FR-001 |
| Default | `duplex` | FR-001, FR-008 |
| Available on | `lernkarten build` **and** `lernkarten check` | FR-007 |
| Deck may declare it | **no** — there is no `sides:` key in `cards/*.yaml` | FR-012 |
| Unknown value | exit **2**, before any card file is read, naming both accepted values | FR-005 |
| Interaction with every other flag | none — `--grid`, `--margin`, `--topic`, `--subtopic`, `--language`, `--no-logo`, `--check` all behave identically | FR-007 |

`lernkarten check` accepts it because `bin/lernkarten` forwards `argv` to
`build_pdf.main()` unchanged. That is inherited, not implemented — but it is
asserted, because it is the kind of thing a refactor silently removes.

`--sides both` (or any other value) is rejected by the argument parser, which
already produces the required shape:

```console
$ lernkarten build cards/*.yaml --sides both
usage: lernkarten build [-h] ...
lernkarten build: error: argument --sides: invalid choice: 'both'
(choose from 'duplex', 'simplex')
```

Exit 2, no PDF written, both values named.

## The closing line

`build_pdf.main()` prints one line on success. The mode-dependent part is
produced by `print_order_note(page_count, sides)`.

### Duplex — unchanged, verbatim

```console
OK: 29 cards (english, german, greek, russian) -> output/cards.pdf (8 pages, duplex, flip on long edge).
```

`print_order_note(8, "duplex")` → `"duplex, flip on long edge"`.

**This string does not move.** `tests/test_e2e.py` asserts `"8 pages, duplex"`,
`"4 pages, duplex"` and `"2 pages, duplex"` in five places today, and all five
must pass unmodified after this feature (SC-003). Rewriting one of them is the
failure, not the fix.

### Simplex

```console
OK: 29 cards (english, german, greek, russian) -> output/cards.pdf (8 pages, simplex: print pages 1-4 at 100 % scale, turn the stack over on the long edge, then print pages 5-8).
```

`print_order_note(8, "simplex")` →
`"simplex: print pages 1-4 at 100 % scale, turn the stack over on the long edge, then print pages 5-8"`.

| Element | Why it is in the line | Requirement |
|---|---|---|
| the word `simplex` | so the mode is greppable and unambiguous | FR-006 |
| both page ranges | the two print jobs the user has to start; they must add up to the reported page count | FR-006, SC-004 |
| `at 100 % scale` | "fit to page" shifts fronts off their backs, and this is the one moment the user is about to open a print dialog | FR-006 |
| `turn the stack over on the long edge` | the axis the existing column mirroring assumes | FR-003 |

### Ranges of one page

A range of a single page is written `page N`, never `pages N-N`.

```text
print_order_note(2, "simplex")
→ "simplex: print page 1 at 100 % scale, turn the stack over on the long edge, then print page 2"
```

A one-sheet deck is the common case for someone trying the option out for the
first time; `pages 1-1` reads like a bug in the tool.

### `--check`

Unchanged, verbatim, in both modes — it writes no PDF, so it has no page order
to describe:

```console
OK: 29 cards valid (english, german, greek, russian), test build succeeded (8 pages).
```

The flag is accepted and inert (FR-007, spec scenario 6).

## Page counts, for reference

`N = ⌈cards ÷ (columns × rows)⌉` sheets, `2N` pages, **in both modes**.

| Deck | Grid | Sheets | Pages | Simplex ranges |
|---|---|---|---|---|
| 29 demo cards | `a7` (8 up) | 4 | 8 | `1-4`, `5-8` |
| 29 demo cards | `a8` (16 up) | 2 | 4 | `1-2`, `3-4` |
| ≤ 8 cards | `a7` | 1 | 2 | `page 1`, `page 2` |
