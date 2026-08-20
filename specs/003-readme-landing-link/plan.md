# Implementation Plan: The README links the landing page up front

**Branch**: `docs/readme-landing-link` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-readme-landing-link/spec.md`

## Summary

Issue [#26](https://github.com/mhabedank/lernkarten/issues/26): `README.md`
first names the live landing page at line 168, inside `## The design`, so a
reader who wants to *see* the project before reading 160 lines never finds it.
The fix is one markdown link in the opening block, guarded by a pytest assertion
in `tests/test_repo_hygiene.py` that is committed failing first, plus the manual
half — what a reader sees on github.com, whether the link invites a look, and
whether the URL loads — as a numbered row in `docs/testing.md`. No Python is
added, no format changes, no dependency moves.

## Technical Context

The project's standing context applies unchanged and is not restated here; only
the rows this feature actually engages are worth naming.

**Language/Version**: Python `>=3.12`. This feature uses `pathlib` and `re`,
both already imported across the suite. Nothing is version-sensitive.

**Runtime dependencies**: `pyyaml==6.0.3`, untouched. This feature adds nothing
at runtime — the change never executes in a user's session at all.

**Dev dependencies**: `pytest`, `ruff` — untouched.

**Testing**: pytest, one new case in an existing module. Neither
`LERNKARTEN_E2E=1` nor `LERNKARTEN_DEPS_NET=1` is engaged; the case is pure file
reading and runs offline. **Test-first is mandatory** (constitution XI) and is
the ordering constraint on the whole feature.

**Optional external tools / Typesetting engine**: not involved. Nothing is
typeset, no PDF is built, `scripts/engine.py` is not read.

**Target Platform**: all three, trivially — a text edit and a string assertion
with no platform-specific behaviour. The Windows claim needs no manual leg here
because there is nothing platform-dependent to claim.

**Project Type**: neither half of the pipeline. `README.md` and `docs/testing.md`
are project surfaces; `tests/` is the suite that guards them.

**Constraints**: the assertion must not make a network request (FR-006), so the
liveness of `https://mhabedank.github.io/lernkarten/` stays a manual concern.

**Scale/Scope**: four files touched, two of them documentation. Under twenty
lines changed in total.

**NEEDS CLARIFICATION**: none. Six open questions were carried into Phase 0 and
all six are resolved in [research.md](./research.md).

## Dependency Decisions

**No dependency change.** No Python package, dev tool or self-fetched binary is
added, replaced or removed, and the engine version is untouched. The vetting
tables are therefore deleted rather than filled with "N/A".

### Reuse check (constitution III)

**Is anything being hand-rolled here?** No. The implementation is one line of
markdown and an assertion that finds a heading offset with `re.search` and
compares two `str.index` results. There is no problem of a size worth delegating
to a library, so the question constitution III asks first has no candidate to
name. See [research.md](./research.md) R5.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-checked after Phase 1 design — see
the note under the table.*

| # | Gate | Pass? |
|---|---|---|
| I | The model-driven and deterministic halves stay coupled only through the four file formats | [x] No format is touched, and neither half changes behaviour |
| II | **(GATED)** Any new dependency installs with a plain `pip install` … | [x] No new dependency, no new binary |
| III | **(GATED)** Nothing is hand-rolled that a vetted library already does | [x] See the Reuse check above and research R5 |
| IV | **(GATED)** Every new dependency has a completed vetting table above | [x] Vacuous — there is none |
| V | Code lands in an existing module where one fits; any new `scripts/` file has a reason and a docstring | [x] `tests/test_repo_hygiene.py` fits; no new file anywhere. Research R1 records why the two alternatives were rejected |
| VI | Script imports stay acyclic; the format reader and the engine locator remain leaves | [x] No import changes; nothing under `scripts/` is edited |
| VII | **(GATED)** No user content committed; nothing forced past `.gitignore`; examples stay subject-agnostic | [x] The only content added is a link to this project's own landing page. Nothing subject-specific enters the README — it is a URL, not an example. **PR note required** since the gate is marked GATED |
| VIII | No binaries committed; new test material is generated from a text source | [x] No test material at all — the subject of the test is the repository's own `README.md` |
| IX | Typst sources edited, never generated files; nothing in `output/` hand-edited | [x] No Typst, no `output/` |
| X | Skill frontmatter valid | [x] No skill is touched |
| XI | **(NON-WAIVABLE)** Every behaviour was tested first: the test is committed failing, on the assertion, before the implementation | [x] Enforced by task order below; the layout carve-out is used for FR-007 and the row is **named** in `docs/testing.md`, as the principle requires |
| XII | The four gates pass; ruff config not loosened without a stated reason | [x] All four run in [quickstart.md](./quickstart.md) step 3; ruff config untouched |
| XIII | English throughout | [x] |
| XIV | Branch is `<prefix>/<short-kebab-name>`; `main` untouched directly; commit subjects prefixed | [x] `docs/readme-landing-link`; commits prefixed `docs:` and `test:` |
| XV | Engine version unchanged, or every platform checksum bumped with it | [x] Unchanged |
| XVI | `docs/design.md` read before any visible change; colour doubled by shape; no type shrunk to fit; brand PNGs re-rendered | [x] `docs/design.md` read. The change is a line of prose in a file GitHub types and colours; it adds no graphic, shrinks no type, and carries no meaning in colour — the link is a word either way. No brand PNG re-render |
| XVII | Card style and Typst escaping rules respected | [x] No card is touched |

**Post-design re-check**: unchanged. Phase 1 added no file under `scripts/`, no
import, no dependency and no format — the only design decisions taken were
*which existing test module* (V, decided in research R1) and *how sharp the
assertion can honestly be* (XI, decided in research R2). Both strengthen the
gates rather than strain them, so no row moves and Complexity Tracking stays
empty.

**Open-item check**: this feature does not touch the constitution's one open
item (dependencies pinned by version rather than hash). It adds no dependency,
so it neither closes nor works around it.

## Project Structure

### Documentation (this feature)

```text
specs/003-readme-landing-link/
├── plan.md                  # This file
├── spec.md                  # /speckit-specify output
├── research.md              # Phase 0 — six questions, six decisions
├── data-model.md            # Phase 1 — "no format change", plus the README regions the test slices
├── quickstart.md            # Phase 1 — red-first run guide and the four gates
├── checklists/
│   └── requirements.md      # spec quality checklist, all items passing
└── tasks.md                 # Phase 2 (/speckit-tasks — NOT created here)
```

No `contracts/` directory. Contracts under this project mean the four file
formats, and none is touched — creating an empty folder to say so would be
noise. [data-model.md](./data-model.md) states it in one table instead.

### Source Code (repository root)

Four files change. The rest of the tree is listed nowhere here because none of
it is engaged — no `scripts/`, no `bin/`, no `skills/`, no `templates/`, no
`assets/`, no fixtures.

```text
README.md                    # EDIT — one link in the opening block; the design section keeps docs/index.html
docs/
└── testing.md               # EDIT — new manual row 33; the "still buries the landing page" note removed
tests/
├── test_repo_hygiene.py     # EDIT — the new assertion, plus a widened module docstring
└── test_landing_page.py     # EDIT — docstring only: it says repo_hygiene has "one" landing-page check
```

**Structure Decision**: the assertion goes in `tests/test_repo_hygiene.py`
because that module already reads `README.md` through `versioned_files()` and
already owns claims about the *text* of versioned documentation. The other two
candidates were considered and rejected in [research.md](./research.md) R1:
`tests/test_landing_page.py` is scoped by its own docstring to how
`docs/index.html` is *built*, and a new `tests/test_readme.py` would violate
constitution V's "existing module where one fits" while falling outside the
seven-module placement table in constitution XI.

The fourth file is the cost of that choice and is not optional: two docstrings
describe the boundary this feature moves, and a docstring that describes the
old boundary is worse than none.

### The two halves

**Model-driven work** (`skills/`): none. No prompt changes, so no
`check_project.py` check is needed — the constitution's prompt-change clause
does not apply.

**Deterministic work** (`tests/`, plus two documentation files): one new case in
`tests/test_repo_hygiene.py`, covered by that module at the repo-hygiene level
in `docs/testing.md`'s table. The assertion that goes red first is invariant 1
in [data-model.md](./data-model.md): the landing page URL is absent from the
opening block of `README.md`.

**The seam**: none — the halves are untouched. Nothing crosses between them,
because no file format carries this change.

## Phase 0: Research

Complete. [research.md](./research.md) resolves six questions:

| # | Question | Decision |
|---|---|---|
| R1 | Which test module carries the assertion? | `tests/test_repo_hygiene.py`; both affected docstrings move with it |
| R2 | How does a test say "the opening block", and how sharp can it get? | Above the first `^## `; pinned between `Claude_Code-plugin` and `assets/example-cards.png`; placement relative to the intro paragraph left to the manual row |
| R3 | Does an absolute URL disturb the docs gate? | No — `scripts/check_docs.py:174` skips absolute links. No change, and no network call added |
| R4 | Where does the manual half go? | New row 33 under "The landing page" in `docs/testing.md`; the "still buries the landing page" sentence rewritten |
| R5 | Reuse / dependencies? | Nothing hand-rolled, nothing added |
| R6 | Duplicate pointers to the page? | Deliberate — absolute URL up top for the newcomer, relative `docs/index.html` in `## The design` for the contributor |

The template's standing Phase 0 questions are answered by not applying: no
library candidate exists (R5), no Typst layout is involved, the demo project
needs no extension because the test's subject is the repository's own
`README.md`, and there is no degraded path — nothing executes without
`pdftotext` or an engine because nothing executes at all.

## Phase 1: Design

### Test plan first

The order below is the constitution's, not a preference. Each assertion is
listed with the state it must be in when committed.

| Order | Assertion | Where | State at commit |
|---|---|---|---|
| 1 | The landing page URL appears in the opening block of `README.md` — everything above the first `^## ` | `test_the_readme_points_a_newcomer_at_the_landing_page` | **RED**, on the assertion, naming `README.md` |
| 2 | Within that block it sits after `Claude_Code-plugin` and before `assets/example-cards.png` | same case | RED with 1 (same case, so it goes green with it) |
| 3 | `## The design` still contains a relative link to `docs/index.html` | `test_the_readme_still_names_the_landing_page_source` | **GREEN from the start** — a regression guard for FR-004, proved load-bearing by a mutation check rather than by a red commit it cannot produce |
| 4 | Manual row 33 | `docs/testing.md` | n/a — the half no test reaches, named per constitution XI |

Assertion 3 being green on `main` is deliberate and worth stating so a reviewer
does not read it as a missed red step: FR-004 protects behaviour that already
exists, and a guard for existing behaviour has nothing to fail against. The red
that matters is assertion 1.

Two cases, not one. Invariants 1–3 answer the newcomer's question and belong
together: they cover one edit, and splitting them would produce three failures
for it. Invariant 4 answers the contributor's, which is a different question
with a different reader and a different verification story — it cannot go red,
so it is mutation-checked instead. Folding it into the first case would report a
lost `docs/index.html` link as a failure of a test named for the newcomer, and
would leave US2 with no command of its own to prove it.

### What the user sees

No error message, no exit code, no output line. The only user-facing surface is
the README as GitHub renders it, and the only new text is the link itself. FR-003
constrains it to read as an invitation to look rather than to read; issue #26
offers `**[See it →](https://mhabedank.github.io/lernkarten/)**` as the shape and
the plan adopts that shape, leaving the exact wording to the edit.

Placement: between the introductory paragraph and the `assets/example-cards.png`
screenshot. That satisfies both halves of the issue's suggestion, keeps the link
adjacent to the sentence explaining what the project is, and lands inside the
region assertion 2 pins.

### Where this gets documented

| File | What goes in it |
|---|---|
| `docs/testing.md` | Row 33 in the "The landing page" table: at github.com, the link is visible without scrolling past the intro paragraph, reads as an invitation to look, and the URL loads. Then the closing paragraph loses its second clause and "Two things" becomes "One thing" |
| `tests/test_repo_hygiene.py` | Module docstring widened past "stays subject-agnostic" to cover the doc-text guards it has accumulated |
| `tests/test_landing_page.py` | Docstring corrected: `test_repo_hygiene.py` no longer has "one" landing-page check |

No new markdown link that `check_docs.py` must resolve is introduced anywhere
except the absolute URL, which it skips. `docs/design.md` needs no edit — it
governs the card, the mark and the landing page, none of which changes.

### Risks

| Risk | Handling |
|---|---|
| The Pages URL changes and two copies drift | Row 33 catches it by eye; research R6 leaves it open whether the design section keeps its own absolute copy |
| A future copy edit reshuffles the opening block and breaks assertion 2 | The anchors are a badge URL and a committed file path, not prose — see data-model.md. If either legitimately moves, the test is *supposed* to be looked at |
| The docstring edits are dropped as "cosmetic" during review | They are tasks, not cleanup: research R1 records that this feature is what makes the old wording wrong |

## Complexity Tracking

Empty. The Constitution Check has no "no", and nothing in Phase 1 introduced
one.
