---
description: "Task list for BUG-010 — the A8 default's description never moved"
---

# Tasks: A8 becomes the default grid — BUG-010 fix

**Input**: [spec.md](./spec.md), [bugs/BUG-010.md](./bugs/BUG-010.md)

**Prerequisites**: none. There is no `plan.md` and no `research.md` for this
feature, and **that is the bug**: the phase that enumerates the blast radius of
a moved constant is the phase that was skipped. See the assumption added to
`spec.md` on 2026-09-07.

> **Line numbers rebased 2026-09-07.** BUG-009's fix (PR #96, `1371542`/`6760beb`)
> landed while this list was being written and added 87 lines to
> `scripts/check_project.py` and 19 to `skills/cards/SKILL.md`. All fourteen
> sites survive; two files' line numbers moved. The numbers below are current at
> `b7768bd`. **Re-locate by content, not by number**, if anything else lands
> first.
>
> | site | BUG-010 says | now |
> |---|---|---|
> | picture advisory | `check_project.py:990` | **`:1074`** |
> | absent-means-A7 comment | `check_project.py:920` | **`:1004`** |
> | `--strict` grid advice | `check_project.py:930-935` | **`:1014-1019`** |
> | advisory text | `check_project.py:1041` | **`:1126`** |
> | schema block | `skills/cards/SKILL.md:178` | **`:178`** |
> | grid prose | `skills/cards/SKILL.md:191-196` | **`:191-196`** |
>
> The other seven files are untouched by that merge and their numbers stand.

**Implemented 2026-09-07** on `fix/a8-default-description`; all 28 tasks done.

**Created 2026-09-07** by [BUG-010](./bugs/BUG-010.md). This list covers the
**fix**, not the feature — the feature shipped in v0.9.0 and its own work is
done. 009 is deliberately *not* retrofitted with a plan after the fact; what
this list exists to preserve is the **enumeration of the fourteen sites**, so
it lives somewhere durable rather than in a commit message.

**Tests**: test-first is mandatory and not waivable (constitution XI). Every
behaviour's test is committed **failing on its assertion** before its
implementation task starts.

> **The ordering rule this list is built around: the gate comes before the
> sweep.** BUG-010 exists because a sweep was done by memory and the memory was
> incomplete. Doing the sweep first and then writing a gate proves nothing —
> the gate would be authored against the corpus it was just made to pass, which
> is the same act that shipped the bug. So the gate is written **while the
> repository is still wrong**, and its red state is the fourteen real sites.
> Every site is then fixed until the gate goes green on its own.
>
> This is the third time this repository has needed such a gate
> (`check_sheet_capacity()`, `check_print_order()`), and the second one's own
> comment already names the failure mode.

**Organization**: by defect class, not by user story — this is a fix, and the
classes have genuinely different red artifacts.

## Format: `[ID] [P?] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- Always name the exact file path
- 🔴 a test that must be **red on its assertion** before the next task begins
- 🛡 a **regression guard**: correct before any code and never red

## Path Conventions

Single flat module — no `src/`. Test placement follows `docs/testing.md`:
`tests/test_build_pdf.py` is unit and needs no typesetter; `tests/test_e2e.py`
drives `bin/lernkarten` as a subprocess; `tests/test_check_docs.py` covers the
docs gate; `tests/test_check_project.py` covers what the model-driven steps
write into a *user's* project; `tests/test_landing_page.py` parses
`docs/index.html`.

---

## Phase 1: The behavioural defect *(FR-013, SC-010)*

**Goal**: a grid-less deck and a `grid: a8` deck print identically, so they must
be advised identically. Today only the one that says so is.

- [x] T001 🔴 `tests/test_check_project.py::test_a_gridless_deck_with_a_picture_is_advised_about_a8` — a project with one card carrying a `back_image` and **no `grid:` key** produces the `pictures at A8 print about a third of the area` advisory. Fails today: no advisory. This advisory has **no test at all** right now — `dense_with_pictures` and its message appear nowhere in the test file — which is why nothing went red when the default moved *(SC-010)*
- [x] T002 🛡 [P] In the same test, assert the identical deck **stating `grid: a8`** produces the advisory, and a deck stating **`grid: a7`** does not. Green before and after; it is what pins the fix to "resolve the default" rather than "always warn" *(SC-010)*
- [x] T003 Fix `scripts/check_project.py:1074` — replace the literal `parse_grid(data.get("grid") or "a7")` with a resolution through `build_pdf`'s own constant, so check and build cannot disagree again. Same arrangement FR-002 forced on the scale reference: each idea of "which grid" is named once and never retyped. **No shared helper** — `check` reports on one file and the build resolves across files with `--grid` in play, so the questions are not the same shape; one name instead of one literal is the whole fix. Until T001 passes *(FR-013)*

---

## Phase 2: The generator *(FR-010, SC-009)*

**Goal**: `/cards` stops writing the wrong value into user data. This is the
damaging site — everything else in this list is a sentence, and this one is a
file the user then owns.

- [x] T004 🔴 Add a check to `scripts/check_project.py` (and its case to `tests/test_check_project.py`) for the model-driven half, per `docs/testing.md`: a deck stating `grid: a7` is legal, so the check cannot be about the value. The red artifact is the **`--strict` grid remark** at `:1014-1019` — assert it stays silent for a deck stating `grid: a8` and fires for a silent deck, which is what SC-009 needs to be checkable at all. If no failing check can be written for a prompt change, the requirement is too vague to implement *(CLAUDE.md § Repo rules)* *(SC-009, FR-009)*
- [x] T005 `skills/cards/SKILL.md:178` — the schema block writes `grid: a8`, not `grid: a7`. **The one edit in this list that changes what lands in a user's file** *(FR-010)*
- [x] T006 `skills/cards/SKILL.md:191-196` — invert the prose: `a8` (4 x 4 per sheet) unless the user asks for A7; *"omitting the key still prints at A7"* becomes A8. **Fix the dimensions in the same edit**: A8 is **74.25 × 52.5 mm landscape**, not the `52.5 x 74` portrait that [BUG-007](../003-card-grid/bugs/BUG-007.md) removed and that this paragraph still quotes. Keep the "say it rather than imply it" argument — FR-006's report and the `--strict` advice both ask a silent deck to state its grid, so the generator states it *(FR-010)*

---

## Phase 3: The gate, written while the repository is still wrong *(FR-012, SC-011)*

**Goal**: FR-011 becomes something CI holds, not something a person remembers.
**Nothing in Phase 4 starts until this phase is red for the right reason.**

- [x] T007 🔴 [P] `tests/test_check_docs.py` — a crafted line calling A7 the default is reported, and a line that names the grid it is talking about is not. Fails: no such check. Narrow the pattern against the real corpus the way `check_sheet_capacity()` was — its first regex flagged `3–8 cards per subtopic`, a different claim entirely *(SC-011)*
- [x] T008 [P] Add the check to `scripts/check_docs.py` until T007 passes. It must catch **both halves of FR-011**: the word (*"a7 is the default"*, *"absent means A7"*, *"8 up, the default"*) and the numbers (the A7 card's dimensions, sheet capacity or cut count given as a default build's output). It must **not** fire on `specs/`, on `docs/design.md`'s deliberate explanation of why the *reference* stays A7, or on a line that names the grid it describes *(FR-012)*
- [x] T009 Widen the gate's file set beyond `markdown_files()` (`scripts/check_docs.py:167`, today root `*.md` + `docs/*.md` + `skills/*/SKILL.md`) to also read `scripts/*.py` and `templates/*.typ`. Without this, **six of the fourteen sites are outside every gate in the repository** — the docstring, the comment, the Typst header and the four landing-page ones. A gate that cannot see the file is no better than the grep it replaces *(FR-012)*
- [x] T010 🔴 [P] `tests/test_landing_page.py` — assert `docs/index.html` neither calls A7 the default nor states the A7 card's dimensions, capacity or cut count as the default output. Fails today on four sites. **This file owns the landing page's claims** and already parses it; `check_docs.py` does not read HTML and should not become the second thing that does *(FR-012, SC-011)*
- [x] T011 **Checkpoint** — run `python3 scripts/check_docs.py` and `pytest tests/test_landing_page.py`. Between them they must now name **all fourteen sites** from BUG-010. A gate that reports fewer has a hole; find it here, not after the sweep

---

## Phase 4: The fourteen sites *(FR-011, SC-011)*

**Goal**: turn the gate green by fixing the repository, not by narrowing the
gate. Each task is one file; `[P]` throughout except where noted.

- [x] T012 [P] `scripts/build_pdf.py:4` — the module docstring of the file that **owns `DEFAULT_GRID`**, four lines above the constant it contradicts. Fixed once already by 003-card-grid's T026 and stale again *(FR-011)*
- [x] T013 [P] `scripts/check_project.py:1004` — the comment *"The grid is optional and absent means A7"*, **eight lines above** the warning at `:1015` that says the deck prints at A8 since v0.9.0. Do not fold into T003; that task changes behaviour and this one changes a sentence *(FR-011, FR-009)*
- [x] T014 [P] `templates/cards.typ:10` — *"2 x 4 is DIN A7 (8 up, the default)"*. The other half of 003-card-grid's T026 *(FR-011)*
- [x] T015 `README.md` — three sites in one file, which currently contradicts itself: `:155` the cut count (A8 is three vertical and three horizontal, not one and three), `:181-183` the default and borderless card dimensions (71.75 × 50 and 74.25 × 52.5 at the default grid), `:195` *"and `a7` is the default grid"* — **51 lines after `:144` says the default is `a8`**. One task, because the three have to end up saying the same thing *(FR-011)*
- [x] T016 [P] `docs/workflow.md:328` — `# Borderless printing: full A7 cards instead of 100 × 71.75 mm`, on a build with no `--grid` *(FR-011)*
- [x] T017 `docs/testing.md:262` — the manual matrix labels the `--grid a7` column **(the default)**. **Also a decision, not only a label**: steps 17–19 are registration and cut geometry, and a tester walking them believes they are exercising the default path. Put A8 first and mark it the default, so the column order matches what a user gets *(FR-011)*
- [x] T018 `docs/index.html` — four sites: `:430` the hero facts band (`8 cards / A4 page` · `105 × 74.25 mm`, the first numbers a visitor reads), `:676` *"One vertical cut down the middle, then three horizontal ones: eight cards"*, `:680-690` the cutting **SVG and its `aria-label`**, `:691` the margin paragraph. The SVG is a drawing of a 2 × 4 sheet, so this is a design change and not a text edit — **read `docs/design.md` first** (constitution XVI) *(FR-011)*
- [x] T019 [P] `tests/test_landing_page.py:505` — the assertion **message** still says *"and A7 is the default"*. The assertion itself is correct and passes; only the explanation a failure would print is wrong. Cosmetic, and listed so the sweep is complete *(FR-011)*
- [x] T020 **Checkpoint** — `python3 scripts/check_docs.py` and `pytest tests/test_landing_page.py` both green, with the gate unchanged since T011. If a site needed the gate narrowed to pass, the gate was wrong or the site is a real exception; say which in the commit *(SC-011)*
- [x] T021 🛡 Sabotage check — put one of the fourteen sentences back and watch the gate go red, then revert. SC-011 asserts a check *fails* on reintroduction, and an assertion of absence cannot demonstrate that. Same reasoning that made 003-card-grid's CHK005 necessary *(SC-011)*

---

## Phase 5: What the fix cannot reach *(FR-014, SC-012)*

- [x] T022 Release notes for the version carrying this fix: decks written by `/cards` since v0.9.0 carry `grid: a7` and print at the size the card box does not fit. Say how to check (`grep '^grid:' cards/*.yaml`) and that removing the line or changing it to `a8` is the whole fix. **`lernkarten check` will never tell them** — FR-006's report fires on decks that are *silent*, and these state a grid. No new check: reporting every `grid: a7` deck would nag every deliberate A7 deck, the demo corpus included *(FR-014, SC-012)*
- [x] T023 [P] `specs/003-card-grid/contracts/cards-yaml-grid.md` — states *"absent means a7"* as the live contract at `:16`, `:33` and `:46`. Add a superseded-by note pointing at 009 FR-001. **Inside `specs/`, so the T008 gate must not fire on it** — this is a hand edit for a reader's sake, and a deliberate exception to the sweep

---

## Phase 6: Gates

- [x] T024 `ruff check . && ruff format --check .`
- [x] T025 `pytest` — the full suite, including the new T001/T007/T010 cases
- [x] T026 `lernkarten check cards/example.yaml`
- [x] T027 `python3 scripts/check_docs.py`
- [x] T028 One `LERNKARTEN_E2E=1` run. Not optional here: the fix touches the build's module docstring and the landing page, and `tests/test_e2e.py` skips silently without a typesetting engine *(docs/testing.md)*

---

## Dependencies

```
T001 → T002 → T003                     the behavioural fix, self-contained
T004 → T005, T006                      the generator
T007 → T008 → T009 ┐
T010               ├→ T011 → T012…T019 → T020 → T021
                   ┘                     the gate before the sweep
T022, T023                             independent of everything above
T012…T023 → T024…T028
```

**The one hard edge**: T011 gates all of Phase 4. Fixing a site before the gate
can see it is how BUG-010 happened.

## Parallel opportunities

- T001/T002 (Phase 1) and T007/T010 (Phase 3) touch different test files and can
  run together
- T012, T013, T014, T016, T019, T023 are one file each with no shared text
- T015 and T018 are **not** `[P]` with themselves — each holds several sites in
  one file that must end up consistent
