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

**Revision**: rewritten after `/speckit-analyze`, which found one CRITICAL and
three HIGH issues. What changed is recorded at the bottom under *Analyze
remediation*.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1 or US2
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

Single flat module, no `src/`. Tests in `tests/test_<module>.py`.

---

## Phase 1: Setup

- [ ] T001 `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff
- [ ] T002 `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)

**Not needed**: `make_testdata.py` and the typesetting engine. Nothing here
compiles or renders anything.

---

## Phase 2: Dependencies

**⚠️ Skipped entirely** — plan.md says *"No dependency change."*

---

## Phase 3: Foundational — make the commit legitimate before making it

**Purpose**: constitution VIII forbids committed binaries except for a named
list. Committing first and amending the rule afterwards would leave the
repository contradicting itself for the length of the branch.

**⚠️ BLOCKING**: T004 must complete before T008 commits the PDF.

<!-- sequential -->

- [ ] T003 🔴 In `tests/test_repo_hygiene.py`, assert Principle VIII in `.specify/memory/constitution.md` names `assets/card-box.pdf` in its stated exception. **Red because** it names only the brand PNGs. — *Without this, a branch that commits the PDF and forgets the amendment is fully green, and the one mechanism making this feature constitutionally legitimate is the one thing nothing checks.*
- [ ] T004 Amend Principle VIII in `.specify/memory/constitution.md`: extend the stated exception to name the card box alongside the brand PNGs, on the same reasoning ("nobody should have to run a renderer to print a box"). Add `assets/card-box.pdf` to the *Source* line. **Keep the rule intact** — generated test material stays generated, and the exception stays a short named list, never a general permission. Bump **Version** to `2.7.0`, set *Last Amended*, and add the dated rationale paragraph to Governance in the house style of 2.0.0–2.6.0. **(FR-009)** — makes T003 green

---

## Phase 4: User Story 1 — Download the box (Priority: P1)

**Goal**: the PDF is in the repository and reachable in one click from the
landing page.

**Independent test**: `git ls-files` contains it, and the deployed page links it.

### Tests 🔴

<!-- parallel-group: 1 (max 3 concurrent) -->

- [ ] T005 🔴 [P] [US1] In `tests/test_repo_hygiene.py`, add three assertions: `ignored(["assets/card-box.pdf"]) == set()`; `"assets/card-box.pdf" in versioned_files()`; and that the PDF is **exactly one page at A4 portrait** (210 × 297 mm) — reuse the `MediaBox` regex helper at `tests/test_e2e.py:663` rather than writing a second one. **Red because** `.gitignore:43` is `*.pdf`, the file is untracked, and there is nothing to measure. **(covers FR-001, FR-002, SC-002)**
- [ ] T006 🔴 [P] [US1] In `tests/test_landing_page.py`, add two assertions: the page source links `card-box.pdf`, and `.github/workflows/pages.yml` both copies `assets/card-box.pdf` into `_site/` and lists it under `paths:`. Assert the workflow **as text** — a 404 on the deployed site is invisible to every other kind of test. **Red because** neither the link nor the copy exists.

**Also confirm green from the start** (regression guard, not a red task):
`test_the_page_stays_one_self_contained_file` must still pass — it inspects
`<link rel=stylesheet>` and `<img src>`, not `<a href>`, so a download link does
not change the external sub-resource set.

### Implementation

<!-- sequential -->

- [ ] T007 [US1] In `.gitignore`, negate the `*.pdf` build-leftover rule for this one file: add `!assets/card-box.pdf` with a comment saying why, in the shape of the existing `!cards/example.yaml` carve-out. Leave `*.pdf` itself intact. **(FR-001)**
- [ ] T008 [US1] `git add assets/card-box.pdf` and commit it **unchanged** — do not regenerate, re-export or open it in an editor. Commit subject uses the `feat/` prefix. **(FR-002)** — **Depends on T007** (git refuses the file before it) **and on T004** (the rule before the exception to it).

<!-- parallel-group: 2 (max 3 concurrent) -->

- [ ] T009 [P] [US1] In `.github/workflows/pages.yml`, add `cp assets/card-box.pdf _site/card-box.pdf` to the *Assemble the site* step and `assets/card-box.pdf` to the `paths:` trigger. Update the step's comment — the site is no longer "that file and nothing else". **(FR-003, plan.md F1)**
- [ ] T010 [P] [US1] In `docs/index.html`, add the download link `href="card-box.pdf"` in the section about printing — relative, same origin, not a `raw.githubusercontent.com` URL. **Add an HTML comment** stating that the path is correct on the deployed site, where `pages.yml` puts the two files side by side, and dead when the file is opened straight from `docs/`. `check_docs.py` link-checks markdown only, so nothing else records this. **(FR-003)**

**Checkpoint**: `pytest tests/test_repo_hygiene.py tests/test_landing_page.py` green.

---

## Phase 5: User Story 2 — Know before you print whether it fits (Priority: P1)

**Goal**: a user with the default A7 deck learns the box will not fit *before*
spending card stock on it.

**Why this is a separate story**: US1 can ship without it and would be actively
harmful — a download offered to everyone that fits only the non-default grid.

### Tests 🔴

<!-- sequential -->

- [ ] T011 🔴 [US2] In `tests/test_landing_page.py`, assert the text beside the download names the grid (`a8`) **and** the default margin. **Red because** no such text exists. Do **not** assert against the PDF's own wording — the sheet says `a4 landscape` and `cards 70 × 49 mm`, and both are wrong (plan.md F2).

### Implementation

- [ ] T012 [US2] In `docs/index.html`, add the caption beside the download: fits a deck printed at `--grid a8` at the default margin; card 71.75 × 50 mm, inner box 73 × 24 × 52 mm, ≈ 90 cards, 160–250 gsm. Reading text stays at or above the 15 px screen floor. **(FR-004)** — same file as T010, so **not** parallel with it

**Checkpoint**: `pytest tests/test_landing_page.py` green.

---

## Phase 6: Polish & cross-cutting

### Tests 🔴

<!-- sequential -->

- [ ] T013 🔴 In `tests/test_repo_hygiene.py`, add three assertions: (a) no versioned file still says a deck's box is one **you can buy**; (b) `docs/design.md` has a box section naming the card size and the `a8` constraint; (c) `README.md` names the box. **Red because** two files still say it and neither document mentions the box. **(covers FR-005, FR-006, FR-008)**
  **Watch the extension filter.** The obvious model, `test_the_repo_does_not_still_promise_five_commands`, skips anything not `.md/.html/.typ/.yaml` (`test_repo_hygiene.py:233`) — so copying it verbatim would **not** scan `scripts/build_pdf.py`, which is exactly one of the two offenders. Include `.py`, or scan all versioned text. Keep the `specs/` exemption: those files record what was true when each feature was written.

### Implementation

<!-- parallel-group: 3 (max 3 concurrent) -->

- [ ] T014 [P] In `scripts/build_pdf.py:41-45`, correct the comment: the two grids cut to a card you can *print* a box for — one of them ships with this project. **(FR-008)**
- [ ] T015 [P] In `docs/design.md`, fix the *The press sheet* sentence at line 179, and add a **The box** section: card 71.75 × 50 mm, inner 73 × 24 × 52 mm, ≈ 90 cards, 160–250 gsm, A4 portrait, `a8` only, and that it has no Typst source and is edited outside this repository. State the cut/fold/glue encoding — solid, dashed, tinted-plus-labelled — so the doubling rule is on record. This section is the canonical vocabulary for the artifact; use it consistently ("the box", "the sheet"). **(FR-005, FR-008)**
- [ ] T016 [P] In `README.md`, name the box under *Printing and cutting* (line 142) with a link to the file. **(FR-006)**

<!-- parallel-group: 4 (max 3 concurrent) -->

- [ ] T017 [P] In `skills/print/SKILL.md`, add one sentence after the cutting instructions naming the box and where to get it. **(FR-007)** — run output, so no automated test; it goes on the manual checklist instead
- [ ] T018 [P] In `docs/testing.md`, add the four manual checklist items: follow the deployed link and confirm a PDF downloads; print at 100 %, measure the scale bar, fold, glue, fill with an A8 deck; read the caption and confirm an A7 user would stop; confirm the `/print` sentence appears in a real run. Constitution XI requires run-output requirements to be **named** on the checklist, never left implicit.

<!-- sequential -->

- [ ] T019 Run the four gates: `ruff check . && ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`. `check_docs.py` fails on a documentation link that does not resolve, so T015 and T016 are the likely offenders.
- [ ] T020 Write the PR description. It **must** state two things a reviewer would otherwise have to infer: that the `.gitignore` negation is a deliberate carve-out and not a `git add -f` (constitution VII, and Governance requires the note), and that the Principle VIII amendment in T004 is what makes the committed binary legitimate.

---

## Dependencies

```
T001, T002  (setup)
    │
T003 🔴 ──► T004  constitution VIII + version bump   ← BLOCKING, precedes T008
    │
    ├── T005 🔴 ║ T006 🔴        (parallel — different test files)
    │       │
    │   T007 .gitignore ──► T008 commit the PDF      (also needs T004)
    │       │
    │   T009 pages.yml ║ T010 index.html link        (parallel)
    │       │
    │   T011 🔴 ──► T012 index.html caption          (same file as T010)
    │
    └── T013 🔴 ──► T014 ║ T015 ║ T016               (parallel)
                     T017 ║ T018                     (parallel)
                          │
                     T019 gates ──► T020 PR description
```

**Story order**: US1 then US2. They touch the same file (`docs/index.html`), so
they are not parallel — but US1 should not be merged without US2.

## Parallel opportunities

| Group | Tasks | Why safe |
|---|---|---|
| 1 | T005, T006 | different test files |
| 2 | T009, T010 | `pages.yml` vs `index.html` |
| 3 | T014, T015, T016 | `build_pdf.py` vs `design.md` vs `README.md` |
| 4 | T017, T018 | `SKILL.md` vs `testing.md` |

Three sequential constraints are load-bearing: **T003 before T004**, **T007
before T008** (git refuses the file otherwise), and **T004 before T008** (the
rule before the exception to it).

## Requirement coverage

| Requirement | Task | Assertion |
|---|---|---|
| FR-001 `.gitignore` | T007 | T005 |
| FR-002 commit PDF | T008 | T005 |
| FR-003 link + Pages | T009, T010 | T006 |
| FR-004 caption | T012 | T011 |
| FR-005 `design.md` | T015 | T013 |
| FR-006 README | T016 | T013 |
| FR-007 `/print` | T017 | manual (XI carve-out) — named in T018 |
| FR-008 stale sentence | T014, T015 | T013 |
| FR-009 constitution | T004 | T003 |
| SC-002 page geometry | — | T005 |

**8 of 9 requirements carry a red assertion.** FR-007 is the one exception, and
it is exempt for the stated reason rather than by omission.

## Analyze remediation

What `/speckit-analyze` found, and what changed:

| Finding | Severity | Fix |
|---|---|---|
| FR-009 had no assertion — nothing verified the amendment that legitimises the whole feature | **CRITICAL** | New T003, ahead of everything |
| SC-002 (1 page, A4 portrait) had no task at all | HIGH | Folded into T005 |
| T013's named model skips `.py`, so the `build_pdf.py` fix would be unasserted | HIGH | Called out explicitly in T013 |
| FR-005 and FR-006 had tasks but no assertions, contradicting SC-006 | HIGH | Folded into T013 |
| The amendment did not record itself — no version bump, no rationale note | MEDIUM | Added to T004 |
| `href="card-box.pdf"` is right deployed, dead locally, and ungated | MEDIUM | Documented in T010 |
| Vocabulary drift between "box", "sheet", "net", "artifact" | LOW | T015 fixes the canonical text |

**Total: 20 tasks.** 15 of them are one line or one paragraph in a file that
already exists.
