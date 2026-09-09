# Contract: the `docsite/` layout and the link tables

**Status**: 012. **No user-facing file format changes** — `sources.yaml`,
`knowledge/`, `catalog/topics.md` and `cards/*.yaml` are untouched. What follows
is the *internal* contract this feature introduces, written down because three
tests and two later features (013, 014) read it.

## 1 — Where a page may live

| Path | Holds | Rule |
|---|---|---|
| `docsite/conf.py` | Sphinx configuration | hand-written. Inside `ruff` gate #1 from the first commit; a copied Sphinx template does not pass |
| `docsite/_ext/*.py` | build-time extensions | **imports nothing from `scripts/`** — asserted by a test, not by intent. 013's skill extension inherits this directory and this rule |
| `docsite/_static/*` | stylesheet, fonts | the only place a visual override lives |
| `docsite/**/*.md` | page sources | covered by `scripts/check_docs.py` (FR-037) |
| `docsite/_build/` | build output | gitignored |
| `_site/` | the assembled site | gitignored |

**Excluded by name** (FR-028): symlinks into `docsite/` (Windows developer mode),
and a build-time copy of a source file into `docsite/` (a second editable file on
disk).

## 2 — How a document outside `docsite/` reaches the site

One MyST `{include}`, and nothing else in the file:

````markdown
```{include} ../../docs/workflow.md
:relative-images:
```
````

**The options are a contract, not a preference:**

| Option | Use | Why |
|---|---|---|
| `:relative-images:` | **always** | resolves `../assets/pipeline.png` against the *included* file, so FR-030 and FR-041 hold |
| `:relative-docs:` | **never** | rewrites link targets against the *including* page, breaking FR-029's "relative to the source file's own location" |
| `:heading-offset:` | **never** | pushes `###` to depth 4, out of `myst_heading_anchors = 3`, silently breaking `#the-checklist` |
| a wrapper heading | **never** on an include-only page | retypes a title (FR-008). The included H1 becomes the page title and the `toctree` entry |

## 3 — How a link inside a `docsite/` page is written (FR-037)

**The paths below are written from a page in `docsite/user/` or
`docsite/contributing/`**, which is where every page 012 ships lives — two
levels down, so a repository file is `../../`. A page at the `docsite/` root
(only `index.md` today) uses one `../` less. The depth is part of the example,
not decoration: `check_docs.check_links` resolves the target on the file system
from the page's own directory, so a `../` too few is a dead link in gate #4.

| Target | Write (from `docsite/<area>/`) | Renders as |
|---|---|---|
| another `docsite/` page in the same area | `[the workflow](workflow.md)` | an internal link |
| a repository Markdown file that is also a site page | `[design.md](../../docs/design.md)` | an internal link (needs the `refdomain == "doc"` branch — see C3) |
| a repository file that is not a page | `[the card template](../../templates/card.typ)` | a GitHub `blob` URL |
| a file served at the site root | `[the method](../../docs/leitner.html)` | a depth-aware relative link to the root — this is the FR-032 wrapper's link, the one instance 012 ships |

Never an extension-less MyST reference (`[the workflow](workflow)`):
`check_docs.check_links` resolves a relative target **against the file system**,
so the `.md` has to be there for the gate to see it.

## 4 — `PAGES`: a repository file that is also a page

Read by `docsite/_ext/repolinks.py`. Adding a page to the site means adding a row.

| Repository file | Document |
|---|---|
| `docs/workflow.md` | `user/workflow` |
| `docs/design.md` | `contributing/design` |
| `docs/testing.md` | `contributing/testing` |
| `CONTRIBUTING.md` | `contributing/guide` |

## 5 — `SERVED`: a repository file served at the site root

The value is **relative to the site root**; the transform prefixes
`"../" * (docname.count("/") + 1)` so it is correct from any depth (C2).

| Repository file | On the deployed site | Reached from `docs/contributing/design.html` as |
|---|---|---|
| `docs/index.html` | `/index.html` | `../../index.html` |
| `docs/leitner.html` | `/leitner.html` | `../../leitner.html` |
| `assets/card-box.pdf` | `/card-box.pdf` | `../../card-box.pdf` |

This table is FR-031's, with the mechanism moved from a hand-edit to the build
(see plan.md, C1) so the source files keep the paths `check_docs.check_links`
already accepts.

## 6 — Resolution order in the transform

For a link written in file *S* with target *T*:

1. `name = (dirname(S) / T)` relative to the repository root. Outside the
   repository → leave alone.
2. `name in PAGES` → internal cross-reference, anchor preserved.
3. `name in SERVED` → depth-aware relative link to the site root.
4. the file exists → `…/blob/main/<name>` (`…/tree/main/<name>` for a directory),
   anchor preserved.
5. otherwise → leave alone, so MyST warns and the build fails (FR-020).

## 7 — The assembled `_site`

The same tree locally (`python3 scripts/build_docs.py`) and on GitHub Pages
(`pages.yml`), which is what makes the local build a preview (FR-038).

**Who writes what** — the three root files are written **twice on CI, on
purpose**: `pages.yml` keeps its `cp` lines (two existing tests read them as
text, and CI never executes the workflow) and `build_docs.py` performs the same
copies (so the local build is a real preview). Both write identical bytes and
both are idempotent. Stated in full in
[plan.md § The `_site` assembly](../plan.md#the-_site-assembly-stated-once);
this contract does not restate the reasoning.

| Path | `pages.yml` | `build_docs.py` |
|---|---|---|
| `index.html`, `leitner.html`, `card-box.pdf`, `.nojekyll` | yes (`cp`/`touch`) | yes (`shutil.copy2`/`touch`) |
| `docs/**` | no | yes (Sphinx) |

```text
_site/
├── .nojekyll
├── index.html          # docs/index.html, byte-identical
├── leitner.html        # docs/leitner.html, byte-identical, ONE copy (SC-012)
├── card-box.pdf        # assets/card-box.pdf
└── docs/               # the Sphinx output
    ├── index.html
    ├── user/…
    └── contributing/…
```

## 8 — What 013 and 014 inherit

- A third and fourth `toctree` entry in `docsite/index.md` — a reference area and
  a tutorial area — with **no restructuring** of what 012 ships (FR-012).
- `docsite/_ext/`, with the "imports nothing from lernkarten" test already
  written — the mitigation the spec's extraction decision promised.
- Section 3's link rules, which bind 014 hardest: its pages will be full of grid
  and card-size claims, and `gated_files()` now reads them.
