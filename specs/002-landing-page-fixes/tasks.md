---
description: "Task list for 002-landing-page-fixes"
---

# Tasks: Three landing page fixes

**Input**: Design documents from `/specs/002-landing-page-fixes/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md)

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every story opens with its failing assertions, committed red before the fix. The three claims no assertion can reach — rendered geometry and discoverability — become named rows on the manual checklist in Phase 7, per constitution XI's carve-out for layout work.

**Organization**: one phase per user story, in the spec's priority order. The three stories touch disjoint parts of one file and are independent of each other: any one can ship alone.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task serves (US1, US2, US3)
- Always name the exact file path
- 🔴 marks a task whose output must be a **failing** test before the next task begins

## Path Conventions

Only four paths change in this feature:

- The page: `docs/index.html`
- Its tests: `tests/test_landing_page.py` *(new)*
- The testing docs: `docs/testing.md`
- The feature docs: `specs/002-landing-page-fixes/`

**Phases 2 and 3 of the template are deleted, not left empty.** plan.md says *No
dependency change* and *No format change*: nothing is added to `scripts/deps.py`
or `requirements-dev.txt`, and none of the five file formats moves. There is no
`contracts/` directory for the same reason.

**One shared file drives most of the [P] markers.** All eight assertions live in
`tests/test_landing_page.py`, so test tasks are **not** parallel with each other
even across stories. The implementation tasks all edit `docs/index.html` and are
likewise serialized. What genuinely parallelises is small and marked.

---

## Phase 1: Setup

**Purpose**: get the environment able to verify the work

- [X] T001 [P] `python3 -m pip install --user -r requirements-dev.txt` — pytest and ruff
- [X] T002 [P] `scripts/install-hooks.sh` — pre-commit (no user content) and pre-push (no direct `main`)
- [X] T003 Confirm the branch: `git branch --show-current` reads `fix/landing-page`, and `git merge-base --is-ancestor origin/main HEAD` succeeds. *(Originally this checked against `feat/goal-driven-catalog`, on which the branch was stacked; feature 001 landed in `main` as PR #32 on 2026-08-19 and the branch was rebased onto it — see the base-branch assumption in [spec.md](spec.md#assumptions).)*

`make_testdata.py` and `lernkarten engine --check` are **deliberately skipped**:
this feature builds no PDF and adds no fixture, so neither the binary test
material nor the typesetting engine is needed to verify it.

---

## Phase 2: Foundational (Blocking)

**Purpose**: the two things every story needs before it can go red

- [X] T004 Create `tests/test_landing_page.py` with a module docstring saying what it guards and **why it is not in `tests/test_repo_hygiene.py`** (that module is scoped to user content and committed binaries — see [research.md R1](research.md#r1--how-does-a-landing-page-requirement-become-an-assertion-that-fails-first)); add a helper that reads `docs/index.html` from the repo root and one that parses it with `html.parser` from the standard library. No assertions yet — this task is infrastructure, not a test
- [X] T005 **Spike (thrown away)**: in a scratch file outside the repo, build the `<details>` desktop override — `summary { display: none }` above 760 px plus an explicit `display` on the panel — and open it in current Chromium, Firefox and Safari. Record in [research.md](research.md#r2--which-no-javascript-disclosure-pattern-for-the-mobile-navigation) whether the override holds against the user-agent rule, then **delete the scratch file**. *(Done: variant B, measured in Chrome 151; Gecko and WebKit are not installed here and ride on T039.)* If it fails, switch to the documented fallback (`open` in the markup, summary hidden above the breakpoint). Constitution XI: a spike is never promoted straight to a pull request

**T005 blocks T012–T014 (the US1 implementation), not T006–T008 (the US1 tests).**
Both the primary pattern and the fallback use `<details>`/`<summary>`, so the
assertions about the element and its summary hold either way — only the CSS
differs. The red tests can therefore be written while the spike runs.

**Checkpoint**: the test module exists and imports cleanly; the nav pattern is settled by observation rather than by assumption.

---

## Phase 3: User Story 1 — Every nav link is reachable on a phone (Priority: P1) 🎯 MVP

**Goal**: the four navigation links are reachable at every viewport width, with a control that says what it is, and without JavaScript.

**Independent Test**: `python3 -m pytest tests/test_landing_page.py -q` covers the structure; row 1 of the new manual checklist covers what only an eye can settle. Shipping this alone leaves a page whose navigation works.

### 🔴 Red — before any change to the page

> Each must fail **on its assertion**. A failure reading `FileNotFoundError` or `ImportError` does not count.

- [X] T006 🔴 [US1] Assertion A1 in `tests/test_landing_page.py`: no `overflow-x: auto` applies to the nav link row — red today, `.nav__links` declares it at `docs/index.html:101` (FR-001)
- [X] T007 🔴 [US1] Assertion A2 in `tests/test_landing_page.py`: the nav contains exactly one `<details>` whose `<summary>` has non-empty text content — red today, the page has no `<details>` at all. Assert on text, not on the element's presence alone: a summary holding only an SVG fails FR-002 (FR-002)
- [X] T008 🔴 [US1] Assertion A3 in `tests/test_landing_page.py`: all four nav links (`#how`, `#cards`, `#print`, `#install`) sit inside that `<details>`, and `.nav__home` and `.nav__gh` sit outside it — the second half guards FR-004's one-line bar (FR-002, FR-003, FR-004)

**Checkpoint**: `pytest tests/test_landing_page.py` is red on three assertions. Commit here.

### 🟢 Green — `docs/index.html`

- [X] T009 [US1] Wrap `.nav__links` in `<details class="nav__menu">` with `<summary>menu</summary>` at `docs/index.html:355-360`, keeping the four links, their `href` values and their order exactly as they are; leave `.nav__home` and `.nav__gh` as siblings of the `<details>` (see the tree in [data-model.md](data-model.md#the-navigation))
- [X] T010 [US1] Style the control in the stylesheet near the other nav rules: remove the default disclosure marker (`summary { list-style: none }` plus `summary::-webkit-details-marker { display: none }` for older Safari), and give it the same `label` treatment the existing nav links have — no icon carries the meaning (constitution XVI)
- [X] T011 [US1] In the `@media (max-width: 760px)` block at `docs/index.html:316-321`, make the summary the visible control; above the breakpoint hide the summary and force the panel visible, using whichever of the two patterns T005 settled on
- [X] T012 [US1] Delete `overflow-x: auto`, `scrollbar-width: none` and the `.nav__links::-webkit-scrollbar` rule at `docs/index.html:101-103` — they have nothing left to do once the row is not an overflow container (the *Anything this makes redundant* line in [spec.md](spec.md#dependency--portability-impact))
- [X] T013 [US1] Replace the comment at `docs/index.html:96-97` — it explains a sideways scroll that no longer exists. The new one says why the bar still refuses to wrap, so the next reader does not undo T009 with a `flex-wrap`

### Refactor

- [X] T014 [US1] Green now — clean up. Check the new rules sit with their neighbours rather than at the end of the stylesheet, and that the nav block still reads top to bottom

**Checkpoint**: A1–A3 green, US1 stands alone.

---

## Phase 4: User Story 2 — The band note stops inflating the section heading (Priority: P2)

**Goal**: no section note sets its heading row's height, in any of the three bands that have one.

**Independent Test**: `python3 -m pytest tests/test_landing_page.py -q`; row 2 of the manual checklist for the geometry. Shipping this alone leaves a page whose section headings sit in rows sized by their headings.

### 🔴 Red

- [X] T015 🔴 [US2] Assertion A4 in `tests/test_landing_page.py`: no `<p class="band__note">` is a child of a `<div class="band">` — red today, all three are (FR-006, FR-007)
- [X] T016 🔴 [US2] Assertion A5 in `tests/test_landing_page.py`: each `band__note` is the immediate next sibling of a `band`, and there are exactly three of them — the sibling check is what keeps the reading order in SC-004 (FR-007, SC-004)
- [X] T017 🔴 [US2] Assertion A6 in `tests/test_landing_page.py`: `.band__note` declares no `border-left`, and the `@media (max-width: 1080px)` block no longer redefines the note's borders — red today at `docs/index.html:82` and `:295` (FR-009)

**Checkpoint**: three more assertions red. Commit here.

### 🟢 Green — `docs/index.html`

- [X] T018 [US2] Move the `<p class="band__note">` out of its `<div class="band">` in all three sections — `01 the pipeline` (`:420`), `03 print it, cut it` (`:590`) and `04 install` (`:669`) — making each the band's immediate next sibling. **Do not touch section `02`**: its band holds a `.toggle` button, not a note (`:502`)
- [X] T019 [US2] Rewrite `.band__note` at `docs/index.html:81-84`: drop `width: 400px` for full width, drop `border-left`, add `border-bottom: var(--rule)`. **No `border-top`** — the band's existing `border-bottom` already separates heading from note, and adding one would stack into a 4 px rule (FR-009)
- [X] T020 [US2] In the `@media (max-width: 1080px)` block, delete `.band__note { width: 100%; border-left: 0; border-top: var(--rule) }` (`:295`) and `.install .band__note { border-top-color: var(--sand) }` (`:296`) — both existed only to fake this arrangement on narrow screens. **Keep `.band { flex-wrap: wrap }` (`:293`) and `.band h2 { flex-basis: calc(100% - 72px) }` (`:294`)**: section `02`'s toggle still needs them (`:297`). This is the one deletion that could quietly break something the bug report never mentions
- [X] T021 [US2] Change `.install .band__note` at `docs/index.html:257` from `border-left-color: var(--sand)` to `border-bottom-color: var(--sand)`; the selector itself needs no change, because it is rooted at `.install`, not at `.band`, and still matches after the move (FR-010)

**Checkpoint**: A4–A6 green. `01`, `03` and `04` restructured, `02` untouched.

---

## Phase 5: User Story 3 — "show the back" turns the card over (Priority: P3)

**Goal**: the `hidden` attribute takes effect against every element on the page.

**Independent Test**: `python3 -m pytest tests/test_landing_page.py -q`; row 3 of the manual checklist for the interaction and the no-JS fallback.

### 🔴 Red

- [X] T022 🔴 [US3] Assertion A7 in `tests/test_landing_page.py`: the stylesheet contains a `[hidden]` rule declaring `display: none` **with `!important`** — red today, the file has no `[hidden]` rule anywhere. Assert the `!important` explicitly: without it the rule is a no-op, because `[hidden]` and `.card` tie at specificity (0,1,0) and `.card` wins on source order (FR-012, [research.md R4](research.md#r4--how-is-the-hidden-attribute-made-effective-without-setting-a-new-trap))

**Checkpoint**: red. Commit here.

### 🟢 Green — `docs/index.html`

- [X] T023 [US3] Add `[hidden] { display: none !important; }` to the reset near `docs/index.html:40`, beside `*, *::before, *::after { box-sizing: border-box }`, with a one-line comment saying why `!important` is right here — `hidden` is a statement that the element is not relevant, not a style preference

**No markup change.** The cards and the button are already correct: both cards
are authored without `hidden` (`:507`, `:527`) and only the script sets it, which
is why the no-JS fallback works today and is unaffected. Out of scope by the
maintainer's decision: relabelling the cards, moving the button, or dropping the
toggle — those stay open on issue #28.

**Checkpoint**: A7 green.

---

## Phase 6: Regression guard & docs

- [X] T024 [P] Assertion A8 in `tests/test_landing_page.py`: the file holds exactly one `<script>` block and no external stylesheet, script or image reference. **Green today** — label it in the test as a regression guard, not as a red assertion, so nobody looks for a failure that cannot exist without breaking the page on purpose (FR-014, SC-007)
- [X] T025 [P] Add a `page` row to the automated-levels table in `docs/testing.md:111-117`: `tests/test_landing_page.py` | page | the structure of the landing page — the seven other levels are listed there and this one is new
- [X] T026 Add a landing-page subsection to the manual checklist in `docs/testing.md` (after the numbered pipeline steps) with the three rows from [plan.md](plan.md#test-plan-first), each naming the viewport width and the JavaScript state to test at. "On a phone" is not reproducible; 360 px is
- [X] T027 Confirm every relative link added to `docs/testing.md` resolves — `python3 scripts/check_docs.py` fails on a dead one

`docs/design.md` needs **no** change: nothing in it becomes untrue. The page is
still flat colour and type, still one self-contained file, and the step strip's
measure rule is untouched. `README.md` is issue #26, not this feature. No brand
PNG is re-rendered — `assets/brand/` is untouched, so `scripts/render_brand.py`
is not run.

---

## Phase 7: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

- [X] T028 [P] `ruff check .`
- [X] T029 [P] `ruff format --check .`
- [X] T030 `pytest`
- [X] T031 [P] `bin/lernkarten check cards/example.yaml`
- [X] T032 [P] `python3 scripts/check_docs.py`
- [X] T033 Evidence for SC-008: check out the parent commit, run `pytest tests/test_landing_page.py -q`, confirm **seven** assertions fail on their assertions (A8 is the guard and passes), and paste the output into the pull request
- [X] T034 `git status` clean of user content — no `sources.yaml`, `knowledge/`, `catalog/`, non-example `cards/`, `output/`, no binaries
- [X] T035 Push the branch and open a pull request against **`main`** — [PR #35](https://github.com/mhabedank/lernkarten/pull/35). Feature 001 landed in main as PR #32, so the stacking this task originally described no longer applies. Confirm commit subjects use the `fix:`, `test:` and `docs:` prefixes

**Deliberately skipped, with the reason stated rather than silently dropped**:
`make_testdata.py`, the `LERNKARTEN_E2E=1` suites, `check_project.py --strict`,
the borderless and other-language builds, and the Python-floor build. This
feature touches no pipeline step, no fixture, no card and no PDF — running them
would prove nothing about it. They stay in CI, where they guard the rest.

---

## Phase 8: By Hand

**Purpose**: the three claims no assertion in this repo can reach. Constitution XI allows the split for layout work only on condition that these are named, so they are numbered here and land in `docs/testing.md` at T026.

Open `docs/index.html` directly — no server, no build.

- [X] T036 **Navigation, at 360 px**: the bar is one line at rest; the control reads as a word; opening it shows all four links; following `install` arrives at the install section; the control takes keyboard focus and opens with Enter or Space. Then **disable JavaScript and repeat** — this is FR-003 and the row most likely to be skipped. Widen past 760 px: the bar is the row it is today
- [X] T037 **Section bands, above 1080 px**: the heading rows of `01`, `03` and `04` are the same height and none is taller than its heading needs; each note is a full-width block directly under its band; every rule is single — no doubled 4 px rule, none missing; `04 install` keeps `--sand` on `--ink` with a `--sand` rule beneath. Then narrow below 1080 px and confirm the reading order is unchanged in all four sections: number, heading, note, content
- [X] T038 **The card toggle**: on load exactly one card and "show the back"; click swaps it and the label; click again returns. Then **disable JavaScript and reload** — both cards side by side, no button
- [X] T039 Repeat T036 in the three engines the spike covered — Chromium, Firefox and Safari. *(All three pass: Chromium measured headless, Safari by hand, Firefox 154 after it was installed. Firefox also supplied the 360 px measurement Chrome's 500 px window clamp had made impossible — see research.md R2.)* CI has no browser leg and will not grow one for this feature, so this is the only place the cross-browser claim is checked

**Known and not a regression** — name these so a reviewer does not file them
again: the toggle still does not explain itself (the open half of issue #28), the
notes are still 14 px against a 15 px floor (issue #30, frozen here by FR-011),
and the README still buries the landing page (issue #26).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: no dependencies
- **Foundational (2)**: T004 blocks every red task; T005 blocks only US1's implementation
- **US1 (3)**, **US2 (4)**, **US3 (5)**: each depends on T004. They do **not** depend on each other
- **Docs (6)**: after the behaviour it describes settles
- **Gates (7)**: last
- **By Hand (8)**: after the gates pass

### Story Independence

The three stories touch disjoint regions of `docs/index.html` — the nav block,
the three band sections, and the reset — and disjoint requirements. Any one can
ship alone and be verified alone. US1 is the MVP: it is the only one of the three
that hides functionality rather than looking wrong.

### Within a Story

1. 🔴 All assertions, seen failing — commit at the checkpoint
2. 🟢 The change to `docs/index.html`
3. Refactor

Never move an implementation task above its test. That is the one rule here with
no exception (constitution XI).

### Parallel Opportunities

- T001 and T002 together
- T005 (the spike) runs alongside T006–T008 (US1's red tests) — the assertions hold for both the primary pattern and the fallback
- T024 and T025 are different files
- T028, T029, T031 and T032 are independent commands; only T030 must follow the implementation

### Not Parallel

- 🔴 and 🟢 for the same behaviour. Ever
- **All test tasks with each other.** T006–T008, T015–T017, T022 and T024 all write `tests/test_landing_page.py`. Serialize them, even across stories — this is the single biggest [P] trap in this feature
- **All implementation tasks with each other.** T009–T013, T018–T021 and T023 all edit `docs/index.html`
- T026 and T025 both edit `docs/testing.md`

---

## Notes

- **Test-first, always.** Seven assertions must be seen failing. T033 captures the evidence for SC-008
- **The spike is thrown away** (T005). A spike never goes straight into a pull request
- **T020 is the dangerous task.** Deleting the wrong rule from the 1080 px block breaks section `02`'s toggle, which no assertion covers and which the bug report never mentions
- **T007 asserts on text, not presence.** A `<summary>` holding only a hamburger glyph would pass a naive check and fail FR-002
- **T022 asserts `!important`.** Without it the rule is a no-op — the whole point of [research.md R4](research.md#r4--how-is-the-hidden-attribute-made-effective-without-setting-a-new-trap)
- **The PR targets `main`** (T035). It was stacked on `feat/goal-driven-catalog` until that landed as PR #32; the branch has since been rebased onto `main`
- Commit after each task or logical group, and always at a 🔴 checkpoint

---

## Phase 9: Bugfix (BUG-006)

**Bugfix**: 2026-08-19 — [BUG-006](bugs/BUG-006.md) Updated from bugfix patch.

**Purpose**: the landing page sets Archivo running prose below the 15 px floor
that `docs/design.md` and constitution XVI both state, in four places. This
feature's own spec asserted the floor, exempted the note from it, and certified
the page as compliant — three readings that do not survive being read together.
FR-016 settles the page; FR-017 settles the rule.

**No manual checklist row.** Unlike the three bugs this feature was written for,
nothing here is about rendered geometry: a `font-size` is a declaration in the
stylesheet, so the assertion reaches all of it.

### 🔴 Red

- [X] T040 🔴 Assertion A9 in `tests/test_landing_page.py`: no rule setting
      Archivo running prose declares a `font-size` below 15 px — red today on
      **six** declarations, not the four issue #30 named — `.rule-item p`
      (13.5 px) and `.principle p` (14.5 px) were found by asking the question of
      the whole stylesheet instead of of a list, which is the argument for
      writing the exemption as a rule. Exempt the Jost
      `label` runs and the IBM Plex Mono literals **by name**, and say in the
      test why each exemption is one — an exemption list nobody can read becomes
      a place to hide the next violation (FR-016)

**Checkpoint**: one assertion red on four declarations. Commit.

### 🟢 Green — `docs/index.html`

- [X] T041 Raise the four to 15 px. `.print__cut p` is 13 px and rises with the
      other three rather than to its own size — the anatomy and printing
      descriptions are the same kind of text and there is no reason for them to
      differ (FR-016)
- [X] T042 The inline `style` at `:624` is the only one of the four not in the
      stylesheet. Give it the class the paragraph beside it would have used, so
      A9 does not have to parse inline styles forever (FR-016)

### 🟢 Green — the rule

- [X] T043 [P] `docs/design.md`: the floor sentence at `:55` says which faces it
      binds — Archivo reading prose yes, Jost `label` runs and Plex Mono literals
      no. It scopes the rule; it does not relax it (FR-017)
- [X] T044 [P] `.specify/memory/constitution.md`: the same scope on principle
      XVI, and a version bump with the amendment line the file's own governance
      section requires (FR-017)

### By hand

- [ ] T045 **Still open — the one thing here nobody has looked at.** Above 1080 px and at 360 px: the three section notes, the anatomy
      list and the printing descriptions still sit where T037 left them, and no
      band's heading row grew. This is the check that the coupling really is
      gone rather than merely believed to be

### Gates

- [X] T046 `pytest tests/test_landing_page.py` — nine assertions, A9 green
- [X] T047 `python3 scripts/check_docs.py` — T043 and T044 add links
- [X] T048 Evidence for SC-010: on the parent commit A9 fails naming four
      declarations; on the merge commit it passes

### Dependencies

- T040 before T041 and T042 — the one rule with no exception here
- T043 and T044 are different files and may run together
- T045 after T041 and T042
