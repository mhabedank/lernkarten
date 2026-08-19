# Implementation Plan: Three landing page fixes

**Branch**: `fix/landing-page` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-landing-page-fixes/spec.md`

## Summary

Three reported bugs in `docs/index.html` — a mobile navigation whose links are
unreachable, three section notes that inflate their heading rows, and a card
toggle defeated by a CSS specificity tie. All three are fixed in one file with
markup and CSS only: a `<details>`-based disclosure for the nav, the notes moved
out of their bands, and one global `[hidden]` rule. The verification splits in
two, because no test here can measure rendered geometry: a new
`tests/test_landing_page.py` asserts the structure and goes red first, and a new
landing-page subsection in `docs/testing.md` carries the visual claims by name.

## Technical Context

The project's values are unchanged by this feature and are not restated. What
this feature narrows them to:

**Language/Version**: no Python changes to the shipped code. The only Python
written is a new test module, on the same floor as the rest — 3.12.

**Secondary language**: none. No Typst is touched: the card, the press sheet and
`assets/brand/*.typ` are all untouched, so no brand PNG is re-rendered.

**Runtime dependencies**: unchanged. `pyyaml==6.0.3` and nothing else.

**Dev dependencies**: unchanged. The new test module uses `pytest` and the
standard library's `html.parser`; neither is new.

**Storage**: not involved. This feature reads and writes no user artifact.

**Testing**: pytest, one new module at a new *page* level, plus a new subsection
on the manual checklist. Test-first is mandatory and the red assertions are
listed under *Phase 1* below.

**Target Platform**: for the first time in this repo, the platform that matters
is a **browser**, not an operating system. The fix must hold in current Chromium,
Firefox and Safari. CI has no browser leg and will not grow one for this — that
is why R2's override carries a spike and why the visual rows exist.

**Project Type**: unchanged. This touches the published documentation surface,
not the CLI and not the plugin.

**Constraints**: `docs/index.html` stays one self-contained file with exactly one
`<script>` block and no external asset; flat colour and type only; reading text
never below its current size (see FR-011 and issue #30).

**Scale/Scope**: one HTML file of ~750 lines, one new test module, two doc edits.

## Dependency Decisions

**No dependency change.** No Python package, no dev tool, no self-fetched binary
is added, removed or moved. The vetting tables are deleted as the template
instructs.

One reuse note belongs here anyway, because constitution III applies to code as
well as to packages: the structural assertions that ask "is this element a child
of that one" use `html.parser` from the standard library rather than a regular
expression. A regex over nested markup is exactly the hand-rolled parser the
principle exists to prevent, and the standard library already answers the
question. Text-level matching is kept only for the CSS assertions, where there is
no tree to walk and `tests/test_repo_hygiene.py` already reads this file as text.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Pass? |
|---|---|---|
| I | The halves stay coupled only through the file formats | [x] Neither half is touched. No skill, no script, no format. |
| II | **(GATED)** Dependencies install cleanly / binaries self-fetch | [x] Nothing added. |
| III | **(GATED)** Nothing hand-rolled that a vetted library does | [x] `html.parser` used instead of a regex for tree questions — see *Dependency Decisions*. |
| IV | **(GATED)** Vetting table completed for each new dependency | [x] N/A — none. |
| V | Code lands in an existing module where one fits | [!] One new file, `tests/test_landing_page.py`. Three existing modules were considered and rejected in [research.md R1](research.md#r1--how-does-a-landing-page-requirement-become-an-assertion-that-fails-first); it gets a docstring saying what it guards. Recorded in Complexity Tracking. |
| VI | Script imports stay acyclic; readers stay leaves | [x] No `scripts/` file changes. |
| VII | **(GATED)** No user content committed | [x] Only `docs/`, `tests/` and `specs/`. |
| VIII | No binaries committed | [x] No asset added — the nav control is a word, not an icon file. |
| IX | Typst sources edited, never generated files | [x] No Typst touched, nothing in `output/`. |
| X | Skill frontmatter valid | [x] No skill touched. |
| XI | **(NON-WAIVABLE)** Every behaviour tested first | [x] Eight assertions listed in *Phase 1*, each red before its fix. The three claims no test can reach are named on the manual checklist rather than left implicit — constitution XI's own carve-out for layout, used explicitly and not as a loophole. |
| XII | The four gates pass; ruff not loosened | [x] Ruff config untouched; the new test module is ordinary Python under `tests/`. |
| XIII | English throughout | [x] |
| XIV | Branch `<prefix>/<short-kebab-name>`; `main` untouched | [x] `fix/landing-page`, cut from the tip of `feat/goal-driven-catalog` and rebased onto `main` once that landed as PR #32 — see the base-branch assumption in the spec. |
| XV | Engine version unchanged, or all checksums bumped | [x] `scripts/engine.py` untouched. |
| XVI | `docs/design.md` read before a visible change | [x] Read, and it bound three decisions: the control is a word rather than a hamburger glyph (colour and shape never carry meaning alone), the page stays one self-contained file, and note type size is frozen at 14 px so this feature does not pre-empt issue #30. No brand PNG needs re-rendering — `assets/brand/` is untouched and the step strip's own geometry does not change. |
| XVII | Card style and Typst escaping respected | [x] No card content involved. |

**Open-item check**: the constitution's one remaining open item is that
dependencies are pinned by version rather than by hash. This feature adds no
dependency, so it neither closes the item nor works around it. It is untouched.

## Project Structure

### Documentation (this feature)

```text
specs/002-landing-page-fixes/
├── plan.md               # This file
├── spec.md               # Phase -1
├── research.md           # Phase 0 — R1..R5
├── data-model.md         # Phase 1 — no format change; the DOM change instead
├── quickstart.md         # Phase 1 — how to verify, by command and by eye
├── checklists/
│   └── requirements.md   # spec quality checklist
└── tasks.md              # Phase 2 (/speckit-tasks — NOT created here)
```

No `contracts/` directory. The template scopes it to the file formats that
couple the two halves, and this feature touches none of them. There is nothing
to put there but a file saying so.

### Source Code (repository root)

Only four paths change. The rest of the tree is untouched and is not restated:

```text
docs/
├── index.html              # CHANGED — all three fixes; the only shipped file that changes
└── testing.md              # CHANGED — a new landing-page subsection on the manual
                            #   checklist, and a new row in the automated-levels table

tests/
└── test_landing_page.py    # NEW — structural assertions over docs/index.html
```

**Structure Decision**: the feature is one file plus its verification. The new
test module is the only addition, and constitution V's question — which existing
module was considered first — is answered in research.md R1 with the three
candidates and the reason each fails. `docs/testing.md` changes twice because its
two halves are both incomplete for this surface: the automated table has no *page*
level, and the manual checklist has no landing page rows at all.

### The two halves

**Model-driven work** (`skills/`): none. No prompt changes, so no
`check_project.py` check is needed or possible.

**Deterministic work**: `docs/index.html`, covered by the new
`tests/test_landing_page.py`. The red assertions and their order are in *Phase 1*.

**The seam**: none — the halves are untouched. This feature sits beside them, on
the documentation surface.

## Phase 0: Research

Complete. Five questions, all resolved, in [research.md](research.md):

| | Question | Answer |
|---|---|---|
| R1 | How does a landing page requirement become a failing assertion? | New `tests/test_landing_page.py` at a new *page* level; `html.parser` for tree questions; what it can and cannot assert is spelled out |
| R2 | Which no-JS disclosure pattern for the nav? | `<details>`/`<summary>`; `:target` and the checkbox hack rejected with reasons; **one spike needed** |
| R3 | How does the note leave the band without breaking the rules? | Sibling below the band, `border-bottom` not `border-top`; the install selector survives; the `flex-wrap` rule must **not** be deleted |
| R4 | How is `[hidden]` made effective? | `[hidden] { display: none !important }` — the specificity tie makes the gentler options no-ops |
| R5 | Where do the manual entries go? | A new landing-page subsection in `docs/testing.md` |

**The one open technical risk** is R2's desktop override: hiding the `<summary>`
above 760 px and forcing the panel visible relies on overriding the user-agent
rule that hides a closed `<details>`' children, and that rule has changed shape
across browser versions. It is a spike — built in a scratch file, checked in
three engines, then thrown away — and it is the first task, before any test is
written, because a red assertion for a pattern that does not work is wasted work.
research.md records the fallback if it fails.

## Phase 1: Design

### The change, file by file

**`docs/index.html` — the reset.** One rule added near the top, with the other
reset rules: `[hidden] { display: none !important; }`. Fixes US3 entirely.

**`docs/index.html` — the navigation.** `.nav__links` becomes the panel of a
`<details>` whose `<summary>` reads `menu`. Above 760 px the summary is hidden
and the panel forced visible; below it, the summary is the control. The
`overflow-x: auto`, `scrollbar-width: none` and `::-webkit-scrollbar` rules are
deleted along with the comment that justified them, and a new comment says why
the bar still refuses to wrap.

**`docs/index.html` — the three bands.** In sections `01`, `03` and `04`, the
`<p class="band__note">` moves out of `<div class="band">` to become its next
sibling. `.band__note` loses `border-left`, gains `border-bottom`, and drops its
fixed `width: 400px` for full width. In the `@media (max-width: 1080px)` block
the three note rules go; **`.band { flex-wrap: wrap }` and the `h2` flex-basis
stay** — section `02`'s toggle still needs them. `.install .band__note` keeps its
selector and swaps `border-left-color` for `border-bottom-color`.

**`tests/test_landing_page.py` — new.** Docstring: what it guards and why it is
not in `test_repo_hygiene.py`.

**`docs/testing.md` — two edits.** A `page` row in the automated-levels table,
and a landing-page subsection on the manual checklist.

### Test plan first

Eight assertions. Each goes red before the change that turns it green, and the
order matters — the spike settles R2 before anything is written against it.

| # | Assertion | Red today because | Covers |
|---|---|---|---|
| A1 | No `overflow-x: auto` applies to the nav link row | `.nav__links` declares it at `:101` | FR-001 |
| A2 | The nav contains a `<details>` with a `<summary>` whose text is non-empty | there is no `<details>` on the page | FR-002 |
| A3 | All four nav links sit inside that `<details>` | they sit in a bare `<div>` | FR-002, FR-003 |
| A4 | No `<p class="band__note">` is a child of a `<div class="band">` | all three are | FR-006, FR-007 |
| A5 | Each `band__note` is the immediate next sibling of a `band` | they are inside it | FR-007, SC-004 |
| A6 | The stylesheet declares no `border-left` on `.band__note`, and the 1080 px block no longer redefines the note's borders | both exist at `:82` and `:295` | FR-009 |
| A7 | The stylesheet contains a `[hidden]` rule declaring `display: none` with `!important` | the file has no `[hidden]` rule at all | FR-012 |
| A8 | The file holds exactly one `<script>` block and no external stylesheet, script or image reference | **green today** — a regression guard, not a red assertion | FR-014, SC-007 |

A8 is deliberately the odd one out and is labelled so rather than dressed up as
red: it guards a property the feature must not break, and constitution XI asks
for tests that were seen failing, which this one cannot be without first breaking
the page on purpose.

**What is deliberately not asserted.** FR-011 freezes the note's type size at
14 px. A test pinning `font-size: 14px` would be a test of a scope boundary
rather than of a behaviour, and it would have to be deleted the moment issue #30
is decided. It stays a review point and a line in the spec, not an assertion.

**The three visual claims**, which no assertion above can reach, become numbered
rows on the manual checklist per constitution XI:

1. At 360 px, all four nav links are reachable, the bar is one line at rest, and
   the control reads as a control. Repeat with JavaScript disabled.
2. Above 1080 px, the heading rows of `01`, `03` and `04` are the same height and
   none is taller than its heading needs; the rules above and below each note are
   single, including the inverted install band.
3. The toggle swaps the visible card both ways; with JavaScript disabled both
   cards stand side by side and no button appears.

### Where this gets documented

`docs/testing.md` only. `docs/design.md` needs no change: nothing in it becomes
untrue — the page is still flat colour and type, still one self-contained file,
and the step strip's measure rule is untouched. `README.md` is not involved;
that is issue #26.

Every link added to `docs/testing.md` must resolve, or `scripts/check_docs.py`
fails. That gate runs as part of the four.

**Bugfix**: 2026-08-19 — [BUG-006](bugs/BUG-006.md) Updated from bugfix patch.

The plan's US2 section reasoned about the note's type size as *band geometry* —
correct while `.band` was `display: flex` with `align-items: stretch`, because
the note's height set the heading row's and its font size was therefore a lever
on the row. **T018–T021 removed that coupling.** Every note is now a full-width
block below its band, so its type size reaches nothing but itself.

That has one consequence the plan should carry forward, because it changes a
decision rather than a detail: the cost that made FR-011 freeze the note at
14 px — "raising it makes every section band taller" — was paid off by the fix
that shipped in the same feature. Raising the four sub-floor declarations is now
a local change with no geometric consequence, which is why
[BUG-006](bugs/BUG-006.md) supersedes FR-011 with FR-016 rather than leaving the
choice open. FR-017 adds the scoping sentence to `docs/design.md` and
constitution XVI so the floor states which faces it binds.

The test plan gains one assertion, at the level the rest of this feature already
uses: source-text structure, not rendered geometry. Type size is declared in the
stylesheet, so unlike a row height it is fully assertable and needs no manual
checklist row.

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| New file `tests/test_landing_page.py` | V | The three bugs need red assertions before their fixes, and no existing module's purpose covers structural claims about a hand-written HTML page | `test_repo_hygiene.py` is scoped to user content and committed binaries; `test_check_project.py` to the model-driven steps' artifacts; `test_e2e.py` to the built PDF. Detail in [research.md R1](research.md#r1--how-does-a-landing-page-requirement-become-an-assertion-that-fails-first) |

Principle XI has no row here. It is not waivable.
