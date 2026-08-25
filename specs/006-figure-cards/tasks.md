---
description: "Task list for figure cards — pictures from the sources on a card"
---

# Tasks: Figure cards — pictures from the sources on a card

**Input**: Design documents from `/specs/006-figure-cards/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [contracts/](./contracts/)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story below opens with a test task, and that test is committed *failing on its assertion* before the implementation task starts.

**Organization**: grouped by user story so each can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task serves (US1–US4)
- Always name the exact file path
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

Single flat module — there is no `src/`. Entry point `bin/lernkarten`;
implementation `scripts/<module>.py`; prompts `skills/<name>/SKILL.md`; layout
`templates/card.typ`; tests `tests/test_<module>.py`; test material
`tests/fixtures/demo-project/`.

---

## Phase 1: Setup

**Purpose**: get the environment able to verify the work

- [X] T001 [P] `python3 -m pip install --user -r requirements-dev.txt` — pytest, ruff and Pillow (Pillow is load-bearing here: T044 renders PDF pages with it)
- [X] T002 [P] `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [X] T003 [P] `python3 scripts/make_testdata.py` — build the existing binary test material
- [X] T004 [P] `bin/lernkarten engine --check` — confirm typst 0.15.1; this feature does **not** bump it
- [X] T005 Create the branch: `git switch -c feat/figure-cards`
- [X] T006 Land the constitution amendment **first, on its own branch** (`/speckit-constitution`): Principle I's format table in `.specify/memory/constitution.md` gains a sixth row — `figures/<source-id>/<file>` — pictures worth showing rather than only describing; written by `/ingest`, read by the build, gitignored like `knowledge/`. This feature is checked *against* the constitution, so it cannot also be the change that widens it

---

## Phase 2: Dependencies — `pypdfium2`

**Purpose**: adopt the one dependency this feature needs, as an *optional* runtime set, with the vetting done rather than assumed.

- [X] T007 Confirm the vetting table in [plan.md](./plan.md#vetting-constitution-iv) is complete and read by a reviewer — wheels incl. `win_arm64`, released 2026-08-13, zero transitive deps, BSD-3/Apache-2.0, not a typo-squat, no advisory (constitution IV)
- [X] T008 🔴 Add `tests/test_deps.py::test_the_optional_set_is_not_installed_with_the_default_one` — asserts `deps.REQUIREMENTS` still holds exactly one entry and `deps.FIGURES` is absent from it. Fails: `FIGURES` does not exist
- [X] T009 🔴 Add `tests/test_deps.py::test_the_optional_set_gets_its_own_cache_directory` — asserts `deps.target_dir(deps.FIGURES) != deps.target_dir()`. Fails on the same missing name
- [X] T010 🔴 Add `tests/test_deps.py::test_missing_reports_the_optional_set_separately` — `deps.missing(deps.FIGURES)` names `pypdfium2` on a machine that does not have it. Fails
- [X] T011 Declare `FIGURES = [("pypdfium2==5.13.0", "pypdfium2")]` in `scripts/deps.py`, above `REQUIREMENTS`, with a one-line comment: renders a figure region off a PDF page for `/ingest`; optional, and only that
- [X] T012 Make T008–T010 pass; confirm `missing()`, `install()` and `target_dir()` need no signature change — they already take a requirement list
- [X] T013 Extend `lernkarten deps --check` in `scripts/deps.py` `main()` to report the optional set as *optional, not installed* rather than as a failure
- [X] T014 Confirm cold start is unchanged: `bin/lernkarten` must not import `figures`, and nothing in `scripts/` may import `pypdfium2` at module level
- [ ] T015 Record in the PR description that `.github/dependabot.yml` does not read `scripts/deps.py` — a pre-existing gap this pin widens, tracked against the constitution's one open item, not closed here

**Checkpoint**: the dependency is justified in writing, declared, exercised by three tests, and pays nothing at cold start.

---

## Phase 3: Format Contracts (Blocking)

**Purpose**: settle the **card schema** — the format both the MVP and the check path rest on (constitution I). The knowledge-frontmatter format is US2's and its checks live there, so that story keeps a red test of its own.

- [X] T016 The contract is written — review [contracts/cards-yaml.md](./contracts/cards-yaml.md) and fix anything the implementation contradicts, including the **validation order**: extension → inside-project → exists → engine. Order is what keeps the four causes distinguishable (FR-004)
- [X] T017 🔴 Add `tests/test_build_pdf.py::test_load_cards_carries_the_picture_keys` — a card with `front_image:`/`back_image:` comes back with both. Fails: the keys are dropped by `load_cards`
- [X] T018 🔴 [P] Add `tests/test_build_pdf.py::test_a_picture_path_resolves_against_the_project_root` — the same deck resolves identically from two working directories (R5). Fails
- [X] T019 🔴 [P] Add `tests/test_check_project.py::test_a_card_picture_must_exist_and_be_an_accepted_format` — missing path, `.tiff`, and an escaping `../` each error, naming card and face. Fails: all three accepted today
- [X] T020 🔴 [P] Add `tests/test_check_project.py::test_a_picture_key_at_the_top_level_is_an_error` — `back_image:` beside `topic:` is refused, the way a top-level `grid:` on a card already is. Fails
- [X] T021 Implement path resolution + the four-cause validation in `scripts/build_pdf.py` `load_cards()`, and mirror the rules in `scripts/check_project.py` `check_cards()` — same order, same wording. `cardid.problems_in` is the precedent for rules that must not drift between the two
- [X] T022 [P] Document the two keys in `CLAUDE.md` under **Conventions → Cards**, beside `id`, `language` and `grid` — including the accepted formats and that a path is project-relative
- [X] T023 [P] Add `assets/example-figure.svg` — a subject-agnostic three-box flow diagram. **SVG is text**, so constitution VIII (no committed binaries) is satisfied and a fresh checkout has a picture to print. `assets/` already holds four committed SVGs, so no precedent is being set
- [X] T024 [P] Add one figure card to `cards/example.yaml` with `back_image: 'assets/example-figure.svg'` — it resolves against the repo root per R5, so no `figures/` directory is needed, SC-010 becomes reachable, and the gate `bin/lernkarten check cards/*.yaml` then exercises a figure card on every CI run
- [X] T025 [P] Confirm a deck with no picture keys is untouched: `tests/test_build_pdf.py::test_a_deck_without_pictures_is_unchanged` compares `payload()` against the pre-feature shape plus two empty strings
- [X] T026 Confirm existing projects on disk still build — both keys optional, nothing renamed, no migration (SC-007)

**Checkpoint**: `python3 scripts/check_project.py tests/fixtures/demo-project --strict` passes, and both halves have a settled card contract.

---

## Phase 4: User Story 1 — A card carries a picture (P1) 🎯 MVP

**Goal**: a card file naming a picture prints it on the face that named it, at the right size, without costing a page.

**Independent Test**: `lernkarten build tests/fixtures/demo-project/cards/*.yaml -o /tmp/figures.pdf` — page count still `2 × ⌈n ÷ 8⌉`, picture on the face that named it.

### Test material first — `tests/fixtures/demo-project/`

- [X] T027 [US1] Give `tests/fixtures/demo-project/generators/tide-chart.typ` a **distinctive flat colour** that appears nowhere in the card design (`#ff00ff`; the design uses `#c2251b`, `#f0c000`, `#0a3f8f`, `#141414`, `#fbfaf6`, `#e9e5da`, `#3a3733`, `#8c8779`, `#b5b0a2`). Comment why: T044 finds the picture by looking for that colour
- [X] T028 [US1] Add a `figures/island-images/tide-chart.png` target to `scripts/make_testdata.py` and to `.gitignore` (`tests/fixtures/demo-project/figures/`) — generated, never committed (constitution VIII)
- [X] T029 [US1] Add two figure cards to `tests/fixtures/demo-project/cards/tides.yaml` — one `back_image:`, one `front_image:`, both pointing at that picture
- [X] T030 [US1] Update `DEMO_CARD_COUNT` in `tests/test_e2e.py` (29 → 31)
- [X] T031 [P] [US1] Add a figure card to `tests/fixtures/demo-project/grids/tides-a8.yaml` so the A8 path has something to render

### 🔴 Red — before any implementation

- [X] T032 🔴 [P] [US1] `tests/test_build_pdf.py::test_pictures_are_staged_content_addressed` — one picture on three cards is copied into the workdir **once**, named `fig-<sha256[:12]>.<ext>`. Fails: no staging exists
- [X] T033 🔴 [P] [US1] `tests/test_build_pdf.py::test_payload_carries_staged_names_not_project_paths` — `payload()` emits the staged file name, or `""` for a face without a picture. Fails
- [X] T034 🔴 [US1] `tests/test_e2e.py::test_a_figure_deck_builds_without_costing_a_page` — 31 cards → 8 pages. Fails (needs `LERNKARTEN_E2E=1`)
- [X] T035 🔴 [US1] `tests/test_e2e.py::test_a_picture_lands_on_the_face_that_named_it` — render page 1 and page 2 with Pillow and assert `#ff00ff` is present on the back page and absent from the front, then the mirror case for `front_image:`. Fails
- [X] T036 🔴 [US1] `tests/test_e2e.py::test_text_plus_picture_over_the_field_warns` — the existing `WARNING: card … does not fit` names the card when answer text plus the **minimum** picture height exceed the field (R1). Fails
- [X] T037 🔴 [US1] `tests/test_e2e.py::test_an_a8_deck_with_a_picture_builds` — the A8 fixture builds and the picture scales with the card. Fails
- [X] T038 🔴 [US1] `tests/test_check_project.py::test_an_a8_deck_with_pictures_is_noted_once` — one note per run, not one per card (FR-007). Fails: silent today

**Checkpoint**: `pytest` is red for exactly the reasons this story exists. **Commit here.**

### 🟢 Green — the deterministic half

- [X] T039 [US1] Implement content-addressed staging in `scripts/build_pdf.py` `typeset()`, beside the existing `shutil.copy` of `templates/*.typ` — one copy per distinct picture per run (R2)
- [X] T040 [US1] Add `front_image`/`back_image` to `payload()` in `scripts/build_pdf.py`, holding the staged name or `""` — empty string, never a missing key, for the same reason `id` is
- [X] T041 [US1] Add the once-per-run A8 note to `scripts/check_project.py` — collected during `check_cards()`, emitted after the loop

### Layout — `templates/card.typ`

> Read `docs/design.md` before touching anything visible (constitution XVI).

- [X] T042 [US1] Front face in `templates/card.typ`: prompt, then the picture below it, `fit: "contain"`. The prompt keeps 14 pt and its position
- [X] T043 [US1] Back face in `templates/card.typ`: the picture takes the `1fr` row where the note rules live; a face with a picture has **no** note rules
- [X] T044 [US1] Overflow in `templates/card.typ`: measure against a **minimum useful picture height**, not the room the picture is given — otherwise a picture squeezed to 2 mm reports "fits". Make T036 pass
- [X] T045 [US1] Verify the three bands do not move, so `assets/brand/*.typ` need no re-render — if they do move, `python3 scripts/render_brand.py` and commit the PNGs
- [X] T046 [US1] Eyeball both builds: `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml -o output/figures.pdf` and the same with `--margin 0 --no-logo`

### Refactor

- [X] T047 [US1] Clean up: staging, validation and payload should read as three separate concerns in `scripts/build_pdf.py`, not one long function

**Checkpoint**: a hand-written figure card prints correctly at both grids. This is the MVP — everything below is about *getting* the pictures and *writing* the cards.

---

## Phase 5: User Story 2 — `/ingest` decides which pictures are worth keeping (P2)

**Goal**: every picture in a source is looked at once, judged, and either copied into `figures/` or recorded as rejected.

**Independent Test**: `/ingest island-images handbook` against the scratch demo project, then `python3 scripts/check_project.py .` exits 0 and exits 1 when a kept figure is deleted.

### Test material first

- [X] T048 [P] [US2] Give `tests/fixtures/demo-project/generators/handbook.typ` a figure on page 3 **and** a logo in the page header repeated on all four pages — the keep case and the furniture case in one document (FR-013)
- [X] T049 [P] [US2] Add `tests/fixtures/demo-project/raw/field-notes/chart-notes.md` with a relative `![…](…)` link to a picture, plus its generator — the markdown-link path (FR-008)
- [X] T050 [P] [US2] Add an `<img>` to `tests/fixtures/demo-project/raw/web/index.html` and a generator for the picture it points at — the web path
- [X] T051 [US2] Wire all three new targets into `scripts/make_testdata.py` and `.gitignore`; add a row for each to `tests/fixtures/demo-project/README.md`
- [X] T052 [P] [US2] Commit `tests/fixtures/demo-project/knowledge/island-images/tide-chart.md` — a **kept** entry (`visual: chart`, `path: figures/island-images/tide-chart.png`, `caption:`) with the inline marker in the body. Without this the seven checks below only ever run against synthetic `tmp_path` projects, and `check(DEMO)` at `tests/test_check_project.py:124` passes vacuously
- [X] T053 [P] [US2] Commit `tests/fixtures/demo-project/knowledge/island-images/harbour-noticeboard.md` — a **rejected** entry (`visual: none`, `why:`), so the demo exercises both branches of the verdict

### 🔴 Red — `scripts/figures.py` (deterministic)

- [X] T054 🔴 [P] [US2] `tests/test_figures.py::test_extract_reports_a_manifest` — `extract` on the handbook PDF prints the JSON shape in [contracts/figures-cli.md](./contracts/figures-cli.md). Fails: no module
- [X] T055 🔴 [P] [US2] `tests/test_figures.py::test_a_picture_repeated_on_every_page_is_offered_once` — the header logo appears once with `repeated_on: 4`. Fails
- [X] T056 🔴 [P] [US2] `tests/test_figures.py::test_extract_without_pypdfium2_exits_three` — monkeypatch the import away; exit code 3, one stderr line naming the document, **no traceback** (FR-018). Fails
- [X] T057 🔴 [P] [US2] `tests/test_figures.py::test_fetch_uses_the_standard_library` — `fetch` pulls a picture from a local `http.server`, the way `tests/test_ingest_sources.py` already serves the web fixture. Fails
- [X] T058 🔴 [P] [US2] `tests/test_figures.py::test_fetch_refuses_a_redirect_off_the_source_host` — a local server 302-ing to another host is refused, naming the URL; and no cookie or auth header is ever sent (FR-016). Fails: no module
- [X] T059 🔴 [P] [US2] `tests/test_figures.py::test_place_slugs_dedups_and_never_overwrites` — kebab-case slug, `-2` on collision, same bytes twice → one file, existing destination left alone without `--force` (FR-014). Fails

### 🔴 Red — the knowledge frontmatter contract (model-driven half)

> These are the artifact checks that make the prompt change verifiable at all (constitution XI). Each fails against what `/ingest` writes **today**.

- [X] T060 🔴 [US2] `tests/test_check_project.py::test_figures_must_be_a_list_of_entries_with_at_and_visual` — K1, K2 from [contracts/knowledge-frontmatter.md](./contracts/knowledge-frontmatter.md). Fails: accepted today
- [X] T061 🔴 [US2] `tests/test_check_project.py::test_visual_is_a_closed_vocabulary` — K3: `diagram`, `chart`, `map`, `none`, nothing else. Fails
- [X] T062 🔴 [US2] `tests/test_check_project.py::test_a_rejected_figure_needs_a_why_and_no_path` — K4. Fails
- [X] T063 🔴 [US2] `tests/test_check_project.py::test_a_kept_figure_needs_a_path_and_a_caption_that_resolve` — K5, K6, K8: exists, under `figures/<source>/`, accepted extension, source matches the folder. Fails
- [X] T064 🔴 [US2] `tests/test_check_project.py::test_a_kept_figure_must_be_shown_in_the_body` — K7: the path appears as a markdown image link. Fails — this is the one that catches half an edit
- [X] T065 🔴 [US2] `tests/test_check_project.py::test_two_figures_may_not_share_a_path` — K9. Fails
- [X] T066 🔴 [US2] `tests/test_check_project.py::test_a_rejected_figure_is_silent` — K10: no warning, for the reason `content: sparse` is silent. Fails if the implementation warns

### 🟢 Green

- [X] T067 [US2] Write `scripts/figures.py` — `extract | fetch | place`, module docstring in the established style (what it does, who invokes it, why it exists). Imports `deps` only; `pypdfium2` imported inside `extract` (constitution VI)
- [X] T068 [US2] Implement `check_knowledge()`'s `figures:` validation in `scripts/check_project.py` until T060–T066 pass; add `VISUAL_KINDS` beside `CONTENT_STATES`
- [X] T069 [US2] Update `skills/ingest/SKILL.md`: judge every picture; the four places pictures come from (folder file, PDF page, web page, markdown link); call `figures.py` with an explicit `--project`, as the Zotero path already does; record the verdict for **both** answers; mark kept figures inline in the transcription; count pictures towards the existing "ask before more than 20" threshold; report unreadable ones and continue
- [X] T070 [US2] Keep `skills/ingest/SKILL.md` frontmatter valid — `name: ingest`, `description` still names its triggers (`check_docs.py` enforces it)
- [X] T071 [US2] Add `figures/*` and `!figures/.gitkeep` to `.gitignore`, create `figures/.gitkeep`, and add `"figures/"` to `BLOCKED` in `tests/test_repo_hygiene.py`
- [X] T072 🔴→🟢 [US2] `tests/test_repo_hygiene.py::test_figures_are_not_versioned` — written failing before T071, green after
- [X] T073 [US2] Refactor: the figure rules in `check_project.py` should read as one block, not scattered through `check_knowledge()`

**Checkpoint**: `/ingest` judges, keeps and records; a second run changes nothing; deleting one figure brings back exactly that one.

---

## Phase 6: User Story 3 — `/cards` writes three kinds of card from one figure (P3)

**Goal**: a figure yields a description card, a recognition card and text-only detail cards.

**Independent Test**: `/cards` against a catalog whose subtopic references a document with a kept figure, then `lernkarten check cards/*.yaml` and `python3 scripts/check_project.py .` both exit 0.

- [X] T074 🔴 [P] [US3] `tests/test_check_project.py::test_a_face_with_a_picture_needs_text` — C6/FR-023: `back_image:` with an empty `back:` errors. Fails: accepted today
- [X] T075 🔴 [P] [US3] `tests/test_check_project.py::test_a_figure_is_not_printed_on_six_cards` — C7/FR-022: more than one card using a figure on the same face warns. Fails: silent today
- [X] T076 🔴 [P] [US3] `tests/test_check_project.py::test_a_figure_also_yields_a_text_only_card` — C10/FR-024: a file in which every card of a picture-bearing subtopic carries a picture warns. Fails: silent today. This is the red artifact FR-024 lacked — a `skills/` requirement that writes a file is assertable, and constitution XI does not waive it
- [X] T077 [US3] Implement all three checks in `scripts/check_project.py` `check_cards()`
- [X] T078 [US3] Update `skills/cards/SKILL.md`: the three card kinds and what each is for; at most one description and one recognition card per figure; the answer text comes from the figure's `caption`; the picture never replaces the text; the existing `Status: gap` / `out of scope` rules apply unchanged; report how many cards carry a picture
- [X] T079 [US3] Keep `skills/cards/SKILL.md` frontmatter valid — `name: cards`, `description` still names its triggers
- [X] T080 [US3] Confirm nothing about ids, topic files, merging or the text budget changed — a figure card is an ordinary card with one more key

**Checkpoint**: a `/cards` run over a figure-bearing catalog produces a deck that checks clean and prints.

---

## Phase 7: User Story 4 — The user finds out before printing (P4)

**Goal**: `lernkarten check` names the card, the face and the path, and the four causes read differently from one another.

**Independent Test**: the four broken fixtures each exit non-zero with a distinct message.

- [X] T081 [P] [US4] Add `tests/fixtures/demo-project/broken/missing-image.yaml` — `back_image:` naming a file that is not there
- [X] T082 [P] [US4] Add `tests/fixtures/demo-project/broken/image-wrong-format.yaml` — a `.tiff`, which typst refuses (verified in R3)
- [X] T083 [P] [US4] Add `tests/fixtures/demo-project/broken/image-outside-project.yaml` — a `../../` path that escapes the project
- [X] T084 [US4] Add `tests/fixtures/demo-project/broken/unreadable-image.yaml` plus a `make_testdata.py` target writing a text file named `.png` — a real file, an accepted extension, and not an image. Generated, never committed
- [X] T085 [US4] Add four rows to `tests/fixtures/demo-project/broken/README.md`, one per fixture, each naming the expected reaction
- [X] T086 🔴 [US4] Add the four fixtures to the parametrised `test_a_broken_card_file_is_rejected_with_its_reason` in `tests/test_e2e.py`, asserting **four different messages**. Fails
- [X] T087 [US4] Make them pass: the three Python causes in `scripts/build_pdf.py` in the T016 order, and the fourth attributed to its card by `offending_card()` (R4)
- [X] T088 [US4] Confirm a deck written before ids existed still names the card — the positional ref stands in, as the overflow warning already does

**Checkpoint**: nothing reaches the printer with a hole in it.

---

## Phase 8: Docs & Cross-Cutting

- [X] T089 [P] Add a section to `docs/design.md`: how a picture sits in the field, what it may displace (the note rules), what it never may (prompt, answer, source line, bands) — and the honest limit, that a source's chart may carry meaning in colour and turn to grey on grey
- [X] T090 [P] Add `figures/` to the artifact list in `docs/workflow.md`, beside `knowledge/`
- [X] T091 [P] Update `docs/testing.md`: the fixture table gains the new material, and the manual checklist gains **four named items** — the `/ingest` summary line for an unreadable picture (FR-015), the picture count folded into the "ask before more than 20" threshold (FR-017), the `/cards` count of picture-bearing cards (FR-025), and *hold a printed figure card* (constitution XI's run-output carve-out; naming them is required, not optional)
- [X] T092 [P] Update `README.md` and `docs/index.html` — **the first optional runtime dependency lands here**, so any claim that nothing needs installing has to be re-read and corrected if it is now false
- [X] T093 [P] Add any new expected file to `REQUIRED_FILES` in `scripts/check_docs.py` (`scripts/figures.py`, if the list covers scripts)
- [X] T094 English throughout: code, comments, docstrings, docs, commit messages

---

## Phase 9: Gates

- [X] T095 `ruff check .`
- [X] T096 `ruff format --check .`
- [X] T097 `pytest`
- [X] T098 `bin/lernkarten check cards/*.yaml`
- [X] T099 `python3 scripts/check_docs.py`
- [X] T100 `python3 scripts/make_testdata.py` — the new generated material builds from its Typst sources
- [X] T101 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py tests/test_testdata.py tests/test_ingest_sources.py tests/test_figures.py -v`
- [X] T102 `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
- [X] T103 `bin/lernkarten build tests/fixtures/demo-project/cards/*.yaml --margin 0 --no-logo -o output/borderless.pdf`
- [X] T104 Build on the Python floor (3.12) with only the declared dependencies installed
- [X] T105 With `pypdfium2` deliberately absent: a full `/ingest` still completes and names the documents whose figures it could not extract (SC-005)
- [X] T106 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, `figures/`, non-example `cards/`, `output/`, no binaries
- [ ] T107 Push the branch and open a pull request; confirm the branch is `feat/figure-cards` and every commit subject carries an allowed prefix

---

## Phase 10: By Hand

- [ ] T108 `python3 scripts/demo.py ~/lernkarten-demo --raw`, then drive `/ingest` and `/cards` in a real Claude session against the four picture paths
- [ ] T109 Print duplex, flip on long edge, 100 % scale — each back exactly behind its front, pictures included
- [ ] T110 Cut along the grey lines — nothing of a picture clipped
- [ ] T111 **Photocopy test**: does the figure still read in black only? This is the one gate XVI cannot automate
- [ ] T112 Print an A8 figure sheet and decide by eye whether the once-per-run note says enough
- [ ] T113 Install from scratch on a machine that has never run this, on each platform reachable — the optional set must fetch itself on first PDF ingest and degrade cleanly offline

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: none
- **Dependencies (2)**: before `scripts/figures.py` exists (T067). Independent of Phase 3
- **Format Contracts (3)**: blocks US1 and US4. Does **not** block US2 — its format is validated inside US2
- **US1 (4)**: needs Phase 1 and Phase 3. **The MVP**
- **US2 (5)**: needs Phase 2 (for `extract`). Independent of US1 — a hand-written card already proves the build
- **US3 (6)**: needs US2 (there must be a figure to write about) and Phase 3 (the keys must exist)
- **US4 (7)**: needs Phase 3 and US1's validation code
- **Docs (8)**: after the behaviour settles
- **Gates (9)** then **By Hand (10)**: last, in that order

### Within a Story

1. Test material, so a test can fail for the right reason
2. 🔴 all tests, seen failing **on their assertions** — commit here
3. 🟢 deterministic half, then model-driven half
4. Layout, if anything visible changes
5. Refactor

Never move an implementation task above its test. That is the one rule here with no exception (constitution XI).

### Parallel Opportunities

- T001–T004 (setup) all at once
- T018–T020, T022–T025 (Phase 3, different files) once T016 settles the contract
- T032, T033 (unit) alongside T034–T038 (e2e) — different files
- T048–T050 (three demo generators) all at once
- T054–T059 (`test_figures.py`) all at once; T060–T066 are all `test_check_project.py` and must be **serialised**
- T074–T076 in parallel; T081–T083 in parallel
- T089–T092, T093 (docs) once behaviour is fixed

### Not Parallel

- 🔴 and 🟢 for the same behaviour. Ever
- `scripts/check_project.py` is touched by Phases 3, 5, 6 and 7 — serialise every edit to it
- `scripts/make_testdata.py` is touched by T028, T051 and T084 — serialise
- Anything writing `tests/fixtures/demo-project/cards/tides.yaml` (T029) and `DEMO_CARD_COUNT` (T030)

---

## Notes

- **Test-first, always.** 29 assertions are enumerated in [plan.md](./plan.md#test-plan-first-the-red-order); each appears here as a 🔴 task before its implementation
- **The three requirements with no red assertion** (FR-015, FR-017, FR-025) are named on the manual checklist by T091. Naming them is the constitution's requirement, not a nicety
- **`pypdfium2` is optional at runtime.** A user who never ingests a PDF never downloads it; a user offline gets exit 3 and a working ingest for everything else
- Never `git add -f` anything under `knowledge/`, `catalog/`, `cards/` (except `example.yaml`), `figures/`, `output/`, or `sources.yaml`
- Never commit a binary — the new pictures are generated by `scripts/make_testdata.py`
- Extend the demo project; do not start a second corpus
- `LERNKARTEN_E2E=1` opts into the engine-dependent tests, so a fresh checkout never downloads 30 MB unasked
