# Implementation Plan: Configurable press-sheet grid

**Branch**: `feat/card-grid` | **Date**: 2026-08-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-card-grid/spec.md`

## Summary

Make the A4 press sheet carry either 8 cards (2 × 4 = DIN A7, today's default) or
16 (4 × 4 = DIN A8), selected with `--grid` and recorded per deck in a new
optional `grid:` key in `cards/*.yaml`. The two constants already at the top of
`templates/cards.typ` become `--input` parameters, copying the pattern `margin`
and `logo` already use; `scripts/build_pdf.py` grows a validated flag, a
three-source resolution rule and a grid-aware page count; and the model-driven
half learns to write for a declared size.

The A8 card is exactly the next standard size down, so cards still fit a
box you can buy — which is why the ticket's suggested 3 × 4 was dropped.

## Technical Context

Unchanged from the project baseline. This feature adds no language, no runtime
dependency, no dev dependency, no binary, and does not move the Python floor.
It touches Python (`scripts/`) and Typst (`templates/`), both already in use.

**One value does change**: the project has described itself as producing a fixed
105 × 74.25 mm A7 card. It now produces one of two standard sizes. See
[Constitution Check](#constitution-check) — this reaches the constitution text
itself, not only the docs.

## Dependency Decisions

**No dependency change.**

### Reuse check (constitution III)

**Is anything being hand-rolled here?** Yes, trivially: parsing `"4x4"` into two
integers and mapping four alias strings.

This is a legitimate Principle III exception under the principle's own wording —
"the need is a three-line slice of a library that would drag in thirty packages".
There is no library for "split two integers on an x", and `argparse` (standard
library, already used) supplies the validation hook. Nothing was rejected,
because nothing plausible was found to consider. See [research.md](./research.md) R1.

No vetting table: no dependency is being added, so constitution IV has nothing
to gate.

**Removals**: none. `CARDS_PER_PAGE` stops being a module constant but the
module stays.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-checked after Phase 1 design — see
the note under the table.*

| # | Gate | Pass? |
|---|---|---|
| I | The halves stay coupled only through the file formats | **yes** — the seam is `cards/*.yaml` and it is the only new coupling. Contract written before code: [contracts/cards-yaml-grid.md](./contracts/cards-yaml-grid.md) |
| II | **(GATED)** New dependency installs cleanly everywhere / binary self-fetching | **n/a** — none added |
| III | **(GATED)** Nothing hand-rolled that a library does | **yes** — see Reuse check above |
| IV | **(GATED)** Vetting table completed for every new dependency | **n/a** — none added |
| V | Code lands in an existing module; a new file has a reason | **yes** — `build_pdf.py`, `check_project.py`, `cards.typ`. No new file |
| VI | Import graph stays acyclic; format reader and engine stay leaves | **yes** — no import changes at all |
| VII | **(GATED)** No user content; examples stay subject-agnostic | **yes** — new fixtures are demo-project cards about tides, as the corpus already is |
| VIII | No binaries committed | **yes** — new fixtures are YAML text |
| IX | Typst sources edited, never generated files | **yes** — `templates/cards.typ` only |
| X | Skill frontmatter valid | **yes** — `skills/cards` and `skills/print` bodies change; `name` and `description` untouched |
| XI | **(NON-WAIVABLE)** Test-first, committed failing on the assertion | **yes** — ordered red list in [Phase 1](#test-plan-the-red-assertions-in-order) |
| XII | Four gates pass; ruff config not loosened | **yes** |
| XIII | English throughout | **yes** |
| XIV | Branch `<prefix>/<short-kebab-name>`; `main` untouched | **yes** — `feat/card-grid`, commits prefixed `feat:` / `test:` / `docs:` |
| XV | Engine version unchanged, or all six checksums bumped | **yes** — unchanged (0.15.1) |
| XVI | `docs/design.md` read; colour doubled; no type shrunk to fit; brand PNGs re-rendered | **read.** No colour change. `scale` stays 1.0 so no type shrinks. Brand PNGs unaffected — `faces()` is unchanged. **But see below** |
| XVII | Card style and Typst escaping rules respected | **yes** — but the *stated limits* become grid-dependent. **See below** |

### XVI and XVII need amending, not just satisfying

Both principles state A7 as *the* card size:

- **XVI**: "The card is 105 × 74.25 mm landscape (A7), three bands that never move."
- **XVII**: "Front at most ~2 lines, back at most ~6".

This feature makes each of those one of two cases. The constitution's own
Governance section says "Amendments go through a pull request like anything
else", so the amendment rides in this PR beside the `docs/design.md` and
`CLAUDE.md` edits FR-017 and FR-019 already require.

This is bookkeeping, not a change of intent. Every *rule* those principles state
survives untouched: bands that never move, colour doubled by shape, type never
shrunk to fit, a card that does not fit is reported. Only the single quoted
dimension becomes two. Recorded in [Complexity Tracking](#complexity-tracking).

**Open-item check**: this feature does not touch the one item in the
constitution's Reconciliation → Still open table (dependencies pinned by version
rather than hash). It neither closes nor works around it.

**Post-design re-check**: all rows above still hold after Phase 1. The design
added no module, no import, no dependency and no binary. The one thing Phase 0
changed was scope *inside* `check_project.py` — a third card-style check joins
the two already there — which is squarely within gate V.

## Project Structure

### Documentation (this feature)

```text
specs/003-card-grid/
├── plan.md                        # this file
├── spec.md                        # clarified, 16/16 on its checklist
├── research.md                    # Phase 0 — all measured against the real engine
├── data-model.md                  # Phase 1 — the in-process model and resolution rule
├── quickstart.md                  # Phase 1 — runnable validation, incl. the print gate
├── contracts/
│   └── cards-yaml-grid.md         # Phase 1 — the format change
├── checklists/requirements.md     # from /speckit-specify, re-validated by /speckit-clarify
└── tasks.md                       # Phase 2 — NOT created here
```

### Source code touched

```text
bin/lernkarten                     # unchanged — argv passes through already

scripts/
├── build_pdf.py                   # CHANGED — the flag, the alias table, resolution,
│                                  #   grid threaded to 5 sites, page count derived
└── check_project.py               # CHANGED — validate grid:, grid-aware MAX_FRONT /
                                   #   MAX_BACK, NEW head-band label budget check

skills/
├── cards/SKILL.md                 # CHANGED — write grid:, size text to the declared grid
└── print/SKILL.md                 # CHANGED — document --grid beside --margin / --no-logo

templates/
└── cards.typ                      # CHANGED — columns/rows from --input, defaults 2/4
                                   # card.typ UNCHANGED — faces() signature untouched

tests/
├── test_build_pdf.py              # unit: parsing, aliases, resolution, conflict
├── test_check_project.py          # the red artifact for the prompt-half change
├── test_e2e.py                    # page counts, overflow at A8, refusal, no-PDF-on-error
│                                  #   also: fix stale "31 cards" comments at lines 78, 230
└── fixtures/demo-project/
    ├── grids/                  # NEW dir: decks that declare a grid — deliberately
    │                           #   outside cards/, which tests/test_e2e.py globs
    ├── broken/                 # NEW: overflows-only-at-a8.yaml, the trap-catcher fixture
    └── cards/                  # unchanged file count; the six decks gain `grid: a7`

cards/example.yaml                 # CHANGED — show the grid: key
CLAUDE.md                          # CHANGED — per-grid card-style guidance (FR-017)
docs/design.md                     # CHANGED — press sheet is a configurable grid (FR-019)
docs/testing.md                    # CHANGED — step 15 formula, steps 17/18 per grid (FR-020)
.specify/memory/constitution.md    # CHANGED — XVI and XVII, see above
```

**Structure Decision**: no new module. Every change lands where the equivalent
existing concern already lives — the flag beside `--margin` in `build_pdf.py`,
the card-file validation beside `check_cards()` in `check_project.py`, the sheet
geometry in `cards.typ`. Constitution V is satisfied without argument because
nothing new is created.

### The two halves

**Deterministic work** (`scripts/`, `templates/`): the flag and its validation,
the alias table, the three-source resolution rule, threading the grid to all five
call sites, deriving the page count, and reading `columns`/`rows` from `--input`
in the sheet template. Covered by `tests/test_build_pdf.py` (unit) and
`tests/test_e2e.py` (behaviour through the real binary).

**Model-driven work** (`skills/`): `/cards` writes the `grid:` key and sizes its
output to the declared grid; `/print` documents the flag. Per constitution XI a
prompt change is only verifiable through a `check_project.py` check, and this
feature has three: the `grid:` value is valid, the front/back lengths are within
the *grid's* thresholds, and — new — the `TOPIC / SUBTOPIC` label is within the
grid's budget. Each gets a failing case in `tests/test_check_project.py` first.

**The seam**: `cards/*.yaml`, via the new optional `grid:` key. This is one of
the five formats in constitution I, so the change is breaking and its blast
radius is handled in full: `skills/cards`, `scripts/build_pdf.py`,
`scripts/check_project.py`, `cards/example.yaml`, `CLAUDE.md`, the demo cards,
`docs/`.

## Phase 0: Research

Complete. Full detail in [research.md](./research.md); everything was measured
against Typst 0.15.1 rather than estimated. Four findings matter to this plan,
and **two contradict the spec**:

| # | Finding | Effect |
|---|---|---|
| R1 | No library needed for grid parsing | Constitution III satisfied by the principle's own exception |
| **R2** | **Zero of the 29 demo cards overflow at A8** | **Contradicts spec.** The spec assumed some would and planned a "measure the golden set" step. Not needed — the assertion becomes the stronger, fixed "none overflow at either grid" |
| R3 | Measured capacity: front 291 → 145 chars, back 455 → 185 | Gives real numbers for the grid-aware `MAX_FRONT` (120 → 60) and `MAX_BACK` (400 → 160) |
| **R4** | **Head-band label budget is ~53 chars at A7, ~22 at A8 — and 11 of 38 shipped cards already clip at A7 today** | **Contradicts spec.** SC-007 as written ("label not clipped on the demo topics") is unachievable; the corpus has never been clip-free. Also produces the check that makes the prompt change testable |
| R5 | Demo corpus needs two new fixtures | A deck declaring `grid:`, and a second that disagrees, for FR-014 |
| R6 | The grid must reach five call sites | `overflowing()` is the dangerous one — miss it and every warning is wrong while the PDF is right, with no test failing |
| R7 | Constitution XVI and XVII state A7 as a fixed fact | Amendment rides in this PR |

### Spec corrections this plan required — applied 2026-08-19

The spec was wrong on two measured points. All three corrections below were
applied to spec.md before Phase 5 generated tasks; they are recorded here as the
reasoning behind the change, not as outstanding work:

1. **Delete** the Assumption "Some demo cards are expected to overflow at A8".
   Replace User Story 3 scenario 5 and SC-005 with: *no demo card overflows at
   either grid; `overflowing-2` is reported at both.*
2. **Restate SC-007.** The gate cannot be "the label is not clipped on the demo
   topics". It should be: a label within the ~22-character A8 budget is complete
   and legible, and an over-budget label clips cleanly without disturbing the
   layout. The demo corpus cannot demonstrate the first half — a short-label card
   must be printed alongside.
3. **Add** the pre-existing A7 label clipping (11 of 38 shipped cards) as a
   known defect this feature surfaces but does not fix. It deserves its own
   ticket.

## Phase 1: Design

### The user-facing surface

```
--grid COLSxROWS        2x4 | 4x4, or the aliases a7 | a8   (default: 2x4)
```

Error messages, which are part of the contract:

| Situation | Message must name |
|---|---|
| malformed value | the value received, and the `COLSxROWS` form expected |
| well-formed, unsupported (`3x4`, `2x6`) | the value, **and** the supported set with A-series names |
| deck value invalid | the file, the value, and the supported set |
| decks disagree, no flag | **both** files and **both** values |

In every failing case the output PDF is not written or overwritten.

### Where it is documented

`skills/print/SKILL.md` (the flag), `CLAUDE.md` (per-grid card style),
`docs/design.md` (the press sheet), `docs/testing.md` (steps 15, 17, 18),
`cards/example.yaml` (the key in situ). A doc link that does not resolve fails
`check_docs.py`, so all cross-links are relative and checked.

### Test plan: the red assertions, in order

Constitution XI is non-waivable: each assertion below is committed **failing, on
the assertion**, before the code that satisfies it. Ordered so that each one can
actually go red on its own.

| # | Test | Red assertion | File |
|---|---|---|---|
| 1 | grid parsing | `parse_grid("4x4") == (4, 4)` — function does not exist | `test_build_pdf.py` |
| 2 | aliases | `parse_grid("a8") == parse_grid("4x4")` | `test_build_pdf.py` |
| 3 | malformed refused | `parse_grid("3 x 4")` raises, message names the value | `test_build_pdf.py` |
| 4 | unsupported refused | `parse_grid("3x4")` raises, message lists `2x4` and `4x4` | `test_build_pdf.py` |
| 5 | page count derives | `pages(29, (4, 4)) == 4` and `pages(1, (4, 4)) == 2` | `test_build_pdf.py` |
| 6 | resolution precedence | flag beats deck; deck beats default; all-absent gives `(2, 4)` | `test_build_pdf.py` |
| 7 | conflict errors | two decks disagreeing, no flag → raises naming both files | `test_build_pdf.py` |
| 8 | **A8 builds 4 pages** | `pdf_pages(...) == 4` with `--grid a8` over the demo cards | `test_e2e.py` |
| 9 | **the trap-catcher** | `broken/overflows-only-at-a8.yaml` — a card that fits A7 and overflows A8 — is reported at `--grid a8` and **not** at the default | `test_e2e.py` |
| 9a | overflow still reported at both grids | `overflowing.yaml --grid a8` reports `overflowing-2` | `test_e2e.py` |
| 10 | no demo card overflows at A8 | `--grid a8` over the 29 demo cards emits no `WARNING` | `test_e2e.py` |
| 11 | default unchanged | no flag → 8 pages, identical to pre-feature output | `test_e2e.py` |
| 12 | refusal writes nothing | `--grid 2x6` exits non-zero and no PDF exists | `test_e2e.py` |
| 13 | deck-declared grid | fixture with `grid: a8` builds 4 pages with no flag | `test_e2e.py` |
| 14 | flag overrides deck | same fixture with `--grid a7` builds 8 pages | `test_e2e.py` |
| 15 | `grid:` validated | `check_project.py` errors on `grid: 3x4`, naming file and value | `test_check_project.py` |
| 16 | grid-aware length warnings | a 300-char back warns at A8, not at A7 | `test_check_project.py` |
| 17 | **label budget check** | a 40-char `TOPIC / SUBTOPIC` warns at A8 | `test_check_project.py` |

**Corrected after cross-model review.** This section first claimed tests 9a and
10 together catch the R6 trap. They do not. If `overflowing()` misses the grid
the query runs at A7, where the demo cards also do not overflow — so test 10
returns an empty set and passes on **both** the correct and the buggy path.
Re-measured to confirm. An assertion of *absence* cannot detect this.

**Test 9 is the trap-catcher**, and the only one: a card that fits A7 and
overflows A8, asserted *present* at A8 and *absent* at A7. Tests 9a and 10 are
regression guards and are worth keeping, but neither may be mistaken for the
thing that bites when the grid goes missing.

Tests 15–17 are the red artifacts for the model-driven half. Without them the
`/cards` prompt change is unverifiable and constitution XI is not met.

### What cannot be tested to an exit code

The release gate, SC-007. Registration, cutting tolerance and label legibility on
paper are judged by a person. [quickstart.md](./quickstart.md) §9 is the
procedure, with the caveat that the demo corpus cannot demonstrate an unclipped
A8 label — a short-label card must be printed alongside. The user has confirmed
they have a duplex printer and stock. This is a real step with a real owner and
it blocks the merge; it is not a footnote.

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| Amending constitution XVI and XVII | XVI, XVII | Both quote A7 as *the* card size; the feature makes it one of two | Leaving them would make the constitution contradict `docs/design.md` and `CLAUDE.md` in the same PR that changes those. Governance already provides for amendment by PR |
| A third card-style check in `check_project.py` (head-band label budget) | V, XI | It is the only red artifact available for the `/cards` prompt change, and it turns an existing silent truncation into a named warning | Shipping the prompt change with no check fails XI outright. Putting the check in a new module fails V — it belongs beside `MAX_FRONT`/`MAX_BACK` |
| A new `grids/` directory plus one `broken/` fixture | XI, V | FR-014's conflict needs two decks that disagree, and the FR-010 trap needs a card that fits A7 and overflows A8 | Keeping the declaring decks in `cards/` was rejected after cross-model review: `tests/test_e2e.py:24` globs that directory, so a deck declaring a grid there changes or breaks every unflagged demo build. `grids/` sits inside the demo project, so `CLAUDE.md`'s rule still holds |

Principle XI has no row here. It is not waivable, and this plan meets it.
