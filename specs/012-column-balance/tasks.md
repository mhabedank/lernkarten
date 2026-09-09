---
description: "Task list for 012-column-balance"
---

# Tasks: The landing page's two-column sections carry their weight

**Input**: Design documents from `/specs/012-column-balance/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [quickstart.md](quickstart.md). No `contracts/` —
no file format is touched.

**Tests**: **Test-first is mandatory and not waivable** (constitution XI). Every
story opens with its assertion, committed *failing on its assertion* before the
markup moves.

**Organization**: grouped by user story so each can be shipped and verified alone.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which user story the task serves (US1, US2, US3)
- Always name the exact file path
- 🔴 marks a task whose output must be a **failing** test before the next begins

## Path Conventions

This feature touches four files, three of them documentation:

- `docs/index.html` — the page; markup and CSS
- `docs/design.md` — the two-column rule
- `docs/testing.md` — the by-hand rows
- `tests/test_landing_page.py` — the four assertions
- `.specify/memory/constitution.md` — one bullet in XVI

**The single biggest `[P]` trap in this feature**: all four assertions write
`tests/test_landing_page.py`, and all three markup moves write
`docs/index.html`. Almost nothing here is parallel. See *Not Parallel* below.

---

## Phase 1: Setup

**Purpose**: know the numbers before touching anything, so "better" can be
demonstrated rather than asserted.

- [X] T001 Record the baseline. Measure both sections in a browser against the
      current `docs/index.html` and write the figures into the pull request
      description: section 02 is 269 px of content in a 644 px cell, section 03
      is 327 px in 1176 px. Re-derive them rather than copying from
      [spec.md](spec.md) — if they no longer reproduce, `main` has moved and this
      plan needs re-reading. **The measuring trap is in
      [quickstart.md](quickstart.md#measuring-instead-of-eyeballing)**: `.sheet`
      is stretched and is not ink

**Checkpoint**: the "before" is a number, not a memory. This is the step whose
absence let BUG-011 ship.

---

## Phase 2: Dependencies

**⚠️ Skipped entirely** — [plan.md](plan.md#dependency-decisions) says *No
dependency change*.

---

## Phase 3: Format Contracts

**⚠️ Skipped entirely** — [data-model.md](data-model.md) says *No format change*.
None of the four formats is read or written.

---

## Phase 4: User Story 1 — Section 02 shows the card it is talking about (Priority: P1) 🎯 MVP

**Goal**: both card faces visible at every width, no toggle, and the four
explanations beside them all checkable against what is on screen.

**Independent Test**: `python3 -m pytest tests/test_landing_page.py -q` covers
the structure; rows 1, 2 and 5 of [quickstart.md](quickstart.md#3-the-proportion-by-hand)
cover what only an eye can settle. Shipping this alone leaves a section whose
picture matches its prose.

### 🔴 Red — the tests, before any implementation

- [X] T002 🔴 [US1] Assertion **A11** in `tests/test_landing_page.py`: no element
      inside `.anatomy__cards` carries a `hidden` attribute, **and** the page
      declares no element with class `toggle`. Red today on both halves — the
      script gives `#card-back` `hidden` on load and `button.toggle#flip` sits in
      the band. Assert **both**, and say in the test why: deleting the button
      while the script still sets `hidden` leaves one card and no way back;
      deleting the script while the button stays leaves a dead control. Either
      half alone passes a half-done removal *(FR-001, FR-002)*
- [X] T003 🔴 [US1] Restate **A14** in `test_the_page_stays_one_self_contained_file`:
      **at most one** `<script>` block, not exactly one. Green today at one and
      green after at zero. Do **not** weaken it to "any number" — the rule it
      defends is "one self-contained file with almost no script", and a page that
      grows a *second* script has left that rule whether or not the first was
      removed. Leave the `EXTERNAL_SUBRESOURCES` half untouched. Record in the
      docstring that this supersedes SC-007 and FR-014 of feature 002 *(FR-011)*

**Checkpoint**: `pytest tests/test_landing_page.py` is red on A11, and A14 is
green-but-restated. Commit here.

### 🟢 Green — `docs/index.html`

- [X] T004 [US1] Delete `button.toggle#flip` from the `02` band at
      `docs/index.html:573`, leaving `.band__no` and the `<h2>` as the band's two
      children (the tree in [data-model.md](data-model.md#section-02--one-card-one-idea))
- [X] T005 [US1] Delete the entire `<script>` block. The page now has zero. Its
      comment — *"The one piece of behaviour on the page"* — goes with it; there
      is no behaviour left to describe *(FR-002)*
- [X] T006 [US1] Delete the `.toggle` base rule and its `@media (max-width: 1080px)`
      override. Then delete `.band { flex-wrap: wrap }` and
      `.band h2 { flex-basis: calc(100% - 72px) }` from that same block — the
      comment above them says *"Only section 02 still has a child that needs
      this"*, and the toggle **is** that child ([research.md R5](research.md#r5--what-else-does-the-toggle-take-with-it)).
      Delete the comment with the rules it explains
- [X] T007 [US1] **Keep** the `[hidden]` reset and adjust the comment beside it at
      `docs/index.html:44`, which currently explains the toggle. It stays as a
      *reset* against a class of bug — an author `display` outranking the
      user-agent rule — not as the toggle's fix. Deleting it with its one caller
      would re-arm that class silently. This is a comment edit and a deliberate
      non-deletion, which is why it is its own task *(FR-012)*. T002 goes green

**Checkpoint**: A11 green, section 02 shows two cards with and without
JavaScript, and nothing dead is left in the stylesheet.

---

## Phase 5: User Story 2 — Section 03 puts the pictures with the pictures (Priority: P2)

**Goal**: the cutting diagram beside the sheets, the card box full width beneath
both columns, and no hole under either.

**Independent Test**: the structure assertions, plus rows 3 and 4 of
[quickstart.md](quickstart.md#3-the-proportion-by-hand). Shipping this alone
leaves a printing section with no hole in it.

### 🔴 Red — the tests, before any implementation

- [X] T008 🔴 [US2] Assertion **A12** in `tests/test_landing_page.py`:
      `.print__box` is not a descendant of `.print__rules`, and is a following
      sibling of `.print`. Red today — it is the last child of `.print__rules`.
      Write it in the idiom of `test_no_band_note_is_a_child_of_its_band` and
      `test_every_band_note_follows_its_band`, which assert the same shape for
      the move this one copies *(FR-003)*
- [X] T009 🔴 [US2] Assertion **A13** in `tests/test_landing_page.py`:
      `.print__cut` is a descendant of `.print__sheets`. Red today — it is a
      child of `.print__rules`. **Not parallel with T008**: same file *(FR-004)*

**Checkpoint**: A12 and A13 red on their assertions. Commit here.

### 🟢 Green — `docs/index.html`

- [X] T010 [US2] Move `.print__cut` from `.print__rules` into `.print__sheets`,
      as its third child, after the two `.sheet` blocks
- [X] T011 [US2] Adjust the `.print__cut` rule for its new home: drop `flex: 1`
      and `justify-content: center` — both written for its old life as filler at
      the bottom of a text column — and drop the padding that now duplicates the
      40 px `.print__sheets` already applies ([research.md R2](research.md#r2--where-does-the-cutting-diagram-go-and-what-does-it-cost)).
      Same file as T010, so **not** parallel with it
- [X] T012 [US2] Move the whole `.print__box` block out of `.print__rules` to
      become a sibling of `.print`, inside `#print`. It moves **as one unit**:
      heading, `card-box.pdf` link, the `--dividers 4` paragraph with its
      `leitner.html` link, and the `.print__box-note` caption. **The HTML comment
      above it moves with it** — it records why the href is relative and dead
      when opened off disk, and it is the only place that is written down *(FR-005)*
- [X] T013 [US2] Get the rules right at the new boundaries: `.print__box` keeps
      its `border-top` and must **not** gain a `border-bottom` — `#print` already
      carries one inline, and a second doubles it. Check the table in
      [data-model.md](data-model.md#the-rules-between-the-blocks); this is the
      detail [research.md R1](research.md#r1--how-does-a-block-leave-a-column-and-become-full-width)
      names as most likely to be got wrong *(FR-006)*. T008 and T009 go green
- [X] T014 [US2] Check the narrow widths rather than assuming them: below 1080 px
      the box was already full width via `.print__rules { width: 100% }`, and
      below 760 px the diagram inherits `.print__sheets { min-width: 0 }`, which
      is what stops that column holding the page open at 320 px
      ([research.md R6](research.md#r6--does-anything-below-1080-px-break)) *(FR-007)*

**Checkpoint**: A12 and A13 green; US1 and US2 both stand on their own.

---

## Phase 6: User Story 3 — The next feature cannot reopen the hole (Priority: P3)

**Goal**: a rule a contributor reads *before* adding a block, and a constitution
that points at it.

**Independent Test**: revert either markup move and an assertion goes red naming
its section (SC-006).

- [X] T015 [US3] Add the two-column rule to `docs/design.md` § *The screen
      surfaces*: a two-column section is proportioned by its heavier column, so a
      new block joins the column whose *kind* it is — pictures with pictures,
      prose with prose. A block belonging to neither kind, or one that would make
      a column outgrow the other by more than about half, becomes a full-width
      block beneath both, the way the section notes did. Name both worked
      examples. **No numeric threshold**: the assertions are structural and could
      not enforce one, and false precision invites arguing about the number
      instead of looking at the page ([research.md R4](research.md#r4--what-does-the-design-rule-say-and-where-does-it-live)) *(FR-008)*
- [X] T016 [P] [US3] Add one bullet to constitution XVI in
      `.specify/memory/constitution.md` pointing at that rule, in the shape the
      type floor already has there. Different file from T015, so parallel with it
      — but the wording depends on T015, so write T015 first *(FR-008)*
- [X] T017 [US3] Verify the assertions actually bite, one revert at a time, using
      the table in [quickstart.md](quickstart.md#1-the-assertions). Each of the
      four must fail and name its section. An assertion that passes both before
      and after its move is not a guard *(SC-006, FR-009)*

**Checkpoint**: the rule exists, the constitution points at it, and each
assertion has been seen failing for its own reason.

---

## Phase 7: Docs & Cross-Cutting

- [X] T018 Add the by-hand rows to `docs/testing.md` § *The landing page*,
      continuing the existing numbering: both sections' proportion above 1080 px,
      the four explanations checked against two visible cards, every rule at the
      moved boundaries single, and the sections at 360 px. Every link added must
      resolve or `check_docs.py` fails
- [X] T019 Update the `docs/testing.md` line that says the landing-page module
      *"reads `docs/index.html`; it never renders it"* — still true, and now the
      reason four of its assertions are about arrangement rather than proportion.
      Say so there, where the next person writing an assertion will read it
- [X] T020 Note in `specs/002-landing-page-fixes/spec.md` that FR-013, SC-005 and
      SC-006 are superseded by this feature, and that FR-014 and SC-007 are
      restated by FR-011. Strikethrough with a reason, the convention BUG-006
      established there — a shipped requirement is retired in writing, never by
      silence

---

## Phase 8: Gates

**Purpose**: exactly what CI checks. All green before the pull request.

- [X] T021 [P] `ruff check . && ruff format --check .`
- [X] T022 [P] `pytest`
- [X] T023 [P] `lernkarten check cards/example.yaml`
- [X] T024 [P] `python3 scripts/check_docs.py` — matters more than usual here:
      T015, T016 and T018 all add links
- [X] T025 `LERNKARTEN_E2E=1 pytest tests/test_e2e.py` once before the PR, per
      `CLAUDE.md`. Nothing here touches the build, so this is a formality — but
      it is a required one

---

## Phase 9: By Hand

**Purpose**: the proportion itself, which no assertion in this repository can
reach. Constitution XI allows the split for layout work only on condition that
these are named, so they are numbered here and land in `docs/testing.md` at T018.

Open `docs/index.html` straight off disk — no server, no build.

- [X] T026 **Both sections, above 1080 px**: two cards filling the column in
      `02`; sheets and diagram left, three rules right, box full width beneath in
      `03`. No hole under either column. Then **measure** rather than judge:
      section 02 at 564 px of content in 644 px, and section 03 with **both**
      columns closing together at 433 px — not the sheets column alone, which is
      how the first attempt passed while leaving 161 px under the rules
      ([BUG-012](bugs/BUG-012.md)). At 1120, 1280, 1440 and 1800 px
      *(SC-001, SC-002, SC-003)*
- [X] T027 **The four explanations against the two cards**: header band, field,
      footer band, note space — all visible. Three of the four differ front to
      back, which is the argument for two cards that is not about layout at all
- [X] T028 **Every boundary in `03`**: each rule single. None doubled where the
      box meets the columns, none missing. Compare against the previous commit
      rendered beside it, not from memory — that is the instruction BUG-011
      added to row 24 after the last time a by-hand row passed something broken
- [X] T029 **360 px**: one column per section, reading order unchanged, nothing
      holding the page open sideways *(FR-007, SC-007)*
- [X] T030 Repeat T026 and T028 in Chromium, Firefox and Safari. CI has no
      browser leg and will not grow one for this page, so this is the only place
      the cross-engine claim is checked. Safari needs *Allow remote automation*
      switched on by hand if it is driven rather than clicked

**Known and not a regression** — name these so a reviewer does not file them
again: `T045` of feature 002 is still open and tracked in
[#101](https://github.com/mhabedank/lernkarten/issues/101).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: no dependencies, but T001 must happen *before* any markup moves
  or the baseline is gone
- **Dependencies (2)** and **Format Contracts (3)**: skipped, nothing to do
- **US1 (4)**, **US2 (5)**: independent of each other — different sections,
  different assertions. Either can ship alone
- **US3 (6)**: depends on both, because the rule it writes describes what they
  did. Writing it first would be writing it from a plan rather than from a page
- **Docs (7)**: after the behaviour settles
- **Gates (8)**: last
- **By Hand (9)**: after the gates pass

### Story Independence

US1 and US2 touch disjoint regions of `docs/index.html` — the `02` band and card
column, and the `03` print columns — and disjoint requirements. **US1 is the
MVP**: it is the section that teaches the format the whole project is about, and
the only one whose gap was introduced by a fix rather than accreted.

They are *not* parallel despite being independent, because they edit the same
two files. Sequential, either order.

### Within a Story

1. 🔴 All assertions, seen failing — commit at the checkpoint
2. 🟢 The markup move
3. 🟢 The CSS that goes with it
4. The narrow-width check

Never move an implementation task above its test. That is the one rule here with
no exception (constitution XI).

### Parallel Opportunities

Genuinely few, and the honest list is short:

- T015 and T016 are different files (but write T015 first — T016 quotes it)
- T021–T024, the four gates, are independent commands
- Nothing else

### Not Parallel

- 🔴 and 🟢 for the same behaviour. Ever
- **All four assertions with each other.** T002, T003, T008 and T009 all write
  `tests/test_landing_page.py`. Serialize them, even across stories — this is the
  single biggest `[P]` trap in this feature, and feature 002's list of the same
  trap went stale by omitting six of its fifteen writers. Do not let this one
  drift the same way
- **All markup and CSS tasks with each other.** T004–T007 and T010–T014 all edit
  `docs/index.html`
- T018 and T019 both edit `docs/testing.md`

---

## Notes

- **Test-first, always.** A test written after the code tells you what the code
  does; only a test seen failing tells you it does what was asked.
- **T001 is not ceremony.** BUG-011 shipped because a by-hand row was checked
  against a "before" that was already committed and gone. Measure first.
- **T007 is a non-deletion on purpose.** The `[hidden]` reset outlives its one
  caller. A task that says "keep this" exists because the obvious move is to
  delete it.
- **T020 retires two shipped requirements.** Strikethrough with a reason, never
  silent deletion — the trail is what lets the next reader tell a decision from
  an oversight.
- Commit after each task or logical group, and always at a 🔴 checkpoint.

---

## Bugfix (BUG-012)

**Bugfix**: 2026-09-08 — [BUG-012](bugs/BUG-012.md) Updated from bugfix patch.

**No task is reopened, and no task is added.** T026's target figures were wrong
and are corrected in place; the work it names was performed, and performing it is
what found the defect. The neighbouring row T028 — *"look at every boundary in
`03`"* — is what actually caught it: the automated measurement reported 0 % and
was not lying, because it measured the one column SC-002 named.

That is the whole value of this phase existing. Constitution XI allows layout
work to split its verification only on condition the manual claims are named, and
this is the second time in two features that the named manual row caught what the
assertions could not. The first was BUG-011, where the row existed and was
checked from memory; here it existed and was walked.

**Corrected, not reopened**: T026 (`docs/testing.md` figures, both columns).
**Unchanged**: everything else. Phases 1–9 stand as completed.
