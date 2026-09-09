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
`pydata-sphinx-theme==0.21.0`. Pure-Python wheels; 32-distribution closure with
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
one new `scripts/` module, one new workflow job, 25 test rows (19 red-first, 6
guards) and three new manual checklist rows.

## Dependency Decisions

### Reuse check (constitution III)

**Is anything being hand-rolled here?** **No.** Static site generation, Markdown
parsing and checked cross-references are all taken from libraries. The single
piece of bespoke code is the FR-029 link transform (~42 lines of logic), and it
is bespoke because no library knows this repository's `_site` layout, its
`PAGES` mapping or its GitHub URL. Nothing on PyPI does that.

### Vetting (constitution IV)

The full three-package table, the 32-distribution wheel matrix and the licence
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
| **Transitive tree** | **32 distributions — a stated cost, not a clean pass.** See the note below |
| **Cold-start import cost** | none: FR-003/FR-005 keep every one of them off the runtime path, and SC-009 asserts `lernkarten build` runs with none of them installed |
| **No known unfixed advisory** | none outstanding on any of the 33 at adoption |
| **Dependabot covers the declaring manifest** | yes, with no edit — `.github/dependabot.yml` already declares `package-ecosystem: pip, directory: "/"`, which picks up a new root-level `requirements-docs.txt` |

**On the transitive tree.** Principle IV asks for "a shallow transitive tree" and
names "thirty packages to get one function" as the failing shape. Thirty-three is
over that number and the plan says so rather than rounding it down. Three things
make it acceptable, and all three are structural rather than rhetorical:

1. It is not thirty-two packages for one function; it is a documentation
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
| XI | **(NON-WAIVABLE)** Tested first, red on the assertion | **yes** — 25 rows in [Phase 1](#phase-1-design), of which 19 are red-first and 6 are guards, each labelled and justified in [Guards, and how XI is satisfied](#guards-and-how-xi-is-satisfied). Requirements no test can reach get **numbered manual rows 44–46** (FR-025), and no more than three |
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

**Two of these are now closed in `spec.md`, not only here.** A finding recorded
in a plan is a finding a later reader implements *around*; FR-031 still read as
an instruction to edit two files, and FR-029's fallback clause still read as
unconditional. Both are amended in place, with the original wording quoted, under
[spec.md § Amendments made during planning](spec.md#amendments-made-during-planning):
FR-031 now describes the build-time behaviour and gives the rendered values
(`../../index.html`, `../../card-box.pdf`), and FR-029 records its ceiling as
**superseded**, with the reason — the FR-029 lookup itself is ~22 lines and
inside the ceiling; the extra twenty are C3 and C4, which the fallback would not
fix while costing 22 links of `check_docs` coverage that SC-005 forbids losing.
The ceiling still binds what it was written to bind.

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
├── test_landing_page.py         # EDIT — one test adapted (FR-016); paths: rows (FR-017)
└── test_repo_hygiene.py         # EDIT — the pre-PR gate count (SC-010), Principle V (FR-039)
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

So the floor costs **about ten declarations**, not thirty-three. (The breakdown
above is internally consistent, but its total is the one Phase 0 number T009
could not reproduce — recounting gives 20, 25 or 43 depending on the rule
applied, and the rule was never stated. See `research.md` § *Re-verified at
T009*. Nothing here depends on it: the override is a blanket rule precisely so
the denominator does not matter, and the qualitative split is what governs.)
The spec's
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

`--site <dir>` and `--source <dir>` are the two options, both defaulting, so
FR-019's "single command with no arguments" is about the default and the default
takes none. `--site` lets `pages.yml` point at the runner's `_site`. `--source`
defaults to `docsite/` and exists so that **no test ever writes into the checked-in
tree**: rows 7 and 10 need a probe page, and an interrupted run that leaves a
`docsite/*.md` behind turns the next build red, turns gate #4 red (FR-037 puts
`docsite/**/*.md` inside `check_links`, and a probe's dead link is exactly what it
reports) and trips guard row 25. Both tests `shutil.copytree` `docsite/` into
`tmp_path` and build the copy; `conf.py`'s `sys.path` insert of `_ext` is relative to
the configuration directory, so a copied tree builds unchanged.

**Step 3 is idempotent by construction** — `shutil.copy2` of bytes that are
already there — which is what lets `pages.yml` keep its own `cp` lines. See
[The `_site` assembly, stated once](#the-_site-assembly-stated-once).

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
the size. It is **not** written green-first: **red row 21** asserts that the
override actually lands — three font-family variable names and the blanket
flattening rule, deliberately not a selector list, because a list would go stale
and become somewhere to put the next violation. What a test cannot judge — whether
the result *reads* as the same system, and whether raising two sizes reflows
anything at 375 px — stays on manual row 44. The fonts are copied out of `assets/fonts/` by `html_static_path` and
declared with `@font-face … format("truetype")`, with `font-weight: 100 900` on
the two variable faces.

### Relative internal links (FR-018)

**`html_baseurl` is left unset, deliberately, and `conf.py` carries a comment
saying so.** Sphinx's HTML builder emits document-relative URIs by default, so
FR-018 holds — but it holds by the *absence* of a line, which is the kind of
property that regresses when somebody later adds `html_baseurl` for a sitemap or
an Open Graph tag. Two things make it a decision rather than an accident:

- the comment in `conf.py`, naming FR-018 and the sub-path;
- an assertion folded into **red row 13**, which already walks `_site/docs` for
  URL shapes: no `href`/`src` starts with `/`, and none contains
  `mhabedank.github.io`. Root-anchored and absolute-site URLs are the two ways
  this breaks, and both are one grep.

### `scripts/check_docs.py` (FR-037)

`markdown_files()` gains `sorted((ROOT / "docsite").rglob("*.md"))`. Three
consequences, all of which hold under the layout above:

- **`check_links`** walks the `docsite/` pages. Fenced `{toctree}` and
  `{include}` blocks are stripped by `CODEBLOCK` before targets are read, so an
  include-only page contributes no links, and the wrapper page's
  `../../docs/leitner.html` resolves on the file system.
- **The five drift gates** start reading them, by **two different routes** —
  worth naming so an implementer does not look for one: `check_a7_is_not_the_default`,
  `check_cut_count` and `check_borderless_size` go through `gated_files()`, while
  `check_sheet_capacity` (line 577) and `check_print_order` (line 598) call
  `markdown_files()` **directly** and do not strip code blocks. The outcome is the
  same for 012's pages, which carry no grid or capacity claim; the mechanism is
  not, and 014's pages will be full of exactly those claims.
- **`check_leitner_intervals` is unaffected.** It reads `LEITNER_PAGE`
  (`scripts/check_docs.py:252`) directly — a single hard-coded path — and never
  goes through `markdown_files()`. Widening the glob cannot reach it, cannot
  dilute it and cannot turn it into a no-op, which is what FR-011 protects.
  `docs/leitner.html` does not move, so `tests/test_check_docs.py`'s existence
  assertion is untouched as well. Stated because "nothing changed" is a claim,
  and the whole point of FR-011 is that it should not be left as one.

### The `_site` assembly, stated once

*This section exists because an earlier draft of this plan specified the assembly
in two places and the two disagreed. It is now stated **here only**; every other
section points at it.*

**Decision: `pages.yml` keeps all three `cp` lines it has today, and
`build_docs.py` performs the same three copies. The duplication is deliberate.**

| | `pages.yml` | `scripts/build_docs.py` |
|---|---|---|
| `docs/index.html` → `_site/index.html` | `cp` line | `shutil.copy2` |
| `docs/leitner.html` → `_site/leitner.html` | `cp` line | `shutil.copy2` |
| `assets/card-box.pdf` → `_site/card-box.pdf` | `cp` line | `shutil.copy2` |
| `_site/.nojekyll` | `touch` | `Path.touch()` |
| `_site/docs/` | — | Sphinx |

Why both, rather than letting the script do it alone:

- **Two existing tests read the `cp` lines as text, and SC-005 forbids weakening
  either.** `test_the_pages_workflow_assembles_every_relative_link`
  (`tests/test_landing_page.py:562`) requires a literal
  `^\s*cp\s+\S*<ref>\s+\S*_site/` for every ref derived from `docs/index.html`,
  and `test_the_pages_workflow_publishes_the_box` (line 529) requires the box's
  line specifically — **that second test is the one an earlier draft of this plan
  never mentioned**, and it alone would have gone red on a `cp`-free workflow.
  CI never executes the workflow, so reading it as text is the only check there
  is; the `cp` lines are the workflow's *declaration* of what the site contains,
  which is exactly what PR #105 made them.
- **The script's copies are what make the local build a preview** (FR-038).
  Without them `python3 scripts/build_docs.py` produces a documentation tree with
  two dead links out of it.
- **Order does not matter and neither does duplication**: both write identical
  bytes, and `cp`/`copy2` are idempotent. `pages.yml` runs the `cp` block first
  (unchanged from today), then the build.

The rejected alternative was a `--docs-only` flag so the workflow assembles and
the script does not. It costs a second assembly code path, and the two would be
free to drift — which is the one thing FR-038's "the local build is a preview"
must not allow.

### `.github/workflows/pages.yml` (FR-015, FR-017, FR-033)

Rebuilt to four steps, in this order:

1. `checkout`;
2. **the existing assembly block, unchanged** — `mkdir -p _site`, the three `cp`
   lines, `touch _site/.nojekyll`;
3. install `requirements-docs.txt`, then
   `python3 scripts/build_docs.py --site _site && test -f _site/docs/index.html`;
4. `configure-pages` → `upload-pages-artifact` → `deploy-pages`.

**All-or-nothing** falls out of the shape — one job, and a failing build fails it
before `upload-pages-artifact` runs, so nothing is published (FR-033). The
`&& test -f _site/docs/index.html` on step 3 does two jobs and neither is optional:
it makes a build that exits 0 while writing nothing fail *before* the upload, which
is FR-033 at its strongest; and it is the only honest way the workflow text comes to
contain the string `_site/docs`, which is the token the FR-016 adaptation below
reads. Without it row 15 cannot go green and the quickest repair is a comment saying
`_site/docs` — a derivation that reads a word instead of a fact.

`paths:` gains **eight** entries — `docs/*.md`, `CONTRIBUTING.md`, `docsite/**`,
`requirements-docs.txt`, `assets/pipeline.png`, `assets/example-cards.png`,
`scripts/build_docs.py` and **`assets/fonts/**`** — and the **four** existing entries
stay (FR-017):
`docs/index.html`, `docs/leitner.html`, `assets/card-box.pdf` **and
`.github/workflows/pages.yml` itself**, which the file already lists today.
**Twelve** in total, all asserted by red row 22.

**`assets/fonts/**` is an input, not an asset a page renders.** FR-027 and the theme
task copy the three faces out of it through `html_static_path` (SC-014), so replacing
or re-hinting a face changes the built site and must redeploy it. It is named here
because it is the one input FR-017's own enumeration does not spell out.

*(Two earlier drafts of this paragraph were wrong in the same family and one step
apart. The first said "the three existing entries" and "all ten", absorbing the
workflow's own path silently. The second fixed the number to eleven and left the
list — the count was reconciled against itself in four places and never against
FR-027's inputs. Under row 22's "one assertion per entry" either would have produced
a test that was wrong by construction.)*

### `.github/workflows/ci.yml` (FR-023, FR-034)

One new job, **id `docs-build`**, name "Documentation build". Not `docs` — that
id is taken by the "Skills & docs" job and reusing it is a YAML error found as a
red run rather than at review (FR-023 says so explicitly; verified against the
file). Matrix `[ubuntu-latest, macos-latest, windows-latest]`, Python 3.12,
`shell: bash` like the other multi-OS jobs.

**It runs two commands, not one:**

```yaml
- run: python -m pip install -r requirements-dev.txt -r requirements-docs.txt
- run: python scripts/build_docs.py
- run: python -m pytest
```

**`python`, not `python3`** — every existing multi-OS job in `ci.yml` uses
`python` under `shell: bash`, and inventing a third convention inside one job
risks a Windows leg that fails for a reason unrelated to this feature.
`python3 scripts/build_docs.py` stays the documented human command (FR-019); the
two are not in conflict, because FR-019 is about what a contributor types, not
about what a runner resolves.

The second `run` is not optional and is the point of the job. FR-023 says CI
must have a job that installs the docs requirements **and runs those tests**; a
job that only builds would leave red rows 5–13 skipping in every CI job and
executing nowhere, which is not a test suite. Running the *whole* suite rather
than just the docs module is deliberate and nearly free: it is the only leg that
exercises the transform, `{include}` resolution and text encoding on macOS,
which is a platform the `test` job does not cover at all. Red row 16 asserts
both commands.

### `docs/index.html` (FR-014)

**Two edits, both inside the button row at lines 767–770.**

1. A link added, pointing at **`docs/`** — the directory, matched by FR-016's test.
2. The existing **`full walkthrough`** button (line 769) retargeted from
   `https://github.com/mhabedank/lernkarten/blob/main/docs/workflow.md` to
   **`docs/user/workflow.html`**.

The second is not a tidy-up. That button is the most literal instance of the
complaint this feature answers: the landing page's own call to action sends a
newcomer to raw Markdown on GitHub, and after 012 it would do so from the same
section that offers `docs/` into the site. It is decided the way FR-042 decided the
README's three references — leaving it reintroduces the split one link deep — and it
is recorded in FR-042 rather than left as a remark, because it edits a file with its
own test suite. `.button-row` is `flex-wrap: wrap` (line 152), so a third button
reflows rather than overflowing.

Nothing else on the page changes, so every existing assertion in
`tests/test_landing_page.py` still passes (SC-005) — including the four-link nav
assertions, which is why both edits are in the body and not in the nav.

### `tests/test_landing_page.py` (FR-016) — adapted, never weakened

`test_the_pages_workflow_assembles_every_relative_link` keeps deriving its target
set from `docs/index.html` and keeps requiring **every** target. It learns one
second route: a target may also arrive because the documentation build writes
`_site/docs/`. The rule is derived from the workflow text, not allow-listed:

```python
built = bool(re.search(r"_site/docs\b", workflow)) and (
    ref.rstrip("/") == "docs" or ref.startswith("docs/")
)
```

**The subtree, not one literal.** FR-016's *permitted* clause admits any target
"produced by the documentation build into `_site/docs/`", and after the two edits
above the page carries two of them: `docs/` and `docs/user/workflow.html`. A rule
matching only the literal `docs` would reject the second and force it back onto a
`cp` line that can never produce it — which is a weakening dressed as strictness.

**The token the first half reads is real.** `pages.yml`'s build step ends with
`&& test -f _site/docs/index.html`, so `_site/docs` appears in the workflow as a
check the deploy actually runs. Stated because the alternative — a comment carrying
the string — would satisfy the regex while proving nothing, and an earlier draft of
this section described the adaptation as verified against a draft workflow that no
artifact contained.

Verified against a draft workflow: `card-box.pdf` and `leitner.html` still match
through their `cp` lines, which [The `_site` assembly](#the-_site-assembly-stated-once)
keeps in `pages.yml` for exactly this reason; and `cp docs/index.html
_site/index.html` does **not** falsely satisfy `docs/`, because `\S*docs/`
requires whitespace after the slash. The derived set is unchanged, so this is the
adaptation FR-016 permits and not the weakening it forbids.

**`test_the_pages_workflow_publishes_the_box` (line 529) is not touched at all.**
It asserts `cp …assets/card-box.pdf …_site/` and the `assets/card-box.pdf`
`paths:` entry, and both survive the rebuild unchanged. It is named here because
an earlier draft of this plan did not name it, and a workflow written from that
draft would have turned it red.

### Test plan first (constitution XI) — the red order

Every **red** row goes red on its *assertion*, not on an import, before the
implementation beside it exists. **Six** rows are **guards** rather than
red-first cases, and are marked *(guard)* in the table rather than left to be
discovered — see [Guards, and how XI is satisfied](#guards-and-how-xi-is-satisfied)
below. *(An earlier draft of this paragraph said three while the table marked
four; the count is now stated in one place and repeated nowhere.)*

**Two ordering constraints bind this table, and belong in the task list rather
than in a contributor's memory:**

1. **`requirements-docs.txt` must be written and installed before rows 5–13 are
   written.** Those rows skip when the docs requirements are absent — FR-023
   requires that skip and SC-006 asserts it — so a contributor who writes them
   first sees *skipped*, not red, and has not seen the red constitution XI
   demands. Row 1 lands the manifest; `pip install -r requirements-docs.txt`
   comes immediately after it.
2. **The Phase 0 probes are re-run at that same point, before row 8 is written.**
   Every number in `research.md` R2, R4 and R5 — the post-transform priorities
   (5 against MyST's 9, `doctree-read` 100 against `DownloadFileCollector`'s
   500), the 32-distribution closure, the three version pins, the 131/78/33
   stylesheet counts and the byte-identical rebuild — came from a spike that
   cannot be re-run from a checkout without Sphinx installed. They are recorded
   as measured, which is the right place for them, but the first task after the
   manifest lands re-runs them rather than assuming them. The three pins in
   particular are only truly exercised by the first green `docs-build` run on all
   three operating systems.

| # | Red assertion | Goes green with |
|---|---|---|
| 1 | `test_the_docs_requirements_are_pinned_exactly` — `requirements-docs.txt` exists, names the three packages with `==`, one comment each | `requirements-docs.txt` |
| 2 *(guard)* | `test_the_docs_requirements_are_not_a_runtime_dependency` — no name from `requirements-docs.txt` appears in `scripts/deps.py` `REQUIREMENTS`, and no module in the **import closure of `bin/lernkarten`** imports one (FR-003, FR-005). **Scoped to the closure, not to `scripts/` as a directory**: `scripts/build_docs.py` imports `sphinx` on purpose from T015, so a directory-wide rule goes red eight tasks after it is written and the cheap repair is a name-list exclusion — a guard that no longer guards. `bin/lernkarten` imports `engine`, `deps`, `cardid`, `setup_cmd` and `build_pdf` (lines 30–71) and `check_docs.real_graph()` already derives each module's local imports, so the closure is computed rather than listed, and `build_docs` — a leaf nothing imports — falls outside it by construction. FR-005's own wording is the narrow one: "any script a **user's run** reaches" | nothing — it guards FR-003/FR-005 against a later feature that puts a docs package on a user-reachable module |
| 3 | `test_the_build_directory_is_ignored` — `docsite/_build/` and `_site/` are matched by `.gitignore` (FR-022) | `.gitignore` |
| 4 | `test_check_docs_covers_the_docsite` — `markdown_files()` contains every `docsite/**/*.md` (FR-037) | `markdown_files()` |
| 5 | `test_the_build_exits_zero_and_writes_an_index` — skips without the docs requirements, naming `requirements-docs.txt` (FR-023, SC-006) | `scripts/build_docs.py` + `docsite/conf.py` |
| 6 | `test_every_migrated_document_is_in_the_toctree` — walks the built `toctree` from the root document; all five reachable, user and contributing separate top-level branches (SC-002) | the `docsite/` sources |
| 7 | `test_a_missing_reference_fails_the_build` — a temporary page with a dead cross-reference; build exits non-zero and the message names the source and the target (SC-003, FR-020) | `-W` in `build_docs.py` |
| 8 | `test_every_repository_link_resolves` — the transform's own test (FR-029 requires one). Asserts the rendered `href` for a representative of each of the four branches, including the anchor-preserving one, the `/tree/` one, and the two `SERVED` ones (**C1**, **C2**) | `docsite/_ext/repolinks.py` |
| 9 | `test_the_method_page_is_never_duplicated` — no `_downloads/` in the build output and no second `leitner.html` in `_site` (**C4**, FR-010, SC-012) | the `doctree-read` hook |
| 10 | `test_a_docsite_page_may_link_a_repository_file` — FR-037's prescribed spelling renders as a link, and the build stays clean (**C3**) | the `refdomain == "doc"` branch |
| 11 | `test_the_images_are_rendered_not_linked` — `pipeline.png` and `example-cards.png` appear as `<img>` under `_images/`, not as GitHub URLs (FR-030, FR-041) | `:relative-images:` |
| 12 *(guard)* | `test_building_twice_is_byte_identical` — two builds, HTML compared, `.doctrees/` and `.buildinfo` excluded (SC-004) | nothing — Sphinx is already deterministic; it guards a later `conf.py` line that would not be |
| 13 *(guard)* | `test_the_site_loads_no_third_party_subresource` — no `<link>`/`<script>`/`<img>` with an `http(s)` URL anywhere in the output, and (FR-018) no `href`/`src` beginning with `/` and none naming `mhabedank.github.io` (SC-014, FR-018) | **nothing.** Research R4 measured that the stock theme already loads no third-party sub-resource — FontAwesome ships bundled under `_static/vendor/` — and Sphinx's URIs are already document-relative, so this row is green the moment it is written. It guards a later `@font-face` pointing at a CDN and a later `html_baseurl` line. **The positive half of SC-014 — the three faces actually being served from the site — is asserted by row 21**, because a build with no font at all satisfies this row |
| 14 *(guard)* | `test_the_extension_imports_nothing_from_lernkarten` — `docsite/_ext/` imports no `scripts/` module (the purity rule 013 inherits) | nothing — it is the enforcement the spec's extraction decision promised |
| 15 | `test_the_pages_workflow_assembles_every_relative_link` — **existing test**, red once `docs/index.html` gains `docs/` | the adaptation above + the rebuilt `pages.yml` |
| 16 | `test_the_ci_docs_job_runs_the_docs_tests` — `ci.yml` has a docs-build job; its id is **not** `docs`; it runs on all three OSes; it installs `requirements-docs.txt`; **and it runs `pytest`** (FR-023, FR-034). The last clause is the one that matters: without it rows 5–13 execute in no CI job at all. **Parsed with `yamlio` and asserted on the job object**, selected by its `build_docs.py` step — against `ci.yml` as text four of the five clauses are already true today (`cards` and `e2e` list three runners, `test` runs `pytest`, `requirements-dev.txt` is installed in four places), so an unscoped test is red on one clause and vacuous on the rest. Same discipline as row 24's "scoped to the first block" | `ci.yml` |
| 17 | `test_the_deploy_is_all_or_nothing` — `pages.yml` uploads only after the build step, in one job (FR-033, SC-013 first half) | `pages.yml` |
| 18 | `test_the_readme_points_at_the_published_pages` — the three `README.md` links are site URLs, **and** `](docs/index.html)` inside `## The design` is untouched (FR-042) | `README.md` |
| 19 | `test_the_design_doc_describes_the_documentation_site` — `docs/design.md` § *The screen surfaces* has a third row naming `docsite/` (FR-036) | `docs/design.md` |
| 20 | `python3 scripts/check_docs.py` — red until Principle VI lists `build_docs` (FR-039). **This one is a gate, not a pytest case**, and it is the reason the constitution amendment is a named task rather than an afterthought | the constitution amendment |
| 21 | `test_the_theme_override_lands` — the built `_static/lernkarten.css` sets `--pst-font-family-base`, `--bs-font-sans-serif` and `--bs-font-monospace`, and carries the blanket `border-radius: 0` / `box-shadow: none` rule (FR-027). **Not a selector list** — three variable names and one rule, chosen because the measurement that produced them is exactly what regresses silently: overriding only the three `--pst-` variables leaves `body` on the system stack. **It also asserts that the faces arrived**: the built `_static/` carries `Archivo.ttf`, `Jost.ttf` and `IBMPlexMono-Regular.ttf`, and the stylesheet declares four `@font-face` blocks with `format("truetype")`. Without that clause a build whose `html_static_path` never reached `assets/fonts/` passes both this row and row 13 and falls back to a system stack silently — the spec's *A font that is not there* edge case, which nothing else can see | `docsite/_static/lernkarten.css` |
| 22 | `test_the_pages_workflow_triggers_on_every_input` — all **twelve** `paths:` entries are present (FR-017), one assertion per entry, following the pattern already at `tests/test_landing_page.py:539`. Twelve, not ten: the four the file has today include `.github/workflows/pages.yml`, and the eight new ones include `assets/fonts/**` | `pages.yml` |
| 23 | `test_principle_v_names_the_documentation_directory` — Principle V's table has a `docsite/` row and its `docs/` row names `leitner.html` (FR-039, the half nothing enforces) | the constitution amendment |
| 24 *(guard)* | `test_the_pre_pr_gates_have_not_grown` — the **first** fenced `bash` block under `CONTRIBUTING.md` § *Before the pull request* still holds exactly **five** command lines (`ruff check .`, `ruff format --check .`, `pytest`, `lernkarten check cards/example.yaml`, `python3 scripts/check_docs.py`) — five lines for what the project calls four gates, because `ruff` runs twice. SC-010's second half, and FR-024's "no fifth gate". Lives in `tests/test_repo_hygiene.py`, beside the other "the repository still says what it says" assertions. **Scoped to the first block**: the section carries a second one (`make_testdata.py`, `LERNKARTEN_E2E=1 pytest`) which is not a pre-PR gate | nothing — the only thing standing between FR-024 and a future feature quietly adding a sixth line |
| 25 *(guard)* | `test_the_docsite_holds_no_symlink_and_no_copy` — nothing under `docsite/` is a symlink, and no file under `docsite/` repeats the bytes of a migrated document (`docs/*.md`, `CONTRIBUTING.md`). FR-028 excludes both mechanisms **by name** and says it is written "so that a later change does not 'simplify' it into a move", which is a rule with no enforcement until this row exists | nothing — the two mechanisms are already absent; it is the enforcement FR-028's own sentence asks for. A pytest case, **not** a manual row, so FR-025's cap of three stays intact |

### The three manual rows (FR-025, constitution XI)

`docs/testing.md`'s checklist reaches 43 today (the Leitner dividers). This
feature adds **44, 45 and 46 — and no more**, each named where it is claimed.
FR-025's cap is a real constraint and it is respected: **SC-007 was given a home
inside row 46 rather than a fourth row of its own**, because the two are the same
post-merge moment and rows 33 and 34 already establish that shape — row 33 is
read on github.com and row 34 on the deployed site, neither in a checkout.
SC-010's second half got the opposite treatment: it turned out to be assertable
(red row 24) and so it gets a test instead of a row.

| # | Verifies | Why no test can |
|---|---|---|
| 44 | **SC-008 / FR-035** — at 375 px every page reads without horizontal scrolling and no Archivo prose renders below 15 px | `test_reading_text_is_never_below_the_screen_floor` reads one hand-written file's `<style>` blocks; it cannot reach a theme's compiled stylesheet |
| 45 | **SC-005** — the reviewer reads the diff of `tests/test_landing_page.py` and `scripts/check_docs.py` and confirms no assertion deleted, no target dropped from a derived set, no condition relaxed | "unweakened" is a judgement about a diff; no command reports it |
| 46 | **SC-013 and SC-007** — the documentation build ran on the pull request that introduced the change; then, after the merge, walk `https://mhabedank.github.io/lernkarten/`: the landing page is the repository copy, its `docs/` link reaches the documentation in one click, `/leitner.html` serves the method page and no copy of it exists under `/docs/` | both are properties of a *process and a deployment*, not of an artifact in the checkout. Quickstart § 11 is the script for the second half |

### Guards, and how XI is satisfied

Constitution XI is not waivable, so the plan says plainly which rows are red-first
and which are not rather than letting "(green by construction)" pass as an answer.

**Red-first — 19 rows**: 1, 3–11, 15–23. Each is written first, run, and
seen failing on its assertion.

**Guards — rows 2, 12, 13, 14, 24 and 25.** They are green the moment they are written,
because there is no behaviour to satisfy: each states an invariant that already
holds and that a *later* change could break. That is an established and
documented shape in this repository, not an improvisation —
`tests/test_landing_page.py::test_the_page_stays_one_self_contained_file` says so
in its own docstring ("Unlike the seven assertions above this one was never red,
and it could not be without breaking the page on purpose"). XI asks for red on
every *behaviour*; a guard asserts the absence of a behaviour, and there is
nothing to make red without first writing the defect.

Row 12 is the one worth naming individually, because it is not quite the same
shape: `test_building_twice_is_byte_identical` cannot even be **collected** before
`scripts/build_docs.py` exists, so writing it first produces an *error*, which XI
explicitly refuses to count as red ("fails with ImportError does not count").
Making it genuinely red would mean writing a deliberately non-deterministic build
and then removing it, which is a spike promoted to a pull request — the thing XI's
spike clause forbids. So it is written **after** row 5, as a guard, and labelled
one. Determinism itself is Sphinx's property, verified in the Phase 0 spike
(research R5); what row 12 defends is a future `conf.py` line that would destroy
it.

**Row 13 is a guard for the same reason, and an earlier draft of this plan got
it wrong.** Its "goes green with" column used to read *the `@font-face` block*,
which research R4 contradicts: the stock theme already loads no third-party
sub-resource, so the row passes before a single font is declared. Calling it
red-first would have produced a row that was never red *and* hidden the real
gap — that nothing asserted the faces had actually arrived. Row 21 now carries
that assertion, and row 13 is labelled what it is.

**Row 25 is a guard by construction.** FR-028 excludes a symlink and a
build-time copy *by name*; both are absent today, and making the row red would
mean committing the very arrangement the requirement forbids. It is the same
shape as row 14, and 013 inherits it along with the directory.

## Complexity Tracking

| Violation | Gate | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|---|
| A 32-distribution transitive tree | IV | Sphinx is the toolchain FR-001 settled on, and its `sphinxcontrib-*` set plus `requests` are hard requirements of it | Hand-written HTML has no checked cross-references, which is the whole reason for the feature. MkDocs is a smaller tree but has no domain model and no `metadata.docs` path for 013 |
| A new module under `scripts/` | V | FR-019's one command, and FR-038's assembly, which `sphinx-build` cannot do | `check_docs.py` is a gate and `render_brand.py` is a renderer; adding a build to either gives it a second job and a second import graph |
| A new top-level directory | V | FR-028 settled it: `docs/index.md` beside `docs/index.html` is the confusion this feature removes | Sources under `docs/` — rejected in the spec, with the reason recorded |
| An in-repo Sphinx extension | III | No library knows this repository's `_site` layout, `PAGES` mapping or GitHub URL | Nothing on PyPI does repository-relative link rewriting to a project-specific published layout |

Principle XI has no row here. It is not waivable.
