---
description: "Task list for 013-side-marker-metadata"
---

# Tasks: The side marker leaves the card and becomes document metadata

**Input**: Design documents from `/specs/013-side-marker-metadata/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [contracts/face-map.md](./contracts/face-map.md)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story opens with tests, committed *failing on their assertions*, before the implementation task starts.

**Organization**: grouped by user story. The two P1 stories run in a fixed order — **US2 before US1** — because US2 builds the signal that replaces what US1 deletes. Removing the ink first would leave the print-order guarantee from #48 unverified in between. Both are P1, so this is sequencing, not a priority inversion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task serves (US1–US4)
- Always name the exact file path
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

Single flat module, no `src/`. Implementation in `scripts/*.py`, layout in `templates/*.typ`, tests in `tests/test_*.py`, the shared corpus in `tests/fixtures/demo-project/`.

---

## Phase 1: Setup

**Purpose**: get the environment able to verify the work.

- [X] T001 [P] `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff
- [X] T002 [P] `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [X] T003 [P] `bin/lernkarten engine --check` — confirm Typst 0.15.1 is cached, or let the first build fetch it
- [X] T004 [P] `python3 scripts/make_testdata.py` — needed for the full `pytest` run, not for this feature's own tests (the demo cards reference only the committed `tide-chart.svg`)
- [X] T005 `git switch -c design/side-marker-metadata` — `design/`, because the change is visible on the card

**Checkpoint**: `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` is green on an untouched tree. That is the baseline every 🔴 below is measured against.

---

## Phase 2: Dependencies

**Skipped.** plan.md says *No dependency change*: nothing is added, and `json` is stdlib. One optional tool (`pdftotext`) loses a caller, which is a deletion, not an adoption.

## Phase 3: Format Contracts

**Skipped.** plan.md and [data-model.md](./data-model.md) say *No format change*: none of the six formats moves, and `cards.json` — the payload handed to the engine — stays byte-identical. The one interface this feature adds is a diagnostic, specified in [contracts/face-map.md](./contracts/face-map.md), and it belongs to US2 below.

---

## Phase 4: User Story 2 - The print order stays verifiable (Priority: P1) 🎯 MVP

**Goal**: the front/back identity of every page is readable from a real build, exactly, without `pdftotext` — so the #48 guarantees survive the deletion in US1.

**Independent Test**: `lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/d.pdf --grid a7 --face-map /tmp/d.json` writes a map whose pages alternate front/back; the same with `--sides simplex` groups them. Neither needs a text layer. See [quickstart.md](./quickstart.md) § 1.

### Test material

- [X] T006 [US2] None needed — confirm rather than assume: the demo deck's 33 cards and the `--dividers` flag already cover every case in this story. Do **not** start a new fixture (constitution XI notes, second corpus).

### 🔴 Red — before any implementation

> Each must fail on its assertion, not on an `ImportError`. The e2e ones skip without an engine; run them with `LERNKARTEN_E2E=1`.

- [X] T007 🔴 [P] [US2] Unit test in `tests/test_build_pdf.py`: `face_map()` groups query entries by page into the shape in [contracts/face-map.md](./contracts/face-map.md) — fails, the function does not exist
- [X] T008 🔴 [P] [US2] Unit test in `tests/test_build_pdf.py`: `face_map()` pads to the page count, so a page carrying no face is listed with `"faces": []` rather than skipped — fails
- [X] T009 🔴 [US2] E2E in `tests/test_e2e.py`: `--face-map` on the demo deck writes JSON naming `sides`, `grid` and every page, ref and side; 33 cards yield 66 faces, each ref once as `front` and once as `back` — fails, the option does not exist
- [X] T010 🔴 [US2] E2E in `tests/test_e2e.py`: the map for `--sides simplex` groups the faces while the map for `--sides duplex` alternates them, on the same deck — fails. **This is the R3 trap**: a face query built without passing `sides` satisfies every other assertion in this phase
- [X] T011 🔴 [P] [US2] E2E in `tests/test_e2e.py`: a build with no `--face-map` writes the PDF and nothing beside it — fails
- [X] T012 🔴 [P] [US2] E2E in `tests/test_e2e.py`: `--face-map` pointed at an unwritable path exits non-zero with a message naming the path, and no traceback — fails
- [X] T013 🔴 [P] [US2] E2E in `tests/test_e2e.py`: with `SOURCE_DATE_EPOCH` pinned in the environment, the PDF is byte-identical with and without `--face-map` — fails. The pin is required; Typst writes `/CreationDate` (research R5)
- [X] T014 🔴 [US2] E2E in `tests/test_e2e.py`: `--grid a8 --dividers 4` over `tests/fixtures/demo-project/cards/tides.yaml` yields a map whose divider-only pages are present with no faces — fails

**Checkpoint**: `pytest` is red for exactly eight reasons, all of them this story's. Commit here.

### 🟢 Green — the implementation

- [X] T015 [US2] Emit the label in `templates/card.typ`: as the first act of `face(card, back, body)`, `context [#metadata((ref: card.ref, side: …, page: here().page()))<face>]`. It goes in `face()` because that is the one place that knows which side it is laying out, and dividers never pass through it
- [X] T016 [US2] Add `face_entries(binary, workdir, margin, logo, grid, sides)` to `scripts/build_pdf.py`, modelled on `overflowing()` — **and pass `sides` to `engine_inputs()`**, with a comment at the call site saying why this query is the exception that `overflowing()`'s docstring describes (research R3)
- [X] T017 [P] [US2] Add the pure `face_map(entries, page_count)` to `scripts/build_pdf.py` — groups by page, pads to `page_count`, returns the `sides`/`grid`/`pages` object. Pure so T007–T008 need no engine
- [X] T018 [US2] Add `write_face_map(path, mapping)` to `scripts/build_pdf.py`: `json.dumps`, UTF-8, and `sys.exit(f"ERROR: cannot write the face map to {path}: …")` on `OSError` — never a traceback (T012)
- [X] T019 [US2] Add `--face-map PATH` to the parser in `scripts/build_pdf.py` with the help text from [contracts/face-map.md](./contracts/face-map.md). No change to `bin/lernkarten` or `scripts/lernkarten` — they pass arguments straight through
- [X] T020 [US2] Wire it into `main()` in `scripts/build_pdf.py`: move the page-count arithmetic (`pages(...)`, raised to `2 * (divider_page + 1)` for dividers) **above** the `with tempfile.TemporaryDirectory()` block, and write the map inside that block beside `warn_about_overflow(...)`. The workdir is gone after it, which is the whole reason this lives in the real command
- [X] T021 [US2] Confirm `--face-map` works with `--check` too (research R10) — the document is compiled either way; no special case, no refusal to explain

### Migrate the guarantee onto the new signal

> Still with the marker printed, so a mistake here is a failure and not a gap.

- [X] T022 [US2] Replace `face_marks_per_page()` in `tests/test_e2e.py` with a helper that builds with `--face-map` and reads the JSON; delete the text-layer version and its docstring about `1/2` / `2/2`
- [X] T023 [US2] Point `test_simplex_puts_every_front_before_any_back`, `test_simplex_keeps_every_back_behind_its_own_front`, `test_simplex_groups_the_faces_at_the_denser_grid_too` and `test_a_single_sheet_deck_looks_the_same_in_both_orders` in `tests/test_e2e.py` at the new helper, keeping every assertion's meaning
- [X] T024 [US2] Remove the `pdftotext` skip from the print-order path and verify by hiding it: `PATH=/usr/bin LERNKARTEN_E2E=1 pytest tests/test_e2e.py -k "simplex or print_order"` (or rename the binary) — the tests must run, not skip

### Refactor

- [X] T025 [US2] Tidy: one docstring on `face_entries()` naming the `sides` trap, one on `face_map()` naming the padding guarantee. Both are the kind of thing the next reader will otherwise get wrong

**Checkpoint**: the print order is asserted from the document metadata, by the real command, with the marker still printed. `main` would be green here.

---

## Phase 5: User Story 1 - The footer band gets quieter (Priority: P1)

**Goal**: `1/2` / `2/2` leaves the card. Which face you hold is still unmistakable — red hollow circle against yellow solid disc, hollow against solid mark box — and both survive a photocopier.

**Independent Test**: build the demo deck and read the text layer: no token matching `[12]/2` on any page, at either grid, with or without `--no-logo`, while every card id still appears twice. [quickstart.md](./quickstart.md) § 2.

### 🔴 Red

- [X] T026 🔴 [P] [US1] E2E in `tests/test_e2e.py`: no page of the demo deck carries a `[12]/2` token, at `a7` and `a8`, with and without `--no-logo` — fails, the template prints it
- [X] T027 🔴 [P] [US1] E2E in `tests/test_e2e.py`: the `·` separator appears nowhere, and each card id still appears exactly twice — fails on the separator
- [X] T028 🔴 [US1] Update `MEASURE` in `tests/test_e2e.py` to measure the bare id (`A45DK`, not `A45DK · 1/2`) and rewrite the headroom comment in `test_the_id_fits_the_box_it_is_clipped_to_by_measurement` — "room for a longer side marker" stops being a reason once there is no side marker. Expect ~52.80 pt against the 94.49 pt cap, the number `docs/design.md` already states

### 🟢 Green

- [X] T029 [US1] In `footer()` in `templates/card.typ`: delete the `side` binding and set the id block's text to the bare `card.id`. Nothing else in the band moves — the mark, the wordmark, the band height and the top rule are untouched (FR-011)
- [X] T030 [US1] Eyeball both builds against `docs/design.md`: `bin/lernkarten build cards/example.yaml -o output/cards.pdf` and the same with `--margin 0 --no-logo` — the band still reads as quiet, nothing shifted, duplex alignment intact

**Checkpoint**: the ink is gone and the print order is still proven. `pytest` green.

---

## Phase 6: User Story 3 - A card with no id leaves no smudge (Priority: P2)

**Goal**: a deck written before ids existed prints no right-hand footer block **and no vertical rule in front of it**. The band keeps its height and its top rule.

**Independent Test**: build a deck whose cards carry no `id`, with and without `--no-logo`; nothing is printed in the block, the build exits 0 with no warning. [quickstart.md](./quickstart.md) § 3.

### 🔴 Red

- [X] T031 🔴 [US3] Rewrite `test_a_card_without_an_id_prints_the_side_marker_alone` in `tests/test_e2e.py` as `…_prints_nothing_in_the_id_block`: neither `·` nor `1/2` nor `2/2` — fails, the marker is still there
- [X] T032 🔴 [P] [US3] E2E in `tests/test_e2e.py`: `NO_ID_DECK` built with `--no-logo` exits 0 with no `WARNING` on stderr — the band is empty apart from its top rule
- [X] T033 🔴 [P] [US3] E2E in `tests/test_e2e.py`: the template places the id block and its rule only under a condition on the id. This one reads `templates/card.typ` — a drawn rule is not in the text layer and this repo has no image comparison; the precedent is `test_the_template_sets_the_id_at_the_agreed_size`, and the *appearance* gets a manual row instead (T048)
- [X] T034 🔴 [P] [US3] E2E in `tests/test_e2e.py`: a deck where some cards carry an id and some do not is handled per card — the block appears on the ones that have one

### 🟢 Green

- [X] T035 [US3] In `footer()` in `templates/card.typ`: make the id box **and** the vertical rule at `dx: cw - id-w` conditional on `card.id != ""`, with `id-w` falling to `0mm` so the wordmark box takes the freed width. The band's height and top rule are unconditional
- [X] T036 [US3] Rewrite the comment at `templates/card.typ:92-95`. It explained why a separator with nothing in front of it was avoided; that reasoning is exactly what now requires the block to collapse, so it stays and says so
- [X] T037 [US3] Eyeball `--no-logo` on a deck with no ids: an empty band with one rule across the top, at both grids. This is the judgement this story exists for

**Checkpoint**: every footer state — id, no id, logo, no logo — is correct on paper and asserted where it can be.

---

## Phase 7: User Story 4 - No shipped document still claims the printed marker (Priority: P3)

**Goal**: every document describes the card as it now prints, and a gate keeps it that way. A hand-written grep let two stale claims ship once before; this is the fifth check of that shape in `check_docs.py` and it is there for the same reason.

**Independent Test**: `python3 scripts/check_docs.py` exits 0 on the repository and non-zero on a document that reintroduces the claim, naming file and line.

### 🔴 Red

- [X] T038 🔴 [P] [US4] Case in `tests/test_check_docs.py`: a synthetic doc saying the card prints `1/2` / `2/2` is reported with its file and line — fails, the check does not exist
- [X] T039 🔴 [P] [US4] Case in `tests/test_check_docs.py`: `1/2/5/8/14 cm` is **not** reported. This is `scripts/leitner.py:25` today, so a naive `\b[12]/2\b` ships a false positive on day one (research R8)
- [X] T040 🔴 [P] [US4] Case in `tests/test_check_docs.py`: a historical sentence ("the card printed `1/2` until v0.9.2") is not reported — the file's existing exemption idiom (`was`, `until`, `since v`, `no longer`) applies here too

### 🟢 Green

- [X] T041 [US4] Add `check_printed_side_marker(errors)` to `scripts/check_docs.py`: token `(?<![\d/])[12]\s*/\s*2(?![\d/])`, the historical exemption, an error naming file, line and what the card does now. Register it with the other checks
- [X] T042 [US4] Widen that check's file set to `gated_files() + sorted((ROOT / "docs").glob("*.html"))` — `markdown_files()` and `gated_files()` reach neither `docs/index.html` nor any HTML, and three facsimile cards there carry the claim (research R8)

### The documents

- [X] T043 [P] [US4] `docs/design.md`: the footer row of the band table (line ~101), the id paragraph (~112) and the no-id sentence (~123). Add the *reason* — the face was encoded three times, two of them colour-plus-shape, and the third has moved into the document. Leave line 99 alone: the header's red circle and yellow disc are still the side marker
- [X] T044 [P] [US4] `docs/workflow.md` (~309): the card description
- [X] T045 [P] [US4] `docs/index.html`: the three `card__id` values (~489, ~611, ~635) and the footer-band paragraph (~651). While editing those exact strings, give the facsimiles valid five-character Crockford ids — `example-3` and `probability-3` are the format `docs/design.md` says was replaced (spec Assumptions)
- [X] T046 [P] [US4] `docs/testing.md`: rewrite the footer row (step 23a) — the id is now the whole block, and the measured support (52.80 pt against a 92.85 pt wordmark) still holds
- [X] T047 [P] [US4] `docs/testing.md`: document `--face-map` where contributors read, including that the print-order tests no longer need `pdftotext`
- [X] T048 [P] [US4] `docs/testing.md`: add the manual row for the empty band — no ids, `--no-logo`, both grids: one rule across the top, nothing else, the band's height unchanged
- [X] T049 [P] [US4] `templates/divider.typ` (line 3): the comment says "a side marker would be false". Still true of the header marker; reword so it does not read as a reference to text the card no longer prints

**Checkpoint**: `python3 scripts/check_docs.py` green, and no document, comment or facsimile still promises the marker.

---

## Phase 8: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

- [X] T050 `ruff check .` and `ruff format --check .`
- [X] T051 `pytest`
- [X] T052 `bin/lernkarten check cards/example.yaml`
- [X] T053 `python3 scripts/check_docs.py`
- [X] T054 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py -v` — the whole module, not only the changed tests
- [X] T055 Walk [quickstart.md](./quickstart.md) end to end, all six checks
- [X] T056 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries
- [ ] T057 Push the branch and open a pull request; confirm commit subjects are prefixed (`design:`, `test:`, `docs:`)

---

## Phase 9: By Hand

**Purpose**: what no script can judge. The full checklist is in `docs/testing.md`.

- [ ] T058 Print a sheet duplex, flip on long edge, 100 % scale — each back exactly behind its front. The id block changed width; this is the check that it did not disturb the alignment
- [ ] T059 Look at the footer band as a whole, at both grids: does it still read as quiet, now that the id stands alone?
- [ ] T060 Print the no-id, `--no-logo` deck and look at the empty band — a rule with nothing behind it is the failure this feature set out to avoid
- [ ] T061 Photocopy a sheet in black only: front and back still tell themselves apart from the header marker and the footer box. This is the premise of the whole change, and the one thing that would make it wrong

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: none
- **Dependencies (2), Format Contracts (3)**: skipped — nothing to do
- **US2 (4)**: after Setup. **Blocks US1** — it builds the signal US1 deletes
- **US1 (5)**: after US2, specifically after T024. Never before
- **US3 (6)**: after US1 — the same function in `templates/card.typ`, and T035 assumes T029's edit is in place
- **US4 (7)**: after US1 and US3, because the documents describe what those two leave behind. T038–T042 (the gate and its tests) could be written earlier, but T043–T049 cannot
- **Gates (8)**: last
- **By Hand (9)**: after the gates

### Within a Story

1. 🔴 all tests, seen failing on their assertions — commit
2. 🟢 implementation
3. Refactor

Never move an implementation task above its test (constitution XI).

### Parallel Opportunities

- T001–T004 together
- T007, T008, T011, T012, T013 together — different assertions, and only T009/T010/T014 share the face-map helper they will grow
- T026 and T027 together
- T032, T033, T034 together
- T038, T039, T040 together — all in `tests/test_check_docs.py`, but independent cases
- T043–T049 all together once US1 and US3 have landed — seven different files

### Not Parallel

- 🔴 and 🟢 for the same behaviour. Ever
- T015, T029, T035, T036 — all `templates/card.typ`, and two of them the same function
- T016–T021 — all `scripts/build_pdf.py`, and T020 depends on the other four
- T022 and T023 — the same helper in the same test module
- T041 and T042 — the same new check

---

## Implementation Strategy

**MVP**: Phase 4 (US2) alone. At that point the print-order guarantee reads the document metadata instead of the printed marker, through the real command, and the card is unchanged. It is shippable on its own and it is the part that carries risk.

**Then**: US1 (two lines of Typst and three tests), US3 (the edge case that makes the deletion safe), US4 (the documents and the gate that keeps them honest).

**Stop points**: the checkpoint at the end of each phase is a place where `main` would be green. There is no half-state in which the page order is unverified.

## Notes

- The one ordering rule that is not negotiable: US2 before US1. Deleting the marker first leaves #48 unchecked, however briefly
- `--face-map` is a diagnostic, not a feature: off by default, explained in `docs/testing.md`, absent from `README.md`
- `typst query` stays deprecated-but-consistent (research R6). Migrating it and `overflowing()` to `typst eval` is a separate issue
- By `CONTRIBUTING.md` § Releases this ships as a **minor** — a flag exists that never did. The release itself is not part of this branch
- Commit at every 🔴 checkpoint. That is the artifact constitution XI asks for
