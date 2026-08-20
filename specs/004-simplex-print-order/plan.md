# Implementation Plan: Simplex print order — all fronts, then all backs

**Branch**: `feat/simplex-print-order` | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-simplex-print-order/spec.md`

## Summary

`lernkarten build` interleaves the sheet faces — front, back, front, back —
which is right for a duplex printer and useless for a one-sided one. Add a
print-run option (`--sides duplex|simplex`, default `duplex`) that reorders the
same pages into all fronts followed by all backs, and make the build say how to
print what it produced.

The reordering happens where the pages are produced, in `templates/cards.typ`,
reached by one more `--input` pair. Python contributes the flag, the input pair
and the closing line; it never touches the PDF after the engine writes it. No
file format changes, no dependency changes, and the default path comes out
identical to today.

## Technical Context

**Language/Version**: Python `>=3.12` (`pyproject.toml`), ruff targeting `py312`. CI tests 3.12 and 3.13, and an `oldest-python` job builds cards on the floor. The floor is part of constitution II because it decides which libraries are eligible — it has already been moved twice by that fact, most recently off 3.11 because PyYAML has no cp311 `win_arm64` wheel.

**Secondary language**: Typst — the card (`templates/card.typ`), the press sheet (`templates/cards.typ`), the brand graphics (`assets/brand/*.typ`) and the test-data generators. **This feature's real work is here**: the page loop at the foot of `cards.typ`.

**Runtime dependencies**: `pyyaml==6.0.3`, declared in `REQUIREMENTS` in `scripts/deps.py` and read through `scripts/yamlio.py`. Unchanged by this feature.

**Dev dependencies**: `pytest>=9.1.1`, `ruff==0.16.2`, `pillow>=11,<13`, plus `pyyaml` (`requirements-dev.txt`). Unchanged.

**Optional external tools**: `pdftotext` (poppler-utils). This feature leans on it harder than any before: `-bbox-layout` is how the page order is read back out of the finished PDF. Absent, or present but not poppler's, the new end-to-end tests **skip** — the existing `card_grid_per_page` already handles both cases and the new helper reuses that guard.

**Storage**: plain files on disk. No database. No new artifact on disk.

**Testing**: pytest, `testpaths = ["tests"]`, `addopts = "-q"`. **Test-first is mandatory** (constitution XI). The page-order assertions live in `tests/test_e2e.py`, which needs `LERNKARTEN_E2E=1` once before the PR.

**Lint/format**: ruff — line length 100, `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`.

**Typesetting engine**: Typst, pinned by version and SHA-256 per platform in `scripts/engine.py`. **Version unchanged** — `cards.typ` uses only `sys.inputs`, `range`, `.map` and `.enumerate`, all long-standing.

**Target Platform**: Windows, macOS and Linux as equals. Page order is decided in Typst and reported in Python; nothing platform-specific. The one platform caveat is the reader, not the writer: windows-latest carries a `pdftotext` without `-bbox-layout`, so the order tests skip there and Linux/macOS carry them.

**Project Type**: CLI tool + Claude Code plugin (skills). Single module, flat `scripts/`.

**Performance Goals**: unchanged — the same pages are typeset in a different order, so the build does the same work.

**Constraints**: the default path must stay bit-for-bit the behaviour of today (FR-008), because every existing project and every existing e2e assertion depends on it.

**Scale/Scope**: small. One flag, one `--input` pair, one Typst loop rewritten, one new docs gate, one prompt section, six documentation passages.

## Dependency Decisions

**No dependency change.**

### Reuse check (constitution III)

**Is anything being hand-rolled here?** No — and the tempting way to get this wrong is worth naming, because it is the obvious solution.

The obvious implementation is to build the duplex PDF and then reorder its
pages: `pypdf`, `pikepdf` and `fitz` all do it in five lines. That is rejected,
and not on a "we can write it ourselves" argument, which constitution III
forbids. It is rejected because **the pages do not need reordering — they need
producing in a different order**, and the code that produces them already takes
parameters. Adding a PDF-manipulation library would buy a post-processing step
to undo work the generator was about to do correctly, and it would be the first
runtime dependency this project cannot deliver to a plugin user (constitution
II: there is no mechanism to ship one today). Nothing is hand-rolled by
declining it: no PDF is parsed, edited or written by our code in either mode.

The same reasoning covers the test side. The order is read back with
`pdftotext -bbox-layout`, already in use, rather than with a PDF library added
as a dev dependency.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Pass? |
|---|---|---|
| I | The model-driven and deterministic halves stay coupled only through the four file formats | [x] The seam here is the *command line*, not a format. `skills/print/SKILL.md` learns a flag; no artifact under `cards/`, `catalog/`, `knowledge/` or `sources.yaml` changes shape, and FR-012 forbids a deck key on purpose |
| II | **(GATED)** Any new dependency installs with a plain `pip install` on Windows, macOS and Linux…; any new binary is self-fetching + checksum-pinned, or genuinely optional | [x] No new dependency and no new binary. `pdftotext` gains a use, in tests only, and keeps its skip |
| III | **(GATED)** Nothing is hand-rolled that a vetted library already does — or the Reuse check above says why | [x] See Reuse check: no PDF is parsed or rewritten in either mode, so there is nothing for a library to do |
| IV | **(GATED)** Every new dependency has a completed vetting table above | [x] N/A — no dependency proposed |
| V | Code lands in an existing module where one fits; any new `scripts/` file has a reason and a docstring | [x] No new file. `scripts/build_pdf.py` gains one flag, one helper and one input pair; `scripts/check_docs.py` gains one check beside `check_sheet_capacity`; `templates/cards.typ` rewrites its page loop |
| VI | Script imports stay acyclic; the format reader and the engine locator remain leaves | [x] No import changes at all |
| VII | **(GATED)** No user content committed; nothing forced past `.gitignore`; examples stay subject-agnostic | [x] Nothing added to the corpus. The docs gain printing instructions, which name no subject |
| VIII | No binaries committed; new test material is generated from a text source | [x] No new test material — the existing 29 demo cards fill 4 sheets at `a7` and 2 at `a8`, which is enough for every order assertion |
| IX | Typst sources edited, never generated files; nothing in `output/` hand-edited | [x] `templates/cards.typ` is the source and is the thing edited |
| X | Skill frontmatter valid — `name` == folder, `description` names its triggers | [x] `skills/print/SKILL.md` frontmatter gains simplex triggers ("one-sided printer", "print at simplex"); `name: print` unchanged. `check_docs.check_skills` still has to see the domain word |
| XI | **(NON-WAIVABLE)** Every behaviour was tested first | [x] Sixteen red assertions listed in Phase 1, in order, each naming the module it goes in and what it fails with today |
| XII | The four gates pass; ruff config not loosened without a stated reason | [x] No ruff config change |
| XIII | English throughout | [x] |
| XIV | Branch is `<prefix>/<short-kebab-name>`; `main` untouched directly; commit subjects prefixed | [x] `feat/simplex-print-order`. **Note**: the current worktree sits on `build/release-0-4-2`; the branch has to be cut before the first commit |
| XV | Engine version unchanged, or every platform checksum bumped with it | [x] Unchanged — no new Typst feature is used |
| XVI | `docs/design.md` read before any visible change; colour doubled by shape; no type shrunk to fit; brand PNGs re-rendered | [x] Read (`docs/design.md:145` states the page order and is one of the passages that has to change). Nothing on the card moves: same card, same scale, same mirroring — only the sequence of pages. No PNG re-render |
| XVII | Card style and Typst escaping rules from `CLAUDE.md` respected | [x] No card text is written or changed |

**Open-item check**: this feature does not touch the one item in
[Reconciliation → Still open](../../.specify/memory/constitution.md) —
dependencies pinned by version rather than by hash. It adds no dependency, so
it neither closes nor works around it.

**Post-Phase-1 re-check**: unchanged. The design added no file, no dependency
and no format change; the one thing it added to the risk surface is a docs gate
that can produce a false positive on future prose, which is bounded in
Phase 1 and mirrors an existing, accepted gate.

## Project Structure

### Documentation (this feature)

```text
specs/004-simplex-print-order/
├── plan.md                 # This file
├── research.md             # Phase 0 — where the order is decided, and how it is read back
├── data-model.md           # Phase 1 — sheets, faces, and the two orderings as a mapping
├── quickstart.md           # Phase 1 — how to prove it works, by command and by paper
├── contracts/
│   ├── cli.md              # the user-facing contract: the flag and the closing line
│   └── engine-inputs.md    # the internal contract: build_pdf.py -> cards.typ
├── checklists/
│   └── requirements.md     # written by /speckit-specify
└── tasks.md                # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
bin/
└── lernkarten              # TOUCHED: not at all. It forwards argv to build_pdf, so
                            #   `check` inherits --sides for free — worth a test, not a change

scripts/
├── build_pdf.py            # TOUCHED: SIDES tuple, --sides flag, sides threaded through
│                           #   engine_inputs(), new print_order_note(), closing line
├── check_docs.py           # TOUCHED: new check_print_order() beside check_sheet_capacity()
├── check_project.py        # untouched — it gates model-written artifacts, and no artifact changes
├── engine.py               # untouched — version and checksums stay
└── (deps, yamlio, demo, make_testdata, render_brand, zotero_*)  # untouched

skills/
└── print/SKILL.md          # TOUCHED: frontmatter triggers, the --sides row, and the
                            #   instructions it states after handing over the PDF
    (sources, ingest, catalog, cards)   # untouched

templates/
├── card.typ                # untouched — the card is identical in both orders
└── cards.typ               # TOUCHED: the page loop at the foot becomes order-driven

tests/
├── test_build_pdf.py       # TOUCHED: engine input pair, print_order_note()
├── test_e2e.py             # TOUCHED: the order assertions, and a shared bbox reader
├── test_check_docs.py      # TOUCHED: the three-test pattern for the new gate
└── fixtures/demo-project/  # untouched — 29 cards is 4 sheets at a7 and 2 at a8

docs/
├── workflow.md             # TOUCHED: the print step, and the troubleshooting row
├── design.md               # TOUCHED: the "fronts and backs on consecutive pages" passage
├── testing.md              # TOUCHED: check 17 splits into 17a duplex / 17b simplex
└── index.html              # TOUCHED by hand — prose the docs gate does not read

README.md                   # TOUCHED: the "Printing and cutting" section
```

**Structure Decision**: no new file anywhere. Every change lands in a module
that already owns the concern — `build_pdf.py` owns the build's command line and
its closing line, `cards.typ` owns pagination, `check_docs.py` owns "a doc
states as fixed something that is now a setting". Constitution V is satisfied
without an argument, which is the point: this feature is a parameter, not a
subsystem.

### The two halves

**Model-driven work** (`skills/print/SKILL.md`): the skill learns when to pass
`--sides simplex` (the user says their printer prints one side), what to print
in its frontmatter triggers, and — the part that actually matters — that the
instructions it states depend on the mode it built.

The verifiable artifact for a prompt change is normally a `check_project.py`
check, because a prompt is verified through what it writes. This prompt writes
no file: it runs a command and speaks. So the red artifact is
`check_docs.check_print_order`, which reads `skills/print/SKILL.md` as one of
its inputs and fails on `SKILL.md:65` today. That is the same class of gate for
the same reason — a claim in a prompt that has silently become false — and it
is the gate that already exists for the previous instance of exactly this
mistake (`check_sheet_capacity`, written after a hand grep let two stale claims
ship in v0.4.0).

**Deterministic work** (`scripts/`, `templates/`): the flag, the input pair, the
Typst loop, the closing line, the new docs check. Covered by
`tests/test_build_pdf.py` (unit), `tests/test_e2e.py` (the real PDF) and
`tests/test_check_docs.py` (the gate).

**The seam**: none of the four file formats. The seam is the build's command
line and its closing line, and both are written down in
[contracts/cli.md](contracts/cli.md).

## Phase 0: Research

Consolidated in [research.md](research.md). In short:

- **Where the order is decided**: in `templates/cards.typ`, not in Python.
  Post-processing the PDF would need a runtime dependency the project cannot
  deliver, to undo work the generator was about to do right.
- **Is a library needed?** No. Asked first, per constitution III; answered by
  the fact that no PDF is parsed or written by our code in either mode.
- **Does Typst support it?** Yes, with the primitives already in the file. The
  loop can be rewritten so both orders fall out of one list of faces, which
  *removes* a duplicated `pagebreak()` rather than adding a branch.
- **Does the mirroring change?** No — and the rewrite makes that structural:
  `mirror` and "this is a back page" are the same boolean, so no ordering can
  desynchronise them.
- **Can the order be read back out of the PDF?** Yes, exactly. Every card
  footer already prints `<id> · 1/2` on the front and `<id> · 2/2` on the back
  (`templates/card.typ:96`), so which face a page carries is in the text layer.
  `card_grid_per_page` in `tests/test_e2e.py` already reads word positions with
  `pdftotext -bbox-layout`; the face marks come from the same parse.
- **Does the fixture suffice?** Yes. 29 demo cards = 4 sheets at `a7`, 2 at
  `a8`, and a `--topic` filter cuts a 1-sheet deck. No new material.
- **Degraded path**: no `pdftotext`, or a non-poppler one → the order tests
  skip, using the guard that already exists. No engine → the build fails before
  the flag matters.

## Phase 1: Design

### What a user sees

```console
$ lernkarten build cards/*.yaml -o output/cards.pdf --sides simplex
OK: 29 cards (english, german, greek, russian) -> output/cards.pdf
(8 pages, simplex: print pages 1-4 at 100 % scale, turn the stack over on the
long edge, then print pages 5-8.)
```

The duplex line does not move: `(8 pages, duplex, flip on long edge).` Existing
assertions on `"8 pages, duplex"` stay green untouched, which is FR-008 and
SC-003 enforced by the tests that already exist.

Two details fixed in [contracts/cli.md](contracts/cli.md) because they are the
kind of thing that gets decided by accident:

- A one-page range is written `page 1`, not `pages 1-1`. A single-sheet deck is
  the common case for someone trying the feature out, and `pages 1-1` reads
  like a bug.
- `--check` keeps today's line verbatim. It writes no PDF, so it has no page
  order to describe; the flag is accepted and inert (FR-007, scenario 6).

### The Typst loop

The current loop emits `front, pagebreak, back` per sheet and suppresses the
last break. The rewrite computes the face sequence first and then walks it:

```typst
#let sheets = range(0, calc.ceil(cards.len() / per-page))
#let order = if sides == "simplex" {
  sheets.map(i => (i, false)) + sheets.map(i => (i, true))
} else {
  sheets.map(i => ((i, false), (i, true))).fold((), (a, p) => a + p)
}
```

then one loop places `pagebreak()` before every face but the first. `sides`
arrives as `sys.inputs.at("sides", default: "duplex")`, matching how `columns`,
`rows`, `scale` and the sheet size already arrive — an absent input means the
old behaviour, so an engine call that forgets it cannot silently change a
build.

Two properties this buys, both asserted:

- The mirror flag *is* the is-back flag. FR-003 holds by construction at every
  grid and in both orders.
- Page count is `2 × len(sheets)` in both branches, so `pages()` in Python
  needs no change and FR-004 holds without a second implementation of the rule.

`.flatten()` is deliberately not used for the duplex branch: it flattens
deeply and would destroy the pairs.

### The docs gate

`check_print_order(errors)` sits beside `check_sheet_capacity`, over the same
`markdown_files()` — `*.md`, `docs/*.md`, `skills/*/SKILL.md`.

- **Claim**: a line naming `duplex`, or naming a flip on the long edge.
- **Qualified when**: the same line also names the other mode or the option —
  `simplex`, `one-sided`, `--sides`, `two-pass`, or `both orders`.
- **Reported otherwise**, naming the file and the phrase, the way
  `check_sheet_capacity` does.

The rule is the same one as its neighbour: an instruction that *was* a fact
about the sheet and is now a setting must name the setting. It fails today on
`README.md:128` and `:130`, `docs/workflow.md:273` and `:321`,
`docs/design.md:145`, `docs/testing.md:232`, and `skills/print/SKILL.md:4`
and `:65` — eight lines, more than the three the spec promised at minimum.

**Known limitation, accepted**: this is a prose gate and can false-positive on
future writing that mentions duplex in passing. So does `check_sheet_capacity`,
which has been in place since v0.4.0 without trouble, and the cost of a false
positive is adding four characters to a sentence. The cost of not having it is
on the record: two stale claims shipped.

`docs/index.html` is outside `markdown_files()` and stays outside — teaching the
gate HTML is a bigger change than this feature, and `tests/test_landing_page.py`
guards that file's structure, not its prose. It is updated by hand, and the
quickstart names it so it is not forgotten.

### Where this gets documented

`README.md` (the "Printing and cutting" section gains the one-sided path),
`docs/workflow.md` (the print step and the troubleshooting table),
`docs/design.md` (the page-order passage), `docs/testing.md` (check 17 becomes
17a duplex / 17b simplex, both per grid), `docs/index.html`, and
`skills/print/SKILL.md`. Every internal link added has to resolve —
`check_docs.check_links` is the gate.

### Test plan first

Sixteen assertions, in the order they should be written and seen failing. Each
names what it fails with **today**, so "red on the assertion" is checkable
rather than asserted.

**A. Unit — `tests/test_build_pdf.py`**

| # | Assertion | Red today with |
|---|---|---|
| 1 | `engine_inputs(5, True, DEFAULT_GRID, "simplex")` contains `--input sides=simplex` | `TypeError: engine_inputs() takes 3 positional arguments but 4 were given` |
| 2 | `engine_inputs(..., "duplex")` contains `sides=duplex` — the default is stated, not implied by absence | same `TypeError` |
| 3 | `print_order_note(8, "duplex") == "duplex, flip on long edge"` | `AttributeError: module 'build_pdf' has no attribute 'print_order_note'` |
| 4 | `print_order_note(8, "simplex")` names `pages 1-4` and `pages 5-8` | `AttributeError` |
| 5 | `print_order_note(2, "simplex")` names `page 1` and `page 2` — no `1-1` | `AttributeError` |
| 6 | `SIDES == ("duplex", "simplex")` and `DEFAULT_SIDES == "duplex"` | `AttributeError` |

**B. The gate — `tests/test_check_docs.py`** (mirrors the `check_sheet_capacity` trio exactly)

| # | Assertion | Red today with |
|---|---|---|
| 7 | A temp `README.md` reading "print duplex, flip on long edge" is reported, naming the file | `AttributeError: ... has no attribute 'check_print_order'` |
| 8 | A temp doc reading "duplex, flip on long edge — or `--sides simplex` for a one-sided printer" passes | `AttributeError` |
| 9 | `check_print_order` over the repo itself produces no errors | **fails on the eight shipped lines above** — this is the sweep, enforced |

**C. End-to-end — `tests/test_e2e.py`** (all skip without a poppler `pdftotext`)

| # | Assertion | Red today with |
|---|---|---|
| 10 | `--sides simplex` at `a7`: 8 pages, and `face_marks_per_page` reads `1/2` on pages 1-4 and `2/2` on pages 5-8 — the literal SC-001 | `error: unexpected argument '--sides'` (exit 2) |
| 11 | Same build: `pages[4 + i]` is `pages[i]` mirrored per row, for every `i` — each back sheet is behind its own front (SC-002) | exit 2 |
| 12 | Same at `--grid a8`: 4 pages, `1/2` on 1-2, `2/2` on 3-4, mirrored across four columns | exit 2 |
| 13 | Simplex and duplex builds of the same cards have the same page count, at both grids (SC-001) | exit 2 |
| 14 | A one-sheet deck (`--topic` filtered) has identical layout in both orders | exit 2 |
| 15 | The closing line reports `8 pages, simplex`, `pages 1-4` and `pages 5-8` (SC-004) | exit 2 |
| 16 | `--sides both` exits 2, writes no PDF, and the message names `duplex` and `simplex`; and `lernkarten check ... --sides simplex` exits 0 with `29 cards valid` | the first half passes for the wrong reason (argparse rejects an unknown flag) — write it after 10 so it is red on the *choice*, not on the flag |

**Not a new test**: `test_no_grid_flag_leaves_the_default_untouched` and
`test_the_backs_are_mirrored_across_the_requested_columns` already assert the
duplex order and must pass **unmodified** at the end. SC-003 is "no assertion
was rewritten", so rewriting one is the failure, not the fix.

**One refactor inside the tests**: `card_grid_per_page` and the new
`face_marks_per_page` both need words with coordinates, per page. Extract the
`pdftotext -bbox-layout` call and its two skip guards into `bbox_pages(path)`
and build both readers on it. Reuse rather than a second copy of the guard
(constitution III applies to test code too), and the two existing tests that
assert the guard *skips* keep working against the extracted function.

## Complexity Tracking

No "no" rows. The Constitution Check passes on all seventeen.

The one judgement call worth recording even though it is not a violation: the
new docs gate is prose-matching, which is inherently approximate. It is
accepted on precedent (`check_sheet_capacity`, same shape, same reason, in
place since v0.4.0) and because the alternative — a hand-run grep — is the
documented cause of the last two stale claims that shipped.
