---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, contracts/

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story below opens with a test task, and that test is committed *failing on its assertion* before the implementation task starts. Test tasks are never optional here and never come second.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task serves (US1, US2, …)
- Always name the exact file path
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

This is a single flat module — there is no `src/`.

- Entry point: `bin/lernkarten`
- Implementation: `scripts/<module>.py` (flat, imported by bare name)
- Prompts: `skills/<name>/SKILL.md`
- Layout: `templates/card.typ`, `templates/cards.typ`, `assets/brand/*.typ`
- Tests: `tests/test_<module>.py`
- Test material: `tests/fixtures/demo-project/` (the one shared corpus)
- Docs: `docs/workflow.md`, `docs/design.md`, `docs/testing.md`, `README.md`

<!--
  ============================================================================
  The tasks below are SAMPLES showing the phase shape for this project.
  /speckit-tasks MUST replace them with real tasks from spec.md and plan.md.
  Delete any phase the feature does not touch — do not keep empty scaffolding.
  The 🔴-before-implementation ordering is NOT a sample; it is required.
  ============================================================================
-->

## Phase 1: Setup

**Purpose**: get the environment able to verify the work

- [ ] T001 `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff
- [ ] T002 `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [ ] T003 `python3 scripts/make_testdata.py` — build the binary test material (PDFs, scan, JPEG, DOCX, Zotero attachments)
- [ ] T004 `bin/lernkarten engine --check` — confirm the typesetting engine, or let the first build fetch it
- [ ] T005 Create the branch: `git switch -c <prefix>/<short-kebab-name>` — prefix required (`fix/`, `feat/`, `skill/`, `build/`, `docs/`, `ci/`, `test/`, `design/`)

---

## Phase 2: Dependencies

**Purpose**: adopt or replace a dependency, with the vetting done rather than assumed.

**⚠️ Skip entirely if plan.md says "No dependency change".**

- [ ] T006 Confirm the vetting table in plan.md is complete — wheels on Windows/macOS/Linux, last release, adoption, provenance, typo-squat check, licence, transitive tree, no advisory (constitution IV)
- [ ] T007 **Runtime or dev-only?** A runtime package goes in `REQUIREMENTS` in `scripts/deps.py`, pinned exactly, and needs a wheel for every supported platform — `--only-binary :all:` refuses it otherwise. A dev-only package goes in `requirements-dev.txt`.
- [ ] T008 Declare it with a version bound and a one-line comment saying what it is for — libraries get a range, dev tools an exact pin
- [ ] T009 🔴 Write the test that fails without the dependency doing its job — not merely an import check
- [ ] T010 Verify a clean install works on all three platforms — the Windows CI legs block a merge, so a green run there means something
- [ ] T011 Confirm cold `lernkarten` start is not visibly slower
- [ ] T012 Delete anything the dependency makes redundant — hand-rolled code it replaces, and any dependency now unused
- [ ] T013 Confirm `.github/dependabot.yml` covers the manifest that declares it

**Checkpoint**: the dependency is justified in writing, installed, exercised by a test, and nothing dead is left behind.

---

## Phase 3: Format Contracts (Blocking)

**Purpose**: the four file formats are the entire interface between the two halves (constitution I). Settle them before either half is written.

**⚠️ Skip entirely if plan.md says "No format change" — do not invent work here.**

- [ ] T013 Define the change to [`sources.yaml` | knowledge frontmatter | `catalog/topics.md` | the card schema] in `specs/[###-feature]/contracts/`
- [ ] T014 🔴 Add cases to `tests/test_check_project.py` for the new shape — valid and invalid — and watch them fail
- [ ] T015 Update the reader/validator in `scripts/check_project.py` until they pass
- [ ] T016 [P] Update `scripts/build_pdf.py` if the card schema moved
- [ ] T017 [P] Update the documented schema in `CLAUDE.md`
- [ ] T018 [P] Update `sources.example.yaml` / `cards/example.yaml` to match
- [ ] T019 Confirm existing projects on disk still build, or document the migration

**Checkpoint**: `python3 scripts/check_project.py tests/fixtures/demo-project --strict` passes and both halves have a settled contract.

---

## Phase 4: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [what this story delivers]

**Independent Test**: [the command that proves it, run against the demo project]

### Test material first — `tests/fixtures/demo-project/`

> The test needs something to read before it can fail for the right reason.

- [ ] T020 [P] [US1] Extend the demo project with material for this feature — invent, never quote (constitution VII)
- [ ] T021 [US1] If binaries are involved, add a generator under `tests/fixtures/demo-project/generators/` and wire it into `scripts/make_testdata.py` — never commit the binary
- [ ] T022 [P] [US1] A new failure mode gets a file in `tests/fixtures/demo-project/broken/` and a row in that folder's README
- [ ] T023 [US1] Update `DEMO_CARD_COUNT` if the demo card count changed

### 🔴 Red — the tests, before any implementation

> Each of these must fail **on its assertion**, not on an ImportError or a missing file. Run them and paste the failure into the pull request if it is not obvious.

- [ ] T024 🔴 [P] [US1] Unit test in `tests/test_[module].py` for [behaviour] — fails
- [ ] T025 🔴 [US1] End-to-end case in `tests/test_e2e.py` — runs `bin/lernkarten` as a subprocess and inspects the PDF; fails (skips without an engine, so run with `LERNKARTEN_E2E=1`)
- [ ] T026 🔴 [US1] Error-path test: the message names the offending file and key — fails
- [ ] T027 🔴 [US1] Degraded-path test: no `pdftotext` / no engine / on the Python floor — fails
- [ ] T028 🔴 [US1] For a prompt change: a check in `scripts/check_project.py` plus a case in `tests/test_check_project.py` that fails against what the *current* prompt produces. If no failing check can be written, stop — go back to the spec (constitution XI)

**Checkpoint**: `pytest` is red for exactly the reasons this story exists. Commit here.

### 🟢 Green — the deterministic half (`scripts/`, `bin/`, `templates/`)

- [ ] T029 [P] [US1] Implement [behaviour] in `scripts/[module].py` — prefer a vetted library over hand-rolling (constitution III)
- [ ] T030 [US1] Wire it into `bin/lernkarten` if it needs a subcommand or flag (mirror into `scripts/lernkarten` — one task, both files)
- [ ] T031 [US1] Make the error-path test pass
- [ ] T032 [US1] Make the degraded-path test pass

### 🟢 Green — the model-driven half (`skills/`)

- [ ] T033 [US1] Update the procedure in `skills/[name]/SKILL.md` until T028 passes — terse, action-oriented, a procedure not a theory
- [ ] T034 [US1] Keep the frontmatter valid: `name` == folder name, `description` names its triggers

### Layout — `templates/`, `assets/brand/`

> Only if something visible changes. Read `docs/design.md` first (constitution XVI).

- [ ] T035 🔴 [US1] Assert the assertable part first — page count, card count, an overflowing card *reported* rather than shrunk, exit code
- [ ] T036 [US1] Edit `templates/card.typ` / `templates/cards.typ` — the Typst source, never a generated file
- [ ] T037 [US1] Verify by eye: colour doubled by shape or position; no type below 11 pt; duplex alignment intact
- [ ] T038 [US1] `python3 scripts/render_brand.py` and commit the updated PNGs
- [ ] T039 [US1] Eyeball both builds: `bin/lernkarten build cards/example.yaml -o output/cards.pdf` and the same with `--margin 0 --no-logo`

### Refactor

- [ ] T040 [US1] Now that it is green, clean it up — the third step of red-green-refactor is not optional either

**Checkpoint**: US1 works end to end against the demo project, and every assertion covering it was seen failing first.

---

## Phase 5: User Story 2 - [Title] (Priority: P2)

**Goal**: [what this story delivers]

**Independent Test**: [verification]

- [ ] T041 🔴 [P] [US2] [Failing test at the matching level]
- [ ] T042 [P] [US2] [Implementation task with exact path]
- [ ] T043 [US2] Integrate with US1 where needed, without breaking its independent test

**Checkpoint**: US1 and US2 both stand on their own.

---

[More story phases as needed, same 🔴-then-🟢 shape]

---

## Phase N: Docs & Cross-Cutting

- [ ] T0XX [P] Update `docs/workflow.md` if the user-facing flow changed
- [ ] T0XX [P] Update `docs/testing.md` — the fixture table and the manual checklist, if a new source type or failure mode landed
- [ ] T0XX [P] Update `docs/design.md` if a visible rule changed
- [ ] T0XX [P] Update `README.md` / `docs/index.html` if the pitch or the commands changed
- [ ] T0XX Update `CLAUDE.md` if a card or format convention changed
- [ ] T0XX **If the first runtime dependency landed**: `README.md` and `docs/index.html` still say nothing needs installing — true only while `dependencies = []`, so revisit both
- [ ] T0XX Add any new expected file to `REQUIRED_FILES` in `scripts/check_docs.py`
- [ ] T0XX Check every relative markdown link resolves — `check_docs.py` fails on a dead one
- [ ] T0XX English throughout: code, comments, docstrings, docs, commit messages

---

## Phase N+1: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

- [ ] T0XX `ruff check .`
- [ ] T0XX `ruff format --check .`
- [ ] T0XX `pytest`
- [ ] T0XX `bin/lernkarten check cards/*.yaml`
- [ ] T0XX `python3 scripts/check_docs.py`

Plus, once, for anything touching the pipeline or the test data:

- [ ] T0XX `python3 scripts/make_testdata.py`
- [ ] T0XX `LERNKARTEN_E2E=1 pytest tests/test_e2e.py tests/test_testdata.py tests/test_ingest_sources.py -v`
- [ ] T0XX `python3 scripts/check_project.py tests/fixtures/demo-project --strict`
- [ ] T0XX `bin/lernkarten build cards/*.yaml --margin 0 --no-logo -o output/borderless.pdf`
- [ ] T0XX `bin/lernkarten build cards/*.yaml --language german -o output/other-language.pdf`
- [ ] T0XX Build on the supported Python floor with only the declared dependencies installed

For the ingest and zotero paths, with their servers running:

```bash
python3 -m http.server 8137 --directory tests/fixtures/demo-project/raw/web
python3 scripts/zotero_stub.py        # fakes the Zotero 7 local API on 23119
```

- [ ] T0XX `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries
- [ ] T0XX Push the branch and open a pull request (`main` rejects direct pushes)
- [ ] T0XX Confirm the branch name is `<prefix>/<short-kebab-name>` and commit subjects are prefixed

---

## Phase N+2: By Hand

**Purpose**: what no script can judge — whether the cards are worth learning, and whether front and back land on top of each other. The full checklist is in `docs/testing.md`.

- [ ] T0XX `python3 scripts/demo.py ~/lernkarten-demo --raw` and drive the changed skill in a real Claude session
- [ ] T0XX Print duplex, flip on long edge, 100 % scale — each back exactly behind its front
- [ ] T0XX Cut along the grey lines — 100 × 72 mm cards, nothing clipped
- [ ] T0XX Non-Latin cards show letters, not empty boxes
- [ ] T0XX Photocopy test: does it still read in black only?
- [ ] T0XX If a dependency landed: install from scratch on a machine that has never run this, on each platform you can reach

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: no dependencies
- **Dependencies (2)**: before any code that imports the new package. Skip if none.
- **Format Contracts (3)**: blocks every story that touches a file format. Skip if none do.
- **User Stories (4+)**: depend on Setup, on Phase 2 where a package landed, and on Phase 3 where a format moved
- **Docs (N)**: after the behaviour it describes settles
- **Gates (N+1)**: last, and non-negotiable
- **By Hand (N+2)**: after the gates pass

### Within a Story — the ordering that matters

1. Test material, so a test can fail for the right reason
2. 🔴 **All tests, seen failing on their assertions** — commit here
3. 🟢 Deterministic half, then model-driven half
4. Layout, if anything visible changes
5. Refactor

Never move an implementation task above its test. That is the one rule in this
file with no exception (constitution XI).

Also:

- The format reader and the engine locator stay leaves — nothing of ours imports into them (constitution VI)
- The artifact check in `check_project.py` lands *with* the prompt change, not after
- Brand PNGs re-rendered after the card, never before

### Parallel Opportunities

- Setup T001–T004 all in parallel
- Within Phase 3, the example files, `CLAUDE.md` and `build_pdf.py` updates are independent once the contract settles
- Failing tests at different levels can be written in parallel — they are different files
- Docs tasks are independent once behaviour is fixed
- Demo-project extensions are independent of the code, as long as `DEMO_CARD_COUNT` is updated once

### Not Parallel

- 🔴 and 🟢 for the same behaviour. Ever.
- `bin/lernkarten` and `scripts/lernkarten` are mirrors — one task, both files
- `scripts/check_project.py` is touched by nearly every story; serialize edits to it
- Anything writing `tests/fixtures/demo-project/sources.yaml`

---

## Notes

- **Test-first, always.** A test written after the code tells you what the code does; only a test seen failing tells you it does what was asked.
- **Prefer a library.** Hand-rolling needs a reason in plan.md (constitution III). The two things this project once hand-rolled have both been replaced, so neither is precedent.
- **A dependency is a decision, not a task.** It needs the Principle IV vetting table filled in and read by a reviewer.
- Never `git add -f` anything under `knowledge/`, `catalog/`, `cards/` (except `example.yaml`), `output/`, or `sources.yaml`.
- Never commit a binary. Generate it from a text source.
- Never hand-edit `output/` or a rendered PNG. Edit the Typst source and re-render.
- Extend the demo project. Do not start a second fixture corpus.
- Engine-dependent tests skip without an engine, so a fresh checkout never downloads 30 MB unasked. `LERNKARTEN_E2E=1` opts in.
- Windows, macOS and Linux are equals, and all three block a merge.
- A runtime dependency reaches users via `scripts/deps.py`; check `lernkarten deps --check` after adding one.
- Commit after each task or logical group, and always at the 🔴 checkpoint.
