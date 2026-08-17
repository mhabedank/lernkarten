# Implementation Plan: [FEATURE]

**Branch**: `[prefix]/[short-kebab-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

[Primary requirement from the spec + the technical approach in two or three sentences]

## Technical Context

<!--
  These values are the project's, not placeholders. Change one only if this
  feature genuinely changes it.
-->

**Language/Version**: Python `>=3.12` (`pyproject.toml`), ruff targeting `py312`. CI tests 3.12 and 3.13, and an `oldest-python` job builds cards on the floor. The floor is part of constitution II because it decides which libraries are eligible — it has already been moved twice by that fact, most recently off 3.11 because PyYAML has no cp311 `win_arm64` wheel.

**Secondary language**: Typst — the card (`templates/card.typ`), the press sheet (`templates/cards.typ`), the brand graphics (`assets/brand/*.typ`) and the test-data generators.

**Runtime dependencies**: `pyyaml==6.0.3`, declared in `REQUIREMENTS` in `scripts/deps.py` and read through `scripts/yamlio.py`. They reach the user by installing themselves on first use — `pip install --target` into a cache directory, `--only-binary :all:`, reported by `lernkarten deps --check`. A new one must be pinned exactly and must have a wheel for every supported platform, Windows ARM64 included.

**Dev dependencies**: `pytest>=9.1.1`, `ruff==0.16.2`, `pillow>=11,<13`, plus `pyyaml` so a checkout can run the tests without waiting for the bootstrap (`requirements-dev.txt`). Tools pinned exactly; libraries get a range.

**Optional external tools**: `pdftotext` (poppler-utils) for PDF text. Absent → the path degrades or the test skips, never fails. This is one of the two acceptable shapes for a binary dependency.

**Storage**: plain files on disk — `sources.yaml`, `knowledge/`, `catalog/topics.md`, `cards/*.yaml`, `output/`. No database.

**Testing**: pytest, `testpaths = ["tests"]`, `addopts = "-q"`. Seven levels; see `docs/testing.md`. **Test-first is mandatory** (constitution XI). Two suites are opt-in: `LERNKARTEN_E2E=1` lets the engine be fetched, `LERNKARTEN_DEPS_NET=1` lets one test install from PyPI.

**Lint/format**: ruff — line length 100, `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]`.

**Typesetting engine**: Typst, one self-contained binary, pinned by version and SHA-256 per platform in `scripts/engine.py` — Darwin arm64/x86_64, Linux x86_64/aarch64, Windows AMD64/ARM64. Fetched once on first build. Override with `LERNKARTEN_ENGINE`. This is the reference pattern for a self-fetching binary.

**Target Platform**: Windows, macOS and Linux, treated as equals (constitution II). `scripts/engine.py` covers all six platform pairs, and CI runs windows-latest legs on the `test`, `cards` and `e2e` jobs. All three platforms block a merge, so a Windows failure is a failure.

**Project Type**: CLI tool + Claude Code plugin (skills). Single module, flat `scripts/`.

**Performance Goals**: cold start matters — a fresh checkout reaches a PDF from one command. No throughput target; the workload is one user, a few hundred cards. A new dependency must not visibly slow a cold invocation (constitution IV).

**Constraints**: frictionless install on all three platforms; works offline once installed and once the engine is cached; output must survive a black-only laser print and a photocopier.

**Scale/Scope**: ~2 000 lines of Python across 11 flat modules, 5 skills, 2 Typst templates, ~1 900 lines of tests, one shared fixture corpus.

## Dependency Decisions

> Fill this in if the feature adds, replaces or removes a dependency — Python package, dev tool, or self-fetched binary. Otherwise write "No dependency change" and delete the tables.

### Reuse check (constitution III)

**Is anything being hand-rolled here?** [no / yes → name it]

If yes: which libraries were considered, and why did each fail Principle II or IV? "Only 200 lines" is not a reason. Both things this project once hand-rolled under the retired rule are gone — `minyaml` to PyYAML, `sips`/`magick` to Pillow — so neither is available as precedent.

### Vetting (constitution IV)

One table per proposed dependency. A row you cannot fill is a reason to stop.

| Gate | Answer |
|---|---|
| **Package + version bound** | [e.g. `pyyaml>=6.0,<7`] |
| **What it is for** (one line, goes in the manifest as a comment) | |
| **Wheels for Windows / macOS / Linux**, or pure Python | [confirm all three — sdist-only needing a compiler is rejected] |
| **Plain `pip install`**, no apt/brew/choco, no PATH edit, no post-install step | |
| **Works on the supported Python floor** | |
| **Last release** (date) | [within ~12 months] |
| **Issues/PRs triaged; not archived or unmaintained** | |
| **Stable line** — no alpha/beta/rc; ≥ 1.0 or long stable track record | |
| **Adoption** — download volume, real dependents | |
| **Provenance** — maintainer/org, public repo, PyPI history matches it, signed/attested if available | |
| **Not a typo-squat** — spelling checked against the package actually meant | |
| **No install-time scripts** that build, download or phone home | |
| **Licence** compatible with MIT | |
| **Transitive tree** — how many packages does it pull? | [thirty for one function → copy the three lines instead] |
| **Cold-start import cost** acceptable | |
| **No known unfixed advisory** | |
| **Dependabot covers the declaring manifest** | |

**Removals**: [any dependency this makes unused — it gets deleted, not left in place]

## Constitution Check

*GATE: must pass before Phase 0 research. Re-check after Phase 1 design.*

<!--
  Each row maps to a principle in .specify/memory/constitution.md. Answer all of
  them. A "no" is not automatically fatal, but it goes in Complexity Tracking
  with a justification. Rows marked (GATED) need more than a checkbox — see the
  note in each.
-->

| # | Gate | Pass? |
|---|---|---|
| I | The model-driven and deterministic halves stay coupled only through the four file formats | [ ] |
| II | **(GATED)** Any new dependency installs with a plain `pip install` on Windows, macOS and Linux, with wheels and no compiler; any new binary is self-fetching + checksum-pinned, or genuinely optional | [ ] |
| III | **(GATED)** Nothing is hand-rolled that a vetted library already does — or the Reuse check above says why | [ ] |
| IV | **(GATED)** Every new dependency has a completed vetting table above, and a reviewer read it | [ ] |
| V | Code lands in an existing module where one fits; any new `scripts/` file has a reason and a docstring | [ ] |
| VI | Script imports stay acyclic; the format reader and the engine locator remain leaves | [ ] |
| VII | **(GATED)** No user content committed; nothing forced past `.gitignore`; examples stay subject-agnostic — needs an explicit note in the PR description if touched | [ ] |
| VIII | No binaries committed; new test material is generated from a text source | [ ] |
| IX | Typst sources edited, never generated files; nothing in `output/` hand-edited | [ ] |
| X | Skill frontmatter valid — `name` == folder, `description` names its triggers | [ ] |
| XI | **(NON-WAIVABLE)** Every behaviour was tested first: the test is committed failing, on the assertion, before the implementation. Prompt changes have a failing `check_project.py` check | [ ] |
| XII | The four gates pass; ruff config not loosened without a stated reason | [ ] |
| XIII | English throughout — code, comments, docs, commit messages | [ ] |
| XIV | Branch is `<prefix>/<short-kebab-name>`; `main` untouched directly; commit subjects prefixed | [ ] |
| XV | Engine version unchanged, or every platform checksum bumped with it | [ ] |
| XVI | `docs/design.md` read before any visible change; colour doubled by shape; no type shrunk to fit; brand PNGs re-rendered | [ ] |
| XVII | Card style and Typst escaping rules from `CLAUDE.md` respected | [ ] |

**Open-item check**: does this feature touch the one thing left in the constitution's [Reconciliation → Still open](../memory/constitution.md#still-open) table — dependencies pinned by version rather than by hash? If so, say whether this plan closes it or works around it.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan output)
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output — for this project usually a *format* change
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output — the four file formats, if touched
└── tasks.md              # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

<!--
  This is the real layout. Mark the files this feature touches; delete the rows
  it does not. Do not replace it with a generic src/ tree.
-->

```text
bin/
└── lernkarten              # entry point; dispatches build | check | engine

scripts/                    # flat, imported by bare name via sys.path
├── deps.py                 # LEAF — installs the pinned runtime deps on first use
├── engine.py               # LEAF — finds/fetches Typst, pinned by SHA-256, 6 platforms
├── yamlio.py               # → deps. PyYAML plus a one-line error with the line number
├── build_pdf.py            # → engine, yamlio. The PDF build and --check
├── check_project.py        # → build_pdf, yamlio. Gate on model-written artifacts
├── check_docs.py           # → yamlio. Skill frontmatter, doc links, required files
├── make_testdata.py        # → engine. Generates the binary test material
├── demo.py                 # → make_testdata. Scratch copy of the demo project
├── render_brand.py         # → engine. Renders assets/brand/*.typ to PNG
├── zotero_ingest.py        # Zotero local API → knowledge/
├── zotero_stub.py          # Fakes the Zotero 7 API for tests
├── lernkarten              # mirror of bin/lernkarten
└── install-hooks.sh

skills/                     # the model-driven half — one prompt per step
├── sources/SKILL.md
├── ingest/SKILL.md
├── catalog/SKILL.md
├── cards/SKILL.md
└── print/SKILL.md

templates/
├── card.typ                # the card — 105 × 74.25 mm, three fixed bands
└── cards.typ               # the press sheet — A4, 8 up, duplex

assets/
├── brand/*.typ             # graphic sources
└── *.png, *.svg            # rendered marks and graphics (committed)

tests/
├── test_yamlio.py          # unit
├── test_deps.py            # the dependency bootstrap
├── test_engine.py          # unit
├── test_build_pdf.py       # unit
├── test_testdata.py        # the generator; the scan has no text layer
├── test_ingest_sources.py  # web over http.server, zotero over the stub
├── test_e2e.py             # bin/lernkarten as a subprocess, PDF taken apart
├── test_check_project.py   # contracts of the four model-driven steps
├── test_repo_hygiene.py    # no user content, no committed binaries
└── fixtures/
    ├── demo-project/       # THE shared corpus — raw, knowledge, catalog, cards, broken, generators
    └── zotero/             # library.json + generated attachments

docs/
├── workflow.md  design.md  testing.md  index.html

cards/example.yaml          # the only versioned card file of "your own"
sources.example.yaml
```

**Structure Decision**: [Which of the above this feature touches, and why. If it adds a file, say which existing module was considered first and why it did not fit — constitution V.]

### The two halves

<!--
  Split the work explicitly. The halves are verified differently, so a plan that
  blurs them produces tasks that cannot be checked.
-->

**Model-driven work** (`skills/`): [what prompt changes — and the `check_project.py` check that will be written *first* and seen failing, since that is the only way a prompt change is verifiable at all]

**Deterministic work** (`scripts/`, `bin/`, `templates/`): [what code changes, which test module covers it, and which assertion goes red first]

**The seam**: [which of the four file formats carries the change, or "none — the halves are untouched"]

## Phase 0: Research

[Unknowns to resolve before design. Typical ones here:]

- **Is there a library for this?** Constitution III makes this the *first* question, not the last. Name the candidates.
- Do the candidates ship wheels for Windows (including ARM64), macOS and Linux, on the floor? What is their transitive tree?
- Is the need runtime or dev-only? Runtime goes through `scripts/deps.py` and must have a wheel everywhere; dev-only goes in `requirements-dev.txt`.
- Does Typst support the layout this needs?
- Does the demo project already carry material for this, or must the fixture be extended?
- What does the degraded path look like without `pdftotext` / without an engine?

## Phase 1: Design

[Format changes (as a contract under `contracts/`), module placement, the error messages a user will see, and where in `docs/` this gets documented. Remember: a doc link that does not resolve fails `check_docs.py`.]

**Test plan first**: list the assertions that will go red, in order, before any implementation task exists. If a requirement has no red assertion, it is not specified sharply enough yet (constitution XI).

## Complexity Tracking

> Fill ONLY if the Constitution Check above has a "no".

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| [e.g. dependency with an sdist-only build] | II | [need] | [why no wheel-shipping alternative works] |
| [e.g. hand-rolling a parser] | III | [need] | [why every library candidate failed II or IV] |
| [e.g. a new module under `scripts/`] | V | [need] | [why no existing module fits] |
| [e.g. a second fixture corpus] | XI | [need] | [why the demo project cannot be extended] |

Principle XI has no row here. It is not waivable.
