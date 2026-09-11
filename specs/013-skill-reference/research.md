# Phase 0 research: Sphinx documentation foundation (013)

**Method**: everything below was **measured**, not estimated. A throwaway venv
(`sphinx 9.0.4`, `myst-parser 5.1.0`, `pydata-sphinx-theme 0.21.0`) and a
throwaway copy of this repository's five migrated documents were built with the
real toolchain under `-W`, and every claim about warnings, node types, rendered
`href`s and file counts comes from that build. The spike is thrown away
(constitution XI); what survives is this file.

The spec's seventeen recorded decisions are treated as constraints. Where the
measurement **contradicts** the spec, it is recorded here under
[Findings that contradict the spec](#findings-that-contradict-the-spec) rather
than planned around silently.

---

## R1 — Dependency vetting (Principle IV, FR-002 … FR-004)

### Reuse check (constitution III)

Nothing is hand-rolled. Static site generation and checked cross-references are
solved problems; Sphinx is adopted. The one piece of code this feature writes
itself is the FR-029 link transform (~40 lines of logic), and it exists because
no library knows this repository's publication layout.

### The direct three

| Gate | `sphinx` | `myst-parser` | `pydata-sphinx-theme` |
|---|---|---|---|
| **Pin** | `sphinx==9.0.4` | `myst-parser==5.1.0` | `pydata-sphinx-theme==0.21.0` |
| **What it is for** | builds the documentation site | reads the Markdown this repository already has | the theme pandas and numpy use |
| **Wheels Win/macOS/Linux** | pure Python (`py3-none-any`) | pure Python | pure Python |
| **Plain `pip install`** | yes | yes | yes |
| **Python floor** | `>=3.11` — clears 3.12 | `>=3.11` | `>=3.11` |
| **Stable line** | 9.0.4, ≥ 1.0 | 5.1.0, ≥ 1.0 | 0.21.0, pre-1.0 **but** it is the theme of pandas, numpy, SciPy, Jupyter and Bokeh — the "long, obviously stable track record and wide adoption" clause of Principle IV |
| **Maintained** | sphinx-doc/sphinx, releases continuously | executablebooks/MyST-Parser | pydata/pydata-sphinx-theme |
| **Provenance** | public repo, PyPI history matches | public repo | public repo, PyData organisation |
| **Typo-squat** | `sphinx`, not `sphinxs`/`spinx` | `myst-parser`, not `myst` | `pydata-sphinx-theme`, not `pydata-sphinx` |
| **Install-time scripts** | none — wheel install only | none | none |
| **Licence** | BSD-2-Clause | MIT | BSD-3-Clause |
| **Cold-start cost** | **none on the runtime path** — FR-003/FR-005: nothing under `bin/` or `scripts/` that a user's run reaches imports any of them | same | same |

### Wheel coverage, verified rather than asserted

`pip download --only-binary=:all: --python-version 3.12 --abi cp312` resolved the
**complete** closure (32 distributions) for `win_arm64`, `manylinux2014_x86_64`
and `macosx_11_0_arm64`. `win_arm64` is the platform that decided this project's
3.12 floor, so it is the one that matters. Only three distributions in the tree
are not `py3-none-any` — `charset-normalizer`, `MarkupSafe`, `PyYAML` — and all
three publish a `cp312` wheel for every one of those platforms. **No compiler is
needed anywhere.**

### Licences across the whole closure

Every one of the 32 is permissive: BSD-2/3, MIT, Apache-2.0, PSF-2.0,
`0BSD OR CC0-1.0`, public domain (docutils), and `MPL-2.0` for `certifi`.
MPL-2.0 is file-level copyleft on `certifi`'s own files only; nothing is
modified and nothing is redistributed, so it is compatible. **No advisory** is
outstanding on any of them at the time of writing.

### The one gate that is not a clean pass

**Transitive tree: 32 distributions.** Principle IV asks for "a shallow
transitive tree" and gives "thirty packages to get one function" as the failing
shape. This is thirty-two. It is recorded as a **stated cost, not a pass**:

- It is not thirty packages for *one function* — it is a documentation
  toolchain, and the spec chose it over hand-writing HTML for reasons FR-001
  records.
- FR-002's separate `requirements-docs.txt` is precisely the mitigation: the
  tree lands on nobody who is not building documentation. `requirements-dev.txt`
  stays four lines and installs in seconds; `pytest` keeps passing without any
  of this (SC-006).
- It never reaches a user: FR-003 keeps it out of `scripts/deps.py`, so
  `lernkarten build` installs none of it (SC-009).

Two entries in the tree are worth naming because a reviewer will notice them:
**`requests`** (plus `certifi`, `urllib3`, `idna`, `charset-normalizer`) is a
*hard* dependency of Sphinx 9 — `Requires-Dist: requests>=2.30.0`, used by the
`linkcheck` builder — and of `pydata-sphinx-theme`. It is not something this
plan adds and it cannot be dropped. The docs build itself makes no network call
(SC-001 asserts an offline build), which is the property that matters.

### Pinning strategy

**All three pinned exactly**, in `requirements-docs.txt`. Principle IV pins
*tools* exactly and gives *libraries* a range; Sphinx here is a tool — its
output is compared byte-for-byte between two runs (SC-004) and its warning set
is a gate (FR-020), so a patch release drifting under a contributor is exactly
the failure the exact-pin rule exists to prevent. This is the same reasoning
that pins `ruff` exactly. Transitive pins are **not** written down: pinning the
closure would mean a 33-line hash table to maintain by hand, which is the open
Reconciliation item, not this feature's job.

`.github/dependabot.yml` already watches `package-ecosystem: pip, directory: "/"`,
which picks up a new root-level `requirements-*.txt` with no change. Principle
IV's "dependabot covers the declaring manifest" gate is met without an edit.

**No dependency fails a `CONTRIBUTING.md` gate.** Nothing here is a
stop-and-report.

---

## R2 — The FR-029 repository-link transform, measured against its ceiling

### What the build actually does with the 31 links

Built as-is, with `{include}` and no transform, the five migrated documents
produce **27 `myst.xref_missing` warnings** — every one of them fatal under
FR-020's warnings-as-errors. The build named each one with the **real source
file and its real line number** (`docs/design.md:50`, not the wrapper page),
which is the property the whole design rests on.

### The hook is not `missing-reference`

The obvious design — a `missing-reference` handler in `conf.py` — **does not
work**, and this was found by building it and watching it never fire.
`myst_parser.sphinx_ext.myst_refs.MystReferenceResolver` sets
`default_priority = 9`, ahead of Sphinx's own `ReferencesResolver` (10), and
warns instead of emitting the `missing-reference` event. The working hook is a
`SphinxPostTransform` with `default_priority = 5`, which sees the
`pending_xref` nodes before MyST gets to them.

The node carries exactly what FR-029 requires: `node.source` is the **absolute
path of the file the link was written in** — `/…/docs/design.md`, not the
wrapper page — so "resolve relative to the source file's own location" is a
two-line expression and not a reconstruction problem.

### The measurement

| Version | Handles | File | Non-blank | Executable logic |
|---|---|---|---|---|
| Minimal | exactly what FR-029 asks: the 22 repository links + the site-root pair | 59 | 48 | **~22** |
| Complete | the above, plus the two problems below that FR-029 does not mention | 94 | 76 | **~42** |

**Verdict on the ceiling**: FR-029's transform *as specified* is **~22 lines of
logic — inside the ~30-line ceiling**, and the recorded fallback (hard-coded
GitHub URLs, with the `check_docs` coverage loss) is **not invoked**.

The complete module is ~42 lines of logic, over the ceiling — but the extra
twenty lines are not FR-029's job. They exist because the build does two things
the spec does not anticipate (R3 and R4 below), and the fallback would not fix
either of them: hard-coding URLs in the sources would still leave
`docs/leitner.html` duplicated under `_downloads/` and would still make
FR-037's prescribed link spelling a build failure. So the honest statement is
that the ceiling holds for the requirement it was written about, and the module
that ships is larger for reasons the ceiling was not measuring.

Measured properties of the shipped module: `ruff check` and `ruff format --check`
clean at `line-length = 100` under `select = ["E","F","W","I","UP","B","C4","SIM"]`;
`parallel_read_safe`/`parallel_write_safe`; two fresh builds byte-identical
outside `.doctrees/` and `.buildinfo`.

### The result

With the transform in place the site builds **clean under `-W`** — 27 warnings
to zero — and the rendered `href`s are:

| Source link | Rendered on the site |
|---|---|
| `../templates/card.typ` | `https://github.com/…/blob/main/templates/card.typ` |
| `../assets/fonts/` | `https://github.com/…/tree/main/assets/fonts` (directory → `/tree/`) |
| `../README.md#install` | `https://github.com/…/blob/main/README.md#install` — the anchor survives |
| `../CONTRIBUTING.md` | internal link to the contributing page |
| `design.md#the-box` | internal link + heading anchor |
| `index.html` (in `docs/design.md`) | `../../index.html` — the landing page, **depth-aware** |
| `../assets/card-box.pdf` | `../../card-box.pdf` |

**Every source file keeps its relative path**, so all 31 stay inside
`check_docs.check_links`'s file-system coverage. SC-011 holds.

---

## R3 — `{include}`, images and headings (FR-028, FR-040, FR-041)

Measured, in order of how easy each is to get wrong:

- **`:relative-images:` works.** `../assets/pipeline.png` and
  `../assets/example-cards.png` resolve against the *included* file and land in
  `_images/`. FR-030 and FR-041 are satisfied by that one option; nothing has to
  be copied by hand.
- **`:relative-docs:` must NOT be used.** It rewrites link targets relative to
  the *including* page **before** the transform sees them
  (`../CLAUDE.md` → `../../CLAUDE.md`), which breaks FR-029's
  "relative to the source file's own location" rule and produced two extra
  warnings in the spike. Without it, `node.source` gives the right answer for
  free.
- **`:heading-offset:` must NOT be used either.** It pushes every heading down a
  level, so a `###` becomes depth 4 and drops out of
  `myst_heading_anchors = 3` — which is how `#the-checklist` became a build
  failure in the first spike. Drop the wrapper heading entirely: a page whose
  whole body is one `{include}` takes the **included document's own H1** as its
  title and as its `toctree` entry ("Workflow — from a source to a printed
  card"). That is also the cleanest reading of FR-008: nothing is retyped, not
  even a title.
- **`myst_heading_anchors = 3`** is exactly the depth the migrated documents
  need: `## The box` (2), `## Automated` (2), `### The checklist` (3).

---

## R4 — The theme (FR-027, FR-035, FR-036)

Measured against `pydata-sphinx-theme 0.21.0`'s compiled stylesheet and its
Jinja templates. See [The theme, at selector level](#the-theme-at-selector-level).

One result is worth stating on its own because it removes a risk the spec
flagged: **the stock theme loads no third-party sub-resource.** The built site
contains no `<link>`, `<script>` or `<img>` with an `http(s)` URL; FontAwesome
ships bundled under `_static/vendor/`. SC-014 therefore needs only the three
faces added, not a de-CDN-ing exercise. The theme's footer does *link* to
`sphinx-doc.org` and `pydata-sphinx-theme.readthedocs.io` — links, not
sub-resources, so SC-014 is unaffected; whether they stay is a question for
FR-036's new `docs/design.md` row.

### The fonts

`assets/fonts/` holds `Archivo.ttf` (256 KiB, **variable**), `Jost.ttf`
(131 KiB, **variable**), `IBMPlexMono-Regular.ttf` (132 KiB, static) and
`Archivo-Italic.ttf` (289 KiB, variable). They are served as **TrueType, as-is**:
converting to `woff2` would commit a new binary, and Principle VIII's exception
list is a *named list* that `tests/test_repo_hygiene.py` asserts is complete, so
a converted face would be a constitution amendment rather than a build step.
Consequences for the `@font-face` block: `format("truetype")`, and a
`font-weight: 100 900` range on the two variable faces so Jost 400 and Jost 500
both come off one file. Total transfer for a first-time reader: ~519 KiB for the
three upright faces (~808 KiB with the italic).

---

## R5 — Determinism, portability and the local preview (SC-001, SC-004, FR-038)

- **Two fresh builds are byte-identical** outside `.doctrees/` and
  `.buildinfo` — exactly the exclusion SC-004 names. Verified with `diff -r`.
- **No absolute path appears in the output.** Grepped the whole HTML/JS tree for
  the build root; zero hits.
- **The build makes no network call.** Nothing in the toolchain fetches at build
  time once installed.
- **`_site` assembly**: with `docs/index.html` at `_site/index.html`,
  `docs/leitner.html` at `_site/leitner.html`, `assets/card-box.pdf` at
  `_site/card-box.pdf` and the Sphinx output at `_site/docs/`, every rewritten
  link resolves in both settings. The depth-aware `../` prefix in the transform
  is what makes that true for a page nested under `docs/contributing/`. **Who
  performs those three copies is a plan decision, not a research finding** — see
  [plan.md § The `_site` assembly](plan.md#the-_site-assembly-stated-once); both
  `pages.yml` and `build_docs.py` do, deliberately.
- **Relative internal links**: Sphinx's HTML builder emits document-relative
  URIs with `html_baseurl` unset, which is the default. Grepped the spike output
  for `href="/…"` and for an absolute site URL: zero hits. FR-018 therefore holds
  by the absence of a `conf.py` line, which is why the plan makes it a stated
  decision plus an assertion rather than leaving it to the default.

**One honest caveat on the local preview.** FR-014 makes the landing page link
`docs/` — a *directory*. Over `file://` a browser shows a directory listing
rather than `index.html`; over HTTP (GitHub Pages) it serves `docs/index.html`.
So the local `_site` previews everything FR-038 claims **except** that one hop,
which needs `python3 -m http.server` to check. This does not change FR-014 (the
form is settled and the deployed behaviour is correct); it means SC-007's
"one click" is verified on the deployed site, and the local preview's
instructions should say to serve `_site` rather than open it.

---

## Findings that contradict the spec

Four. None is fatal; each needs a plan-level decision, and all four are folded
into `plan.md`.

### C1 — FR-031's hand-edits would break gate #4

FR-031 says two links in `docs/design.md` "MUST be retargeted by hand":
`index.html` → `../index.html`, and `../assets/card-box.pdf` → `../card-box.pdf`.
**Both edits create dead links in the source file.** `check_docs.check_links`
resolves a relative target against the file system from the file's own
directory: from `docs/`, `../index.html` is `<repo>/index.html` and
`../card-box.pdf` is `<repo>/card-box.pdf`. Neither exists. Gate #4 would go red
on the commit that made the edit, against FR-024 and SC-011.

**Resolution taken in this plan**: do **not** hand-edit them. Add both to the
transform's `SERVED` table, keep the source paths exactly as they are — which
`check_links` already accepts today — and let the build produce `../../index.html`
and `../../card-box.pdf`. This is strictly *more* faithful to FR-029's own
reasoning ("the source files keep their relative paths … resolving them at build
time is what US4 scenario 3 means") than FR-031's hand-edit is. FR-031's table
stays useful as the enumeration of *which* links are site-root links; only the
mechanism moves from "by hand" to "in the transform".

The other two rows of FR-031's table (`../README.md#install`, `../CLAUDE.md`)
already say "via FR-029", and they work unchanged: the anchor survives the
rewrite (verified).

### C2 — FR-031's `../index.html` is only correct for a flat layout

Even as a build-time value, the literal `../index.html` is right only if the
page sits at `/docs/design.html`. Under the two-area layout FR-007 asks for, the
page is at `/docs/contributing/design.html` and the correct value is
`../../index.html`. The transform therefore computes the prefix from the
document's own depth (`"../" * (docname.count("/") + 1)`) instead of hard-coding
it. Same destination, one line of arithmetic.

### C3 — FR-037's prescribed link spelling is a build failure as written

FR-037 requires a page under `docsite/` to write
"a relative path to the source file **including its `.md` extension**", and gives
`[design.md](../docs/design.md)` as an example. Measured: MyST strips the `.md`
and resolves the result as a **document name**, which does not exist —
`WARNING: Unknown source document '…/docs/design'`, fatal under `-W`, and the
text renders with **no link at all**. The other example, `[the workflow](workflow.md)`
pointing at a real `docsite/` page, works fine.

So FR-037's rule is right for links *between* `docsite/` pages and wrong for
links from a `docsite/` page to a repository file. **Resolution**: the transform
gains a branch for `refdomain == "doc"` targets that are not in `env.all_docs` —
it puts the suffix back and runs the same repository lookup. Verified: the exact
spelling FR-037 prescribes then renders as an internal link to the site page.
FR-037's intent (the page stays visible to `check_links`) is preserved without
weakening anything.

### C4 — a relative link to `docs/leitner.html` silently duplicates it

Measured: `[the method page](../../docs/leitner.html)` written in the FR-032
wrapper page becomes a MyST **download reference**. Sphinx copies the file to
`_downloads/<hash>/leitner.html` and emits
`<a class="reference download internal" download="">`. That is a second copy of
`docs/leitner.html` inside the documentation tree, at a second URL, that the
browser *saves* instead of opening — a direct violation of FR-010 ("one page,
one URL") and SC-012, produced by the most natural way to write the wrapper.

The general rule behind it, worth stating because 015 will meet it: **a link
written in a `docsite/` page to a file that exists on disk becomes a download**;
the same link written inside an `{include}`d document does not, because MyST
resolves it against the including page, where it does not exist. The asymmetry
is invisible until something is duplicated.

**Resolution**: the transform also handles `download_reference`, hooked on
`doctree-read` at `priority=100` so it runs **before** Sphinx's
`DownloadFileCollector` (priority 500) copies anything. Verified: `_downloads/`
disappears entirely, and the wrapper's link renders as `../../leitner.html` —
the site root, one URL, FR-010 and SC-012 intact.

---

## Re-verified at T009 (2026-09-09)

*Every number below R1–R5 came from a networked spike taken before this
checkout could install anything. T009 exists to turn them back into
measurements. Run against `sphinx==9.0.4`, `myst-parser==5.1.0`,
`pydata-sphinx-theme==0.21.0` in a Python 3.13.14 virtualenv.*

| Claim | Stated | Measured | |
|---|---|---|---|
| the three pins resolve | 9.0.4 / 5.1.0 / 0.21.0 | identical | ✓ |
| `MystReferenceResolver.default_priority` | 9 | 9 | ✓ |
| `Sphinx.connect` default priority | 500 | 500 | ✓ |
| `--pst-font-size-milli`, `--pst-sidebar-font-size` | `0.9rem` | `0.9rem` | ✓ |
| wheel closure, three platform tags | 33 | **32**, identical on all three | corrected |
| `border-radius` rule blocks | 131 | 131 | ✓ |
| `box-shadow` rule blocks | 78 | 78 | ✓ |
| `font-size` rule blocks below 16 px | 33 | **20 / 25 / 43**, see below | not reproducible |

Both priorities hold, which is what the transform's whole design rests on, and
the wheel matrix resolves `--only-binary=:all:` on `win_arm64`,
`manylinux2014_x86_64` and `macosx_11_0_arm64` alike — so constitution IV's
gate passes on measurement rather than on report. The closure is 32
distributions, not 33; the count was quoted in nine places across two
artifacts and all nine are corrected.

**The stylesheet counts needed a method before they could be checked at all.**
`border-radius` yields 322 if you count occurrences of the string, 146 if you
count declarations, and 131 if you count rule blocks — the last is what the
table below means, and it is exactly right. The same for `box-shadow` at 78.
That was never written down, so neither number was reproducible even though
both were correct.

The sub-16-px count has no such resolution: 20 rule blocks carry a literal
`rem`/`px` value below the floor, 25 route a `font-size` through a `--pst-*`
variable, and 43 if `em` values and the small-variable routes are both counted.
The stated 33 sits inside that range and cannot be recovered without the rule
that produced it. It does not matter to the design: the override is written as
a blanket rule rather than a selector list precisely so that the exact
denominator is irrelevant, and the finding that actually governs — that about
eight of the small rules are Archivo prose while the rest are code literals,
FontAwesome glyphs, or classes this site never emits — is a qualitative
result the recount does not disturb.

**Method, so the next reader can repeat it**: split the compiled stylesheet on
`\{([^{}]*)\}` and count the blocks whose declaration list matches
`<shape>\s*:`. The file is minified, 376 389 bytes, 5 028 rule blocks — the
table's "~5 200" is the same measurement rounded.

Determinism, absolute paths and the offline build (R5) still cannot be probed:
they need `scripts/build_docs.py`, and are re-verified at T034 and T035.

---

## The theme, at selector level

*(FR-027 and FR-036 — the largest unknown in the feature. Measured against
`pydata-sphinx-theme 0.21.0`'s compiled stylesheet: 376 KB, ~5 200 rules, most
of it a bundled Bootstrap 5.)*

| Shape | Rules | Distinct values | Variable-routed? |
|---|---|---|---|
| `border-radius` | 131 | 48 | **no `--pst-*radius*` variable exists**; some `--bs-border-radius`, most hard-coded |
| `box-shadow` | 78 | 37 | partly `--pst-color-shadow` (a colour) and `--bs-*`; many hard-coded `rgba()` |
| gradients | 3 | — | one unused `--bs-gradient` |
| `font-size` < 16 px | 33 | — | 2 through `--pst-*`, 31 direct |
| `font-family` not on a `--pst-*` variable | 9 | — | including `body` and `code` — see below |
| `--pst-color-*` variables | 77 | — | — |

Three results decide the size:

1. **Every `border-radius: 50%` and every gradient in the theme is on a
   Bootstrap class Sphinx never emits** — `.form-check-input[type=radio]`,
   `.spinner-border`, `.spinner-grow`, `.rounded-circle`,
   `.progress-bar-striped`, `.placeholder-wave`. So a blanket
   `*, *::before, *::after { border-radius: 0 !important; box-shadow: none !important; }`
   needs **no exceptions**, and gradients cost one `--bs-gradient: none`.
   A blanket `background-image: none` is **wrong**: the navbar toggler, the
   admonition icons and the external-link marker are inline
   `data:image/svg+xml` backgrounds.
2. **Of the 33 rules below 16 px, about eight are Archivo prose.** Three are code
   literals (`pre`, `code`, `kbd`) that FR-035 exempts by name, eight are
   FontAwesome glyph sizes, one is `sub/sup`, one is a keycap literal, and
   thirteen are on classes this site never emits (eleven Bootstrap form classes,
   ABlog, Read the Docs ads). Two more are the variables
   `--pst-font-size-milli: 0.9rem` and `--pst-sidebar-font-size: 0.9rem`
   (14.4 px each) — raising those two covers every element that reads them,
   which is most of the visible offenders.
3. **The `--pst-font-family-*` variables are not enough.** `body` resolves
   `--bs-body-font-family` → `--bs-font-sans-serif` (a system stack) and
   `code, kbd, pre, samp` resolve `--bs-font-monospace`. Neither reads a `--pst-`
   variable, so the override sets five variables, not three.

Full breakdown, the size verdict and the list FR-036's new `docs/design.md` row
is written from are in [plan.md § The theme work](plan.md#the-theme-work-fr-027-fr-035-fr-036).

---

## Alternatives considered and rejected

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Where does the transform hook? | `SphinxPostTransform`, priority 5 | a `missing-reference` handler in `conf.py` | measured: MyST's own resolver at priority 9 never emits the event |
| How does an included file's link resolve? | `node.source`, with `:relative-images:` only | MyST's `:relative-docs:` | it rewrites targets relative to the *including* page, against FR-029's rule |
| How does the wrapper page get its title? | the included document's own H1 | a wrapper heading + `:heading-offset: 1` | the offset silently pushes `###` past `myst_heading_anchors`, and the wrapper heading retypes a title (FR-008) |
| How are the fonts served? | the vendored `.ttf`, `format("truetype")` | converting to `woff2` | a new committed binary, which Principle VIII's asserted list would have to name |
| Pin depth of `requirements-docs.txt` | the three direct packages, exactly | the full 33-package closure | hand-maintained hash/pin tables are the open Reconciliation item, not this feature |
