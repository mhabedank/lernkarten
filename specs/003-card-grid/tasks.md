---
description: "Task list for feat/card-grid — configurable press-sheet grid"
---

# Tasks: Configurable press-sheet grid

**Input**: Design documents from `/specs/003-card-grid/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [contracts/cards-yaml-grid.md](./contracts/cards-yaml-grid.md)

**Bugfix**: 2026-08-20 — BUG-007: 9 tasks reopened, Phase 11 added (T080–T094).

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

- [x] T001 `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff
- [x] T002 `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [x] T003 `bin/lernkarten engine --check` — confirm the typesetting engine is cached (Typst 0.15.1)
- [x] T004 **Capture the pre-feature baseline**: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/baseline-a7.pdf` and record page count (8) and extracted text to `/tmp/baseline-a7.txt` via `pdftotext`. SC-002 asserts the post-feature no-flag build matches this. Capture it **before** any source change or the comparison is worthless.

**Checkpoint**: tests runnable, engine present, baseline recorded.

---

## Phase 2: Format Contract (Blocking)

**Purpose**: `cards/*.yaml` is one of the five formats in constitution I. Settle it before either half is written. The contract is already specified in [contracts/cards-yaml-grid.md](./contracts/cards-yaml-grid.md) — this phase makes the validator match it.

<!-- sequential -->

- [x] T005 🔴 Add cases to `tests/test_check_project.py` for the new key: `grid: a8` accepted; `grid: 3x4` an **error** naming the file and the value and listing the supported set; `grid: eight` an error; `grid:` on an individual card an error naming the file and card index (FR-021). All fail — `check_cards()` does not look at `grid` yet
- [x] T006 Implement `grid` validation in `check_cards()` in `scripts/check_project.py` until T005 passes. Accept `2x4` / `4x4` / `a7` / `a8` case-insensitively; absent means A7
- [x] T007 Confirm an existing project on disk still validates untouched: `python3 scripts/check_project.py tests/fixtures/demo-project --strict` passes with no `grid:` key anywhere

**Checkpoint**: the format contract is enforced, and every deck without the key still passes.

---

## Phase 3: Foundational — pure functions only (Blocking)

**Purpose**: the grid as a *value*: parsing, aliases, rejection, page count. Nothing is wired into the build here.

> **Scoped down after cross-model review C4.** Threading and the template moved into US1's green step. Previously this phase implemented the whole feature before US1's red tests existed, so those tests could not fail when scheduled — which is not test-first, and constitution XI is not waivable.

<!-- sequential -->

- [x] T008 🔴 Add unit tests to `tests/test_build_pdf.py` for grid parsing — `parse_grid("4x4") == (4, 4)`, `parse_grid("a8") == parse_grid("4x4")`, `parse_grid("2x4") == parse_grid("a7") == (2, 4)`, case-insensitively. Fails: `parse_grid` does not exist *(assertions 1–2)*
- [x] T009 🔴 Extend `tests/test_build_pdf.py` with rejections — `"3 x 4"`, `"3,4"`, `"0x4"`, `"3x0"`, `"-1x4"` raise naming the value; `"3x4"` and `"2x6"` raise listing `2x4` and `4x4` **and** their A-series names. Fails *(assertions 3–4)*
- [x] T010 Implement `parse_grid()`, the supported-set constant and the alias table in `scripts/build_pdf.py` until T008–T009 pass. Standard library only (constitution III)
- [x] T011 🔴 Add page-count tests to `tests/test_build_pdf.py` — `pages(29, (4, 4)) == 4`, `pages(1, (4, 4)) == 2`, `pages(29, (2, 4)) == 8`. Fails: the count is hard-wired to `CARDS_PER_PAGE = 8` *(assertion 5)*
- [x] T012 Replace `CARDS_PER_PAGE` with a derived `pages(n, grid)` in `scripts/build_pdf.py` until T011 passes
- [x] T013 Confirm nothing user-visible has changed yet: `pytest` green, `bin/lernkarten build` output identical to the T004 baseline. No flag exists, so no behaviour can have moved

**Checkpoint**: the grid exists as a value with full unit coverage; the build still behaves exactly as before.

---

## Phase 4: User Story 1 — Print a deck at A8 and halve the paper (Priority: P1) 🎯 MVP

**Goal**: `lernkarten build --grid a8` puts 16 cards on an A4 sheet at DIN A8, halving the paper.

**Independent Test**: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/a8.pdf --grid a8` → 4 pages, against 8 today.

### 🔴 Red — mostly failing on `--grid` being an unknown option

> T016 is the exception: it asserts the *unchanged* default and therefore passes from birth. It is a regression guard carrying a 🔴 for grouping, not a test that can go red here. Same for T031, T032 (Phase 5) and T052, T053 (Phase 7), whose behaviour partly exists once T010/T021 land. The one assertion where red-ness is load-bearing is T030, and T034 exists precisely to *see* it fail.

<!-- sequential -->

- [x] T014 🔴 [US1] `tests/test_e2e.py`: `--grid a8` over the demo cards gives `pdf_pages(...) == 4` and the summary says `4 pages, duplex` *(assertion 8)*
- [x] T015 🔴 [US1] `tests/test_e2e.py`: `--grid 4x4` gives the same page count and geometry as `--grid a8` *(FR-002)*
- [x] T016 🔴 [US1] `tests/test_e2e.py`: **no** `--grid` gives 8 pages and output matching the T004 baseline *(assertion 11, SC-002)*
- [x] T017 🔴 [US1] `tests/test_e2e.py`: **duplex mirroring** — each footer prints the card id, so `pdftotext -layout` gives reading order per page; for every row the back page's ids must be the front's row **reversed** (0↔3, 1↔2, 2↔1, 3↔0 at A8; 0↔1 at A7) *(FR-007, US1 scenario 4)*
- [x] T018 🔴 [US1] `tests/test_e2e.py`: `bin/lernkarten check tests/fixtures/demo-project/cards/*.yaml --grid a8` exits 0 — FR-001 requires **both** subcommands to accept the flag
- [ ] T019 ⚠️ **Reopened (BUG-007)** — it is a 🔴 test **pinning the portrait dimension** — `--grid a8` cuts to 52.5 × 74.25. It passes today and must fail once FR-024 lands. Original: 🔴 [US1] `tests/test_e2e.py`: at `--margin 0`, `--grid a7` cuts to 105 × 74.25 mm and `--grid a8` to 52.5 × 74.25 mm *(SC-003)*
- [x] T020 🔴 [US1] Extend `test_the_build_help_documents_the_options` in `tests/test_e2e.py` to require `--grid` *(review W2)*

**Checkpoint**: `pytest` is red for exactly the reasons this story exists. Commit here.

### 🟢 Green

- [x] T021 [US1] Add `--grid` to the argument parser in `scripts/build_pdf.py`, beside `--margin` and `--no-logo`. `bin/lernkarten` needs no change — argv passes straight through
- [x] T022 [US1] **Build the `--input` list through one shared helper** in `scripts/build_pdf.py`, called by both `typeset()` and `overflowing()`. Structural, not cosmetic: they build their own lists today, which is exactly how the grid reaches the compile call but not the overflow query
- [x] T023 [US1] Parameterise `templates/cards.typ`: read `columns` and `rows` from `sys.inputs` with defaults `2` and `4`, as `margin` and `logo` already do. `cw`, `ch`, `per-page`, the crop-mark loops, the `sheet()` mirroring and the pagination already derive — leave the *logic* alone. **`templates/card.typ` is not edited at all**
- [x] T024 [US1] Thread the grid through all five sites in `scripts/build_pdf.py` — `typeset()`, `overflowing()`, `offending_card()`, `report_failure()`, the page report. Missing `overflowing()` is the silent one; `offending_card()`/`report_failure()` have no assertion of their own because a markup failure is grid-independent
- [x] T025 [US1] Make T014–T020 pass
- [x] T026 [US1] Update the now-stale header comments — `templates/cards.typ` says "A4 with 2 x 4 cards" and "A sheet of up to 8 cards"; the module docstring in `scripts/build_pdf.py` says "A4 with 8 cards (105 x 74.25 mm) per page" *(review W2 — T023's "leave the logic alone" must not freeze wrong comments)*
- [ ] T027 ⚠️ **Reopened (BUG-007)** — it asserts `scale` stays 1.0, which FR-025 supersedes. Original: [US1] Confirm the card is untouched at A8 — reading text still 11 pt, front prompt 14 pt, `scale` 1.0, `head-h` 8.6 mm, `foot-h` 6.2 mm. Read `docs/design.md` first (constitution XVI)
- [x] T028 [US1] Refactor — red-green-**refactor**

**Checkpoint**: A8 builds at half the sheets; the default is provably unchanged. **Shippable increment.**

---

## Phase 5: User Story 3 — Overflow reporting survives both grids (Priority: P2)

**Goal**: a card that does not fit is reported at the grid actually typeset, never silently clipped.

**Independent Test**: ~~`broken/overflows-only-at-a8.yaml` is reported at `--grid a8` and silent at the default.~~ **Inverted by BUG-007** — `broken/overflows-only-at-a7.yaml` is reported at the default and silent at `--grid a8`.

> **Reworked after cross-model review C1.** The original trap-catcher was an assertion of *absence* ("no demo card warns at A8"), which cannot detect the bug: if `overflowing()` misses the grid the query runs at A7, where the demo cards also do not overflow, so it returns an empty set on both paths. Confirmed by re-measurement. Only an assertion of *presence* works.

<!-- sequential -->

- [ ] T029 ⚠️ **Reopened (BUG-007)** — the fixture it added no longer tells the grids apart: nothing fits A7 and overflows A8 once the card scales. Replaced by T096. Original: [US3] Add `tests/fixtures/demo-project/broken/overflows-only-at-a8.yaml` — one card whose back **fits A7 and overflows A8**. Measured: a ~300-character back gives no warning at 2 × 4 and is reported at 4 × 4. Add a row to that folder's `README.md`
- [x] T030 🔴 [US3] `tests/test_e2e.py`: that fixture is reported at `--grid a8` and **not** at the default. ⚠️ **This is the only assertion that catches the FR-010 trap.** Do not merge it with T031 or T032 *(SC-005, FR-010)*
- [x] T031 🔴 [US3] `tests/test_e2e.py`: `broken/overflowing.yaml` is reported at **both** grids *(assertion 9)*
- [x] T032 🔴 [US3] `tests/test_e2e.py`: the 29 demo cards at `--grid a8` emit **no** `WARNING` — a regression guard. Measured: zero overflow at A8. It passes under the bug too, so it is **not** the trap-catcher *(assertion 10)*
- [x] T033 [US3] Make T030–T032 pass. If T022 and T024 were done properly they already do
- [x] T034 [US3] **Prove the test bites**: temporarily remove the grid from the `overflowing()` call only, run `pytest tests/test_e2e.py`, and confirm **T030 fails** while T031 and T032 still pass. Restore. Paste the failure into the pull request — without this nobody knows the trap is covered
- [x] T035 [US3] Confirm an overflowing card is still drawn at full 11 pt with its text clipped — reported, never rescaled (constitution XIV) *(FR-011)*

**Checkpoint**: the silent failure mode is covered by an assertion that has been *seen* to catch it.

---

## Phase 6: User Story 2 — A deck declares the size it was written for (Priority: P2)

**Goal**: a card file records its grid; `/cards` writes to it; the flag overrides; disagreement fails loudly.

**Independent Test**: `grids/tides-a8.yaml` (12 cards) builds 2 pages with no flag and 4 with `--grid a7`.

### Test material first

<!-- parallel-group: 1 (max 3 concurrent) -->

- [ ] T036 ⚠️ **Reopened (BUG-007)** — the twelve cards were written to a ~22-character label budget that FR-023 retires. Original: [P] [US2] Add `tests/fixtures/demo-project/grids/tides-a8.yaml` — **exactly 12 cards**, declaring `grid: a8`, invented content in the existing tides idiom (constitution VII), every label inside the ~22-character A8 budget so it doubles as the short-label sample the print gate needs. ⚠️ **`grids/`, not `cards/`** — `CARDS` in `tests/test_e2e.py:24` globs `cards/*.yaml`, so a declaring deck there would change or break every unflagged demo build *(review C2)*
- [x] T037 [P] [US2] Add `tests/fixtures/demo-project/grids/tides-a7.yaml` — declares `grid: a7`, so the FR-014 conflict has a partner. Add a `README.md` to `grids/` explaining the folder holds decks that declare a grid and is deliberately outside the globbed corpus

<!-- sequential -->

- [x] T038 [US2] Add `"grids"` to `SKIP` in `scripts/demo.py`. **Note the real mechanism**: `SKIP` is currently dead code (defined at `demo.py:33`, referenced nowhere), and `demo.copy()` is safe because it copies an explicit allowlist — `raw`, `goal.md`, `sources.yaml`, then `GENERATED = ("knowledge", "catalog", "cards")`. So `grids/` can never be copied whatever `SKIP` says; adding it is documentary, keeping the constant honest for whoever revives it. Confirm `test_the_demo_copy_is_a_valid_project`'s `== 6` card-file assertion (`tests/test_check_project.py:330`) still holds — it does, because nothing was added to `cards/` *(review C2)*

### 🔴 Red

- [x] T039 🔴 [US2] `tests/test_build_pdf.py`: resolution precedence — flag beats deck, deck beats default, all-absent gives `(2, 4)`. Fails: `resolve_grid` does not exist *(assertion 6, FR-013)*
- [x] T040 🔴 [US2] `tests/test_build_pdf.py`: two decks declaring **different** grids with no flag raises naming both files and both values; with `--grid` it resolves silently *(assertion 7, FR-014)*
- [x] T041 🔴 [US2] `tests/test_build_pdf.py`: **mixed absent and declared** — one `grid: a8` deck plus decks declaring nothing is a **conflict**, and the message distinguishes a declared value from an absent one *(FR-014a, review C2)*
- [x] T042 🔴 [US2] `tests/test_e2e.py`: `grids/tides-a8.yaml` (12 cards) builds **2** pages with no flag and **4** with `--grid a7`. ⚠️ The counts follow `2 × ⌈n ÷ per-page⌉` and constrain the fixture size: at n ≤ 8 both grids give 2 pages and the test cannot distinguish them, so 12 is the smallest round size that works *(assertions 13–14)*
- [x] T043 🔴 [US2] `tests/test_check_project.py`: a 300-character back warns at A8 but **not** at A7; the A7 thresholds are unchanged *(assertion 16, SC-002)*
- [ ] T044 ⚠️ **Reopened (BUG-007)** — it tests the head-band label warning that FR-023 retires. Original: 🔴 [US2] `tests/test_check_project.py`: a 40-character `TOPIC / SUBTOPIC` warns for an **A8** deck and **not** for an A7 one, and is a warning rather than an error *(assertion 17, FR-023)*
- [x] T045 🔴 [US2] `tests/test_check_project.py`: under `--strict`, a deck with no `grid:` key warns; without `--strict` it does not *(FR-015a — the red artifact for the `/cards` prompt change)*

### 🟢 Green

- [x] T046 [US2] Implement `resolve_grid()` in `scripts/build_pdf.py` until T039–T042 pass, and extend `load_cards()` to surface each file's declared grid — it discards top-level keys today, so FR-014's per-file error has nothing to name *(review W2)*
- [x] T047 ✅ **Closed by T086** — reverted rather than re-measured. ⚠️ **Reopened (BUG-007)** — `LIMITS` was split per grid; FR-027 makes one set cover both. Original: [US2] Make `MAX_FRONT` / `MAX_BACK` grid-dependent in `scripts/check_project.py` until T043 passes. A7 stays 120 / 400; A8 becomes 60 / 160. Comment that these are measured (hard limits 291 / 145 and 455 / 185) and tunable in that range
- [x] T048 ✅ **Closed by T087** — reverted rather than re-measured. ⚠️ **Reopened (BUG-007)** — the head-band budget has no subject once the label box scales (FR-023 retired). Original: [US2] Add the head-band label-budget check to `scripts/check_project.py` until T044 passes — **A8 decks only** (~22 characters), a warning. Scoped to A8 because `--strict` makes warnings fatal and 11 shipped cards already exceed the A7 budget *(FR-023, review C3)*
- [x] T049 [US2] Add the `--strict`-only missing-`grid:` warning to `scripts/check_project.py` until T045 passes. It must **not** fire outside `--strict` *(FR-015a)*
- [ ] T050 ⚠️ **Reopened (BUG-007)** — `grid: a7` is still right, but re-check once FR-015b's `--strict` collision dissolves. Original: [US2] Add `grid: a7` to all six decks in `tests/fixtures/demo-project/cards/` so `check_project.py … --strict` — which CI runs at `.github/workflows/ci.yml:120` and gate T070 repeats — stays green *(FR-015b, review C3)*
- [x] T051 [US2] Update `skills/cards/SKILL.md` until **both** T044's label check and T045's `--strict` check pass against what it produces — write the `grid:` key, size card text to the declared grid. Keep the frontmatter valid

**Checkpoint**: the seam works both ways, and this repo's own `--strict` gate is still green.

---

## Phase 7: User Story 4 — A grid the build cannot honour is refused (Priority: P3)

**Goal**: bad input is refused before anything is typeset, and the user's previous output survives.

**Independent Test**: `--grid 2x6` exits non-zero, lists the supported grids, leaves any existing PDF untouched.

<!-- sequential -->

- [x] T052 🔴 [US4] `tests/test_e2e.py`: `--grid 2x6` and `--grid 3x4` exit non-zero, the message lists `2x4 (A7)` and `4x4 (A8)`, and no PDF is written *(assertion 12, FR-003)*
- [x] T053 🔴 [US4] `tests/test_e2e.py`: with a PDF **already present** at the output path, a refused build leaves it byte-identical *(FR-022)*
- [x] T054 [US4] Make T052–T053 pass — validate the grid before the engine is invoked and before the output path is opened
- [x] T055 [US4] Confirm the malformed cases from T009 behave identically end to end, not just at unit level

**Checkpoint**: every rejection path is loud, informative and non-destructive.

---

## Phase 8: Docs, Guidance & Governance

**Purpose**: nothing in the repo may still assert that the sheet holds eight cards or that the card is 100 × 72 mm. Seven distinct files — genuinely parallel.

<!-- parallel-group: 2 (max 3 concurrent) -->

- [ ] T056 ⚠️ **Reopened (BUG-007)** — `docs/design.md` states the A8 card as 52.5 × 74.25 portrait. Original: [P] Update `docs/design.md` — the press sheet is a configurable grid, A7 (2 × 4) default and A8 (4 × 4) dense, with both exact card sizes. Read it before editing (constitution XVI) *(FR-019)*
- [ ] T057 ⚠️ **Reopened (BUG-007)** — `docs/testing.md` states the cut size and the per-grid walk from the portrait card. Original: [P] Update `docs/testing.md` — step 15's page count becomes `2 × ⌈cards ÷ (columns × rows)⌉`; steps 17 and 18 become repeatable **per grid**; add the A8 print gate and the short-label caveat *(FR-020)*
- [x] T058 [P] Update `skills/print/SKILL.md` — document `--grid` beside `--margin` and `--no-logo`, naming both grids and their A-series equivalents *(FR-018)*

<!-- parallel-group: 3 (max 3 concurrent) -->

- [ ] T059 ⚠️ **Reopened (BUG-007)** — `CLAUDE.md` carries the per-grid budget table FR-027 removes. Original: [P] Update `CLAUDE.md` — card style per grid; stop asserting one size. State the A8 writing area is 46 % of A7's and give the per-grid line guidance *(FR-017)*
- [x] T060 [P] Update `cards/example.yaml` — add `grid: a7` explicitly, with a comment saying the key is optional and that A7 is the default. **`a7`, not `a8`**: the example is built by gate T067 and by every user's first run, so declaring A8 would silently switch the shipped example to a different card size *(review W5)*
- [ ] T061 ⚠️ **Reopened (BUG-007)** — constitution XVI is **wrong as ratified in 2.5.0** — it states the portrait dimension. Original: [P] Amend `.specify/memory/constitution.md` — principles XVI and XVII both quote A7 as *the* card size. Change **only** the quoted dimension; every rule they state (bands that never move, colour doubled by shape, type never shrunk to fit, a card that does not fit is reported) survives verbatim

<!-- sequential -->

- [x] T062 Fix the stale comments in `tests/test_e2e.py` at lines 78 and 230 — they say "31 cards"; `DEMO_CARD_COUNT` is 29. Issue #23 inherited the wrong figure from them
- [x] T063 Confirm every relative markdown link added in T056–T061 resolves — `scripts/check_docs.py` fails on a dead one
- [x] T064 English throughout — code, comments, docstrings, docs, commit messages (constitution XIII)

---

## Phase 9: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

<!-- sequential -->

- [x] T065 `ruff check . && ruff format --check .`
- [x] T066 `pytest`
- [x] T067 `bin/lernkarten check cards/example.yaml`
- [x] T068 `python3 scripts/check_docs.py`
- [x] T069 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py -v`
- [x] T070 `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
- [ ] T071 ⚠️ **Reopened (BUG-007)** — the A8 example build must be re-run against the corrected geometry. Original: `bin/lernkarten build cards/example.yaml --grid a8 --margin 0 --no-logo -o output/a8-borderless.pdf` — the flag composes with the existing options

---

---

## Phase 11: BUG-007 — the card is landscape, and scales (Blocking)

**Bugfix**: 2026-08-20 — [BUG-007](./bugs/BUG-007.md). A8 shipped portrait in
v0.4.0 and v0.4.1. Every A-series halving flips the orientation, so the sheet
turns and the card is typeset at a uniform scale off the A7 reference. This
phase blocks the next release.

**Goal**: `--grid a8` gives a landscape 74.25 × 52.5 mm card, and an A7-legal
deck reprints at A8 without rewriting a card.

**Numbered 11 but scheduled before Phase 10**, deliberately: Phase 10 is the
manual print gate, and there is no point printing and cutting a card whose
shape is wrong. Phase 10's own tasks are reopened by this phase for the same
reason. Read the file in phase order 1–9, **11**, 10.

<!-- sequential -->

- [x] T080 🔴 [BUG-007] `tests/test_build_pdf.py`: a `sheet(grid)` helper returns `(210, 297)` for `2x4` and `(297, 210)` for `4x4`, and the derived card is **wider than tall** at both. Fails: the sheet is a constant *(FR-024, SC-010)*
- [x] T081 🔴 [BUG-007] `tests/test_build_pdf.py`: `card_scale(grid)` returns 1.0 at `2x4` and `min(cw/100, ch/71.75)` = 0.6969 at `4x4` *(FR-025)*
- [x] T082 [BUG-007] Make `templates/cards.typ` take the sheet size and the scale as `--input`, add both to `engine_inputs()` so the compile *and* the overflow query receive them (the FR-010 seam), and implement `sheet()`/`card_scale()` in `scripts/build_pdf.py` until T080–T081 pass
- [x] T083 🔴 [BUG-007] `tests/test_e2e.py`: at `--grid a8 --margin 0` a built page measures 297 × 210 mm and a cut card 74.25 × 52.5 mm — read from the PDF's own MediaBox, not assumed *(SC-010)*
- [x] T084 🔴 [BUG-007] `tests/test_e2e.py`: a deck at A7's limits (398-character back, 116-character front) builds at `--grid a8` with **no** overflow warning. This is SC-011, and it is what "half the sheets for the same deck" requires
- [x] T085 [BUG-007] Make T083–T084 pass
- [x] T096 [BUG-007] Replace `broken/overflows-only-at-a8.yaml` with `overflows-only-at-a7.yaml` — a 507-character back, which overflows A7 and fits A8. Measured through the real command: first overflow at 500 characters at `a7` and 520 at `a8`, because the scale takes the tighter ratio and leaves ~3 % width slack. The FR-010 trap needs a card that differs *between* the grids, and the old direction cannot supply one any more. README row and `tests/test_e2e.py` updated with it
- [ ] T095 [BUG-007] Confirm FR-026 still holds under FR-025: a card too long for its *own* card is still reported through `<overflow>` and split by the author, never shrunk to rescue it. FR-025 scales the card to its grid; it must not become a licence to scale text to fit. The existing overflow tests cover the behaviour — this task is the assertion that scaling did not quietly turn into squeezing

### Undo what the portrait card justified

<!-- sequential -->

- [x] T086 [BUG-007] Revert `LIMITS` in `scripts/check_project.py` to one set — front 120, back 400 at every grid *(FR-027)*. Measured: first overflow at 500 characters at `a7` and 520 at the scaled `a8`
- [x] T087 [BUG-007] Remove `LABEL_BUDGET` and the head-band check *(FR-023 retired)*. Its premise was false twice over: the label wraps rather than truncating, and the box is proportionally identical at both grids
- [x] T088 [BUG-007] Update `tests/test_check_project.py` — the per-grid overflow case and the label-budget case go with them; keep the `--strict` missing-`grid:` case, which is unaffected
- [x] T089 [BUG-007] Retire research.md R3 and R4. R3 measured the portrait card; R4's "11 of 38 cards clip silently" is wrong — measured, a label wraps and first loses text near 200 characters, not 53

### The record

<!-- sequential -->

- [ ] T090 [BUG-007] Amend the constitution again. XVI states the portrait dimension and is **wrong as ratified in 2.5.0**. The 11 pt floor needs **scoping, not lowering**: it binds the card at its reference size, and a grid may render that card at an A-series scale. Same move as 2.4.0
- [ ] T091 [BUG-007] Re-sweep `docs/design.md`, `docs/testing.md`, `CLAUDE.md`, `skills/print/SKILL.md`, `cards/example.yaml` and the README for the portrait dimension and the per-grid budget table
- [ ] T092 [BUG-007] Rewrite `tests/fixtures/demo-project/grids/tides-a8.yaml`. Its twelve cards were written to a 22-character label budget that no longer exists; it should now carry cards that are *hard* at A8, not easy
- [ ] T093 [BUG-007] Correct the v0.4.0 and v0.4.1 release notes, which state 52.5 × 74.25 mm to anyone reading them now
- [ ] T094 🚧 [BUG-007] **Walk SC-007 on paper before the next release.** It has failed once by being deferred: a portrait card would not have survived one printed sheet. The open question is now legibility of 7.67 pt reading text on cheap paper, Greek and Cyrillic included

**Checkpoint**: a cut A8 card is landscape, an A7-legal deck reprints at A8 untouched, and nothing in the repo still states the portrait dimension.

---

## Phase 10: The Manual Print Gate 🚧 BLOCKS THE MERGE

**Purpose**: SC-007. Registration, cutting tolerance and label legibility cannot be judged from a PDF viewer, and no automated phase can reach them.

**Owner**: the repository maintainer, who has confirmed a duplex printer and card stock. Procedure: [quickstart.md](./quickstart.md) §9.

> **DEFERRED 2026-08-20, by the maintainer's decision.** T073–T079 need a physical
> print run, and the next one happens when the cards are next published rather than
> on this branch's schedule. They are **not** done and are deliberately left
> unticked. What this costs: SC-007 is the one success criterion no automated phase
> can reach, so until the gate is walked, A8 registration, cutting tolerance, box
> fit and head-band legibility are *unverified on paper* — reasoned from the PDF
> only. The build sheet is reproducible at any time with T072's command, and
> `/tmp/gate.pdf` was generated from it. Treat a print-quality surprise at A8 as
> this gate reporting late rather than as a new bug.


<!-- sequential -->

- [ ] T072 ⚠️ **Reopened (BUG-007)** — the gate sheet was built on the portrait geometry, and its short-label deck answered a budget that no longer exists. Original: Build the gate sheet: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml tests/fixtures/demo-project/grids/tides-a8.yaml -o /tmp/gate.pdf --grid a8`. ⚠️ Include the short-label deck from T036 — **all 38 cards previously shipped in this repo exceed the ~22-character A8 label budget**, so without a short-label card the legibility check is vacuous
- [ ] T073 Print `/tmp/gate.pdf` duplex, flip on long edge, **100 % scale**, on real card stock
- [ ] T074 Check registration — every back sits behind its front. A8 has 5 vertical cut lines to A7's 3, and a 0.5 mm offset costs 1.0 % of a 50 mm card against 0.5 % of a 100 mm one
- [ ] T075 Cut on the crop marks — confirm **5 vertical and 5 horizontal** cut lines at A8 (3 and 5 at A7), and that cards measure 50 × 71.75 mm with nothing clipped that should not be. Deliberately manual: counting stroke objects in a PDF is brittle across engine bumps, and the property that matters is whether the cuts land right *(FR-008, analysis E2)*
- [ ] T076 Confirm a cut card drops into a DIN A8 Lernbox
- [ ] T077 Confirm a label **within** the ~22-character budget is complete and legible at 6 pt
- [ ] T078 Confirm an **over-budget** label clips cleanly at the band edge without disturbing the layout
- [ ] T079 Record the outcome in the pull request description. A screenshot of a PDF viewer does not satisfy this gate

**Checkpoint**: the physical artifact has been made and inspected. Only now is the feature done.

---

## Dependencies

```
Phase 1 (Setup)
   └─> Phase 2 (Format contract)  ── blocking
          └─> Phase 3 (Foundational — pure functions only) ── blocking
                 ├─> Phase 4  US1 (P1)  🎯 MVP — wires the grid in; shippable alone
                 │        └─> Phase 5  US3 (P2)  needs the helper + threading (T022/T024)
                 ├─> Phase 6  US2 (P2)  needs Phase 3; fixtures gate its e2e cases
                 └─> Phase 7  US4 (P3)  needs T021 (the flag) only
                        └─> Phase 8 (Docs) ─> Phase 9 (Gates) ─> Phase 10 (Print gate) 🚧
```

**Why Phase 5 now depends on Phase 4**: the threading tasks moved out of Foundational into US1's green step (review C4), so US3 can only be exercised once T022 and T024 have landed. US2 and US4 still stand on Phase 3 alone.

## Parallel opportunities

Three groups, and no more, because most work lands in five heavily-shared files:

| Group | Tasks | Files |
|---|---|---|
| 1 | T036, T037 | `grids/tides-a8.yaml`, `grids/tides-a7.yaml` |
| 2 | T056, T057, T058 | `docs/design.md`, `docs/testing.md`, `skills/print/SKILL.md` |
| 3 | T059, T060, T061 | `CLAUDE.md`, `cards/example.yaml`, `.specify/memory/constitution.md` |

Everything else is `<!-- sequential -->`. `scripts/build_pdf.py` alone is touched by T010, T012, T021, T022, T024, T046 and T054; `scripts/check_project.py` by T006, T047, T048 and T049. Those must never be dispatched concurrently.

## Implementation strategy

**MVP is Phase 1 → 4.** That delivers the point of the ticket: a deck printed at A8 on half the paper, with the default provably unchanged. Shippable without US2, US3 or US4.

**Then Phase 5 (US3).** T030 is the one assertion that catches the feature's named highest risk, and T034 is what proves it does. Neither is optional, and neither may be merged into T031 or T032 — those pass under the bug.

**Then Phase 6 (US2)** — the seam, and the largest chunk. **Then Phase 7 (US4)** — the error paths.

**Phase 10 is not a formality.** It is the only check that touches what the feature actually produces.

### If this needs splitting

The cross-model review suggested a split, and the seam is the format contract: **PR1** = Phases 1–5 and 7 plus docs (flag, template, overflow, refusal, constitution amendment, print gate); **PR2** = Phase 6 (the `grid:` key, the `check_project` checks, `/cards`). Every design collision the review found — the mixed absent/declared semantics and both `--strict` conflicts — lives entirely in PR2, so PR1 could ship the paper saving while those are settled. Not taken, because the constitution amendment and the card-style guidance are hard to justify without the key; recorded so the option stays open.
