# Implementation Plan: Leitner compartments

**Branch**: `feat/leitner-compartments` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-leitner-compartments/spec.md`

## Summary

Turn a printed deck into a working Leitner box by rendering three or four
coloured **divider cards** into the same PDF as the cards, remembering the
user's choice in a new project settings file, offering the box alongside, and
explaining the loop on a page. The technical approach is deliberately small:
a new leaf module holding the interval strings and the geometry, a `kind`
discriminator in the existing `cards.json`, a block-placement function in
`build_pdf.py`, and a divider renderer in `templates/`. No new dependency, no
PDF manipulation, no scheduler.

**One prerequisite came out of Phase 0**: the crop marks are drawn at the wrong
axis at `--grid a8` ([research.md R3](./research.md)), which is the only grid
this feature supports. That is a shipped bug and is fixed first, on its own
branch.

**Revised 2026-09-07** after the cross-model review returned NOT READY. The
divider is no longer a grid cell: adjacent cells share a cut line and two
colours cannot both bleed across it ([research.md R1](./research.md), superseded
section, and [R6](./research.md)). Dividers are now free-placed as a block. That
also removed the `--margin 0` fallback and the "row above must be card-free"
rule, and it added FR-006b — the block needs cut marks of its own, because it
sits outside the grid the sheet's crop marks describe.

## Technical Context

Unchanged from the project defaults in the template — this feature moves none of
them. Python `>=3.12`, Typst for the card and the press sheet, `pyyaml==6.0.3`
as the only runtime dependency, pytest with test-first mandatory, ruff at line
length 100, the engine pinned by SHA-256 across six platform pairs, Windows /
macOS / Linux as equals.

**What this feature adds to that context**: nothing. It is entirely inside the
deterministic half plus one advisory sentence in a skill.

## Dependency Decisions

**No dependency change.**

### Reuse check (constitution III)

**Is anything being hand-rolled here?** No.

- Rendering the divider is Typst — the engine already pinned by Principle XV.
- Reading and writing `lernkarten.yaml` is `scripts/yamlio.py` over PyYAML, the
  project's existing runtime dependency.
- `output/box.pdf` is `shutil.copyfile`. This is exactly why the spec refuses to
  merge the box into the card PDF: merging needs a PDF library, copying needs
  one standard-library call. Constitution III asks whether a library should do
  the job; here the standard library already does.

The vetting tables are deleted, as the template instructs when nothing is added.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 design — see the second
column.*

| # | Gate | Pass? | Post-design |
|---|---|---|---|
| I | Halves coupled only through the file formats | [x] | Still [x]. None of the six formats changes. `lernkarten.yaml` is a **seventh** artifact, outside the Principle I table by design — it holds choices, never content. |
| II | **(GATED)** No new dependency; any binary self-fetching or optional | [x] | Still [x]. Nothing added; see *Dependency Decisions*. |
| III | **(GATED)** Nothing hand-rolled that a library does | [x] | Still [x]. |
| IV | **(GATED)** Vetting table for every new dependency | [x] | n/a — no new dependency. |
| V | Code lands in an existing module where one fits | [x] | Still [x], with one new file justified below. |
| VI | Imports acyclic; format reader and engine locator stay leaves | [x] | Still [x]. `leitner` is a new **leaf**; `settings` sits above `yamlio`; `yamlio` and `engine` are untouched. **The constitution's own graph is stale** (it omits `cardid` and `figures`) — T012 asserts the real one and the table is corrected separately. See [research.md R2](./research.md). |
| VII | **(GATED)** No user content committed | [x] | Still [x]. `lernkarten.yaml` is user content and joins `.gitignore` in the same commit that first writes it. |
| VIII | No binaries committed | [x] | Still [x]. The divider has a Typst source. `assets/card-box.pdf` is copied, never regenerated or replaced. |
| IX | Typst sources edited, never generated files | [x] | Still [x]. |
| X | Skill frontmatter valid | [x] | Still [x] — `skills/print/SKILL.md` gains body text, not frontmatter. |
| XI | **(NON-WAIVABLE)** Everything tested first, red on the assertion | [x] | **Was [ ] after the review** — five 🔴 tasks could not fail *on their assertion* (a subprocess exiting 2 on an unknown flag is not red). Re-ordered in the reworked task list; see [research.md R7](./research.md) for the `KeyError` class this also prevents. See *The two halves* for which assertion goes red first, and the spec's *Testability note on run output* for why the advisory lines are pytest cases and not checklist items. |
| XII | The four gates pass; ruff not loosened | [x] | Still [x]. |
| XIII | English throughout | [x] | Still [x]. |
| XIV | Branch `<prefix>/<short-kebab-name>`; `main` untouched | [x] | `feat/leitner-compartments`, and `fix/cropmarks-sheet-axis` for the prerequisite. |
| XV | Engine version unchanged | [x] | Still [x]. |
| XVI | `docs/design.md` read; colour doubled by shape; no type shrunk | [x] | Still [x] — and it gains a section. See *Design amendment* below. |
| XVII | Card style and Typst escaping respected | [x] | n/a for dividers: they carry no user text and no Typst markup from a card file. |

**Open-item check**: this feature does not touch the constitution's one open item
(dependencies pinned by version rather than by hash). It adds no dependency, so
it neither closes nor works around it.

### Design amendment (Principle XVI)

`docs/design.md` states a card "never fills the card […] only the two markers
and the footer box on the back carry ink area". A 4 mm border band on both faces
is more ink than that.

It is admitted as an **addition for a new artifact**, not a loosening for cards.
The reasoning goes on that page: a divider carries no user text, never moves
between compartments, and being findable at a glance is its whole function.
Colour is still doubled by shape (Principle XVI) — the oversized numeral carries
the meaning and survives a black-only photocopy; colour only makes finding it
fast. This is the second named exception on that page, beside
`assets/card-box.pdf`'s exception to Principle IX, and it is written down for
the same reason: so the next reader finds a decision rather than a violation.

## Project Structure

### Documentation (this feature)

```text
specs/008-leitner-compartments/
├── spec.md               # what and why (2 clarification sessions, 32 FRs)
├── plan.md               # this file
├── research.md           # R1 band width, R2 single source, R3 crop marks, R6 block layout, R7 cards-vs-records, R8 SC-005
├── data-model.md         # Phase 1 — cards.json `kind`, lernkarten.yaml
├── contracts/            # Phase 1 — the CLI surface and the two file shapes
├── quickstart.md         # Phase 1 — how to prove it works
├── checklists/           # spec-quality (16/16) and print/compat (41 items)
├── reviews/              # the cross-model review that reworked this plan
└── design/               # the two Claude Design exports + what in them is superseded
```

### Source code touched

```text
bin/lernkarten              # + `setup` subcommand; + --dividers / --box on `build`
scripts/
├── leitner.py              # NEW — LEAF. Interval sets, rule lines, colours, geometry constants
├── settings.py             # NEW — → yamlio. Reads/writes lernkarten.yaml (not a leaf; it sits above the format reader)
├── build_pdf.py            # → cardid, engine, yamlio, leitner, settings. Block placement, page arithmetic, advisories
├── check_docs.py           # → yamlio, leitner. Asserts docs/leitner.html cannot drift
└── check_project.py        # untouched. It reads cards/*.yaml and can never see a divider
templates/
├── divider.typ             # NEW — the divider face
└── cards.typ               # dispatches on `kind`; places the divider block and its own cut marks
skills/print/SKILL.md       # relays the advisory, offers `lernkarten setup`
docs/
├── leitner.html            # NEW — the method page, hand-authored
├── index.html              # + one link
├── design.md               # + the divider section (see Design amendment)
└── testing.md              # + the three physical checks, named
.gitignore                  # + lernkarten.yaml
tests/
├── test_build_pdf.py       # unit: placement, page arithmetic, band geometry
├── test_settings.py        # NEW — unit: read, write, unknown key, invalid value
├── test_e2e.py             # the PDF taken apart; the advisory lines on stdout
└── test_check_project.py   # dividers are not counted as cards
```

**Structure Decision**: two new modules, and constitution V asks why an existing
one did not fit.

- **`scripts/leitner.py`** could have lived in `build_pdf.py`. It does not,
  because `check_docs.py` has to read the same strings, and importing
  `build_pdf` there would pull `engine` into the docs gate's import path — a
  gate that today runs without ever touching the engine. A leaf of plain data is
  cheaper and keeps Principle VI's graph shallow.
- **`scripts/settings.py`** could have lived in `yamlio.py`. It does not,
  because `yamlio` is the *format reader* and Principle VI names it as something
  that must stay near the bottom of the graph; giving it knowledge of a
  particular file's keys would make it a policy module. `settings` sits above it
  and knows only about `lernkarten.yaml`.

Both are leaves or near-leaves, and both get the module docstring Principle V
requires: what it does, which commands invoke it, why it exists.

### The two halves

**Model-driven work** (`skills/print/SKILL.md`): relay the build's advisory line
and offer to run `lernkarten setup`; never invent the answers, never write
`lernkarten.yaml`. The failing artifact that comes first is a check in
`scripts/check_project.py` asserting the skill body names `lernkarten setup` — in
`check_docs.py`, which owns `skills/*/SKILL.md`, not in `check_project.py`, which
validates a user's project. Thin, and honestly so, because everything else on this side is run output, which
is asserted on the deterministic side instead.

**Deterministic work** (`scripts/`, `bin/`, `templates/`): everything else. The
assertion that goes red first, per user story:

| Story | First red assertion | Module |
|---|---|---|
| prerequisite | bottom crop marks land inside the page box at A8 | `test_e2e.py` |
| US1 | `--dividers 4` on the demo deck gives 6 pages, not 4 | `test_e2e.py` |
| US1 | a divider box is `card_h + 1.5 mm` tall and `card_w` wide | `test_build_pdf.py` |
| US2 | `settings.load()` on a file with an unknown key **warns** naming file and key | `test_settings.py` |
| US3 | `--box` writes `output/box.pdf` byte-identical to the asset | `test_e2e.py` |
| US4 | `check_docs.py` fails when `docs/leitner.html` omits an interval string | `test_check_docs.py` |

**The seam**: none of the four card-facing formats. The seam this feature
introduces is `lernkarten.yaml`, and it runs the other way from the usual one —
the deterministic half owns the file and the model-driven half only reads what
the build printed.

## Phase 0: Research

Complete. See [research.md](./research.md):

- **R1** the band is 4 mm inward, 3 mm outward, derived from a 2 mm registration
  error plus a 1 mm cut error. *(Its FR-004 tightening is superseded by R6.)*
- **R2** `scripts/leitner.py` as a new leaf; strings travel in `cards.json`.
- **R3** the crop marks are on the wrong axis at A8. Verified against a real
  PDF. Fixed first, separately.
- **R4** the demo project already carries the material; no fixture added.
- **R5** no library is warranted and none is added.

### Spec changes this plan required

*(Second review pass, 2026-09-07: FR-004a added for back-page mirroring, FR-020 narrowed so write-back cannot create a file or fire on `check`, FR-012c fixed the advisory stream, and `PER_ROW` replaced by `LAYOUT`.)*

The first pass tightened FR-004 to keep the bleed off a card. The review showed
that was the wrong problem, and the spec was reworked in a second clarification
session rather than patched here. What changed, and why it is recorded in
`spec.md` rather than only in this plan: FR-003 (no direction, no fallback),
FR-004 (out of the grid), FR-006 (unconditional, own colour), FR-006b (cut marks
for the block), FR-015a, FR-020, FR-021 and SC-005.

**SC-005 in particular could not be met as written.** Byte-identity is
unachievable while the engine stamps a `CreationDate` — see
[research.md R8](./research.md). The guarantee is now `cards.json` byte-identity
plus page count, page size and placement, baselined against post-prerequisite
`main`.

## Phase 1: Design

### Ordering

```
0. fix/cropmarks-sheet-axis   ← prerequisite, own PR, own test
1. scripts/leitner.py         ← data only; nothing depends on it yet
2. templates/divider.typ      ← the face; renders from one divider record
3. cards.json `kind`          ← the discriminator; cards.typ dispatches
4. placement + page count     ← build_pdf; the FR-004 rule
5. scripts/settings.py        ← lernkarten.yaml, + .gitignore
6. bin/lernkarten setup       ← the only place that asks
7. --box                      ← the copy and the stock advisory
8. docs/leitner.html          ← the page, + the check_docs assertion
9. skills/print/SKILL.md      ← the relay
10. docs/design.md, docs/testing.md
```

Steps 1–4 are the artifact and are independently shippable: with them, a user
who types `--dividers 4` gets working dividers and nothing else changes. Steps
5–7 remove the friction, 8–10 explain and document. That ordering matches the
spec's P1 / P2 / P3.

### Geometry, in one place

All of it lives in `scripts/leitner.py` as constants, so `build_pdf` and the
tests read the same numbers and `templates/divider.typ` receives them:

| Constant | Value | Source |
|---|---|---|
| `GROWTH_MM` | 1.5 | box clearance: 52 mm inside vs 50 mm card |
| `BAND_MM` | 4.0 | research R1 — 2 mm registration + 1 mm cut, rounded up |
| `BLEED_MM` | 3.0 | research R1 — the floor; the block's gaps give it room unconditionally |
| `GAP_MM` | 8.0 | research R6 — `2 × BLEED_MM` plus 2 mm of cut tolerance, **cut line to cut line** |
| `LAYOUT` | `{3: (3,), 4: (2, 2)}` | research R6 — a table, not a maximum. `4 × 71.75 = 287.00` is exactly the A8 print width, so four cannot share a row; three can |
| `COLOURS` | `#c2251b #f0c000 #0a3f8f #141414` | `docs/design.md` brand order |
| `INTERVALS[3]` | daily · every 3 days · every 2 weeks | FR-017a |
| `INTERVALS[4]` | daily · every 2 days · weekly · every 2 weeks | FR-017a |
| `RULES` | `new + wrong cards` / `moved up from <n-1>` / `right -> retire` | FR-017b |

**Nothing collapses at `margin == 0` any more.** That fallback existed because
the growth borrowed the page margin and the bleed had nowhere else to go. A
free-placed block reserves its own room and bleeds into its own gaps, so a
divider is full size with a full band at every margin — one branch fewer, and
one advisory line fewer.

### Placement, as a function

`build_pdf` gains one pure function, which is what makes FR-004 a unit test
rather than an end-to-end one:

```
divider_block(card_count, count, grid, margin) -> (page_index, [(x, y), …])
```

It returns which page the block goes on and where each divider sits on it, in
millimetres from the page origin — *not* a grid index, because a divider is no
longer a grid cell. The rule is R6's: laid out by `LAYOUT`, `GAP_MM` between and
around, in the free height below the cards when it fits, on a further page when
it does not.

**Cards and records stay two separate lists** ([research.md R7](./research.md)).
Six places in `build_pdf.py` read a card's fields and break on a divider —
`advise_about_ids` (`:408`), `main_language` (`:423`), `payload` (`:461`),
`offending_card` (`:538`), `page_count` (`:713`) and the closing `languages` set
(`:714`). Every one takes the **card** list; only the `cards.json` writer and the
page count take the **record** list. Conflating them is how this feature would
fail with the `KeyError`-class errors Principle XI refuses to call red.

### Cut marks for the block

FR-006b. The sheet's crop marks are drawn from the grid (`cards.typ:48-61`) and
say nothing about a free-placed block. The block therefore draws its own, and
they cannot be drawn the way the existing ones are: marks come first and cells
second, in `guide` grey, so a `#141414` band would bury them. Options for the
plan to settle in implementation — draw them *after* the cells, knock them out in
paper colour, or hold the bleed clear of the arm zone.

### Contracts

See [contracts/](./contracts/): the CLI surface (`build --dividers/--box`,
`setup`), the `cards.json` record shape with its new `kind`, and the
`lernkarten.yaml` shape.

### Data model

See [data-model.md](./data-model.md).

### Validation

See [quickstart.md](./quickstart.md).

## Complexity Tracking

| Deviation | Why | Cheaper alternative rejected because |
|---|---|---|
| Dividers are placed outside the grid | two adjacent grid cells share a cut line, and two colours cannot both bleed across it | staying in the grid means every divider carries a strip of its neighbour's colour, and no band geometry fixes it |
| Two new `scripts/` modules | `check_docs` must not import `engine`; `yamlio` must not learn a file's keys | putting either in an existing module breaks Principle VI's shape for a saving of one file |
| A prerequisite bug fix on another branch | The crop marks are wrong at A8 today, independently of this feature | folding it in buries a user-facing fix behind four phases of feature work |
| An amendment to the ink rule in `docs/design.md` | A divider needs an edge you can see | a hairline rule fails the R1 arithmetic; no colour at all loses the entire point of a divider |
