# Implementation Plan: Figure cards — pictures from the sources on a card

**Branch**: `feat/figure-cards` | **Date**: 2026-08-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-figure-cards/spec.md`

## Summary

A card gains two optional keys, `front_image:` and `back_image:`, and `/ingest`
gains the job of deciding which pictures in a source are worth showing rather
than only describing. The build resolves each picture against the project root,
stages it into the compile workdir content-addressed, and hands the template a
bare file name — so the engine never leaves its sandbox and every "where did
this come from" question is settled in Python before typesetting starts. One
optional runtime dependency, `pypdfium2`, gets figures off PDF pages; nothing
else needs a library.

## Technical Context

**Language/Version**: Python `>=3.12` (`pyproject.toml`), ruff targeting `py312`. CI tests 3.12 and 3.13, and an `oldest-python` job builds cards on the floor. The floor is part of constitution II because it decides which libraries are eligible — it has already been moved twice by that fact, most recently off 3.11 because PyYAML has no cp311 `win_arm64` wheel. **This feature checked that gate again**: `pypdfium2` publishes `py3-none-win_arm64`, so the floor is not touched.

**Secondary language**: Typst — the card (`templates/card.typ`), the press sheet (`templates/cards.typ`), the brand graphics (`assets/brand/*.typ`) and the test-data generators.

**Runtime dependencies**: `pyyaml==6.0.3`, declared in `REQUIREMENTS` in `scripts/deps.py` and read through `scripts/yamlio.py`. **This feature adds a second, in a new optional set**: `pypdfium2==5.13.0`, installed only when a PDF figure is actually asked for, and degrading rather than failing when it cannot be (FR-018).

**Dev dependencies**: `pytest>=9.1.1`, `ruff==0.16.2`, `pillow>=11,<13`, plus `pyyaml` (`requirements-dev.txt`). Pillow earns a second job here: rendering two pages of a built PDF so a test can prove a picture is on the face that named it.

**Optional external tools**: `pdftotext` (poppler-utils) for PDF text. Absent → the path degrades or the test skips, never fails. `pypdfium2` now sits in the same category, one layer up: a *Python* optional whose absence costs PDF figures and nothing else.

**Storage**: plain files on disk — `sources.yaml`, `knowledge/`, `catalog/topics.md`, `cards/*.yaml`, `output/`, and now `figures/`. No database.

**Testing**: pytest, `testpaths = ["tests"]`, `addopts = "-q"`. **Test-first is mandatory** (constitution XI); the red-first order is in [Phase 1](#test-plan-first-the-red-order). Two suites are opt-in: `LERNKARTEN_E2E=1` lets the engine be fetched, `LERNKARTEN_DEPS_NET=1` lets one test install from PyPI.

**Lint/format**: ruff — line length 100, `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`.

**Typesetting engine**: Typst `0.15.1`, pinned by SHA-256 per platform in `scripts/engine.py`. **Unchanged by this feature** — it already reads PNG, JPEG, GIF, SVG and WebP, verified by spike ([R3](./research.md#r3--which-picture-formats-may-a-card-name)).

**Target Platform**: Windows, macOS and Linux, treated as equals (constitution II). This feature puts *paths* into a file format for the first time, which raises the Windows stake: separators, case sensitivity and the "inside the project" rule all have to behave the same on all three.

**Project Type**: CLI tool + Claude Code plugin (skills). Single module, flat `scripts/`.

**Performance Goals**: cold start unchanged. `pypdfium2` is imported only inside `scripts/figures.py`, which `bin/lernkarten` never imports — so `build` and `check` pay nothing. Staging copies bytes per build; content-addressing keeps it to one copy per distinct picture.

**Constraints**: frictionless install on all three platforms; works offline once installed; output must survive a black-only laser print and a photocopier — a constraint this feature can only half meet, since a source's chart may carry its meaning in colour ([Print & Design](#print--design)).

**Scale/Scope**: ~2 000 lines of Python across 11 flat modules, 5 skills, 2 Typst templates, ~1 900 lines of tests, one shared fixture corpus. This adds one module, one test module, four broken fixtures and two demo generators.

## Dependency Decisions

### Reuse check (constitution III)

**Is anything being hand-rolled here?** No. Three things that look like candidates for hand-rolling were each given to something that already does the job:

| Job | Given to | Rather than |
|---|---|---|
| Getting a figure off a PDF page | `pypdfium2` | a hand-rolled PDF object walker |
| Downloading a picture from a URL | `urllib`, standard library | `requests`, which would be a dependency for something already in the box |
| Deciding whether a file really is the image its extension claims | the typesetting engine, at test-compile | a magic-byte sniffer. `imghdr` was removed from the standard library in 3.13, and promoting Pillow to a runtime dependency for one boolean fails the proportionality gate ([R4](./research.md#r4--what-can-be-checked-in-python-and-what-has-to-be-left-to-the-engine)) |

Alternatives to `pypdfium2` and why each was rejected — PyMuPDF on licence (AGPL), pdfminer.six and pikepdf on capability (object libraries, not renderers), `pdftoppm` on granularity (whole pages) — are in [R6](./research.md#r6--is-there-a-library-for-pulling-figures-out-of-a-pdf-and-does-it-clear-the-gates).

### Vetting (constitution IV)

| Gate | Answer |
|---|---|
| **Package + version bound** | `pypdfium2==5.13.0` — pinned exactly, matching the existing `pyyaml==6.0.3`. `deps.py` keys its cache directory on the requirement string, so a range would make the cache ambiguous |
| **What it is for** (goes in the manifest as a comment) | Renders a figure region off a PDF page for `/ingest`; optional, and only that |
| **Wheels for Windows / macOS / Linux**, or pure Python | All three, `py3-none-*` with a bundled PDFium binary — no C extension, no compiler, no per-Python build. `win32`, `win_amd64`, **`win_arm64`**, `macosx_13_0` arm64 + x86_64, `manylinux_2_17` x86_64 + aarch64, musllinux |
| **Plain `pip install`**, no apt/brew/choco, no PATH edit, no post-install step | Yes |
| **Works on the supported Python floor** | `requires_python >=3.6`; the wheels are `py3-none`, so 3.12 and 3.13 both take the same file |
| **Last release** (date) | `5.13.0`, **2026-08-13** — nine days before this plan |
| **Issues/PRs triaged; not archived or unmaintained** | Active: 129 releases, a maintained 5.x line, public tracker on GitHub |
| **Stable line** — no alpha/beta/rc; ≥ 1.0 or long stable track record | `5.13.0`, well past 1.0 |
| **Adoption** — download volume, real dependents | Widely depended on in the PDF-tooling ecosystem; the standard permissively-licensed alternative to PyMuPDF |
| **Provenance** — maintainer/org, public repo, PyPI history matches it | `pypdfium2-team` on GitHub; PyPI project URLs point at that repo; wheels built in the open |
| **Not a typo-squat** — spelling checked against the package actually meant | Checked: `pypdfium2`, the team's own name. Not `pypdfium`, not `pdfium2` |
| **No install-time scripts** that build, download or phone home | None — the binary is inside the wheel |
| **Licence** compatible with MIT | BSD-3-Clause / Apache-2.0. Both compatible; this is precisely where PyMuPDF failed |
| **Transitive tree** — how many packages does it pull? | **Zero.** `requires_dist` is null |
| **Cold-start import cost** acceptable | Not paid: imported only inside `scripts/figures.py`, which `bin/lernkarten` never imports |
| **No known unfixed advisory** | None at the time of adoption |
| **Dependabot covers the declaring manifest** | `scripts/deps.py` is not a manifest Dependabot reads — **and neither is the existing `pyyaml` pin**. Recorded below as a pre-existing gap this feature widens, not one it introduces |

**Removals**: none.

## Constitution Check

*GATE: must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Pass? |
|---|---|---|
| I | The model-driven and deterministic halves stay coupled only through the four file formats | ⚠️ — still files only, but the contract widens from five artifacts to six. [Complexity Tracking](#complexity-tracking) |
| II | **(GATED)** Any new dependency installs with a plain `pip install` on Windows, macOS and Linux, with wheels and no compiler | ✅ — `py3-none` wheels including `win_arm64`, no compiler, zero transitive deps |
| III | **(GATED)** Nothing is hand-rolled that a vetted library already does | ✅ — [Reuse check](#reuse-check-constitution-iii); three candidates for hand-rolling all handed off |
| IV | **(GATED)** Every new dependency has a completed vetting table, and a reviewer read it | ✅ — filled above; one honest ⚠️ on the Dependabot row |
| V | Code lands in an existing module where one fits; any new `scripts/` file has a reason and a docstring | ✅ — one new module with the reason in [Structure Decision](#structure-decision) and in [contracts/figures-cli.md](./contracts/figures-cli.md#why-one-module-and-not-three) |
| VI | Script imports stay acyclic; the format reader and the engine locator remain leaves | ✅ — `figures` imports `deps` only; `build_pdf` gains no new local import |
| VII | **(GATED)** No user content committed; nothing forced past `.gitignore`; examples stay subject-agnostic | ✅ — `figures/` gitignored at root and in the fixture; demo pictures invented. **Needs the explicit PR note** |
| VIII | No binaries committed; new test material is generated from a text source | ✅ — two new generators under `tests/fixtures/demo-project/generators/` |
| IX | Typst sources edited, never generated files | ✅ — `templates/card.typ` |
| X | Skill frontmatter valid — `name` == folder, `description` names its triggers | ✅ — unchanged; only the bodies of `ingest` and `cards` change |
| XI | **(NON-WAIVABLE)** Every behaviour tested first, red on the assertion. Prompt changes have a failing `check_project.py` check | ✅ — [the red order](#test-plan-first-the-red-order); 29 assertions, 12 of them `check_project.py` checks for the prompt half |
| XII | The four gates pass; ruff config not loosened | ✅ |
| XIII | English throughout | ✅ |
| XIV | Branch is `<prefix>/<short-kebab-name>`; `main` untouched; commit subjects prefixed | ✅ — `feat/figure-cards` |
| XV | Engine version unchanged, or every platform checksum bumped | ✅ — 0.15.1 unchanged; the format set was verified against that exact build |
| XVI | `docs/design.md` read before any visible change; colour doubled by shape; no type shrunk to fit; brand PNGs re-rendered | ⚠️ — read and to be extended. The card's band geometry does not move, so no re-render; **but a source's chart can carry meaning in colour and we cannot fix that.** [Print & Design](#print--design) |
| XVII | Card style and Typst escaping rules from `CLAUDE.md` respected | ✅ — `front`/`back` markup rules untouched; the picture is not markup |

**Open-item check** — the constitution's [Still open](../../.specify/memory/constitution.md) row is *dependencies pinned by version rather than by hash*. This plan **does not close it and slightly widens it**: a second version-pinned package now reaches users through `deps.py`, which Dependabot does not read. Closing it means `--require-hashes` and a hash-bearing requirement list in `deps.py`, which touches `pyyaml` too and belongs on its own branch. Recorded here so the widening is a decision and not a side effect.

## Project Structure

### Documentation (this feature)

```text
specs/006-figure-cards/
├── plan.md                        # this file
├── spec.md
├── research.md                    # Phase 0 — seven questions, four spiked
├── data-model.md                  # Phase 1 — the three formats that change
├── quickstart.md                  # Phase 1 — six runnable scenarios
├── contracts/
│   ├── cards-yaml.md              # front_image / back_image
│   ├── knowledge-frontmatter.md   # the figures: list and the inline marker
│   └── figures-cli.md             # scripts/figures.py — extract | fetch | place
├── checklists/requirements.md
└── tasks.md                       # NOT created by /speckit-plan
```

### Source Code (repository root)

```text
bin/lernkarten                     # untouched

scripts/
├── deps.py                    ✏️  # + FIGURES optional set; missing()/install() already parameterised
├── engine.py                      # untouched — 0.15.1 stays
├── yamlio.py                      # untouched
├── build_pdf.py               ✏️  # + path resolution, validation, staging, two payload keys
├── check_project.py           ✏️  # + the figures: contract, the card picture contract, the a8 note
├── check_docs.py                  # untouched
├── figures.py                 ➕  # NEW — extract | fetch | place. Imports deps only
├── make_testdata.py           ✏️  # + the new generated pictures
├── demo.py                        # untouched
└── render_brand.py                # untouched — band geometry does not move

skills/
├── ingest/SKILL.md            ✏️  # judge every picture; call figures.py; record the verdict
└── cards/SKILL.md             ✏️  # description, recognition and detail cards

templates/
└── card.typ                   ✏️  # a picture on either face, inside the measured body

tests/
├── test_build_pdf.py          ✏️  # resolution, validation, staging
├── test_e2e.py                ✏️  # the built PDF, per face, per grid
├── test_check_project.py      ✏️  # the twelve prompt-half assertions
├── test_deps.py               ✏️  # the optional set
├── test_testdata.py           ✏️  # the new generated material
├── test_repo_hygiene.py       ✏️  # figures/ stays out of the repo
├── test_figures.py            ➕  # NEW — mirrors scripts/figures.py
└── fixtures/demo-project/
    ├── generators/*.typ       ✏️➕ # handbook gains a figure + a repeated header; two new pictures
    ├── broken/                ➕  # four new fixtures for SC-002
    └── figures/               ➕  # generated, gitignored

docs/
├── design.md                  ✏️  # how a picture sits in the field
├── workflow.md                ✏️  # figures/ in the artifact list
└── testing.md                 ✏️  # the manual checklist gains four named items

CLAUDE.md                      ✏️  # the two card keys, in Conventions
.gitignore                     ✏️  # figures/*, plus the fixture's generated pictures
```

**Structure Decision**: everything lands in an existing module except one. The
exception is `scripts/figures.py`, and the three modules considered first were
`zotero_ingest.py` (Zotero-specific), `build_pdf.py` (owns the *output* PDF and
must not learn to read input PDFs — it would also drag the optional dependency
into `bin/lernkarten`'s import path, which is exactly what keeps cold start
free) and `make_testdata.py` (a generator). The new module has one subject and
one optional dependency, which is the right boundary; the full argument is in
[contracts/figures-cli.md](./contracts/figures-cli.md#why-one-module-and-not-three).

### The two halves

**Model-driven work** (`skills/ingest`, `skills/cards`): judge every picture and
record the verdict; call `figures.py` for the two jobs a prompt cannot do; mark
kept figures inline in the transcription; write description, recognition and
detail cards. None of that is verifiable by reading the prompt, so the red
artifacts are **eleven checks in `scripts/check_project.py`** with cases in
`tests/test_check_project.py` — items 13–23 below.

**Deterministic work** (`scripts/`, `templates/`): resolve, validate and stage
pictures; two payload keys; the picture on either face inside the measured
body; the optional dependency set; the degrade. Covered by
`test_build_pdf.py`, `test_e2e.py`, `test_figures.py`, `test_deps.py`,
`test_testdata.py` and `test_repo_hygiene.py` — items 1–17.

**The seam**: two of the shared formats plus one new artifact —
`cards/*.yaml` ([contract](./contracts/cards-yaml.md)),
`knowledge/<id>/<doc>.md` ([contract](./contracts/knowledge-frontmatter.md)),
and `figures/<source-id>/` ([data model](./data-model.md#1-figure--a-picture-worth-showing)).

## Phase 0: Research

Complete — [research.md](./research.md). Seven questions; four settled by
spiking against the pinned engine and PyPI, three by reading the code. The
decisions that shape everything below:

1. `measure()` sees an image, so **the overflow mechanism needs no new
   machinery** — only a minimum picture height to measure against ([R1](./research.md#r1--does-the-overflow-mechanism-still-work-when-a-card-holds-a-picture)).
2. Typst refuses a path that escapes the compile root, so pictures are
   **staged into the workdir**, content-addressed ([R2](./research.md#r2--how-does-the-engine-reach-a-picture-given-the-build-compiles-in-a-temp-workdir)).
3. Accepted formats are **png, jpg, jpeg, gif, svg, webp** — verified against
   0.15.1; TIFF and BMP fail ([R3](./research.md#r3--which-picture-formats-may-a-card-name)).
4. Three of FR-004's four causes are Python's, the fourth is the engine's ([R4](./research.md#r4--what-can-be-checked-in-python-and-what-has-to-be-left-to-the-engine)).
5. A picture path resolves against **the parent of the card file's directory** ([R5](./research.md#r5--what-resolves-a-picture-path-given-a-card-file-can-live-anywhere)).
6. `pypdfium2==5.13.0`, optional, through `deps.py` ([R6](./research.md#r6--is-there-a-library-for-pulling-figures-out-of-a-pdf-and-does-it-clear-the-gates)).
7. The demo project is extended, never duplicated ([R7](./research.md#r7--does-the-demo-project-already-carry-the-material)).

## Phase 1: Design

### The formats

Three contracts, written out in full under [contracts/](./contracts/) and
modelled in [data-model.md](./data-model.md):

- **`cards/*.yaml`** — `front_image:` / `back_image:`, nine rules, four
  distinguishable error messages.
- **`knowledge/<id>/<doc>.md`** — a `figures:` list with a closed `visual:`
  vocabulary (`diagram`, `chart`, `map`, `none`) and an inline markdown marker
  in the body. A boolean was rejected on purpose: `show: yes` parses as `True`
  under YAML 1.1 and `show: "no"` does not.
- **`scripts/figures.py`** — `extract | fetch | place`, with exit code 3 as the
  degrade contract.

### The card

`templates/card.typ`, both faces, inside the block that already gets measured:

- **Front**: prompt, then the picture below it. The prompt keeps 14 pt and its
  position; the picture takes the room under it.
- **Back**: the picture goes into the `1fr` row where the note rules live.
  A face with a picture has **no note rules** — the picture wins, and rules
  crammed into 4 mm are a smudge, not a place to write.
- **Both**: `fit: "contain"`, never cropped, never wider than the field.
- **Overflow**: measured against a *minimum useful picture height*, not against
  the room the picture is given. Otherwise a picture squeezed to 2 mm would
  report "fits" while being useless.

The three bands do not move, so `assets/brand/*.typ` need no re-render.

### What a user sees when it goes wrong

Four messages, each naming the card, the face and the path —
[contracts/cards-yaml.md](./contracts/cards-yaml.md#error-messages). For a deck
written before ids existed, the positional ref stands in, exactly as the
overflow warning already does.

### Print & Design

`docs/design.md` gains a section on how a picture sits in the field, what it
may displace (the note rules) and what it may never displace (the prompt, the
answer, the source line, the bands).

One honest limit, and it is the reason gate XVI is ⚠️ rather than ✅: this
project's own graphics obey *colour never carries meaning alone*, and a chart
lifted from someone else's PDF does not. On a black-only laser a red-vs-green
series becomes grey on grey, and no check can judge it. What the design *can*
guarantee is that the card still works without the picture — the text on the
same face says what the picture shows, which is why FR-023 makes that text
mandatory rather than optional. The rest goes on the manual checklist.

### Where this gets documented

`CLAUDE.md` (the two card keys), `docs/design.md` (the picture in the field),
`docs/workflow.md` (`figures/` in the artifact list), `docs/testing.md` (the
manual checklist). Every relative link has to resolve or `check_docs.py` fails.

### Test plan first: the red order

Twenty-nine assertions, each committed failing **on the assertion** before the
code that satisfies it (constitution XI). Grouped in dependency order.

**Deterministic half**

| # | Test | Goes red on |
|---|---|---|
| 1 | `test_build_pdf.py` — `load_cards` carries `front_image`/`back_image` | the keys are absent from the returned card |
| 2 | `test_build_pdf.py` — a path resolves against the card file's project root, from any cwd | resolution against cwd finds nothing |
| 3 | `test_build_pdf.py` — a missing picture errors, naming card + face | no error raised |
| 4 | `test_build_pdf.py` — a picture outside the project errors | no error raised |
| 5 | `test_build_pdf.py` — an unaccepted extension errors, listing the accepted set | no error raised |
| 6 | `test_build_pdf.py` — staging is content-addressed: one picture on three cards is copied once | the workdir holds three files |
| 7 | `test_figures.py` — `extract` manifest shape; a picture repeated on four pages is offered once with `repeated_on: 4` | offered four times |
| 8 | `test_figures.py` — no `pypdfium2` → exit 3, one stderr line, no traceback | traceback / wrong code |
| 9 | `test_figures.py` — `place` slug rule, collision suffix, same bytes twice → one file | a second copy appears |
| 10 | `test_deps.py` — the optional set is absent from `REQUIREMENTS`, reported by `missing()`, and gets its own cache directory | it installs with the default set |
| 11 | `test_testdata.py` — the new generated pictures exist; the handbook PDF has a figure and a header repeated on every page | files absent |
| 12 | `test_repo_hygiene.py` — `figures/` is ignored at the root and in the fixture | the paths come back as versioned |

**End to end** (needs `LERNKARTEN_E2E=1`; Pillow renders the pages)

| # | Test | Goes red on |
|---|---|---|
| 13 | `test_e2e.py` — a figure deck builds; page count is still `2 × ⌈n ÷ 8⌉` | build fails |
| 14 | `test_e2e.py` — **the picture is on the face that named it**: render page 1 and page 2 to PNG and assert the demo figure's distinctive flat colour appears on the back page and not on the front | the colour is on both or neither |
| 15 | `test_e2e.py` — text plus minimum picture over the field warns, naming the card | no warning |
| 16 | `test_e2e.py` — an `a8` deck with a picture builds | build fails |
| 17 | `test_e2e.py` — the four broken fixtures exit non-zero with four different messages | one message covers two causes |

Assertion 14 is the one that needed designing rather than writing: neither
`pdf_pages()` nor `bbox_pages()` can see a raster. Rendering the two pages and
looking for a colour that appears nowhere in the card design is a real
assertion, not a proxy — and it costs nothing, because Pillow is already a dev
dependency and the demo picture's colour is ours to choose.

**Model-driven half** — `scripts/check_project.py` + `tests/test_check_project.py`

| # | Check | Goes red on |
|---|---|---|
| 18 | `figures:` is a list; every entry has `at:` and `visual:` | accepted today |
| 19 | `visual:` is in the closed vocabulary | accepted today |
| 20 | `visual: none` requires `why:`, forbids `path:` | accepted today |
| 21 | A kept figure requires `path:` + `caption:`; the path exists, sits under `figures/<source>/`, extension accepted | accepted today |
| 22 | A kept figure's path appears in the body as a markdown image link | accepted today |
| 22a | A subtopic with a picture-bearing card also has a text-only card (FR-024) | silent today |
| 23 | Two entries in one document may not share a `path` | accepted today |
| 24 | A card's picture path resolves, exists, is inside the project, has an accepted extension | accepted today |
| 25 | A face with a picture has non-empty text | accepted today |
| 26 | More than one card using a figure on the same face → warning | silent today |
| 27 | A picture key at the top level of a deck → error | silent today |
| 28 | An `a8` deck containing a picture → one note per run, not per card | silent today |

**What has no red assertion, and why** — three requirements produce run output
and touch no file, so constitution XI's carve-out applies and they are **named**
on the manual checklist in `docs/testing.md` rather than left implicit: the
`/ingest` summary line for an unreadable picture (FR-015), the picture count
folded into the "ask before more than N" threshold (FR-017), and the `/cards`
summary count (FR-025). A fourth item is a judgement rather than an assertion:
hold a printed figure card and see whether the chart survived the laser.

### Post-design constitution re-check

Nothing moved. Gate I stays ⚠️ (a sixth shared artifact), gate XVI stays ⚠️ (a
source's colour is not ours to double with shape), gate IV carries one honest ⚠️
inside its table (Dependabot does not read `deps.py`, and did not before this
feature either). Everything else passes as it did before Phase 1. No gate was
downgraded by the design.

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| A sixth shared artifact, `figures/<source-id>/` — the constitution's table names five | I | A picture cannot live in `knowledge/<id>/<doc>.md`: that file is text with one frontmatter block, and the build needs bytes it can hand to the engine. The halves still touch only through files, which is what the principle protects | *Base64 inside the knowledge document* — bloats a file meant to be read, and Typst has no base64 decoder to get it back out ([R2](./research.md#r2--how-does-the-engine-reach-a-picture-given-the-build-compiles-in-a-temp-workdir)). *Referencing the original under `raw/`* — breaks the moment the source folder is reorganised, and for a figure inside a PDF or on a web page there is no stable original to reference at all. **The constitution's format table is amended *before* this PR, on its own branch** — this feature is checked against the constitution, so it cannot also be the change that widens it |
| A second version-pinned runtime dependency reaching users through `deps.py`, which Dependabot does not read | IV | `pypdfium2` is the only permissively-licensed way to get a figure off a PDF page | Closing the gap properly means `--require-hashes` and a hash-bearing requirement list, which changes how `pyyaml` is installed too. That is its own branch; doing it here would hide a dependency-bootstrap change inside a feature |
| A new module, `scripts/figures.py` | V | Three verbs that a prompt cannot perform, sharing one subject and one optional dependency | Putting them in `build_pdf.py` would drag `pypdfium2` into `bin/lernkarten`'s import path and make the output-PDF module also an input-PDF module; `zotero_ingest.py` is Zotero-specific; `make_testdata.py` is a generator |
| A new test module, `tests/test_figures.py` | XI | It mirrors the new source module, which is the convention `docs/testing.md` already sets | Folding it into `test_ingest_sources.py` would mix a unit-level module test with the fixture-server tests, and the degrade case needs to control imports |

Principle XI has no row here. It is not waivable.
