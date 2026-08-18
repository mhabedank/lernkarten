# Implementation Plan: Goal-driven catalog

**Branch**: `feat/goal-driven-catalog` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-goal-driven-catalog/spec.md`

## Summary

Give the pipeline a stated learning goal, then build the catalog *from* that goal
instead of from whatever happened to be ingested — so a branch nothing covers
becomes a visible gap and material the goal does not want becomes a marked
out-of-scope entry rather than a stack of cards.

Technically this is a **prompt-and-contract** feature: two new skills, two
changed skills, and one script (`scripts/check_project.py`) taught to validate a
fifth file format plus three new attribute lines on catalog subtopics. No new
dependency, no build or print code, no card layout change. The deterministic
half's only job is to be the red assertion that makes the prompt changes
testable at all (constitution XI).

## Technical Context

Unchanged from the project baseline. Restated only where this feature touches it:

**Language/Version**: Python `>=3.12`, ruff targeting `py312`. Nothing here needs
a newer floor — the work is line scanning and dict validation.

**Secondary language**: Typst — touched only in `assets/brand/*.typ`, whose
command list and step count are rendered into three committed PNGs.

**Runtime dependencies**: `pyyaml==6.0.3` via `scripts/deps.py`. **Unchanged.**
`goal.md` frontmatter is parsed with the `frontmatter()` helper already in
`check_project.py`, which already goes through `yamlio`.

**Dev dependencies**: unchanged.

**Storage**: plain files. This feature adds one — `goal.md` at the project root,
beside `sources.yaml`.

**Testing**: pytest. Two existing modules grow (`test_check_project.py`,
`test_repo_hygiene.py`) and **one new module appears**: `tests/test_check_docs.py`.
That module does not exist today — `scripts/check_docs.py` has no test coverage
at all — so adding the skill-description rule requires creating it. This is
flagged rather than buried: it is a new file, and it closes a pre-existing gap.

**Lint/format**: ruff, config untouched.

**Typesetting engine**: unchanged. No version bump, no checksum work.

**Target Platform**: unchanged. Nothing platform-specific; the new code is
string handling.

**Project Type**: CLI tool + Claude Code plugin. Unchanged.

**Performance Goals**: unchanged. The catalog parse is one pass over a file of a
few hundred lines.

**Constraints**: the new artifact is user content, so it must be gitignored,
hook-blocked and asserted — and the demo fixture's copy has to be let back in
past `.gitignore`, the same way `sources.yaml` already is.

**Scale/Scope**: this feature adds ~2 skills, ~180 lines to `check_project.py`,
~40 lines to `check_docs.py`, one new test module, and edits to 4 documents,
1 landing page and 3 brand graphics.

## Dependency Decisions

**No dependency change.** No runtime package, no dev package, no external
binary, no engine bump. The vetting tables are therefore deleted, per the
template's instruction.

### Reuse check (constitution III)

**Is anything being hand-rolled here?** Yes, arguably: the catalog gains real
structure (`Parents:`, `Also covers:`, `Related:`, `Status:`) and something has
to parse it. Principle III says ask about a library *first*.

**Candidates considered**: `markdown-it-py`, `mistune`, `marko` — all
maintained, pure Python, permissively licensed, and all would clear Principles
II and IV on their own merits.

**Why none of them is adopted**:

1. **They solve the half we already have.** A markdown AST gives us headings and
   paragraphs. `catalog/topics.md` is a *constrained* format — `##`, `###`, and
   `Key: value` attribute lines inside a subtopic body — and the attribute lines
   are the entire difficulty. Every candidate would hand us paragraph nodes whose
   text we then parse by hand anyway. The library removes the easy 20 % and
   leaves the hard 80 %.
2. **It would be a runtime dependency for a checker.** `check_project.py` is
   reached through `bin/lernkarten check`, so anything it imports goes through
   `scripts/deps.py`, must be pinned exactly, and must have a wheel on Windows
   ARM64. That is a real cost to the user's first run.
3. **The existing code already does this shape of work.** `check_catalog()`
   scans lines for `## ` and `### ` today, and `frontmatter()` already splits and
   YAML-parses a header block. The new lines are the same idiom.

This is the legitimate Principle III exception the constitution names: *"the need
is a three-line slice of a library that would drag in thirty packages"*. It is
recorded here rather than assumed, because Principle III makes hand-rolling the
exception that needs a stated reason.

**Removals**: none.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-checked after Phase 1 design — see
[Post-design re-check](#post-design-re-check).*

| # | Gate | Pass? |
|---|---|---|
| I | The halves stay coupled only through the file formats | ⚠ **amendment** — the coupling stays clean, but this adds a **fifth** format (`goal.md`) to the four the principle enumerates. Recorded in Complexity Tracking; the constitution edit ships in this PR |
| II | **(GATED)** New dependency installs cleanly / new binary self-fetches | ✅ n/a — no dependency added |
| III | **(GATED)** Nothing hand-rolled that a vetted library does | ✅ — markdown parsers considered and rejected with reasons above |
| IV | **(GATED)** Vetting table completed for every new dependency | ✅ n/a — none |
| V | Code lands in an existing module; a new file has a reason and a docstring | ✅ — all script work goes into `check_project.py` and `check_docs.py`. No new `scripts/` module; see [Structure Decision](#structure-decision) |
| VI | Imports stay acyclic; `deps` and `engine` stay leaves | ✅ — no new import edge at all |
| VII | **(GATED)** No user content committed; examples subject-agnostic | ⚠ **work required** — `goal.md` must be added to `.gitignore`, to `.githooks/pre-commit` and to `tests/test_repo_hygiene.py`, **and** let back in for the fixture with `!tests/fixtures/**/goal.md`. `goal.md` has no slash, so like `sources.yaml` it matches at every level. Needs the explicit PR note the constitution requires |
| VIII | No binaries committed; test material generated from text | ✅ — the three re-rendered PNGs are the constitution's deliberate exception, and they come from Typst sources |
| IX | Typst sources edited, never generated files | ✅ — `assets/brand/common.typ` is edited, PNGs re-rendered |
| X | Skill frontmatter valid — `name` == folder, description names triggers | ✅ — and this feature *strengthens* the rule with a domain-word check |
| XI | **(NON-WAIVABLE)** Every behaviour tested first, red on the assertion | ✅ — the whole plan is ordered around it; see [Test plan first](#test-plan-first) |
| XII | The four gates pass; ruff config not loosened | ✅ |
| XIII | English throughout | ✅ |
| XIV | Branch `<prefix>/<short-kebab-name>`; `main` untouched | ⚠ **not yet done** — the repo is on a detached HEAD. `feat/goal-driven-catalog` has to be created before the first commit |
| XV | Engine version unchanged, or all six checksums bumped | ✅ — unchanged |
| XVI | `docs/design.md` read before a visible change; brand PNGs re-rendered | ⚠ **work required** — the landing page step strip and three PNGs change. `docs/design.md` §"The screen surfaces" and §"Type" read; the binding constraint is the caption measure, not the hero's unbreakable-word floor — see [research.md R3](research.md#r3--how-do-seven-steps-fit-a-five-column-strip) |
| XVII | Card style and Typst escaping respected | ✅ — no card text or layout changes |

**Open-item check**: the constitution's one still-open item is *dependencies
pinned by version rather than by hash*. This feature adds no dependency, so it
neither closes that item nor works around it. Untouched.

## Project Structure

### Documentation (this feature)

```text
specs/001-goal-driven-catalog/
├── plan.md               # this file
├── research.md           # Phase 0 — the four questions that needed answers
├── data-model.md         # Phase 1 — the catalog as a graph, and goal.md
├── contracts/
│   ├── goal-md.md        # the new fifth format
│   ├── catalog-topics-md.md  # the three new attribute lines
│   └── sources-yaml.md   # the `research` source type
├── quickstart.md         # Phase 1 — how to prove the feature works
└── checklists/requirements.md
```

### Source Code (repository root)

Only the rows this feature touches:

```text
scripts/
├── check_project.py        # + check_goal(), + parse_catalog(), extended check_sources()
└── check_docs.py           # + the domain-word rule on skill descriptions

skills/
├── learning-goal/SKILL.md  # NEW
├── research-gaps/SKILL.md  # NEW
├── catalog/SKILL.md        # goal-first ordering, Status/Parents/Also covers/Related
├── cards/SKILL.md          # scope skipping, gap warning, primary-parent placement
└── ingest/SKILL.md         # description only — the domain-word retrofit

assets/brand/
├── common.typ              # line 67: the command tuple
├── banner.typ              # "the five commands" in the comment and the art
├── pipeline.typ            # the step strip
└── social-card.typ         # "Five commands." in the standfirst

assets/                     # banner.png, pipeline.png, social-card.png re-rendered

tests/
├── test_check_project.py   # goal, status, graph, research-source cases
├── test_check_docs.py      # NEW — this module does not exist today
├── test_repo_hygiene.py    # goal.md must not be committed outside the fixture
└── fixtures/demo-project/
    ├── goal.md             # NEW — two areas, one uncovered topic, one exclusion
    ├── catalog/topics.md   # gains Status, Parents, Also covers, Related
    ├── sources.yaml        # gains one `research` entry
    └── knowledge/<research-id>/  # NEW — one document with a url in frontmatter

docs/
├── workflow.md             # step sections renumbered; gaps and scope explained
├── index.html              # the step strip: grid, breakpoints, optional marking
└── design.md               # the surfaces table, if the strip gains a new part

README.md  CLAUDE.md  .gitignore  .githooks/pre-commit
.specify/memory/constitution.md   # Principle I's table, the Identity pipeline sentence
```

### Structure Decision

**No new module under `scripts/`.** The catalog parsing grows enough to make a
`catalog_model.py` tempting, and it was considered. Rejected because:

- `check_project.py` is the only consumer. The model-driven half reads the
  catalog as *prose*, and `build_pdf.py` never sees it at all — so a shared model
  module would have exactly one importer, which Principle V calls a file without
  a reason.
- A new module adds an import edge to the graph Principle VI keeps acyclic, for
  no reuse.

Instead the parsing is factored into a **pure function inside
`check_project.py`** — `parse_catalog(text) -> Catalog` — that builds the
structure and returns it without reporting. That keeps it directly unit-testable
(`check_project.parse_catalog(...)` from the test module, the way tests already
import `check_project`) while the reporting stays where the other checks are.
Best of both, no new file, no new edge.

`check_goal()` sits beside `check_sources()` / `check_knowledge()` /
`check_catalog()` / `check_cards()` and is wired into `check()` first, since the
catalog check needs the goal's required topics for the drift warning.

### The two halves

**Model-driven work** (`skills/`): two new prompts (`learning-goal`,
`research-gaps`) and two changed ones (`catalog`, `cards`), plus a description
retrofit on `ingest` and `catalog`.

None of that is verifiable by reading it. The verification is the red assertion
in `check_project.py` written **first**: for every rule a prompt is supposed to
follow, there is a check that fails against a project shaped the way today's
prompts shape it. Where a spec requirement has no such check, it is a
*reporting* requirement (what the skill says to the user in the run), and those
are listed separately in [quickstart.md](quickstart.md) as manual checks — the
plan does not pretend they are automated.

**Deterministic work** (`scripts/`): `check_project.py` gains `check_goal()`,
`parse_catalog()`, the `research` source type, and the graph invariants.
`check_docs.py` gains the domain-word rule. Covered by
`tests/test_check_project.py` and the new `tests/test_check_docs.py`.

**The seam**: three of the five formats — the new `goal.md`, the extended
`catalog/topics.md`, and one new `type:` value in `sources.yaml`. Each has a
contract file under `contracts/`. `knowledge/*.md` frontmatter and `cards/*.yaml`
are untouched, which is what keeps `build_pdf.py` and the card template out of
this feature entirely.

## Phase 0: Research

Four questions had to be answered before design. Full reasoning in
[research.md](research.md); the decisions:

1. **Library for the catalog format?** No — markdown parsers solve the heading
   half we already have and leave the attribute lines, and it would put a runtime
   dependency behind `lernkarten check`. Recorded above under Reuse check.
2. **Where does `goal.md` live, and how does the fixture survive `.gitignore`?**
   Project root. `goal.md` has no slash, so it matches at every level like
   `sources.yaml` — the fixture needs `!tests/fixtures/**/goal.md`, the exact
   pattern already at `.gitignore:18`.
3. **How do seven steps fit a five-column strip?** Recommended: keep the five
   core steps as the visual spine and render the two optional ones as narrower
   flanking cells with a distinct treatment, rather than a seven-column grid.
   Seven equal columns cut the caption measure from ~176 px to ~114 px under
   text already set at 13.5 px. Alternatives and the arithmetic are in
   research.md.
4. **Where do the new broken fixtures go?** In `tmp_path` via the existing
   `project()` helper — **not** in `tests/fixtures/demo-project/broken/`, which
   holds only broken *card YAML* for the build. The spec's Assumptions say the
   same; SC-008's six named failure cases (each naming the culprit) are
   unchanged by where the fixtures live.

## Phase 1: Design

Artifacts: [data-model.md](data-model.md), [contracts/](contracts/),
[quickstart.md](quickstart.md).

The design decisions that constrain implementation:

- **The catalog graph is bipartite.** Topics contain subtopics; the catalog stays
  two levels deep. Multi-parenthood makes it a graph, not a tree — but edges only
  run topic → subtopic, so no cycle can form and there is nothing to check for
  acyclicity. The invariants are reciprocity ones instead.
- **`report.count("subtopics")` must not double-count** a borrowed subtopic, and
  the `subtopics` set handed to `check_cards()` must contain each name once.
  A two-parent subtopic is written once, under its primary; the other parent gets
  an `Also covers:` line, which is deliberately *not* a `###` heading so the
  existing heading scan stays correct.
- **Absence is always valid.** Every new line is optional and its absence means
  today's behaviour. This is what makes SC-006 (a project with no `goal.md`
  produces byte-identical artifacts) achievable rather than aspirational.
- **Error messages name the culprit**, matching the existing style
  (`catalog/topics.md: reference points nowhere -> …`). Every new message names
  the file and the subtopic or source id at fault.

### Test plan first

The order the assertions go red in. Each line is one test that must fail *on its
assertion* — not on an ImportError — before the code beside it exists.

**Wave A — `goal.md` (blocks everything)**

| # | Assertion that goes red | Then implement |
|---|---|---|
| A1 | a `goal.md` missing `kind` is reported, naming the key | `check_goal()` |
| A2 | an unknown `depth` value is reported, naming the value and the closed set | |
| A3 | an `updated` that is not an ISO date is reported | |
| A4 | a `## Required topics` with an area holding no topics is reported, naming the area | |
| A5 | a required topic absent from the catalog **warns** (drift) | wiring `check_goal` before `check_catalog` |
| A6 | *regression guard, green from the start*: a project with no `goal.md` passes | — |

**Wave B — `Status:`**

| # | Assertion | Then implement |
|---|---|---|
| B1 | a subtopic with no references and no `Status: gap` is reported by name | `parse_catalog()` + the status rules |
| B2 | `Status: gap` with `References: none` passes | |
| B3 | an unknown `Status:` value is reported, naming subtopic and value | |
| B4 | *regression guard*: today's demo catalog, with no `Status:` anywhere, still passes | — |

**Wave C — the graph**

| # | Assertion | Then implement |
|---|---|---|
| C1 | a `Parents:` naming a topic that does not exist is reported | the graph invariants |
| C2 | a primary parent that is not the heading the subtopic sits under is reported | |
| C3 | an `Also covers:` naming a subtopic whose `Parents:` omits that topic is reported | |
| C4 | a `Parents:` listing a second topic with no reciprocal `Also covers:` is reported | |
| C5 | a `Related:` name that is not a subtopic is reported | |
| C6 | a two-parent subtopic counts **once** in `report.counts["subtopics"]` and appears once in the returned set | |

**Wave D — the `research` source type**

| # | Assertion | Then implement |
|---|---|---|
| D1 | `type: research` without `gap` is reported | `SOURCE_TYPES` + the `gap` rule |
| D2 | `type: research` with `gap` and neither `path` nor `url` passes | |

**Wave E — skill descriptions** *(new test module)*

| # | Assertion | Then implement |
|---|---|---|
| E1 | a skill whose description names triggers but no domain word is reported | the rule in `check_docs.py` |
| E2 | *regression guard*: every shipped skill passes it — which requires retrofitting `catalog` and `ingest` first | the two description edits |

**Wave F — repo hygiene**

| # | Assertion | Then implement |
|---|---|---|
| F1 | a `goal.md` tracked outside `tests/fixtures/` fails `test_repo_hygiene.py` | `.gitignore`, `.githooks/pre-commit` |
| F2 | the fixture's own `goal.md` **is** tracked — proving the negation pattern works | `!tests/fixtures/**/goal.md` |

**Wave G — prompts.** Only once A–F are green. Each skill is edited until the
demo project, regenerated by running the skill, passes
`check_project.py … --strict`. The demo fixture is extended first so there is
something for the checks to bite on.

**Wave H — docs, landing page, brand.** `check_docs.py` link resolution is the
automated part; the step strip at three breakpoints and the re-rendered PNGs are
on the manual checklist in `docs/testing.md`.

**Not automated, and said so plainly**: the run-output requirements — the
no-goal advisory, the out-of-scope count, the gap warning with names. No file on
disk records what a skill *said*. These are manual checks in
[quickstart.md](quickstart.md). Every requirement that produces an artifact has a
red assertion above; every one that produces only console output does not, and
pretending otherwise would be the failure mode Principle XI exists to prevent.

## Post-design re-check

Design changed nothing in the Constitution Check. The three ⚠ rows are the same
three, all of them work items rather than violations: the constitution amendment
for the fifth format (I), the gitignore/hook/test work plus the PR note (VII),
the branch that does not exist yet (XIV), and the design reading plus re-render
(XVI). No gate moved from pass to fail.

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| A **fifth file format** (`goal.md`), where Principle I enumerates four | I | The goal is the criterion every relevance judgement in this feature depends on. It has to outlive a session, be editable by hand, and be readable by three skills | Putting it in `sources.yaml` conflates "what I want to learn" with "where my material is" and breaks a format the ingest path depends on. Putting it in `catalog/topics.md` makes the goal an output of the step it is supposed to drive. A `/cards` argument does not persist and is invisible to `/catalog`. The constitution is amended in this PR rather than the format being smuggled in |
| A **new test module** (`tests/test_check_docs.py`) | V | The domain-word rule needs a failing test, and `check_docs.py` has none anywhere | There is no existing module it fits: `test_repo_hygiene.py` is about what is committed, `test_check_project.py` about user projects. Adding doc-tool tests to either would misfile them permanently |
| **Three attribute lines** added to `catalog/topics.md` at once (`Status:`, `Parents:`/`Also covers:`, `Related:`) | I | `Status:` is required by the core fix; the graph lines serve catalog fidelity | They could ship in two PRs, and US5 remains the separable one if this proves too large. Shipping the format additions together avoids changing the same contract twice in a row, which costs `check_project.py`, the demo fixture and the docs both times |
| **Four requirements with no red assertion** — FR-013 (the no-goal advisory), FR-016 (the closing counts), FR-018 (the out-of-scope count), FR-019 (the gap warning) | XI | Each of the four is satisfied by what a skill *says during a run*. Nothing on disk records that, so no `check_project.py` check can be written to fail against it — the artifact these prompts produce is identical either way. They are manual checks T107/T108 instead | Deleting the requirements would remove the only thing that tells a user their deck is incomplete (FR-019) and the only route by which `/learning-goal` is ever discovered (FR-013). Inventing a log file for the skills to write, purely so a test can read it, adds a **sixth** file format to make an assertion possible rather than to serve the user |

Principle XI is not waivable, so the row above is **not** a waiver: it records
that the constitution's model-driven clause ("if no failing check can be written,
the requirement is under-specified") has no answer for a requirement whose whole
effect is console output. Constitution XI already carves out exactly this shape
of problem for layout and design — *"whether it looks right is not a pytest
question and belongs on the manual checklist"*. **T114 extends that carve-out to
run output**, in the same amendment T089–T091 is already making. Until T114
lands, these four requirements are the one place this plan is knowingly ahead of
the constitution, and it is written here rather than discovered in review.
