---
description: "Task list for feat/simplex-print-order"
---

# Tasks: Simplex print order — all fronts, then all backs

**Input**: Design documents from `/specs/004-simplex-print-order/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [contracts/](contracts/)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story below opens with test tasks, and those tests are committed *failing on their assertions* before the implementation task starts.

**Organization**: grouped by user story so each can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 — maps to the user stories in [spec.md](spec.md)
- Always name the exact file path
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

Single flat module — there is no `src/`.

- Entry point: `bin/lernkarten` (mirrored in `scripts/lernkarten`)
- Implementation: `scripts/<module>.py`
- Prompts: `skills/<name>/SKILL.md`
- Layout: `templates/cards.typ`
- Tests: `tests/test_<module>.py`
- Docs: `README.md`, `docs/workflow.md`, `docs/design.md`, `docs/testing.md`, `docs/index.html`

**Phases 2 (Dependencies) and 3 (Format Contracts) of the template are deleted**, not left empty: plan.md says *No dependency change*, and all four rows of the spec's Format Contracts table say *none*. There is nothing to do there and scaffolding would invite invented work.

---

## Phase 1: Setup

**Purpose**: get the environment able to verify the work.

- [X] T001 [P] `python3 -m pip install --user -r requirements-dev.txt` — pytest, ruff, pillow, pyyaml
- [X] T002 [P] `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [X] T003 [P] `python3 scripts/make_testdata.py` — the binary test material is not committed, and a full `pytest` run wants it present
- [X] T004 [P] `bin/lernkarten engine --check` — confirm the typesetting engine, or let the first build fetch it
- [X] T005 [P] Confirm a poppler `pdftotext` is on PATH: `pdftotext -v`. Without it every page-order test in this feature **skips** rather than fails — know which of the two you are looking at before you start
- [X] T006 Cut the branch **from `main`, not from the current checkout**: `git fetch origin && git switch -c feat/simplex-print-order origin/main`. This worktree sits on `build/release-0-4-2`; branching off it would drag the release commits into the PR.
  **Deviation, taken deliberately**: branched from `build/release-0-4-2` instead. Its one unpushed commit,
  `21871b4 docs: correct the A8 size in the build --help text`, rewrites the exact docstring paragraph T023
  edits. Branching from `main` would guarantee a conflict, and a conflicting PR in this repo runs no CI at
  all — a silent gate is worse than a slightly wider PR. Rebase onto `main` once the release lands

---

## Phase 2: Foundational (Blocking)

**Purpose**: US1's tests need to read *words with coordinates, per page* out of a PDF. `card_grid_per_page` in `tests/test_e2e.py` already does the `pdftotext -bbox-layout` call and carries both skip guards; a second copy of that would be hand-rolling inside the test suite (constitution III applies to test code too).

This phase is a **refactor under existing green coverage**, not new behaviour — so it carries no 🔴 task. The two tests that assert the guards *skip* are the safety net, and T008 is where you watch them still pass.

- [ ] T007 Extract `bbox_pages(path)` in `tests/test_e2e.py` — the `pdftotext -bbox-layout` invocation plus its two skip guards (non-zero exit / no `<page ` element), returning `[(x, y, word), …]` per page. Rewrite `card_grid_per_page` to call it and keep its id regex `[\w-]+-\d+`
- [ ] T008 `pytest tests/test_e2e.py -q` — `test_a_pdftotext_without_bbox_support_skips_instead_of_blaming_the_pdf` and `test_a_pdftotext_that_returns_bbox_xml_without_pages_also_skips` must still pass, now monkeypatching through `bbox_pages`. Green before Phase 3 starts

**Checkpoint**: the reader is shared, the existing suite is unchanged in behaviour. Commit.

---

## Phase 3: User Story 1 - A PDF a one-sided printer can actually use (Priority: P1) 🎯 MVP

**Goal**: `lernkarten build … --sides simplex` writes a PDF whose first half is every front sheet and second half every back sheet, in the same sheet order, at every grid.

**Independent Test**: `python3 bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/simplex.pdf --sides simplex` gives 8 pages; `pdftotext -f N -l N` shows only `1/2` face marks on pages 1–4 and only `2/2` on pages 5–8.

**No test material task.** The 29 demo cards already give 4 sheets at `a7` and 2 at `a8`, and a `--topic` filter cuts a 1-sheet deck. `DEMO_CARD_COUNT` does not move. Adding a fixture here would be inventing work (research.md, Decision 4).

### 🔴 Red — the tests, before any implementation

> Each must fail **on its assertion**, not on an `ImportError` or a missing file. T010–T015 fail today with `error: unrecognized arguments: --sides` (exit 2) — that is the right red for a flag that does not exist yet.

- [ ] T009 🔴 [P] [US1] `tests/test_build_pdf.py`: assert `build_pdf.SIDES == ("duplex", "simplex")` and `build_pdf.DEFAULT_SIDES == "duplex"` — red with `AttributeError`
- [ ] T010 🔴 [P] [US1] `tests/test_build_pdf.py`: `engine_inputs(5, True, DEFAULT_GRID, "simplex")` contains `--input sides=simplex`, and the `"duplex"` call contains `sides=duplex` — the default is *stated*, never implied by absence. Red with `TypeError: engine_inputs() takes 3 positional arguments but 4 were given`
- [ ] T011 [US1] `tests/test_e2e.py`: add `face_marks_per_page(path)` on top of `bbox_pages` (T007) — the set of `1/2` / `2/2` footer marks per page. A helper, not a test; no 🔴
- [ ] T012 🔴 [US1] `tests/test_e2e.py`: `--sides simplex` at `a7` → 8 pages, `face_marks_per_page` gives `{"1/2"}` for pages 1–4 and `{"2/2"}` for pages 5–8. This is SC-001 read literally off the artifact
- [ ] T013 🔴 [US1] `tests/test_e2e.py`: in the same build, `pages[4 + i]` equals `pages[i]` row-reversed for every `i` — every back sheet behind its own front (SC-002, FR-003)
- [ ] T014 🔴 [P] [US1] `tests/test_e2e.py`: `--sides simplex --grid a8` → 4 pages, `1/2` on 1–2, `2/2` on 3–4, mirrored across **four** columns
- [ ] T015 🔴 [P] [US1] `tests/test_e2e.py`: simplex and duplex builds of the same cards have the same page count, at both grids (SC-001, FR-004)
- [ ] T016 🔴 [P] [US1] `tests/test_e2e.py`: a single-sheet deck (`--topic` filtered) has an identical id-grid layout in both orders — the degenerate case where the two orders coincide (spec scenario 3)
- [ ] T017 🔴 [P] [US1] `tests/test_e2e.py`: `--sides both` exits 2, writes no PDF, and the message names both `duplex` and `simplex` (FR-005). Write this **after** T012 so it is red on the rejected *choice*, not merely on an unknown flag
- [ ] T018 🔴 [P] [US1] `tests/test_e2e.py`: `bin/lernkarten check … --sides simplex` exits 0 with `29 cards valid`, and the check line is unchanged by the flag (FR-007, spec scenario 6)

**Checkpoint**: `pytest` is red for exactly the reasons this story exists, and for no others. Commit here.

### 🟢 Green — the deterministic half

- [ ] T019 [US1] `scripts/build_pdf.py`: add `SIDES = ("duplex", "simplex")` and `DEFAULT_SIDES = "duplex"` beside `GRIDS`/`DEFAULT_GRID`, and the `--sides` argument with `choices=SIDES, default=DEFAULT_SIDES`. `argparse` gives FR-005 (exit 2, both values named, before any card file is read) for free — do not hand-roll the validation
- [ ] T020 [US1] `scripts/build_pdf.py`: widen `engine_inputs(margin, logo, grid, sides)` to emit the `sides` pair, and update **all three** call sites — `typeset()`, `offending_card()` and `overflowing()`. Pass it everywhere, including where page order cannot matter; see [contracts/engine-inputs.md](contracts/engine-inputs.md) rule 2 for why the subset rule is rejected
- [ ] T021 [US1] `templates/cards.typ`: read `sides` from `sys.inputs` with `default: "duplex"`, compute the face sequence once, and walk it with a `pagebreak()` before every face but the first. `mirror` and "is a back page" become one boolean. **Do not use `.flatten()`** — it flattens deeply and destroys the pairs; use `.fold((), (a, p) => a + p)`. Code sketch in [contracts/engine-inputs.md](contracts/engine-inputs.md)
- [ ] T022 [US1] `templates/cards.typ`: update the file's header comment — it currently states "front pages and back pages alternate" as the only behaviour, which this task makes false
- [ ] T023 [US1] `scripts/build_pdf.py`: update the module docstring (the "Fronts and backs sit on consecutive pages" paragraph). It is printed verbatim by `build --help` via `RawDescriptionHelpFormatter`, so a stale line here is a stale line in the user's terminal
- [ ] T024 [US1] Confirm `bin/lernkarten` and `scripts/lernkarten` need **no** change — they forward `argv` to `build_pdf.main()`, which is why `check` inherits the flag. T018 is the proof. The two files are mirrors; if one ever does need editing, it is one task touching both

### Refactor

- [ ] T025 [US1] Clean up now that it is green — the third step of red-green-refactor is not optional either. In particular check that the `cards.typ` page loop reads as *one* walk over a sequence, not as two branches that happen to share a body

**Checkpoint**: US1 works end to end against the demo project at both grids, and every assertion covering it was seen failing first.

---

## Phase 4: User Story 2 - The build says how to print it (Priority: P2)

**Goal**: the closing line names the print order it produced, and in simplex mode names both page ranges and the re-feed step.

**Independent Test**: `python3 bin/lernkarten build … --sides simplex` prints `(8 pages, simplex: print pages 1-4 at 100 % scale, turn the stack over on the long edge, then print pages 5-8).`; without the flag it still prints `(8 pages, duplex, flip on long edge).`

### 🔴 Red

- [ ] T026 🔴 [P] [US2] `tests/test_build_pdf.py`: `print_order_note(8, "duplex") == "duplex, flip on long edge"` — the exact string five existing e2e assertions depend on. Red with `AttributeError`
- [ ] T027 🔴 [P] [US2] `tests/test_build_pdf.py`: `print_order_note(8, "simplex")` names `pages 1-4` and `pages 5-8`, and contains `100 %` and `long edge` (FR-006)
- [ ] T028 🔴 [P] [US2] `tests/test_build_pdf.py`: `print_order_note(2, "simplex")` says `page 1` and `page 2` — **never** `pages 1-1`. A one-sheet deck is the first thing anyone tries the flag on
- [ ] T029 🔴 [US2] `tests/test_e2e.py`: the real closing line reports `8 pages, simplex`, `pages 1-4` and `pages 5-8`, and the two ranges add up to the reported page count (SC-004)

**Checkpoint**: red on four assertions about a function that does not exist. Commit.

### 🟢 Green

- [ ] T030 [US2] `scripts/build_pdf.py`: implement `print_order_note(page_count, sides)` to the strings fixed in [contracts/cli.md](contracts/cli.md), including the single-page range form
- [ ] T031 [US2] `scripts/build_pdf.py`: use it in the success line. Leave the `--check` line **verbatim** — it writes no PDF, so it has no page order to describe (FR-007)
- [ ] T032 [US2] `git diff origin/main -- tests/test_e2e.py | grep '^-' | grep 'pages, duplex'` must print nothing. SC-003 is "no existing assertion was rewritten"; rewriting one is the failure, not the fix

**Checkpoint**: both orders report themselves correctly and the duplex wording has not moved.

---

## Phase 5: User Story 3 - `/print` offers it when the printer needs it (Priority: P3)

**Goal**: the skill passes `--sides simplex` when the user says their printer prints one side, states the matching instructions, and no shipped doc can go on presenting duplex as the only way to print.

**Independent Test**: `python3 scripts/check_docs.py` — red on the repo as it stands, green once every printing instruction names the mode it belongs to.

### 🔴 Red

> The red artifact for this prompt change is a docs gate, not a `check_project.py` check: this prompt writes no file, so what goes stale is its *claim*. Same shape and same file as `check_sheet_capacity`, which exists because the last hand-run sweep let two claims ship (research.md, Decision 6).

- [ ] T033 🔴 [P] [US3] `tests/test_check_docs.py`: a temp `README.md` reading "print duplex, flip on long edge" is reported by `check_print_order`, naming the file and the phrase. Mirror the `test_a_doc_claiming_a_fixed_sheet_capacity_is_reported` monkeypatch pattern exactly. Red with `AttributeError`
- [ ] T034 🔴 [P] [US3] `tests/test_check_docs.py`: a temp doc reading "duplex, flip on long edge — or `--sides simplex` for a one-sided printer" **passes**. Without this the gate is satisfiable by deleting the word `duplex`, which is not what is wanted
- [ ] T035 🔴 [US3] `tests/test_check_docs.py`: `check_print_order` over the repository itself produces no errors. **This is the sweep, enforced** — it fails today on `README.md:128` and `:130`, `docs/workflow.md:273` and `:321`, `docs/design.md:145`, `docs/testing.md:232`, and `skills/print/SKILL.md:4` and `:65`

**Checkpoint**: eight named lines, red. Commit before touching a single doc — the list in the failure output *is* the work list for T037–T041.

### 🟢 Green — the gate

- [ ] T036 [US3] `scripts/check_docs.py`: add `check_print_order(errors)` beside `check_sheet_capacity` and call it from `main()`. Claim = a line naming `duplex` or a flip on the long edge; qualified = the same line also names `simplex`, `one-sided`, `--sides`, `two-pass` or `both orders`. Report file + phrase, same message shape as its neighbour

### 🟢 Green — the sweep

- [ ] T037 [P] [US3] `README.md` — the "Printing and cutting" section: both paths, the simplex two-pass procedure, and the note that a face-up stacker prints the back range in reverse from the print dialog
- [ ] T038 [P] [US3] `docs/workflow.md` — the print step (line ~273) and the troubleshooting row (line ~321): "front and back are offset" now has a second cause, the stack turned the wrong way between passes
- [ ] T039 [P] [US3] `docs/design.md` — the "Fronts and backs on consecutive pages" paragraph (line ~145): consecutive pages is the duplex order, one of two
- [ ] T040 [P] [US3] `docs/testing.md` — manual check 17 splits into **17a duplex** and **17b simplex**, both per grid, and the note that steps 17–19 are per grid still applies to both
- [ ] T041 [US3] `skills/print/SKILL.md` — the `--sides` row in the flags table, step 5's instructions made conditional on the mode built, and the rule for *when* to pass it (the user says their printer prints one side only). Cutting instructions are identical in both modes and must not be duplicated

### 🟢 Green — outside the gate

- [ ] T042 [US3] `skills/print/SKILL.md` frontmatter: add the simplex triggers ("one-sided printer", "print all fronts then all backs"). `name: print` is unchanged and the description must still carry the domain word `flashcard`, or `check_docs.check_skills` fails
- [ ] T043 [US3] `docs/index.html` — the duplex paragraph in the print band. **Not covered by the gate**: `markdown_files()` reads `*.md`, `docs/*.md` and `skills/*/SKILL.md` only, and `tests/test_landing_page.py` guards this file's structure, not its prose. Hand work, listed here so it is not forgotten
- [ ] T044 [US3] `python3 scripts/check_docs.py` → exit 0, and `pytest tests/test_check_docs.py tests/test_landing_page.py -q` → green

**Checkpoint**: all three stories stand on their own, and the sweep is enforced rather than remembered.

---

## Phase 6: Docs & Cross-Cutting

- [ ] T045 [P] `bin/lernkarten build --help` — read it end to end as a user. The module docstring (T023) and the `--sides` help text must agree with [contracts/cli.md](contracts/cli.md); this is the one surface where a stale sentence reaches someone who read no docs
- [ ] T046 [P] Confirm `CLAUDE.md` needs no change — no card convention and no file format moved, and FR-012 keeps `sides` out of the card schema on purpose. Say so in the PR rather than leaving it unexamined
- [ ] T047 [P] English throughout: code, comments, docstrings, docs, commit messages (constitution XIII)

---

## Phase 7: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

- [ ] T048 `ruff check .`
- [ ] T049 `ruff format --check .`
- [ ] T050 `pytest`
- [ ] T051 `bin/lernkarten check cards/example.yaml`
- [ ] T052 `python3 scripts/check_docs.py`

Once, for a change to the print path:

- [ ] T053 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py -v` — confirm the new order tests **ran** rather than skipped. A skip here proves nothing, and on a machine without poppler that is exactly what you get
- [ ] T054 `python3 scripts/check_project.py tests/fixtures/demo-project --strict` — no artifact changed, so this is a confirmation, not a fix
- [ ] T055 [P] `bin/lernkarten build cards/example.yaml --sides simplex --margin 0 --no-logo -o output/borderless.pdf` — the flag combined with the two settings most likely to interact with page geometry
- [ ] T056 [P] `bin/lernkarten build cards/example.yaml --sides simplex --language german -o output/other-language.pdf`
- [ ] T057 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries
- [ ] T058 Push the branch and open a pull request against `main` (direct pushes are rejected by the server and by the `pre-push` hook)
- [ ] T059 Confirm the branch is `feat/simplex-print-order` and every commit subject carries a prefix from the allowed set

---

## Phase 8: By Hand

**Purpose**: what no script can judge — whether the two halves of a sheet land on top of each other when a person, rather than a printer, turns the paper. The full checklist is in `docs/testing.md`.

- [ ] T060 **17a — duplex, the regression check.** Print the no-flag build duplex, flip on long edge, 100 % scale. Every back exactly behind its front. This must *still* pass; it is FR-008 on paper
- [ ] T061 **17b — simplex.** Print pages 1–4 at 100 % scale, take the stack out, turn it over on the long edge, re-feed, print pages 5–8. Every back exactly behind its front (SC-005)
- [ ] T062 Repeat 17a and 17b at `--grid a8`. Registration is what breaks when the column count changes: a 0.5 mm offset costs 1.0 % of a 50 mm card against 0.5 % of a 100 mm one
- [ ] T063 Note which way your printer stacks. If it stacks face-up, the second pass needs reverse page order from the print dialog — confirm that route works, because the spec's Assumptions bet the `--reverse-backs` flag away on it. If it does **not** work, that is a finding, and it becomes its own feature rather than a patch to this one
- [ ] T064 **SC-007**: do 17b again using only the build's closing line and `README.md`. If you had to open the source to know which pages to print or which way to turn the stack, the closing line is not carrying its weight — go back to T030
- [ ] T065 `python3 scripts/demo.py ~/lernkarten-demo --raw`, then in a real Claude session say "my printer only prints one side" and run `/print`. The skill should pass `--sides simplex` unprompted and state the two-pass instructions (FR-009, FR-010)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: no dependencies. T001–T005 are all parallel; T006 last, so the branch is cut from a known-good `main`
- **Foundational (2)**: blocks US1's tests only. US2 and US3 do not touch the PDF reader and could start without it
- **US1 (3)**: needs Phase 2. The MVP
- **US2 (4)**: independent of US1 in code — `print_order_note` is a pure function of `(page_count, sides)` — but pointless before US1, because the line would describe an order the PDF does not have. Sequence it second
- **US3 (5)**: independent of both. The gate and the sweep could be done first; they are last because P3, and because writing the instructions is easier once you have printed something
- **Docs (6)**: after US1–US3 settle
- **Gates (7)**: last, non-negotiable
- **By Hand (8)**: after the gates pass, and needs a printer

### Within a story — the ordering that matters

1. 🔴 **All tests, seen failing on their assertions** — commit here
2. 🟢 Deterministic half, then the model-driven half
3. Refactor

Never move an implementation task above its test. That is the one rule in this file with no exception (constitution XI).

### Parallel Opportunities

| Group | Tasks | Why they are safe together |
|---|---|---|
| Setup | T001–T005 | independent commands, no shared file |
| US1 red — unit | T009, T010 | same file, different functions; write them in one sitting |
| US1 red — e2e | T014, T015, T016, T017, T018 | separate test functions, no shared state; T012 and T013 come first because they define the helper's expected shape |
| US2 red | T026, T027, T028 | three assertions on one pure function |
| US3 red | T033, T034 | temp-dir monkeypatch tests, fully isolated |
| US3 sweep | T037, T038, T039, T040 | four different files, one shared rule |
| Gates | T055, T056 | different output files |

### Not Parallel

- 🔴 and 🟢 for the same behaviour. Ever.
- T007 and anything in Phase 3 — every US1 e2e test reads through `bbox_pages`
- T041 and T042 both edit `skills/print/SKILL.md` — body and frontmatter, one file
- T036 must precede T037–T041: the gate's failure output is the work list, and a doc "fixed" before the gate exists is a doc fixed to a guess
- `bin/lernkarten` and `scripts/lernkarten` are mirrors — if either ever needs editing it is one task touching both (T024 says neither does)

---

## Notes

- **The default path is the contract.** Five existing e2e assertions on `"N pages, duplex"` and `test_the_backs_are_mirrored_across_the_requested_columns` must pass **unmodified** at the end (T032). If one of them needs editing, FR-008 broke and the fix is in the code, not in the test.
- **A skip is not a pass.** Every page-order test skips without a poppler `pdftotext`, and GitHub's windows-latest carries one that takes `-bbox-layout` and returns nothing. T053 is where you confirm they ran.
- **The gate's failure output is the work list.** Do not sweep the docs from memory or from a grep — that is the documented cause of the two stale claims `check_sheet_capacity` now prevents.
- **No fixture, no dependency, no format change.** If a task starts to need one of the three, stop and go back to plan.md — none of them is in scope and each has a written reason.
- Never `git add -f` anything under `knowledge/`, `catalog/`, `cards/` (except `example.yaml`), `output/`, or `sources.yaml`.
- Never hand-edit `output/`. Edit the Typst source.
- Commit after each task or logical group, and always at a 🔴 checkpoint.
