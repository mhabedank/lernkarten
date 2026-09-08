# Implementation Plan: The landing page's two-column sections carry their weight

**Branch**: `design/column-balance` | **Date**: 2026-09-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-column-balance/spec.md`

## Summary

Two sections of the landing page draw a column that is more than half empty —
46 % in `02 one card, one idea`, 65 % in `03 print it, cut it`. Three blocks
move: both cards come back in section 02 and the toggle goes; the cutting
diagram joins the sheets; the card box leaves the rules column for a full-width
block beneath both. Behind them, the reason no gate caught this: the repository
has rules about type size, structure, borders and copy, and none about
proportion. That rule goes into `docs/design.md` with constitution XVI pointing
at it, defended by four assertions over the page's *structure* rather than its
geometry.

## Technical Context

The project-wide values in the template are unchanged by this feature and are
not restated. What is specific to it:

**Language/Version**: none. No Python ships; the only Python written is test
code, under the same 3.12 floor and ruff config as the rest.

**Runtime dependencies**: no change.

**Dev dependencies**: no change.

**Testing**: `tests/test_landing_page.py` only. It parses `docs/index.html` with
the module's existing `HTMLParser` subclass and CSS helpers — `tree()`, `find()`,
`ancestors()`, `rules_for()`, `_innermost_rules()`. No new helper is needed and
no new test module: constitution V says land in an existing module where one
fits, and this one exists precisely for this file.

**Target Platform**: unchanged. The assertions are text over a file, so they run
identically on all three platforms and both Python versions.

**Constraints**: `docs/index.html` stays one self-contained file. Constitution
XVI binds every visible change and requires reading `docs/design.md` first —
done, and the rule this feature adds goes into that same document.

## Dependency Decisions

**No dependency change.** Nothing is added, removed or replaced — no Python
package, no dev tool, no self-fetched binary. The vetting tables are deleted
rather than filled with "n/a".

One thing worth recording because it *was* considered and rejected: adding a
headless browser to CI so the proportion could be asserted directly. See
[research.md R3](research.md#r3--what-can-be-asserted-given-the-module-never-renders-the-page).
It would be the only way to check the requirement literally, and it costs a
browser download on every leg of a six-job matrix to defend one static page.
Feature 002's T039 already recorded that this page's CI will not grow a browser
leg; this plan does not reopen that.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Pass? |
|---|---|---|
| I | The two halves stay coupled only through the four file formats | [x] — neither half is touched; the landing page is a project surface, not a pipeline step |
| II | **(GATED)** Dependencies install cleanly everywhere; binaries self-fetch or are optional | [x] — no dependency change |
| III | **(GATED)** Nothing hand-rolled that a vetted library already does | [x] — nothing is built. Three blocks move and one rule is written |
| IV | **(GATED)** Every new dependency has a completed vetting table | [x] — none to vet |
| V | Code lands in an existing module where one fits | [x] — `tests/test_landing_page.py`, which exists for this file and already owns its claims |
| VI | Script imports stay acyclic; the format reader and engine locator remain leaves | [x] — no `scripts/` module is touched |
| VII | **(GATED)** No user content committed; examples stay subject-agnostic | [x] — the page's example card is the existing Bayes card; no subject content is added or changed |
| VIII | No binaries committed | [x] — none |
| IX | Typst sources edited, never generated files | [x] — no Typst is touched. The *pictures* of sheets move; `templates/cards.typ` does not |
| X | Skill frontmatter valid | [x] — no skill touched |
| XI | **(NON-WAIVABLE)** Every behaviour tested first, committed failing on the assertion | [x] — four assertions, each red before its move. See *Test plan first* below |
| XII | The four gates pass; ruff config not loosened | [x] |
| XIII | English throughout | [x] |
| XIV | Branch `<prefix>/<short-kebab-name>`; `main` untouched directly | [x] — `design/column-balance`, the prefix the visible-change work takes |
| XV | Engine version unchanged, or every checksum bumped | [x] — unchanged |
| XVI | `docs/design.md` read before any visible change; colour doubled by shape; no type shrunk to fit; brand PNGs re-rendered | [x] — read; § *The screen surfaces* is where the new rule lands. No colour, no type size and no brand graphic changes; `render_brand.py` need not run |
| XVII | Card style and Typst escaping respected | [x] — no card is authored |

**One row deserves more than a tick.** XVI is normally the gate a visible change
has to argue past. Here the feature *adds* to what XVI governs: the constitution
gains a bullet about two-column proportion, pointing at the rule in
`docs/design.md`. The precedent is FR-017 of feature 002, which put the type
floor's scope into both documents for the same reason — so the rule could be
checked instead of argued.

**Open-item check**: this feature does not touch the constitution's one open
item (dependencies pinned by version rather than by hash). It adds no
dependency, so it neither closes nor works around it.

## Project Structure

### Documentation (this feature)

```text
specs/012-column-balance/
├── spec.md               # /speckit-specify output
├── plan.md               # this file
├── research.md           # Phase 0 — R1–R6
├── data-model.md         # Phase 1 — the DOM of the two sections, before and after
├── quickstart.md         # Phase 1 — how to validate, including the measuring trap
├── checklists/
│   └── requirements.md   # spec quality, 15/16 with one documented exception
└── tasks.md              # Phase 2 — /speckit-tasks, not created here
```

No `contracts/` directory. Contracts here means the four file formats, and none
is touched — see [data-model.md](data-model.md).

### Source Code (repository root)

Four files, three of them documentation:

```text
docs/
├── index.html          # the three block moves, and the CSS that goes with them
├── design.md           # the two-column rule (new subsection, § The screen surfaces)
└── testing.md          # the by-hand rows for what the assertions cannot see

tests/
└── test_landing_page.py  # four new assertions

.specify/memory/
└── constitution.md     # one bullet in XVI, pointing at design.md
```

**Structure Decision**: nothing new is created. `tests/test_landing_page.py` is
the only test module that parses this file, and 009's T010 already established
that it *owns the landing page's claims* — `check_docs.py` does not read HTML
and should not become the second thing that does. Constitution V is satisfied by
adding to it rather than beside it.

### The two halves

**Model-driven work** (`skills/`): none. No prompt changes, so no
`check_project.py` check.

**Deterministic work**: `docs/index.html` (markup and CSS), covered by
`tests/test_landing_page.py`. Four assertions go red first, in the order below.

**The seam**: none — the halves are untouched.

## Phase 0: Research

Complete. See [research.md](research.md). The template's standard questions
about libraries, wheels, Typst and the demo fixture do not arise: no dependency,
no Typst, no fixture. What did need resolving:

| # | Question | Answer |
|---|---|---|
| R1 | How does a block leave a column and become full width? | Copy US2's `band__note` move exactly; the rule direction flips to `border-top` |
| R2 | Where does the cutting diagram go, and what does it cost? | Third child of `.print__sheets`, **beside** the two sheets rather than wrapping below them — that is what makes both columns end together. Its `flex: 1`, `justify-content` and padding were written for its old life and change with it |
| R3 | What can be asserted, given the module never renders? | Structure, in four places — the same trade FR-008 made for the bands |
| R4 | What does the design rule say, and where? | `docs/design.md` § The screen surfaces, with a bullet in XVI. Direction and remedy, no false-precision number |
| R5 | What else does the toggle take with it? | Three CSS rules the previous feature already flagged as conditional on it. **Not** the `[hidden]` reset |
| R6 | Does anything below 1080 px break? | No, but two of the three moves must be checked there rather than assumed |

## Phase 1: Design

The DOM before and after is in [data-model.md](data-model.md), including the
table of which boundary owns which rule — the detail R1 names as most likely to
be got wrong. How to validate is in [quickstart.md](quickstart.md).

**Where this gets documented**: `docs/design.md` § *The screen surfaces* gains
the two-column rule; constitution XVI gains a bullet pointing at it;
`docs/testing.md` § *The landing page* gains the by-hand rows for the proportion
and the boundaries. Every link added must resolve or `check_docs.py` fails, and
that gate is one of the four.

### Test plan first

Four assertions. Each goes red before the change that turns it green, and they
are ordered so that no implementation task precedes its own test (constitution
XI). All four write the same file, so **none of them is parallel with another** —
this is the same `[P]` trap feature 002 named as its biggest.

| # | Assertion | Red today because | Covers |
|---|---|---|---|
| A11 | Nothing inside `.anatomy__cards` carries `hidden`, and the page declares no `.toggle` element | `#card-back` is given `hidden` on load and the button is in the band | FR-001, FR-002 |
| A12 | `.print__box` is not a descendant of `.print__rules`, and follows `.print` | it is the last child of `.print__rules` | FR-003 |
| A13 | `.print__cut` is a descendant of `.print__sheets` | it is a child of `.print__rules` | FR-004 |
| A14 | The page holds **at most one** `<script>` block, and the same single external sub-resource | green today at one, and stays green at zero — this is A8 restated, not a new claim | FR-011 |

**A14 is the delicate one.** A8 asserts *exactly* one script and would go red the
moment the toggle is deleted — a passing test failing because the code got
better. It is restated to "at most one" rather than deleted, because the design
rule it defends is "one self-contained file with almost no script", and a page
that grows a *second* script has left that rule whether or not the first was
removed. Weakening it to "any number" would throw away the guard along with the
count. The `EXTERNAL_SUBRESOURCES` half of A8 is untouched.

**A11 asserts absence twice, deliberately.** No `hidden` inside the card column
*and* no `.toggle` anywhere. Either alone passes a half-done removal: deleting
the button while the script still sets `hidden` leaves one card and no way back;
deleting the script while the button stays leaves a dead control. FR-002 names
that failure mode and this is where it is caught.

## Complexity Tracking

No Constitution Check row is a "no". Nothing to record.

**Bugfix**: 2026-09-08 — [BUG-012](bugs/BUG-012.md) Updated from bugfix patch.

**No section of this plan changed, and that is a finding rather than luck.** The
plan summarises R2 in one table row — *"Third child of `.print__sheets`; its
`flex: 1`, `justify-content` and padding were written for its old life and change
with it"* — and never says which row the diagram occupies or quotes a figure.
Both the arrangement that failed and the one that shipped are third children of
`.print__sheets`, so the row is true of either.

The lesson is not that the plan was right. It is that the plan was written at a
level where the distinction that mattered could not be expressed, and the
distinction lived in `research.md` instead, where it was wrong. A plan that
abstracts away the thing under test cannot be evidence that the thing under test
is correct.

So the R2 row **has** been sharpened to say *beside* — leaving a row that cannot
distinguish the two answers, having just written down that it cannot, would be
recording the problem instead of fixing it. The row is now one line longer and
says the thing that mattered.
