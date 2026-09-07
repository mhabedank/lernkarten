# Feature Specification: Sphinx documentation foundation

**Feature Branch**: `docs/skill-reference`

**Created**: 2026-09-08

**Status**: Draft (revised — scope split, see *Follow-on features*)

**Input**: User description: "Es gibt keine wirkliche API beschreibung und dokumentation, die webseite verriet nicht wie die einzelnen befehle im detail ausgeführt werden können. gute seiten haben eine übersicht. die sollten wir auch haben. jetzt stellt sich mir aber eine frage: in regulären code können dise aus dem code generiert werden, zum beispiel klassen anhand der docstrings usw. ist sowas auch für skills möglich, wenn ja wäre es nice die auto zu geniereien. vlt sollte jeder skill meta informatiojen dafür zu verfügung stellen. es gibt ein paar solcher dokumentationen die mir am besten gefallen und die ich für dieses projekt auch gerne hätte: 1. Django (python) 2. Pandas 3. numpy — diese sind extrem gut gestaltet, auto generiert und bieten einen echten value. was mir bei pandas und django sehr gut gefällt ist dass es ein sehr gutes tutorial hat und dass die classes, methoden usw. direkt verlinkt sind und man easy hinklicken kann; zudem gibt es noch Themenseiten — das gibt es bei pandas auch (zum Beispiel Visualisierung)."

**Scope note**: the original request is delivered in three features. **This spec is
012, the foundation only**: the toolchain, the theme, the rebuilt publication
workflow, and the migration of the documentation that already exists. It ships a
real, navigable documentation site with **no generated content yet**. The
generated skill/CLI reference is **013**; the tutorial and topic pages are
**014**. Both are recorded in [Follow-on features](#follow-on-features) so they
can be specified later without re-deciding anything.

## Scope in the Pipeline *(mandatory)*

**Pipeline stage(s) touched**: none. All seven steps are *documented*; no step
changes behaviour, and no file a user's project holds is read or written.

**Implementation half**:

- [x] **Deterministic** — Python and configuration under `docs/`, a dependency
      manifest, a rebuilt `.github/workflows/pages.yml`, and pytest cases. **No
      skill prompt changes in 012**; the `SKILL.md` frontmatter change belongs to
      013.

**Who runs into this**: **both** — the user driving Claude in their own project
(who today cannot find out how a command is actually run without opening the
plugin's `SKILL.md`), and a contributor to this repo (who today finds half the
documentation on a website and half in the repository, with nothing explaining
the split).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - All the documentation is in one navigable place (Priority: P1)

Today a reader has to know where to look. The published site is one page,
`docs/index.html`. `docs/workflow.md`, `docs/design.md` and `docs/testing.md` are
Markdown files inside the repository; `CONTRIBUTING.md` is at the root;
`docs/leitner.html` is a second designed page that was, until recently, linked
from the landing page and from the README and served nowhere. Nothing tells a
newcomer that this split exists or why.

They open the site, follow one link off the landing page, and land in a
documentation site with a persistent sidebar and two clearly separated areas: a
**user guide** (how to use the thing) and a **contributing** area (how to work on
it). Everything that was scattered is in one of the two, reachable by browsing
rather than by knowing.

**Why this priority**: this is the user's actual complaint — content split
between the website and the repo for no reason a newcomer can see. It is also
the prerequisite for 013 and 014, which need a site to put pages into.

**Independent Test**: build the site from a clean checkout and assert that every
migrated document is reachable from the site's navigation tree, and that the user
area and the contributing area are separate top-level entries.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** the documentation is built, **Then** the
   navigation contains a user area holding `docs/workflow.md` and the Leitner
   method page, and a contributing area holding `docs/design.md`,
   `docs/testing.md` and `CONTRIBUTING.md`.
2. **Given** the built site, **When** any migrated document is opened, **Then**
   its text is the text of the source file — nothing was retyped or forked into a
   second copy.
3. **Given** `CONTRIBUTING.md`, **When** the repository is browsed on GitHub,
   **Then** the file is still at the repository root where GitHub's contribution
   prompts expect it — the site includes it by reference, it does not move it.
4. **Given** the built site, **When** a page is opened at a viewport of 375 px,
   **Then** it is readable without horizontal scrolling and no reading text
   renders below 15 px.

---

### User Story 2 - Anyone can build the docs locally with one command (Priority: P1)

A contributor wants to see their documentation change before opening a pull
request. There is no docs build today, so there is nothing to run.

They install one requirements file and run one command. The site builds offline,
on Windows, macOS or Linux, with Python 3.12, and opens in a browser from the
filesystem.

**Why this priority**: a documentation system nobody can run locally is a
documentation system that only CI can check, which is how documentation rots.

**Independent Test**: in a fresh virtual environment with only the docs
requirements installed and no network access, run the build command and assert it
exits 0 and produces an index page; run it twice and assert the second run
changes nothing.

**Acceptance Scenarios**:

1. **Given** a fresh checkout and the docs requirements installed, **When** the
   build command runs with no arguments and no network, **Then** it exits 0.
2. **Given** a build that emits any warning, **When** it runs, **Then** it exits
   non-zero — warnings are errors, so a broken reference cannot merge.
3. **Given** an unchanged checkout, **When** the build runs twice, **Then** the
   second run produces the same output as the first.
4. **Given** an environment without the docs requirements, **When** `pytest`
   runs, **Then** the docs-build tests **skip** with a message naming what to
   install, and the rest of the suite passes — the same shape
   `tests/test_e2e.py` already uses for the typesetting engine.
5. **Given** the built site opened from the filesystem, **When** its internal
   links are followed, **Then** they resolve — links are relative, never
   root-anchored.

---

### User Story 3 - The site is published without breaking what was reachable (Priority: P1)

`.github/workflows/pages.yml` today assembles `_site` by copying exactly two
files. That assembly has already produced one live 404: `docs/leitner.html` was
linked from the landing page and from the README and was never copied in. The fix
(PR #105) added a test that derives the relative links out of `docs/index.html`
and requires the workflow to copy each one.

The workflow is rebuilt to build the documentation site and publish it under a
sub-path, with `docs/index.html` still served at the root, unchanged. Nothing
that was reachable before becomes a 404, and the invariant that catches such a
404 still holds.

**Why this priority**: the deployment is the deliverable. A docs site that builds
locally and 404s in production has solved nothing, and this repository has the
scar to prove it.

**Independent Test**: assert the workflow's assembly step places the landing
page, the card box, the Leitner page and the generated site into `_site`, and
that the link-derivation test from PR #105 still passes against the new assembly.

**Acceptance Scenarios**:

1. **Given** the rebuilt workflow, **When** the site is assembled, **Then**
   `docs/index.html` is at the site root, byte-identical to the file in the
   repository.
2. **Given** every relative link in `docs/index.html`, **When** the assembly runs,
   **Then** each target exists in `_site` — the PR #105 invariant, adapted to the
   new assembly shape and never weakened.
3. **Given** the landing page, **When** it is read, **Then** it offers a link
   into the documentation site.
4. **Given** any file that feeds the documentation build, **When** it changes on
   `main`, **Then** the workflow's `paths:` trigger fires and the site
   redeploys.
5. **Given** `tests/test_landing_page.py`, **When** the suite runs after this
   feature, **Then** every existing assertion in it still passes.

---

### User Story 4 - A reference that does not exist fails the build (Priority: P2)

The reason to adopt a documentation system rather than write HTML is that the
system can *check* itself. This repository has already shipped documentation
drift twice — the `--grid` sweep and the A8-default sweep — and both had to be
turned into bespoke regex gates in `scripts/check_docs.py` after the fact.

A contributor writes a cross-reference to a document or section that does not
exist. The build fails and names the file and the reference, before the pull
request is opened.

**Why this priority**: it is the mechanism 013's entire value rests on. Standing
it up in the foundation means 013 inherits checked cross-references rather than
inventing them.

**Independent Test**: add a cross-reference to a non-existent target, build, and
assert the build exits non-zero naming the source file and the target; remove it
and assert the build passes.

**Acceptance Scenarios**:

1. **Given** a document containing a cross-reference to a target that does not
   exist, **When** the site is built, **Then** the build exits non-zero and the
   message names the source document and the missing target.
2. **Given** a document linking a file that has been deleted, **When** the site is
   built, **Then** the build fails rather than publishing a dead link.
3. **Given** the existing dead-link check in `scripts/check_docs.py`, **When**
   the gates run, **Then** it still covers the Markdown sources — the two checks
   overlap deliberately rather than one replacing the other.

---

### User Story 5 - The existing docs gates keep holding (Priority: P2)

`scripts/check_docs.py` carries checks bound to specific files and paths: the
Leitner interval check reads `docs/leitner.html` and compares it against
`scripts/leitner.py` in both directions, and `tests/test_check_docs.py` asserts
that file exists at that path. `tests/test_landing_page.py` asserts against
`docs/index.html` and against `pages.yml`. A migration that moves files silently
turns those gates into no-ops or hard failures.

A contributor runs the four gates after this feature and every one of them still
does what it did, against the same guarantees.

**Why this priority**: a migration that breaks the drift gates while claiming to
prevent drift is worse than no migration. This is a correctness requirement, not
a nicety.

**Independent Test**: run all four existing gates plus the full suite after the
migration and assert nothing was deleted, skipped or loosened; specifically, drop
an interval from the Leitner page and assert `check_docs.py` still reports it.

**Acceptance Scenarios**:

1. **Given** the Leitner method page after migration, **When** an interval that a
   divider prints is removed from it, **Then** `python3 scripts/check_docs.py`
   exits non-zero and names that interval.
2. **Given** the Leitner method page after migration, **When** it mentions an
   interval `scripts/leitner.py` does not define, **Then** the gate reports that
   too — the check stays bidirectional.
3. **Given** the four pre-PR gates, **When** they run after this feature,
   **Then** all four pass, and the pre-PR checklist has gained no fifth command a
   contributor has to remember.

---

### Edge Cases

- **Missing optional tooling**: the docs build must not need a typesetting
  engine, a network connection or a separately installed binary. A contributor
  with Python and one `pip install` must be able to build and read the site.
  (Constitution II.)
- **Docs requirements not installed**: `pytest` must still pass. The docs-build
  tests skip with a message naming what to install, exactly as
  `tests/test_e2e.py` skips without an engine.
- **Fresh install on each platform**: the build runs on Windows, macOS and Linux
  from one ordinary command; the output must contain no absolute paths and no
  platform-dependent path separators.
- **Python floor**: works on 3.12.
- **Encoding**: the migrated documents contain em dashes, ×, °, umlauts and
  typographic quotes, and `docs/workflow.md` contains fenced examples of Typst
  card markup. Output declares UTF-8, and a `#list([…])` example must render as
  text, not as markup.
- **Idempotence**: building twice produces the same output; deleting the build
  directory and rebuilding restores exactly it.
- **Local viewing**: the built index opens from `file://` with working internal
  links.
- **A document that is also a repository file GitHub renders**: `CONTRIBUTING.md`
  is read on GitHub *and* in the site. It has one copy and one location.
- **A hand-written HTML page inside a generated site**: `docs/leitner.html` is
  neither Markdown nor generated. It must survive with its design intact and its
  gates attached.

## Requirements *(mandatory)*

### Functional Requirements

**Toolchain (settled — not a plan-phase question)**

- **FR-001**: The documentation site MUST be built with **Sphinx**, using
  **`myst-parser`** for Markdown sources and **`pydata-sphinx-theme`** for the
  theme. The rationale is recorded and is not reopened in planning: Django,
  pandas and numpy — the three documentation sites the user named as the target —
  are all Sphinx, and pandas and numpy both use `pydata-sphinx-theme`. Sphinx
  domains give *checked* cross-references (a reference to something that does not
  exist fails the build), which is the drift protection this whole feature exists
  for; `myst-parser` means the Markdown this repository already has stays
  Markdown.
- **FR-002**: The documentation dependencies MUST be **development/CI only**,
  declared in a new **`requirements-docs.txt`**, separate from
  `requirements-dev.txt`. The reason for a third file rather than more lines in
  the second: `requirements-dev.txt` is what every contributor installs to run
  the four gates, and Sphinx plus a theme pulls a large transitive tree
  (docutils, Jinja2, Pygments, Babel, and the theme's own web assets) onto every
  contributor for a task most of them never perform. Separating it lets `pytest`
  stay installable in seconds, lets CI install it only in the docs job, and gives
  the Principle IV review one file to point at.
- **FR-003**: The documentation dependencies MUST NOT be routed through
  `scripts/deps.py`. That is the **runtime** channel, and a user running
  `lernkarten build` must never install Sphinx. This is stated explicitly because
  `CONTRIBUTING.md`'s dependency gates are written for runtime dependencies and a
  reviewer will otherwise apply them here.
- **FR-004**: Every documentation dependency MUST install with a plain
  `pip install` on Windows, macOS and Linux, from wheels, with no compiler, on
  Python 3.12.
- **FR-005**: `lernkarten build`, `lernkarten check` and every other runtime path
  MUST be unaffected: no import of a documentation package from anything under
  `bin/` or from any script a user's run reaches.

**Sources and migration**

- **FR-006**: Existing Markdown documentation MUST stay Markdown. No source file
  is converted to reStructuredText.
- **FR-007**: The site MUST present two separate top-level areas: a **user guide**
  holding `docs/workflow.md` and the Leitner method page, and a **contributing**
  area holding `docs/design.md`, `docs/testing.md` and `CONTRIBUTING.md`.
- **FR-008**: Each migrated document MUST have exactly one copy. The site
  includes the existing file; it does not duplicate, retype or fork it.
- **FR-009**: `CONTRIBUTING.md` MUST remain at the repository root, where GitHub
  reads it, and be pulled into the site from there.
- **FR-010**: `docs/leitner.html` is hand-written HTML with a bespoke design, not
  Markdown. It MUST be **embedded, not converted**: the file stays at
  `docs/leitner.html`, byte-identical, is carried into the built site as an extra
  static page, and gets a navigation entry pointing at it. Converting it would
  destroy a designed page and detach the gates named in FR-011.
- **FR-011**: The Leitner interval gate in `scripts/check_docs.py`
  (`LEITNER_PAGE`, `check_leitner_intervals`, checked in both directions against
  `scripts/leitner.py`) MUST keep working, and `tests/test_check_docs.py`'s
  assertion that `docs/leitner.html` exists at that path MUST keep passing. If any
  future change moves the file, the gates move with it — they are never weakened
  or deleted.
- **FR-012**: The site MUST NOT contain generated skill or CLI reference content
  in this feature, but its navigation structure MUST accommodate a reference area
  and a tutorial area being added later without restructuring what 012 ships.

**Landing page and publication**

- **FR-013**: `docs/index.html` MUST stay the site root, unchanged in content and
  design, and MUST keep passing every assertion in `tests/test_landing_page.py`.
  The generated documentation site lives under a sub-path — the arrangement
  Django uses.
- **FR-014**: The landing page MUST link into the documentation site.
- **FR-015**: `.github/workflows/pages.yml` MUST be rebuilt to run the Sphinx
  build and assemble `_site` from the landing page, the card box, the Leitner
  page and the built documentation.
- **FR-016**: The invariant added by PR #105 —
  `test_the_pages_workflow_assembles_every_relative_link`, which derives the
  relative links out of `docs/index.html` and requires the workflow to copy each
  one — MUST keep holding. If the assembly step changes shape, the test is
  **adapted, never weakened**: no target may drop out of the derived set, and no
  assertion may be relaxed to accommodate the new workflow.
- **FR-017**: The workflow's `paths:` trigger MUST cover every input to the
  documentation build — the migrated documents, the documentation configuration,
  `requirements-docs.txt`, and the workflow file itself — so a change to any of
  them redeploys the site.
- **FR-018**: The built site's internal links MUST be relative, so the site works
  under a sub-path and when opened from the filesystem.

**Build behaviour**

- **FR-019**: A single command with no arguments MUST build the whole site, with
  no network access required.
- **FR-020**: The build MUST treat warnings as errors and MUST be strict about
  references: a cross-reference or link to a target that does not exist fails the
  build, and the message names the source document and the target.
- **FR-021**: The build MUST be deterministic and idempotent: the same checkout
  produces the same output, and building twice changes nothing.
- **FR-022**: The build output MUST NOT be committed. The build directory
  (`docs/_build/`) goes into `.gitignore`, consistent with the rule this
  repository already applies to `output/` (constitution IX).
- **FR-023**: Tests that build the documentation MUST **skip** when the
  documentation dependencies are absent, with a message naming what to install —
  the pattern `tests/test_e2e.py` already uses. CI MUST have a job that installs
  them and runs those tests.
- **FR-024**: The four existing pre-PR gates MUST still pass, and the pre-PR
  checklist MUST gain no fifth command; the docs build is a CI job and a local
  convenience, not a fifth thing to remember.
- **FR-025**: Tests MUST be written first and seen failing (constitution XI).
  Nothing in this feature is model-driven, so the red artifacts are pytest cases:
  against the build, against the navigation tree, against the assembly step in
  `pages.yml`, and against the preserved gates.

**Content rules**

- **FR-026**: Every page MUST stay subject-agnostic — examples demonstrate a
  format, never a field of study (constitution VII) — and MUST be in English
  (constitution XIII).
- **FR-027**: The theme MUST be configured so the documentation site and the
  landing page read as one property rather than as a stock template beside a
  bespoke page. `docs/design.md` governs: reading text never below 15 px, colour
  never carrying meaning on its own.

### Format Contracts *(mandatory — state "none" if untouched)*

| Artifact | Change | Also needs updating |
|---|---|---|
| `sources.yaml` | none | — |
| `knowledge/<id>/<doc>.md` frontmatter | none | — |
| `catalog/topics.md` structure | none | — |
| `cards/*.yaml` schema | none | — |

**No format change.** The `SKILL.md` frontmatter change — a `metadata.docs` block
— belongs to **013**, not to this feature. 012 reads no skill metadata and writes
no generated page.

**Backwards compatibility**: nothing a user has on disk is affected, and no
command changes behaviour. For contributors the only new obligation is one more
optional `pip install` to build the docs locally; without it the suite still
passes, with the docs tests skipped.

### Print & Design Impact *(mandatory — state "none" if nothing visible changes)*

- **Visible surfaces touched**: **a new set of published pages**, plus **one link
  added to the landing page**. The card, the press sheet, the mark and the README
  graphics are untouched, and `docs/index.html` keeps its design.
- **Black-only laser print still readable**: N/A for the card. The site pages must
  nonetheless not use colour as the only distinction — an "optional step" badge
  needs a word or a shape, not a hue.
- **Minimum type size respected**: **yes** — 15 px is the floor for reading text
  on every page, including code samples and tables.
- **Brand PNGs need re-rendering**: no.
- **Duplex alignment unaffected**: yes — nothing about the PDF changes.
- **Additional**: `docs/design.md` MUST be read before the theme is configured
  (constitution XVI). A stock `pydata-sphinx-theme` beside this project's landing
  page is a visible regression even though nothing on the card moved.

### Dependency & Portability Impact *(mandatory)*

- **Is anything being hand-rolled that a library already does?** **No — and that
  is the point of this feature's shape.** Static site generation and checked
  cross-references are solved problems, and constitution III makes reuse the
  default. Sphinx is adopted rather than reimplemented. The one thing this
  project will eventually build itself is the Sphinx extension that documents
  Agent Skills, and that is 013's scope, justified there by the finding that no
  such extension exists.
- **New runtime dependency**: **none.** Nothing reaches `scripts/deps.py`
  (FR-003).
- **New dev dependency**: **yes** — `sphinx`, `myst-parser` and
  `pydata-sphinx-theme`, in a new `requirements-docs.txt` (FR-002). All three are
  pure-Python wheels on PyPI, install with a plain `pip install` on all three
  platforms, and support Python 3.12. The Principle IV vetting table
  (maintenance, licence, transitive tree, wheel coverage, pinning strategy) goes
  in `plan.md`.
- **New external binary**: **none.** A documentation toolchain requiring a
  separate binary install would fail constitution II's friction standard for
  contributors.
- **Anything this makes redundant**: not yet. The hand-written command list in
  `README.md` § "The commands" and the pipeline table in `docs/index.html` become
  candidates for removal in **013**, once something generates them; the bespoke
  drift gates in `scripts/check_docs.py` (`SHEET_CAPACITY`, the A7/A8 default
  tokens, the cutting-instruction check) likewise. 012 removes nothing.
- **Engine version change**: no.
- **Platforms verified**: Linux and macOS locally and in CI; Windows through the
  existing CI matrix. The docs job's platform coverage is a plan decision — at
  minimum the build must be *portable*, even if only one platform runs it in CI.
- **Ordering dependency**: **PR #105 (`fix/pages-site-assembly`) must merge
  first.** It rewrites the same workflow and adds the invariant FR-016 requires.
  Building 012 on top of the pre-#105 workflow would either lose that test or
  conflict with it.

### Key Entities

- **Documentation source**: an existing repository file included in the site
  unchanged — `docs/workflow.md`, `docs/design.md`, `docs/testing.md`,
  `CONTRIBUTING.md`.
- **Embedded page**: `docs/leitner.html` — hand-written HTML carried into the
  built site as-is, with a navigation entry and its existing gates intact.
- **Documentation area**: one of the two top-level groupings — *user guide* and
  *contributing*.
- **Site assembly**: the `_site` tree the publication workflow produces — the
  landing page at the root, the card box, the Leitner page, and the built
  documentation under a sub-path.
- **Docs requirements**: `requirements-docs.txt`, the development/CI-only
  dependency channel, distinct from `requirements-dev.txt` and from
  `scripts/deps.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One command with no arguments turns a clean checkout into a built
  documentation site, offline, on Python 3.12, on Windows, macOS and Linux.
- **SC-002**: All five migrated documents — `docs/workflow.md`,
  `docs/leitner.html`, `docs/design.md`, `docs/testing.md`, `CONTRIBUTING.md` —
  are reachable from the site navigation, and each exists in exactly one place in
  the repository.
- **SC-003**: A cross-reference or link to a target that does not exist makes the
  build exit non-zero with a message naming the source document and the target.
- **SC-004**: Building twice on an unchanged checkout produces the same output,
  and no build output is tracked by git.
- **SC-005**: Every assertion in `tests/test_landing_page.py` and every check in
  `scripts/check_docs.py` that existed before this feature still passes,
  unweakened — including the bidirectional Leitner interval check and the PR #105
  link-assembly invariant.
- **SC-006**: With the docs requirements **not** installed, `pytest` passes, with
  the docs-build tests reported as skipped and naming what to install.
- **SC-007**: The deployed site serves `docs/index.html` at the root
  byte-identical to the repository copy, serves every relative link that page
  makes, and serves the documentation under a sub-path reachable from it in one
  click.
- **SC-008**: On a 375 px-wide viewport every documentation page is readable
  without horizontal scrolling, and no reading text renders below 15 px.
- **SC-009**: `lernkarten build` and `lernkarten check cards/example.yaml` run
  unchanged in an environment where no documentation dependency is installed.
- **SC-010**: The four pre-PR gates stay green and the pre-PR checklist has the
  same number of commands as before.

## Assumptions

- The user is on Python 3.12+; the *reader* of the site needs only a browser.
- The published site is served by GitHub Pages from `pages.yml`. No custom
  domain, no search backend, no versioned documentation trees for old releases.
- Documentation search is out of scope for 012. Django, pandas and numpy all have
  it, and `pydata-sphinx-theme` ships a client-side search — turning it on is a
  later, cheap addition once there is enough content to search.
- Localisation is out of scope: the site is English (constitution XIII), even
  though the user wrote the request in German.
- Intersphinx (cross-project references) is not used in 012; if it is ever added,
  it must not make the build require the network.
- `docs/testing.md` and `docs/design.md` are contributor documentation and go into
  the contributing area rather than being hidden — the user explicitly chose
  migrating everything over a user-docs-only site.
- No new corpus and no real subject matter is introduced; anything a page needs by
  way of example comes from the invented demo project (constitution VII).
- Existing behaviour relied on: `scripts/check_docs.py` already walks relative
  Markdown links and already reads `docs/leitner.html`, so both keep working
  against files that have not moved.

## Follow-on features

Recorded here so 013 and 014 can be specified later without re-deciding anything.
**No spec files exist for them yet.**

### 013 — Skill & CLI reference

The generated reference: one entry per skill and per `lernkarten` subcommand, an
overview page, and checked cross-references between them.

- **No existing tool does this.** PyPI and GitHub were searched: there is no
  Sphinx extension — and no MkDocs plugin — that documents Agent Skills /
  `SKILL.md` files. Every hit was the inverse: skills that teach an agent to *use*
  Sphinx. So 013 writes one.
- **Metadata goes in `metadata.docs` inside the `SKILL.md` frontmatter, not in
  new top-level keys.** The Agent Skills standard allows exactly five top-level
  frontmatter keys — `compatibility`, `description`, `license`, `metadata`,
  `name` — and *rejects* unknown ones, hard enough that it also rejects Claude
  Code's own extended fields. Evidence: `github.com/anthropics/claude-code` issue
  #25380, which quotes the validator error `Attribute 'allowed-tools' is not
  supported in skill files. Supported: compatibility, description, license,
  metadata, name.` `metadata` is a free-form map the standard provides for
  exactly this purpose. This matters concretely because this repository ships as
  a Claude Code plugin marketplace.
- **Candidate `metadata.docs` keys**, to be validated in 013 and not fixed now:
  `summary`, `reads`, `writes`, `after`, `before`. `arguments` and
  `argument-hint` already exist as standard fields and should be read from there
  rather than duplicated.
- **The CLI half is free**: `sphinx-argparse` (0.5.2, actively maintained,
  Python >= 3.10, Sphinx >= 5.1) reads the existing `argparse` parsers in
  `scripts/build_pdf.py`, `scripts/cardid.py`, `scripts/figures.py` and others.
- **The extension is built inside this repository, with a planned extraction.** It
  lives in its own directory, imports nothing from lernkarten (enforced by a test,
  not by intent), and has its own tests. The extraction trigger is written down
  now: once the docs site is live and the `metadata.docs` schema has gone one
  release without changing, it is extracted into a standalone package.
  `sphinx-agent-skills` and `sphinx-skills` are both free on PyPI (verified via
  the PyPI JSON API). Rationale for not starting a separate repository today: the
  schema is the real public contract and it has zero validated design so far;
  lernkarten is its first and only consumer and has to shake it out first.
- **A concrete success criterion for 013**: the pipeline order and its file
  mapping is currently hand-maintained in at least four places — `CLAUDE.md:3`,
  two README image alt texts, `docs/workflow.md:9`, plus `docs/index.html`.
  Generating it from `metadata.docs` collapses those to one source.
- **Deferred from 012**: how much of a `SKILL.md` becomes a reference entry — the
  `metadata.docs` block only, or metadata plus rendered sections of the prose
  body. This was FR-004 in the pre-split spec and is 013's to answer.

### 014 — Tutorial & topic pages

The Django-style tutorial and the pandas-style topic pages, written against the
foundation 012 ships and cross-linked into the reference 013 generates.

- The **tutorial** walks the pipeline end to end in order, marks
  `/learning-goal` and `/research-gaps` as optional, and links every command it
  names into its reference entry. `docs/workflow.md` — migrated by 012 — is its
  raw material.
- The **topic pages** explain a theme across several commands without restating
  their argument tables, the way pandas' "Visualization" page does.
- **Topic-page candidate set the user has seen, not chosen yet**: printing &
  grids; card style and Typst markup; the Leitner box; the four file formats;
  learning goals & gaps; use without Claude Code.
- **Deferred from 012**: which topic pages ship. This was FR-015 in the pre-split
  spec and is 014's to answer.
