# Implementation Plan: Sphinx documentation foundation

**Branch**: `docs/skill-reference` | **Date**: 2026-09-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-skill-reference/spec.md`

**Companion artifacts**: [research.md](research.md) (Phase 0 — everything below
that says "measured" is measured there), [data-model.md](data-model.md),
[contracts/docsite-layout.md](contracts/docsite-layout.md),
[quickstart.md](quickstart.md).

## Summary

012 stands up the documentation site: `sphinx` + `myst-parser` +
`pydata-sphinx-theme` in a docs-only dependency channel, a `docsite/` source
tree that `{include}`s the five documents that already exist rather than moving
them, a ~40-line build-time transform that turns their repository links into
site links or GitHub URLs, a theme flattened to `docs/design.md`, and a rebuilt
`pages.yml` that publishes the landing page at the root and the documentation at
`/docs/`. **No generated content** — that is 013 — and **no tutorial** — that is
014.

The spike behind this plan built the real thing. Three of the four hard
questions turned out to have measured answers rather than estimates, and the
fourth (the theme) is sized below. Four places where the spec and the repository
disagree are recorded in [Findings](#findings-carried-from-phase-0) rather than
planned around.

## Technical Context

**Language/Version**: Python `>=3.12` (`pyproject.toml`), ruff targeting `py312`.
CI tests 3.12 and 3.13, and an `oldest-python` job builds cards on the floor.
The three documentation packages all declare `Requires-Python: >=3.11`, so the
floor is untouched by this feature.

**Secondary language**: Typst — untouched by 012.

**Runtime dependencies**: `pyyaml==6.0.3` via `scripts/deps.py`. **Unchanged.**
FR-003 and FR-005 forbid this feature from adding to that channel, and SC-009
asserts it.

**Dev dependencies**: `requirements-dev.txt` unchanged. A **third** manifest,
`requirements-docs.txt`, is added (FR-002).

**Docs dependencies (new)**: `sphinx==9.0.4`, `myst-parser==5.1.0`,
`pydata-sphinx-theme==0.21.0`. Pure-Python wheels; 33-distribution closure with
full `cp312` wheel coverage on `win_arm64`, `manylinux2014_x86_64` and
`macosx_11_0_arm64`. See [Dependency Decisions](#dependency-decisions).

**Storage**: plain files. No format change (`## Format Contracts` in the spec is
"none" on all four rows).

**Testing**: pytest. Docs-build tests **skip** when the docs requirements are
absent, with a message naming `requirements-docs.txt` — the shape
`tests/test_e2e.py` already uses for the engine (FR-023, SC-006).

**Lint/format**: ruff, line length 100, `select = ["E","F","W","I","UP","B","C4","SIM"]`,
**no `exclude`** — so `docsite/conf.py` and the extension module are inside
gate #1 from their first commit (FR-024). Measured: the transform module passes
both `ruff check` and `ruff format --check` as written; a stock Sphinx `conf.py`
does not, and is written by hand instead of copied from the template.

**Target Platform**: Windows, macOS and Linux — FR-034 puts the docs build on
all three in CI, matching SC-001.

**Project Type**: CLI tool + Claude Code plugin, plus (new) a published
documentation site.

**Performance Goals**: none new. The docs toolchain is off every runtime path.

**Constraints**: the build is offline, deterministic, and produces no absolute
paths (all three measured). The site loads no third-party sub-resource
(SC-014).

**Scale/Scope**: five migrated documents, ~10 new source files under `docsite/`,
one new `scripts/` module, one new workflow job, three new manual checklist rows.

## Dependency Decisions

### Reuse check (constitution III)

**Is anything being hand-rolled here?** **No.** Static site generation, Markdown
parsing and checked cross-references are all taken from libraries. The single
piece of bespoke code is the FR-029 link transform (~42 lines of logic), and it
is bespoke because no library knows this repository's `_site` layout, its
`PAGES` mapping or its GitHub URL. Nothing on PyPI does that.

### Vetting (constitution IV)

The full three-package table, the 33-distribution wheel matrix and the licence
survey are in [research.md § R1](research.md#r1--dependency-vetting-principle-iv-fr-002--fr-004).
The summary a reviewer needs:

| Gate | Answer |
|---|---|
| **Package + version bound** | `sphinx==9.0.4`, `myst-parser==5.1.0`, `pydata-sphinx-theme==0.21.0` — **pinned exactly** |
| **What each is for** | build the site / read the Markdown that already exists / the theme pandas and numpy use |
| **Wheels for Win / macOS / Linux**, or pure Python | all three are `py3-none-any`. Verified for the *whole* closure with `pip download --only-binary=:all: --abi cp312` against `win_arm64`, `manylinux2014_x86_64` and `macosx_11_0_arm64`: 33/33 resolve. Only `charset-normalizer`, `MarkupSafe` and `PyYAML` are non-pure, and all three publish `cp312` wheels for each platform |
| **Plain `pip install`**, no apt/brew/choco, no PATH edit, no post-install step | yes — wheel installs only |
| **Works on the supported Python floor** | all three declare `Requires-Python: >=3.11`; 3.12 clears it |
| **Last release** | all three are on current release lines as of 2026-09 |
| **Issues/PRs triaged; not archived** | yes — sphinx-doc, executablebooks and pydata are all active organisations |
| **Stable line** | Sphinx 9.0.4 and myst-parser 5.1.0 are ≥ 1.0. `pydata-sphinx-theme` is 0.21.0, **pre-1.0**, admitted under Principle IV's explicit clause for "a pre-1.0 package with a long, obviously stable track record and wide adoption": it is the theme of pandas, numpy, SciPy, Jupyter and Bokeh, and FR-001 chose it *because* pandas and numpy use it |
| **Adoption** | Sphinx and its `sphinxcontrib-*` set are among the most-downloaded packages on PyPI; the theme's dependents are named above |
| **Provenance** | public repositories (`sphinx-doc/sphinx`, `executablebooks/MyST-Parser`, `pydata/pydata-sphinx-theme`), PyPI history matching each |
| **Not a typo-squat** | spelling checked character by character: `sphinx`, `myst-parser`, `pydata-sphinx-theme` |
| **No install-time scripts** | none — all three install from wheels with no build step |
| **Licence** | BSD-2-Clause / MIT / BSD-3-Clause. The whole closure is permissive; the only non-BSD/MIT/Apache entry is `certifi` (MPL-2.0, file-level copyleft on unmodified files, dev-only, never redistributed) |
| **Transitive tree** | **33 distributions — a stated cost, not a clean pass.** See the note below |
| **Cold-start import cost** | none: FR-003/FR-005 keep every one of them off the runtime path, and SC-009 asserts `lernkarten build` runs with none of them installed |
| **No known unfixed advisory** | none outstanding on any of the 33 at adoption |
| **Dependabot covers the declaring manifest** | yes, with no edit — `.github/dependabot.yml` already declares `package-ecosystem: pip, directory: "/"`, which picks up a new root-level `requirements-docs.txt` |

**On the transitive tree.** Principle IV asks for "a shallow transitive tree" and
names "thirty packages to get one function" as the failing shape. Thirty-three is
over that number and the plan says so rather than rounding it down. Three things
make it acceptable, and all three are structural rather than rhetorical:

1. It is not thirty-three packages for one function; it is a documentation
   toolchain, adopted instead of hand-writing HTML for the reasons FR-001 gives.
2. **FR-002's separate manifest is the mitigation, and it works**: the tree lands
   on nobody who is not building documentation. `requirements-dev.txt` stays as
   it is, `pytest` still installs in seconds, and SC-006 asserts the suite passes
   with none of this present.
3. **It never reaches a user.** FR-003 keeps it out of `scripts/deps.py`;
   SC-009 asserts `lernkarten build` and `lernkarten check` run in an
   environment where no documentation dependency exists.

`requests` (with `certifi`, `urllib3`, `idna`, `charset-normalizer`) is worth
naming because a reviewer will spot a network library in a docs toolchain: it is
a **hard** `Requires-Dist` of Sphinx 9 (for the `linkcheck` builder) and of the
theme. It is not added by this plan and cannot be removed. The build itself makes
no network call, which is what SC-001 actually asserts and what was measured.

**Pinning strategy**: exact, for all three. Principle IV pins *tools* exactly and
gives *libraries* a range; Sphinx is a tool here — SC-004 compares its output
byte-for-byte and FR-020 makes its warning set a gate, so a patch release
drifting under a contributor is exactly what the exact-pin rule exists to stop.
Same reasoning as `ruff==0.16.5`. The transitive closure is **not** pinned:
hand-maintained closure pinning is the constitution's one open Reconciliation
item, and this feature neither closes nor worsens it.

**Removals**: none. 012 removes nothing (the spec says so); the hand-written
command list in `README.md` and the bespoke drift gates become candidates in 013.

**No dependency fails a `CONTRIBUTING.md` gate.** There is nothing here to stop
and report.

## Constitution Check

*Checked before Phase 0 and re-checked after Phase 1 design. Both passes below.*

| # | Gate | Pass? |
|---|---|---|
| I | The two halves stay coupled only through the four file formats | **yes** — 012 touches no skill and no format. Spec's Format Contracts table is "none" on all four rows |
| II | **(GATED)** Plain `pip install`, wheels, no compiler; no new binary | **yes** — measured across three platform tags for the whole 33-package closure. No new binary; the docs build needs no typesetting engine |
| III | **(GATED)** Nothing hand-rolled that a library does | **yes** — see Reuse check. The transform is repository-specific glue, not a reimplementation |
| IV | **(GATED)** Completed vetting table | **yes**, above. One gate (transitive tree) is answered as a stated cost with its mitigation, not ticked |
| V | New `scripts/` file has a reason and a docstring; code lands where it fits | **yes** — `scripts/build_docs.py` is required by FR-019 and gets the established docstring shape. **Requires a constitution amendment** (FR-039): Principle V's table gains a `docsite/` row and its `docs/` row gains `leitner.html` |
| VI | Script imports stay acyclic; `deps` and `engine` stay leaves | **yes** — `build_docs` imports **no local module** and becomes a new leaf. **Enforced**: `check_import_graph()` fails the *Skills & docs* job until Principle VI's fenced block lists it (FR-039) |
| VII | **(GATED)** No user content; examples stay subject-agnostic | **yes** — every page is about the tool. Nothing under `knowledge/`, `catalog/`, `cards/` is touched |
| VIII | No binaries committed | **yes** — the fonts are already committed and already named in Principle VIII. The build **copies** them; it converts nothing, so no new binary appears (this is why `woff2` was rejected — see research R4) |
| IX | Sources edited, never generated files | **yes** — `docsite/_build/` and `_site/` go into `.gitignore` (FR-022) |
| X | Skill frontmatter valid | **yes** — no skill changes in 012 |
| XI | **(NON-WAIVABLE)** Tested first, red on the assertion | **yes** — the red-first order is in [Phase 1](#phase-1-design). Three requirements that no test can reach get **numbered manual rows 44–46** in `docs/testing.md` (FR-025), and no more than three |
| XII | The four gates pass; ruff not loosened | **yes** — and no fifth gate (FR-024). Gate #1's *scope* widens to `docsite/`, which was measured and costs one line-length fix |
| XIII | English throughout | **yes** |
| XIV | Branch `docs/skill-reference`; `main` untouched | **yes** |
| XV | Engine version unchanged | **yes** — untouched |
| XVI | `docs/design.md` read before any visible change | **yes** — read, and the change it governs is the theme. FR-036 amends it with a third surface row, deliberately, in this feature |
| XVII | Card style respected | **n/a** — no cards |

**Open-item check**: the constitution's one open Reconciliation item is
"dependencies are pinned by version, not by hash". This feature **neither closes
nor worsens it**: the three direct packages are pinned exactly by version, in the
same style as `ruff`, and no hash table is introduced. Closing it remains its own
piece of work.

**Post-design re-check**: unchanged. The design added no dependency, no binary,
no import edge and no format change beyond what the pre-check recorded.

## Findings carried from Phase 0

Four measurements contradict the spec. None is fatal; each has a decision here.
Full evidence in [research.md](research.md#findings-that-contradict-the-spec).

| # | The spec says | Measured | Decision |
|---|---|---|---|
| **C1** | FR-031: hand-edit `docs/design.md`'s `index.html` → `../index.html` and `../assets/card-box.pdf` → `../card-box.pdf` | Both edits make the source link **dead on the file system**, so `check_docs.check_links` — gate #4 — goes red on the commit that makes them. Against FR-024 and SC-011 | **Do not hand-edit.** Both go into the transform's `SERVED` table; the sources keep the paths `check_links` already accepts. This is what FR-029's own reasoning asks for; FR-031's table survives as the *enumeration*, only the mechanism moves |
| **C2** | FR-031: the value is `../index.html` | Correct only for a flat `docsite/`. Under FR-007's two areas the page is at `/docs/contributing/design.html` and needs `../../index.html` | The transform computes `"../" * (docname.count("/") + 1)`. Same destination, one line |
| **C3** | FR-037: a `docsite/` page writes `[design.md](../docs/design.md)` | MyST strips `.md`, resolves it as a **docname**, finds nothing, warns (fatal under `-W`) and renders **no link at all** | The transform gains a branch for `refdomain == "doc"` targets absent from `env.all_docs`: put the suffix back, run the same lookup. FR-037's spelling then works and its intent (visible to `check_links`) is preserved |
| **C4** | FR-032: a wrapper page links out to `leitner.html` | Written as a relative path it becomes a MyST **download**: Sphinx copies the file to `_downloads/<hash>/leitner.html`, a **second URL** with a `download=""` attribute. Violates FR-010 and SC-012 | The transform also handles `download_reference`, on `doctree-read` at `priority=100` — ahead of Sphinx's `DownloadFileCollector` (500). Measured: `_downloads/` disappears; the link renders `../../leitner.html` |

One caveat that contradicts nothing but qualifies a claim: FR-014's `docs/` link
is a **directory**, and over `file://` a browser shows a listing rather than
`index.html`. The local preview therefore verifies everything FR-038 promises
except that one hop, which needs `python3 -m http.server _site`. FR-014 is
unchanged (the deployed behaviour is correct); the quickstart says to serve
rather than open.

## Project Structure

### Documentation (this feature)

```text
specs/012-skill-reference/
├── spec.md
├── plan.md                      # this file
├── research.md                  # Phase 0 — the measurements
├── data-model.md                # Phase 1 — the structural entities, no format change
├── contracts/
│   └── docsite-layout.md        # the docsite/ contract and the PAGES/SERVED tables
├── quickstart.md                # Phase 1 — how to verify this feature end to end
└── checklists/requirements.md
```

### Source Code (repository root) — what 012 touches

```text
requirements-docs.txt            # NEW  — FR-002. Three exact pins, one comment each

docsite/                         # NEW  — FR-028. Configuration and page sources
├── conf.py                      #        hand-written; ruff-clean from commit one
├── _ext/
│   └── repolinks.py             #        FR-029/C3/C4 — the build-time link transform
├── _static/
│   └── lernkarten.css           #        FR-027/FR-035 — inks, faces, flattening, floor
├── index.md                      #        root document; the two toctrees
├── user/
│   ├── index.md                 #        the user guide area
│   ├── workflow.md              #        one {include} of docs/workflow.md
│   └── leitner.md               #        FR-032 wrapper — a signpost, never a copy
└── contributing/
    ├── index.md
    ├── design.md                #        {include} of docs/design.md
    ├── testing.md               #        {include} of docs/testing.md
    └── guide.md                 #        {include} of CONTRIBUTING.md

scripts/
└── build_docs.py                # NEW  — FR-019/FR-038. Builds, then assembles _site.
                                 #        LEAF: imports no local module

docs/                            # unchanged on disk — the point of {include}
├── workflow.md  design.md  testing.md    # not moved, not edited (see C1)
├── index.html                   # EDIT — one link added (FR-014): `docs/`
└── leitner.html                 # untouched, byte-identical (FR-010)

CONTRIBUTING.md                  # stays at the root (FR-009); § Development setup
                                 # gains the optional docs install
README.md                        # EDIT — three links retargeted at the site (FR-042)
docs/design.md                   # EDIT — § The screen surfaces gains a third row (FR-036)
docs/testing.md                  # EDIT — three numbered manual rows, 44–46 (FR-025)
.specify/memory/constitution.md  # EDIT — Principles V and VI, version + date (FR-039)
.gitignore                       # EDIT — docsite/_build/ and _site/ (FR-022)
pyproject.toml                   # unchanged
scripts/check_docs.py            # EDIT — markdown_files() covers docsite/**/*.md (FR-037)

.github/workflows/
├── pages.yml                    # REBUILT — FR-015/FR-017/FR-033
└── ci.yml                       # EDIT — one new job, id `docs-build` (FR-023/FR-034)

tests/
├── test_build_docs.py           # NEW  — the build, the toctree, the transform
├── test_docsite_layout.py       # NEW  — assembly, gitignore, requirements, extension purity
├── test_check_docs.py           # EDIT — markdown_files() covers docsite/ (FR-037)
└── test_landing_page.py         # EDIT — one test adapted, never weakened (FR-016)
```

**Structure Decision**. `docsite/` is a new top level because FR-028 settled it
and because `docs/index.md` beside `docs/index.html` is the confusion this
feature exists to remove. `scripts/build_docs.py` is a new module because no
existing one fits: `check_docs.py` is a gate, `render_brand.py` is a renderer,
and putting a docs build into either would give it a second job and a second
import graph. Both additions require the constitution amendment FR-039 names —
the Principle VI half is **enforced** and will fail CI until it is written.

**The `_ext/` placement** is deliberate and forward-looking: 013's skill
extension has to live in its own directory and import nothing from lernkarten,
enforced by a test. Putting 012's transform there now means 013 inherits the
directory and the purity test instead of introducing both.

### The two halves

**Model-driven work** (`skills/`): **none.** 012 changes no prompt. The
`metadata.docs` frontmatter block belongs to 013.

**Deterministic work**: all of it — `docsite/`, `scripts/build_docs.py`,
`scripts/check_docs.py`, the two workflows, and the four documents amended
(`README.md`, `docs/design.md`, `docs/testing.md`, the constitution). Covered by
`tests/test_build_docs.py`, `tests/test_docsite_layout.py`,
`tests/test_check_docs.py` and `tests/test_landing_page.py`.

**The seam**: none — the four file formats are untouched.

## The theme work (FR-027, FR-035, FR-036)

*This is the section the orchestrator asked to be sized honestly. It is measured
against `pydata-sphinx-theme 0.21.0`'s compiled stylesheet, not estimated.*

### Honest size: **bounded, and smaller than the spec feared**

**One stylesheet, roughly 90–130 lines**, of which the two largest blocks —
the `@font-face` declarations and the colour variables — are mechanical. The
genuinely uncertain part is two visual judgements, which is exactly what manual
row 44 exists for. **The spec's assumption that this is bounded holds.**

The reason it is bounded is not that the theme is tidy — it is not — but that
CSS lets a rule be written as broadly as the theme allows, which is what the
spec's own edge case already prescribed ("written as broadly as the theme allows
rather than as a list of selectors").

### What is actually in the stylesheet

`pydata-sphinx-theme.css` is 376 KB and about 5 200 rules, most of it a bundled
Bootstrap 5. Measured counts:

| Shape | Rules in the theme | Distinct values | Routed through a variable? |
|---|---|---|---|
| `border-radius` | **131** | 48 | **No `--pst-*radius*` variable exists at all.** Some go through Bootstrap's `--bs-border-radius` family; most are hard-coded (`.25rem`, `.375rem`, `4px`, `5px`, `.2rem`, `1rem`, `2em`, …) |
| `box-shadow` | **78** | 37 | partly, through `--pst-color-shadow` (a *colour*, not a shape) and `--bs-*`; many hard-coded `rgba()` |
| gradients | **3** | — | one unused `--bs-gradient` variable |
| `font-size` below 16 px | **33** | — | two `--pst-*` variables plus 31 direct rules |
| `font-family` not using a `--pst-*` variable | **9** | — | see the gotcha below |

A per-selector override would therefore be ~212 selectors and would go stale on
the next theme release. A blanket rule is one:

```css
*, *::before, *::after { border-radius: 0 !important; box-shadow: none !important; }
```

**And it needs no exceptions.** Every `border-radius: 50%` in the theme is on a
Bootstrap class Sphinx never emits — `.form-check-input[type=radio]`,
`.spinner-border`, `.spinner-grow`, `.rounded-circle` — so nothing that should
stay circular is flattened. The same is true of gradients: all three live on
`.progress-bar-striped`, `.placeholder-wave` and an unused `--bs-gradient`
variable, so `--bs-gradient: none` closes them and **no real element is
affected**. A blanket `background-image: none` was rejected: the theme draws the
navbar toggler, the admonition icons and the external-link marker with inline
`data:image/svg+xml` backgrounds, and it would erase those too.

### The 15 px floor — 33 rules, of which about 8 matter

The floor binds **Archivo prose only** (FR-035, as narrowed). Sorting the 33 by
what they actually are:

| Class | Count | Selectors | Action |
|---|---|---|---|
| **Reading prose — must be raised** | ~8 | `.small, small` (14 px), `.figure-caption` (14), `.blockquote-footer` (14), `.form-text` (14), `.initialism` (14), `ul.bd-breadcrumbs` (12.8), `ul.bd-breadcrumbs li.breadcrumb-item:not(.breadcrumb-home):before` (12.8), `span.guilabel` (12.8) | raise to ≥ 15 px |
| **Prose, set through a variable** | 2 | `--pst-font-size-milli: 0.9rem` (14.4 px — admonition titles, footer, captions) and `--pst-sidebar-font-size: 0.9rem` (14.4 px — the sidebar nav) | raise both to `1rem`; two lines cover every element that reads them |
| **Code literals — exempt** | 3 | `pre`, `code`, `kbd` (14 px) | none. FR-035 exempts a code sample explicitly |
| **Icon glyphs — not text** | 8 | `.fa-2xs`, `.fa-xs`, `.fa-sm`, `a.headerlink`, `.nav-link.nav-external:after`, `nav.bd-links li>a.reference.external:after`, `a.reference.download:before`, `.bd-sidebar-primary … .fa-chevron-down`, `.bd-navbar-elements li.nav-item i` | none |
| **Typographic sub/superscript** | 1 | `sub, sup` (`.75em`) | none — relative by definition |
| **Keycap literal** | 1 | `.search-button-field .kbd-shortcut__modifier` | none — a literal |
| **Never emitted on this site** | 13 | eleven Bootstrap form classes (`.form-control-sm`, `.valid-feedback`, `.invalid-tooltip`, `.dropdown-header`, …), `.ablog__collection …` (ABlog, not installed), `#ethical-ad-placement …` (Read the Docs ads, not used) | none |

So the floor costs **about ten declarations**, not thirty-three. The spec's
worry that "an unmodified theme violates FR-027, SC-008 and constitution XVI on
the day it is installed" is confirmed — `--pst-font-size-milli` and
`--pst-sidebar-font-size` are both 14.4 px — and the fix is small.

### The three faces — one gotcha, measured

The theme exposes `--pst-font-family-base`, `--pst-font-family-heading` and
`--pst-font-family-monospace`. **Overriding only those does not change the body
text.** Measured: `body` resolves
`--bs-body-font-family` → `--bs-font-sans-serif` (a system stack), and
`code, kbd, pre, samp` resolve `--bs-font-monospace` — neither reads a `--pst-`
variable. The override has to set **five** variables, not three:

```css
:root {
  --pst-font-family-base: Archivo, sans-serif;
  --pst-font-family-heading: Jost, sans-serif;
  --pst-font-family-monospace: "IBM Plex Mono", monospace;
  --bs-font-sans-serif: Archivo, sans-serif;
  --bs-font-monospace: "IBM Plex Mono", monospace;
}
```

Plus four `@font-face` blocks. The faces are served as the vendored **TrueType**
files — `Archivo.ttf` and `Jost.ttf` are *variable* fonts, so each needs
`font-weight: 100 900` for Jost 400 (wordmark) and Jost 500 (labels) to come off
one file, and `format("truetype")` rather than `woff2` because converting would
commit a new binary that Principle VIII's asserted list would have to name
(research R4).

### The inks

77 `--pst-color-*` variables exist. `docs/design.md` gives nine inks, and the
ones that carry a visible surface map onto roughly 14–18 of the theme's:
`background`, `on-background`, `surface`, `text-base`, `text-muted`, `heading`,
`link`, `link-hover`, `border`, `border-muted`, `inline-code`, `primary`,
`secondary`, `accent`, `target`, `shadow`. Mechanical, and colour never carries
meaning alone on this surface because the theme already doubles every state with
an icon or a border.

### What is *not* bounded, and is therefore a manual row

Two things, both visual, both on **row 44**:

1. Whether raising `--pst-sidebar-font-size` and `--pst-font-size-milli` from
   14.4 px to 16 px reflows the sidebar or an admonition title badly at 375 px.
2. Whether the flattened theme *reads* as the same system as the landing page.
   Constitution XVI's rule — a stock theme beside this project's landing page is
   a visible regression — is a judgement, not a measurement.

Neither can be asserted by a test in this repository:
`test_reading_text_is_never_below_the_screen_floor` reads one hand-written
file's `<style>` blocks and cannot reach a compiled stylesheet. That is
constitution XI's stated case for a numbered manual row, and FR-035 already
requires one.

### The one risk that survives

**A theme upgrade that styles a new component.** The blanket rule covers it by
construction — a new `border-radius` on a component that does not exist yet is
still `*`. The font floor does not: a new element set at 14 px is not caught by
anything. `pydata-sphinx-theme` is pinned exactly, so this can only arrive with
a deliberate bump, and the bump is when row 44 is walked again.

### What FR-036's new `docs/design.md` row is written from

§ *The screen surfaces* today says two surfaces are "built from flat colour and
type only — no gradients, no shadows, no rounded corners" and lists five rows.
The third surface gets a row plus a short paragraph naming, concretely, which
theme conventions it keeps:

| Surface | Source |
|---|---|
| documentation site | [`docsite/`](…) — Sphinx + MyST, `pydata-sphinx-theme` overridden to the rules on this page |

**Kept from the theme** (state them, so the next contributor does not "fix"
them):

- the **two-level navigation** — a persistent left sidebar plus an in-page
  right-hand table of contents. It is the shape pandas and numpy have and the
  shape the request asked for.
- the **bundled icon font** (FontAwesome, served from the site itself) for the
  external-link marker, the sidebar disclosure and the admonition icons. Colour
  is never the only distinction there — every one of them is a glyph.
- **admonition colours**, doubled by an icon and a rule, never by hue alone.
- the **footer credit** to Sphinx and the theme (two outbound links, no
  sub-resource).

**Overridden** (the list above, condensed): the three inks; the three faces
self-hosted from `assets/fonts/`; every radius, shadow and gradient flattened;
the 15 px Archivo-prose floor, which the stock theme breaks in about ten places.

**Stated as a rule rather than a list**, for the reason
`tests/test_landing_page.py` already gives about the type floor: a list of
selectors goes stale and becomes somewhere to put the next violation.

## Phase 0: Research

Complete. See [research.md](research.md). Every unknown the spec left to
planning is resolved there with a measurement:

| Unknown | Resolved |
|---|---|
| Principle IV answers for three new dependencies, and their pins | R1 — exact pins, 33-package closure, full wheel matrix on three platform tags, permissive licences throughout; one gate answered as a stated cost |
| The shape of the FR-029 transform, against its ~30-line ceiling | R2 — **~22 lines of logic for what FR-029 asks; the fallback is not invoked.** The shipped module is ~42 lines because of C3 and C4, which the ceiling was not measuring |
| Which hook the transform uses | R2 — a `SphinxPostTransform` at priority 5. `missing-reference` **does not fire**; MyST's own resolver sits at priority 9 |
| Whether `{include}` resolves images, links and headings correctly | R3 — `:relative-images:` yes; `:relative-docs:` **must not** be used; `:heading-offset:` **must not** be used; `myst_heading_anchors = 3` |
| The theme, at selector level | R4 + [The theme work](#the-theme-work-fr-027-fr-035-fr-036) |
| Determinism, absolute paths, offline, the local `_site` | R5 — all four measured green; one caveat on the `docs/` directory link over `file://` |

## Phase 1: Design

### The build command (FR-019, FR-038)

`python3 scripts/build_docs.py`, no arguments. It:

1. checks the docs requirements are importable and, if not, exits non-zero with
   one line naming `pip install -r requirements-docs.txt` — the same courtesy
   `scripts/deps.py` and `scripts/engine.py` already extend;
2. runs Sphinx with `-W --keep-going` into `_site/docs/`;
3. copies `docs/index.html` → `_site/index.html`, `docs/leitner.html` →
   `_site/leitner.html`, `assets/card-box.pdf` → `_site/card-box.pdf`, and
   touches `_site/.nojekyll`;
4. prints the path to open.

`--site <dir>` is the one option, so `pages.yml` can point it at the runner's
`_site`. FR-019's "single command with no arguments" is about the default, and
the default takes none.

**Import graph**: `build_docs` imports `argparse`, `pathlib`, `shutil`,
`subprocess`/`sphinx.cmd.build` — **no local module**. It joins Principle VI's
leaves line: `build_docs, deps, engine, leitner ← leaves, import nothing local`.
`documented_graph()`'s `^([\w, ]+?)\s*(?:→|←)` pattern accepts that form
verbatim.

### The `docsite/` sources (FR-006 … FR-012, FR-028, FR-040, FR-041)

- Every migrated page is **one `{include}` and nothing else**, with
  `:relative-images:` only. No wrapper heading, no `:heading-offset:`, no
  `:relative-docs:` — R3 explains what each of the two rejected options breaks.
  The included document's own H1 becomes the page title and the `toctree` entry,
  so nothing is retyped (FR-008).
- `docsite/index.md` carries **two `toctree`s** — `user/index` and
  `contributing/index` — which are the two top-level branches SC-002 walks.
  FR-012's headroom for 013 and 014 is a third and fourth entry in the same
  list, with no restructuring.
- `docsite/user/leitner.md` is the FR-032 wrapper: a short signpost that
  introduces the method and links out. It restates nothing.
- `myst_heading_anchors = 3` (FR-040) — exactly the depth
  `#the-box`, `#automated` and `#the-checklist` need.

### The transform (FR-029, + C1–C4)

`docsite/_ext/repolinks.py`. Two hooks, one lookup:

| Hook | Priority | Catches |
|---|---|---|
| `doctree-read` | 100 (before `DownloadFileCollector` at 500) | `download_reference` — a link from a `docsite/` page to a file that exists (**C4**) |
| `SphinxPostTransform` | 5 (before `MystReferenceResolver` at 9) | `pending_xref` with `reftype == "myst"`: unresolved links (FR-029) and unknown docnames (**C3**) |

The lookup resolves the target against `Path(node.source).parent` — the file the
link was **written in**, which is what FR-029 requires and what the node
actually carries — and then:

1. **`PAGES`** — the target is a document this site publishes → an internal
   cross-reference, with the anchor preserved.
2. **`SERVED`** — the target is served at the site root (`docs/index.html`,
   `docs/leitner.html`, `assets/card-box.pdf`) → a depth-aware relative link
   (**C1**, **C2**).
3. otherwise, the file exists in the repository → an absolute GitHub URL,
   `/blob/main/` for a file and `/tree/main/` for a directory, anchor preserved.
4. otherwise, leave it alone and let MyST warn — a genuinely dead link stays a
   build failure (FR-020).

Both tables are in [contracts/docsite-layout.md](contracts/docsite-layout.md).

### The theme (FR-027, FR-035, FR-036)

One `docsite/_static/lernkarten.css`, registered with `html_css_files`. See
[The theme work](#the-theme-work-fr-027-fr-035-fr-036) for the selector list and
the size. The fonts are copied out of `assets/fonts/` by `html_static_path` and
declared with `@font-face … format("truetype")`, with `font-weight: 100 900` on
the two variable faces.

### `scripts/check_docs.py` (FR-037)

`markdown_files()` gains `sorted((ROOT / "docsite").rglob("*.md"))`. Consequences,
all of which hold under the layout above: `check_links` then walks the `docsite/`
pages (fenced `{toctree}` and `{include}` blocks are already stripped by
`CODEBLOCK`, so only prose links are read), and all five drift gates start
reading them through `gated_files()`.

### `.github/workflows/pages.yml` (FR-015, FR-017, FR-033)

Rebuilt: install `requirements-docs.txt`, run `python3 scripts/build_docs.py
--site _site`, upload. **All-or-nothing** falls out of the shape — one job, and a
failing build fails the job before `upload-pages-artifact` runs, so nothing is
published (FR-033). `paths:` gains `docs/*.md`, `CONTRIBUTING.md`, `docsite/**`,
`requirements-docs.txt`, `assets/pipeline.png`, `assets/example-cards.png`,
`scripts/build_docs.py`; the three existing entries stay (FR-017).

### `.github/workflows/ci.yml` (FR-023, FR-034)

One new job, **id `docs-build`**, name "Documentation build". Not `docs` — that
id is taken by the "Skills & docs" job and reusing it is a YAML error found as a
red run rather than at review (FR-023 says so explicitly; verified against the
file). Matrix `[ubuntu-latest, macos-latest, windows-latest]`, Python 3.12,
`shell: bash` like the other multi-OS jobs, installing `requirements-docs.txt`
and running `python3 scripts/build_docs.py` (FR-034).

### `docs/index.html` (FR-014)

One link added, pointing at **`docs/`** — the directory, matched literally by
FR-016's test. Nothing else on the page changes, so every existing assertion in
`tests/test_landing_page.py` still passes (SC-005).

### `tests/test_landing_page.py` (FR-016) — adapted, never weakened

`test_the_pages_workflow_assembles_every_relative_link` keeps deriving its target
set from `docs/index.html` and keeps requiring **every** target. It learns one
second route: a target may also arrive because the documentation build writes
`_site/docs/`. The rule is derived from the workflow text, not allow-listed:

```python
built = bool(re.search(r"_site/docs\b", workflow)) and ref.rstrip("/") == "docs"
```

Verified against a draft workflow: `card-box.pdf` and `leitner.html` still match
only through their `cp` lines; `cp docs/index.html _site/index.html` does **not**
falsely satisfy `docs/`. The derived set is unchanged, so this is the adaptation
FR-016 permits and not the weakening it forbids.

### Test plan first (constitution XI) — the red order

Every row goes red on its **assertion**, not on an import, before the
implementation beside it exists.

| # | Red assertion | Goes green with |
|---|---|---|
| 1 | `test_the_docs_requirements_are_pinned_exactly` — `requirements-docs.txt` exists, names the three packages with `==`, one comment each | `requirements-docs.txt` |
| 2 | `test_the_docs_requirements_are_not_a_runtime_dependency` — no name from `requirements-docs.txt` appears in `scripts/deps.py` `REQUIREMENTS`, and nothing under `bin/` or `scripts/` imports one (FR-003, FR-005) | (green by construction; a regression guard, stated as such) |
| 3 | `test_the_build_directory_is_ignored` — `docsite/_build/` and `_site/` are matched by `.gitignore` (FR-022) | `.gitignore` |
| 4 | `test_check_docs_covers_the_docsite` — `markdown_files()` contains every `docsite/**/*.md` (FR-037) | `markdown_files()` |
| 5 | `test_the_build_exits_zero_and_writes_an_index` — skips without the docs requirements, naming `requirements-docs.txt` (FR-023, SC-006) | `scripts/build_docs.py` + `docsite/conf.py` |
| 6 | `test_every_migrated_document_is_in_the_toctree` — walks the built `toctree` from the root document; all five reachable, user and contributing separate top-level branches (SC-002) | the `docsite/` sources |
| 7 | `test_a_missing_reference_fails_the_build` — a temporary page with a dead cross-reference; build exits non-zero and the message names the source and the target (SC-003, FR-020) | `-W` in `build_docs.py` |
| 8 | `test_every_repository_link_resolves` — the transform's own test (FR-029 requires one). Asserts the rendered `href` for a representative of each of the four branches, including the anchor-preserving one, the `/tree/` one, and the two `SERVED` ones (**C1**, **C2**) | `docsite/_ext/repolinks.py` |
| 9 | `test_the_method_page_is_never_duplicated` — no `_downloads/` in the build output and no second `leitner.html` in `_site` (**C4**, FR-010, SC-012) | the `doctree-read` hook |
| 10 | `test_a_docsite_page_may_link_a_repository_file` — FR-037's prescribed spelling renders as a link, and the build stays clean (**C3**) | the `refdomain == "doc"` branch |
| 11 | `test_the_images_are_rendered_not_linked` — `pipeline.png` and `example-cards.png` appear as `<img>` under `_images/`, not as GitHub URLs (FR-030, FR-041) | `:relative-images:` |
| 12 | `test_building_twice_is_byte_identical` — two builds, HTML compared, `.doctrees/` and `.buildinfo` excluded (SC-004) | (green by construction; the guard is the point) |
| 13 | `test_the_site_loads_no_third_party_subresource` — no `<link>`/`<script>`/`<img>` with an `http(s)` URL anywhere in the output (SC-014) | the `@font-face` block |
| 14 | `test_the_extension_imports_nothing_from_lernkarten` — `docsite/_ext/` imports no `scripts/` module (the purity rule 013 inherits) | (green by construction) |
| 15 | `test_the_pages_workflow_assembles_every_relative_link` — **existing test**, red once `docs/index.html` gains `docs/` | the adaptation above + the rebuilt `pages.yml` |
| 16 | `test_the_ci_docs_job_is_not_called_docs` — `ci.yml` has a docs-build job, its id is not `docs`, and it runs on all three OSes (FR-023, FR-034) | `ci.yml` |
| 17 | `test_the_deploy_is_all_or_nothing` — `pages.yml` uploads only after the build step, in one job (FR-033, SC-013 first half) | `pages.yml` |
| 18 | `test_the_readme_points_at_the_published_pages` — the three `README.md` links are site URLs, **and** `](docs/index.html)` inside `## The design` is untouched (FR-042) | `README.md` |
| 19 | `test_the_design_doc_describes_the_documentation_site` — `docs/design.md` § *The screen surfaces* has a third row naming `docsite/` (FR-036) | `docs/design.md` |
| 20 | `python3 scripts/check_docs.py` — red until Principle VI lists `build_docs` (FR-039). **This one is a gate, not a pytest case**, and it is the reason the constitution amendment is a named task rather than an afterthought | the constitution amendment |

### The three manual rows (FR-025, constitution XI)

`docs/testing.md`'s checklist reaches 43 today (the Leitner dividers). This
feature adds **44, 45 and 46 — and no more**, each named where it is claimed:

| # | Verifies | Why no test can |
|---|---|---|
| 44 | **SC-008 / FR-035** — at 375 px every page reads without horizontal scrolling and no Archivo prose renders below 15 px | `test_reading_text_is_never_below_the_screen_floor` reads one hand-written file's `<style>` blocks; it cannot reach a theme's compiled stylesheet |
| 45 | **SC-005** — the reviewer reads the diff of `tests/test_landing_page.py` and `scripts/check_docs.py` and confirms no assertion deleted, no target dropped from a derived set, no condition relaxed | "unweakened" is a judgement about a diff; no command reports it |
| 46 | **SC-013** — the documentation build ran on the pull request that introduced the change | a property of the process, not of an artifact |

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| A 33-distribution transitive tree | IV | Sphinx is the toolchain FR-001 settled on, and its `sphinxcontrib-*` set plus `requests` are hard requirements of it | Hand-written HTML has no checked cross-references, which is the whole reason for the feature. MkDocs is a smaller tree but has no domain model and no `metadata.docs` path for 013 |
| A new module under `scripts/` | V | FR-019's one command, and FR-038's assembly, which `sphinx-build` cannot do | `check_docs.py` is a gate and `render_brand.py` is a renderer; adding a build to either gives it a second job and a second import graph |
| A new top-level directory | V | FR-028 settled it: `docs/index.md` beside `docs/index.html` is the confusion this feature removes | Sources under `docs/` — rejected in the spec, with the reason recorded |
| An in-repo Sphinx extension | III | No library knows this repository's `_site` layout, `PAGES` mapping or GitHub URL | Nothing on PyPI does repository-relative link rewriting to a project-specific published layout |

Principle XI has no row here. It is not waivable.
