---
description: "Task list for 007-card-box — ship the card box as a download"
---

# Tasks: Ship the card box as a download

**Input**: Design documents from `/specs/007-card-box/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md). No `research.md`,
`data-model.md`, `contracts/` or `quickstart.md` — the scope was cut to
publishing an artifact that already exists, and those would be ceremony.

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every
story opens with a test task committed *failing on its assertion* before the
implementation that makes it pass.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1 or US2
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

Single flat module, no `src/`. Tests in `tests/test_<module>.py`.

---

## Phase 1: Setup

**Purpose**: be able to verify the work. The branch already exists.

- [ ] T001 `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff
- [ ] T002 `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)

**Not needed for this feature**: `make_testdata.py` and the typesetting engine.
Nothing here compiles or renders anything.

---

## Phase 2: Dependencies

**⚠️ Skipped entirely** — plan.md says *"No dependency change."*

---

## Phase 3: Foundational — make the commit legitimate before making it

**Purpose**: constitution VIII forbids committed binaries except for a named
list. Committing the PDF *first* and amending the rule afterwards would put the
repository in contradiction with itself for the length of the branch. Amend the
rule, then do the thing the rule now permits.

**⚠️ BLOCKING**: T003 must complete before T006 commits the PDF.

<!-- sequential -->

- [ ] T003 Amend Principle VIII in `.specify/memory/constitution.md` so its stated exception names the card box alongside the brand PNGs, on the same reasoning ("nobody should have to run a renderer to print a box"). Keep the rule intact: generated test material stays generated, and the exception stays a short named list, never a general permission. Add `assets/card-box.pdf` to the *Source* line. **(FR-009)**

---

## Phase 4: User Story 1 — Download the box (Priority: P1)

**Goal**: the PDF is in the repository and reachable in one click from the
landing page.

**Independent test**: `git ls-files` contains it, and the deployed page links it.

### Tests 🔴

<!-- parallel-group: 1 (max 3 concurrent) -->

- [ ] T004 🔴 [P] [US1] In `tests/test_repo_hygiene.py`, add two assertions: `ignored(["assets/card-box.pdf"]) == set()` and `"assets/card-box.pdf" in versioned_files()`. Reuse the existing `ignored()` helper — it already handles Windows quoting. **Red because** `.gitignore:43` is `*.pdf` and the file is untracked.
- [ ] T005 🔴 [P] [US1] In `tests/test_landing_page.py`, add two assertions: the page source links `card-box.pdf`, and `.github/workflows/pages.yml` both copies `assets/card-box.pdf` into `_site/` and lists it under `paths:`. Assert the workflow **as text** — a 404 on the deployed site is invisible to every other kind of test. **Red because** neither the link nor the copy exists.

**Also confirm green from the start** (regression guard, not a red task):
`test_the_page_stays_one_self_contained_file` must still pass — it inspects
`<link rel=stylesheet>` and `<img src>`, not `<a href>`, so a download link does
not change the external sub-resource set.

### Implementation

<!-- sequential -->

- [ ] T006 [US1] In `.gitignore`, negate the `*.pdf` build-leftover rule for this one file: add `!assets/card-box.pdf` with a comment saying why, in the shape of the existing `!cards/example.yaml` carve-out. Leave `*.pdf` itself intact. **(FR-001)** — makes half of T004 green
- [ ] T007 [US1] `git add assets/card-box.pdf` and commit it **unchanged**. Do not regenerate, re-export or open it in an editor. The commit subject uses the `feat/` prefix. **(FR-002)** — makes the rest of T004 green. **Depends on T006**; before it, git refuses the file.

<!-- parallel-group: 2 (max 3 concurrent) -->

- [ ] T008 [P] [US1] In `.github/workflows/pages.yml`, add `cp assets/card-box.pdf _site/card-box.pdf` to the *Assemble the site* step and `assets/card-box.pdf` to the `paths:` trigger. Update the step's comment — the site is no longer "that file and nothing else". **(FR-003, plan.md F1)** — makes half of T005 green
- [ ] T009 [P] [US1] In `docs/index.html`, add the download link `href="card-box.pdf"` in the section about printing. Relative, same origin — not a `raw.githubusercontent.com` URL. **(FR-003)** — makes the rest of T005 green

**Checkpoint**: `pytest tests/test_repo_hygiene.py tests/test_landing_page.py` green.

---

## Phase 5: User Story 2 — Know before you print whether it fits (Priority: P1)

**Goal**: a user with the default A7 deck learns the box will not fit *before*
spending card stock on it.

**Independent test**: the constraint is readable beside the link, without
following it.

**Why this is a separate story**: US1 can ship without it and would be actively
harmful — a download offered to everyone that fits only the non-default grid.

### Tests 🔴

<!-- sequential -->

- [ ] T010 🔴 [US2] In `tests/test_landing_page.py`, assert the text beside the download names the grid (`a8`) **and** the default margin. **Red because** no such text exists. Do not assert against the PDF's own wording — the sheet says `a4 landscape` and `cards 70 × 49 mm`, and both are wrong (plan.md F2).

### Implementation

- [ ] T011 [US2] In `docs/index.html`, add the caption beside the download: the box fits a deck printed at `--grid a8` at the default margin; card 71.75 × 50 mm, inner box 73 × 24 × 52 mm, ≈ 90 cards, 160–250 gsm. Reading text stays at or above the 15 px screen floor. **(FR-004)** — same file as T009, so **not** parallel with it

**Checkpoint**: `pytest tests/test_landing_page.py` green.

---

## Phase 6: Polish & cross-cutting

### Tests 🔴

<!-- sequential -->

- [ ] T012 🔴 In `tests/test_repo_hygiene.py`, assert no versioned file still says a deck's box is one **you can buy**. Follow the shape of the existing `test_the_repo_does_not_still_promise_five_commands` — same exemption for `specs/`, which records what was true when each feature was written. **Red because** two files say it.

### Implementation

<!-- parallel-group: 3 (max 3 concurrent) -->

- [ ] T013 [P] In `scripts/build_pdf.py:41-45`, correct the comment: the two grids cut to a card you can print a box for — one of them ships with this project. **(FR-008)** — half of T012
- [ ] T014 [P] In `docs/design.md`, fix the *The press sheet* sentence at line 179, and add a **The box** section: what it is, card 71.75 × 50 mm, inner 73 × 24 × 52 mm, ≈ 90 cards, 160–250 gsm, A4 portrait, `a8` only, and that it has no Typst source and is edited outside this repository. State the cut/fold/glue encoding — solid, dashed, tinted-plus-labelled — so the doubling rule is on record. **(FR-005, FR-008)** — the other half of T012
- [ ] T015 [P] In `README.md`, name the box under *Printing and cutting* (line 142) with a link to the file. **(FR-006)**

<!-- parallel-group: 4 (max 3 concurrent) -->

- [ ] T016 [P] In `skills/print/SKILL.md`, add one sentence after the cutting instructions naming the box and where to get it. **(FR-007)** — run output, so no automated test; it goes on the manual checklist instead
- [ ] T017 [P] In `docs/testing.md`, add the four manual checklist items: follow the deployed link and confirm a PDF downloads; print at 100 %, measure the scale bar, fold, glue, fill with an A8 deck; read the caption and confirm an A7 user would stop; confirm the `/print` sentence appears in a real run. Constitution XI requires run-output requirements to be **named** on the checklist, never left implicit.

<!-- sequential -->

- [ ] T018 Run the four gates: `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`. `check_docs.py` fails on a documentation link that does not resolve, so T014 and T015 are the likely offenders.
- [ ] T019 Write the PR description. It **must** state two things a reviewer would otherwise have to infer: that the `.gitignore` negation is a deliberate carve-out and not a `git add -f` (constitution VII), and that the constitution VIII amendment in T003 is what makes the committed binary legitimate.

---

## Dependencies

```
T001, T002  (setup)
    │
T003  constitution VIII amendment  ← BLOCKING, must precede T007
    │
    ├── T004, T005 🔴  (parallel — different test files)
    │       │
    │   T006 .gitignore ──► T007 commit the PDF
    │       │
    │   T008 pages.yml  ║  T009 index.html link   (parallel)
    │       │
    │   T010 🔴 ──► T011 index.html caption       (same file as T009)
    │
    └── T012 🔴 ──► T013 ║ T014 ║ T015  (parallel)
                     T016 ║ T017        (parallel)
                          │
                     T018 gates ──► T019 PR description
```

**Story order**: US1 then US2. They touch the same file (`docs/index.html`), so
they are not parallel — but US2 is small and US1 should not be merged without it.

## Parallel opportunities

| Group | Tasks | Why safe |
|---|---|---|
| 1 | T004, T005 | different test files |
| 2 | T008, T009 | `pages.yml` vs `index.html` |
| 3 | T013, T014, T015 | `build_pdf.py` vs `design.md` vs `README.md` |
| 4 | T016, T017 | `SKILL.md` vs `testing.md` |

Everything else is sequential, and two of those constraints are load-bearing:
**T006 before T007** (git refuses the file otherwise) and **T003 before T007**
(the rule before the exception to it).

## Implementation strategy

**MVP is US1 + US2 together**, not US1 alone. Shipping a download without the
caption that says which deck it fits would send the majority of users — A7 is the
default grid — to print a box their cards do not go into.

**Total: 19 tasks.** 15 of them are one line or one paragraph in a file that
already exists.
