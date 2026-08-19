---
description: "Task list for feat/card-grid — configurable press-sheet grid"
---

# Tasks: Configurable press-sheet grid

**Input**: Design documents from `/specs/003-card-grid/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [contracts/cards-yaml-grid.md](./contracts/cards-yaml-grid.md)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story opens with a test task committed *failing on its assertion* before the implementation task starts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 / US4 from spec.md
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## A note on parallelism

This feature has **little real parallelism**, and the task list does not pretend otherwise. `scripts/build_pdf.py`, `scripts/check_project.py`, `tests/test_e2e.py`, `tests/test_build_pdf.py` and `tests/test_check_project.py` each take many changes, and two tasks touching one file must never run concurrently. Genuine `[P]` groups exist only where files are actually distinct: the two new fixtures, and the documentation sweep. Everything else is sequential on purpose.

## Story order

Spec priority is US1 (P1), then US2 and US3 (both P2), then US4 (P3). **US3 is scheduled before US2** even though the spec lists it second: it is the highest-risk story (the silent overflow trap), it depends only on foundational work, and US2 needs new fixtures first. Both are P2, so the order within that tier is free.

---

## Phase 1: Setup

**Purpose**: be able to verify the work, and capture the baseline SC-002 compares against.

<!-- sequential -->

- [ ] T001 `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff
- [ ] T002 `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [ ] T003 `bin/lernkarten engine --check` — confirm the typesetting engine is cached (Typst 0.15.1)
- [ ] T004 **Capture the pre-feature baseline**: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/baseline-a7.pdf` and record page count (8) and extracted text to `/tmp/baseline-a7.txt` via `pdftotext`. SC-002 asserts the post-feature no-flag build matches this. Capture it **before** any source change or the comparison is worthless.

**Checkpoint**: tests runnable, engine present, baseline recorded.

---

## Phase 2: Format Contract (Blocking)

**Purpose**: `cards/*.yaml` is one of the five formats in constitution I. Settle it before either half is written. The contract is already specified in [contracts/cards-yaml-grid.md](./contracts/cards-yaml-grid.md) — this phase makes the validator match it.

<!-- sequential -->

- [ ] T005 🔴 Add cases to `tests/test_check_project.py` for the new key: `grid: a8` accepted; `grid: 3x4` an **error** naming the file and the value and listing the supported set; `grid: eight` an error; `grid:` on an individual card an error naming the file and card index (FR-021). All fail — `check_cards()` does not look at `grid` yet
- [ ] T006 Implement `grid` validation in `check_cards()` in `scripts/check_project.py` until T005 passes. Accept `2x4` / `4x4` / `a7` / `a8` case-insensitively; absent means A7
- [ ] T007 Confirm an existing project on disk still validates untouched: `python3 scripts/check_project.py tests/fixtures/demo-project --strict` passes with no `grid:` key anywhere

**Checkpoint**: the format contract is enforced, and every deck without the key still passes.

---

## Phase 3: Foundational (Blocking — no story can start without this)

**Purpose**: the grid must exist as a value, reach the template, and reach **all five** call sites. This is where the feature's one silent failure mode is created or avoided.

<!-- sequential -->

- [ ] T008 🔴 Add unit tests to `tests/test_build_pdf.py` for grid parsing — `parse_grid("4x4") == (4, 4)`, `parse_grid("a8") == parse_grid("4x4")`, `parse_grid("2x4") == parse_grid("a7") == (2, 4)`. Fails: `parse_grid` does not exist *(plan assertions 1–2)*
- [ ] T009 🔴 Extend `tests/test_build_pdf.py` with the rejection cases — `parse_grid("3 x 4")`, `"3,4"`, `"0x4"`, `"3x0"`, `"-1x4"` raise naming the value; `parse_grid("3x4")` and `parse_grid("2x6")` raise with a message listing `2x4` and `4x4` **and** their A-series names. Fails *(plan assertions 3–4)*
- [ ] T010 Implement `parse_grid()`, the supported-set constant and the alias table in `scripts/build_pdf.py` until T008 and T009 pass. Standard library only — no dependency (constitution III; see plan.md Reuse check)
- [ ] T011 🔴 Add page-count tests to `tests/test_build_pdf.py` — `pages(29, (4, 4)) == 4`, `pages(1, (4, 4)) == 2`, `pages(29, (2, 4)) == 8`. Fails: the count is hard-wired to `CARDS_PER_PAGE = 8` *(plan assertion 5)*
- [ ] T012 Replace `CARDS_PER_PAGE` with a derived `pages(n, grid)` in `scripts/build_pdf.py` until T011 passes
- [ ] T013 **Build the `--input` list through one shared helper** in `scripts/build_pdf.py`, and have `typeset()` and `overflowing()` both call it. This is structural, not cosmetic: the two build their own lists today, and that is exactly how the grid reaches the compile call but not the overflow query (research.md R6). One helper makes the divergence impossible to reintroduce
- [ ] T014 Thread the grid through all five sites in `scripts/build_pdf.py` — `typeset()`, `overflowing()`, `offending_card()`, `report_failure()`, and the page report. Missing `overflowing()` is the silent one
- [ ] T015 Parameterise `templates/cards.typ`: read `columns` and `rows` from `sys.inputs` with defaults `2` and `4`, exactly as `margin` and `logo` already do. Everything else — `cw`, `ch`, `per-page`, the crop-mark loops `range(0, columns + 1)` / `range(0, rows + 1)`, the `sheet()` mirroring `column = columns - 1 - column`, the pagination loop — already derives and must not be touched. **`templates/card.typ` is not edited at all**
- [ ] T016 Add `--grid` to the argument parser in `scripts/build_pdf.py`, beside `--margin` and `--no-logo`. `bin/lernkarten` needs no change — argv passes straight through

**Checkpoint**: `pytest tests/test_build_pdf.py` green; the grid reaches the template and all five call sites.

---

## Phase 4: User Story 1 — Print a deck at A8 and halve the paper (Priority: P1) 🎯 MVP

**Goal**: `lernkarten build --grid a8` puts 16 cards on an A4 sheet at exactly DIN A8, halving the paper for the same deck.

**Independent Test**: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/a8.pdf --grid a8` → 4 pages, against 8 today.

<!-- sequential -->

- [ ] T017 🔴 [US1] Add an end-to-end case to `tests/test_e2e.py`: `--grid a8` over the demo cards gives `pdf_pages(...) == 4` and the summary says `4 pages, duplex`. Fails — the flag is accepted but the sheet is still 2 × 4 until T015 landed; if T015 is done this fails on the page count *(plan assertion 8)*
- [ ] T018 🔴 [US1] Add the alias case to `tests/test_e2e.py`: `--grid 4x4` produces the same page count and card geometry as `--grid a8` *(FR-002)*
- [ ] T019 🔴 [US1] Add the regression guard to `tests/test_e2e.py`: **no** `--grid` flag gives 8 pages and output matching the T004 baseline. Fails if the default drifted *(plan assertion 11, SC-002)*
- [ ] T020 [US1] Make T017–T019 pass — most of the work is already in Phase 3; this task is where the wiring is finished and the defaults proven untouched
- [ ] T021 🔴 [US1] Add the exact-dimension case to `tests/test_e2e.py`: at `--margin 0`, `--grid a7` cuts to 105 × 74.25 mm and `--grid a8` to 52.5 × 74.25 mm — DIN A7 and DIN A8 *(SC-003)*. This is the assertion that ties the feature to the box it has to fit
- [ ] T022 [US1] Make T021 pass
- [ ] T023 [US1] Confirm the card itself is untouched at A8 — reading text still 11 pt, front prompt still 14 pt, `scale` still `1.0`, `head-h` still 8.6 mm, `foot-h` still 6.2 mm. Read `docs/design.md` first (constitution XVI)
- [ ] T024 [US1] Refactor — red-green-**refactor**. Tidy the grid plumbing now it is green

**Checkpoint**: A8 builds at half the sheets; the default is provably unchanged. **This alone is a shippable increment.**

---

## Phase 5: User Story 3 — Overflow reporting survives both grids (Priority: P2)

**Goal**: a card that does not fit is reported at either grid, never silently clipped — and the report is computed against the grid actually typeset.

**Independent Test**: `bin/lernkarten check tests/fixtures/demo-project/broken/overflowing.yaml --grid a8` names `overflowing-2`.

> **Highest-risk story.** Scheduled before US2 because a defect here is invisible: the PDF is correct and every warning is wrong.

<!-- sequential -->

- [ ] T025 🔴 [US3] Add to `tests/test_e2e.py`: `overflowing.yaml` built at `--grid a8` reports `overflowing-2` by id. **Measured**: that card overflows at both grids *(plan assertion 9)*
- [ ] T026 🔴 [US3] Add to `tests/test_e2e.py`: the 29 demo cards at `--grid a8` emit **no** `WARNING`. **Measured in Phase 0**: zero demo cards overflow at A8. ⚠️ **This assertion must not be dropped as redundant with T025.** T025 passes even if `overflowing()` ignores the grid, because `overflowing-2` is reported either way. T026 is the *only* assertion that fails when the overflow query runs against A7 geometry *(plan assertion 10, FR-010)*
- [ ] T027 [US3] Make T025 and T026 pass. If T013 and T014 were done properly they already do — that is the point of the shared helper
- [ ] T028 [US3] **Prove the test bites**: temporarily remove the grid from the `overflowing()` call only, run `pytest tests/test_e2e.py`, and confirm **T026 fails and T025 still passes**. Restore. Paste the failure into the pull request. Without this step nobody knows the trap is actually covered
- [ ] T029 [US3] Confirm an overflowing card is still drawn at full 11 pt with its text clipped — reported, never rescaled (constitution XIV) *(FR-011)*

**Checkpoint**: the silent failure mode is covered by an assertion that has been *seen* to catch it.

---

## Phase 6: User Story 2 — A deck declares the size it was written for (Priority: P2)

**Goal**: a card file records the grid it was written for; `/cards` writes to that size; the flag overrides it; disagreeing decks fail loudly.

**Independent Test**: a fixture carrying `grid: a8` builds 4 pages with no flag, and 8 pages with `--grid a7`.

### Test material first

<!-- parallel-group: 1 (max 3 concurrent) -->

- [ ] T030 [P] [US2] Add `tests/fixtures/demo-project/cards/tides-a8.yaml` — a short deck carrying `grid: a8`, invented content in the existing tides idiom (constitution VII), labels within the ~22-character A8 budget so it is also the short-label sample the print gate needs
- [ ] T031 [P] [US2] Add `tests/fixtures/demo-project/broken/grid-conflict.yaml` — a deck declaring a *different* grid, so the FR-014 conflict error has something to fire against. One file cannot conflict with itself. Add a row to that folder's `README.md`

<!-- sequential -->

- [ ] T032 [US2] Update `DEMO_CARD_COUNT` in `tests/test_e2e.py` and every affected page assertion, now that the demo corpus has grown

### 🔴 Red

- [ ] T033 🔴 [US2] Add resolution tests to `tests/test_build_pdf.py`: flag beats deck; deck beats default; all-absent gives `(2, 4)`. Fails — `resolve_grid` does not exist *(plan assertion 6, FR-013)*
- [ ] T034 🔴 [US2] Add the conflict test to `tests/test_build_pdf.py`: two decks declaring different grids with no flag raises, naming **both** files **and** both values; with `--grid` given it resolves silently. Fails *(plan assertion 7, FR-014)*
- [ ] T035 🔴 [US2] Add end-to-end cases to `tests/test_e2e.py`: the `grid: a8` fixture builds 4 pages with no flag; the same fixture with `--grid a7` builds 8 pages *(plan assertions 13–14)*
- [ ] T036 🔴 [US2] Add grid-aware length cases to `tests/test_check_project.py`: a 300-character back warns at A8 but **not** at A7; the A7 thresholds are unchanged from today *(plan assertion 16, SC-002)*
- [ ] T037 🔴 [US2] Add the label-budget case to `tests/test_check_project.py`: a 40-character `TOPIC / SUBTOPIC` warns at A8; it is a **warning, not an error** (FR-023 — 11 of 38 shipped cards already exceed the A7 budget and an error would fail the gates on unrelated content) *(plan assertion 17)*

### 🟢 Green

- [ ] T038 [US2] Implement `resolve_grid()` in `scripts/build_pdf.py` until T033–T035 pass. Precedence: flag → deck key → `(2, 4)`; disagreement with no flag is an error naming every file and value
- [ ] T039 [US2] Make `MAX_FRONT` / `MAX_BACK` grid-dependent in `scripts/check_project.py` until T036 passes. A7 stays 120 / 400; A8 becomes 60 / 160. Record in a comment that these are measured (hard limits: front 291 / 145, back 455 / 185) and tunable within that range, so the next reader does not treat them as folklore
- [ ] T040 [US2] Add the head-band label-budget check to `scripts/check_project.py` until T037 passes — ~53 characters at A7, ~22 at A8, uppercase `TOPIC / SUBTOPIC`. A warning. This is also the red artifact constitution XI requires for the prompt change in T041
- [ ] T041 [US2] Update `skills/cards/SKILL.md` until T037's check passes against what it produces — write the `grid:` key, and size card text to the declared grid rather than one assumed size. Keep the frontmatter valid: `name` matches the folder, `description` names its triggers

**Checkpoint**: the seam works in both directions — the deck tells the build, and `/cards` writes for the size.

---

## Phase 7: User Story 4 — A grid the build cannot honour is refused (Priority: P3)

**Goal**: bad input is refused before anything is typeset, with a message that says what is allowed, and the user's previous output survives.

**Independent Test**: `--grid 2x6` exits non-zero, lists the supported grids, and leaves any existing PDF untouched.

<!-- sequential -->

- [ ] T042 🔴 [US4] Add to `tests/test_e2e.py`: `--grid 2x6` and `--grid 3x4` exit non-zero, the message lists `2x4 (A7)` and `4x4 (A8)`, and **no** PDF is written *(plan assertion 12, FR-003)*
- [ ] T043 🔴 [US4] Add to `tests/test_e2e.py`: with a PDF **already present** at the output path, a refused build leaves it byte-identical — not truncated, not deleted, not partially written *(FR-022)*
- [ ] T044 [US4] Make T042 and T043 pass in `scripts/build_pdf.py` — validate the grid before the engine is invoked and before the output path is opened
- [ ] T045 [US4] Confirm the malformed cases from T009 produce the same refusal behaviour end to end, not just at the unit level

**Checkpoint**: every rejection path is loud, informative and non-destructive.

---

## Phase 8: Docs, Guidance & Governance

**Purpose**: nothing in the repo may still assert that the sheet holds eight cards or that the card is 100 × 72 mm. Seven distinct files — genuinely parallel.

<!-- parallel-group: 2 (max 3 concurrent) -->

- [ ] T046 [P] Update `docs/design.md` — the press sheet is a configurable grid, A7 (2 × 4) default and A8 (4 × 4) dense, with both exact card sizes. Read it before editing (constitution XVI) *(FR-019)*
- [ ] T047 [P] Update `docs/testing.md` — step 15's page count becomes `2 × ⌈cards ÷ (columns × rows)⌉`; steps 17 and 18 become repeatable **per grid**; add the A8 print gate and the short-label caveat *(FR-020)*
- [ ] T048 [P] Update `skills/print/SKILL.md` — document `--grid` beside `--margin` and `--no-logo`, naming both grids and their A-series equivalents *(FR-018)*

<!-- parallel-group: 3 (max 3 concurrent) -->

- [ ] T049 [P] Update `CLAUDE.md` — card style per grid; stop asserting one size. State the A8 writing area is 46 % of A7's and give the per-grid line guidance *(FR-017)*
- [ ] T050 [P] Update `cards/example.yaml` — show the `grid:` key with a comment saying it is optional and defaults to A7
- [ ] T051 [P] Amend `.specify/memory/constitution.md` — principles XVI and XVII both quote A7 as *the* card size. Change **only** the quoted dimension; every rule they state (bands that never move, colour doubled by shape, type never shrunk to fit, a card that does not fit is reported) survives verbatim

<!-- sequential -->

- [ ] T052 Fix the stale comments in `tests/test_e2e.py` at lines 78 and 230 — they say "31 cards"; `DEMO_CARD_COUNT` is 29. Issue #23 inherited the wrong figure from them
- [ ] T053 Confirm every relative markdown link added in T046–T051 resolves — `scripts/check_docs.py` fails on a dead one
- [ ] T054 English throughout — code, comments, docstrings, docs, commit messages (constitution XIII)

---

## Phase 9: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

<!-- sequential -->

- [ ] T055 `ruff check . && ruff format --check .`
- [ ] T056 `pytest`
- [ ] T057 `bin/lernkarten check cards/example.yaml`
- [ ] T058 `python3 scripts/check_docs.py`
- [ ] T059 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py -v`
- [ ] T060 `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
- [ ] T061 `bin/lernkarten build cards/example.yaml --grid a8 --margin 0 --no-logo -o output/a8-borderless.pdf` — the flag composes with the existing options

---

## Phase 10: The Manual Print Gate 🚧 BLOCKS THE MERGE

**Purpose**: SC-007. Registration, cutting tolerance and label legibility cannot be judged from a PDF viewer, and no automated phase can reach them.

**Owner**: the repository maintainer, who has confirmed a duplex printer and card stock. Procedure: [quickstart.md](./quickstart.md) §9.

<!-- sequential -->

- [ ] T062 Build the gate sheet: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/gate.pdf --grid a8`. ⚠️ Include the short-label deck from T030 — **all 38 cards previously shipped in this repo exceed the ~22-character A8 label budget**, so without a short-label card the legibility check is vacuous
- [ ] T063 Print `/tmp/gate.pdf` duplex, flip on long edge, **100 % scale**, on real card stock
- [ ] T064 Check registration — every back sits behind its front. A8 has 5 vertical cut lines to A7's 3, and a 0.5 mm offset costs 1.0 % of a 50 mm card against 0.5 % of a 100 mm one
- [ ] T065 Cut on the crop marks — cards measure 50 × 71.75 mm with nothing clipped that should not be
- [ ] T066 Confirm a cut card drops into a DIN A8 Lernbox
- [ ] T067 Confirm a label **within** the ~22-character budget is complete and legible at 6 pt
- [ ] T068 Confirm an **over-budget** label clips cleanly at the band edge without disturbing the layout
- [ ] T069 Record the outcome in the pull request description. A screenshot of a PDF viewer does not satisfy this gate

**Checkpoint**: the physical artifact has been made and inspected. Only now is the feature done.

---

## Dependencies

```
Phase 1 (Setup)
   └─> Phase 2 (Format contract)  ── blocking
          └─> Phase 3 (Foundational) ── blocking, creates the grid and all five call sites
                 ├─> Phase 4  US1 (P1)  🎯 MVP — shippable alone
                 ├─> Phase 5  US3 (P2)  needs Phase 3 only
                 ├─> Phase 6  US2 (P2)  needs Phase 3; fixtures gate the e2e cases
                 └─> Phase 7  US4 (P3)  needs Phase 3 only
                        └─> Phase 8 (Docs) ─> Phase 9 (Gates) ─> Phase 10 (Print gate) 🚧
```

**Story independence**: US1, US3 and US4 each stand alone on top of Phase 3. US2 is the only one needing new test material. US3's assertions constrain nothing in US1 — they only observe it.

## Parallel opportunities

Three groups, and no more, because most work lands in five heavily-shared files:

| Group | Tasks | Files |
|---|---|---|
| 1 | T030, T031 | two new fixture files |
| 2 | T046, T047, T048 | `docs/design.md`, `docs/testing.md`, `skills/print/SKILL.md` |
| 3 | T049, T050, T051 | `CLAUDE.md`, `cards/example.yaml`, `.specify/memory/constitution.md` |

Everything else is `<!-- sequential -->`. `scripts/build_pdf.py` alone is touched by T010, T012, T013, T014, T016, T038 and T044 — those must never be dispatched concurrently.

## Implementation strategy

**MVP is Phase 1 → 4.** That delivers the whole point of the ticket: a deck printed at A8 on half the paper, with the default provably unchanged. It is shippable without US2, US3 or US4.

**Then Phase 5 (US3)** — highest risk, and cheap once Phase 3 is right. T028 in particular is the task that turns "we wrote a test" into "we know the test catches it".

**Then Phase 6 (US2)** — the seam, and the largest single chunk. **Then Phase 7 (US4)** — the polish on the error paths.

**Phase 10 is not optional and is not a formality.** It is the only check that touches the thing the feature actually produces.
